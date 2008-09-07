
import re

from namingmuse.albuminfo import *

class FreeDBAlbumInfo(AlbumInfo):
    'Provides metainfo from freedb.'
    tagprovider = "freedb"
    
    def __init__(self, cddb, genre, discid):
        '''
        Initialize FreeDBAlbumInfo.

        init(cddb, genre, discid)
        For binding to a server record.
        @param cddb a CDDBP protocol object for communicating with server
        @genre the cddb lookup genre
        @discid the cddb lookup id
        '''
        self.__freedbrecord = None
        self.__readingrecord = False
        self.__cddb = cddb
        self.__freedbgenre = genre
        self.__freedbdiscid  = discid

    def fromFootPrint(cls, localalbum):
        if localalbum.tagValue('TTPR') == cls.tagprovider:
            discid = localalbum.tagValue('TCID')
            genre  = localalbum.tagValue('TGID')
            self = cls(None, genre, discid)
            self.readFootPrint(localalbum)
            return self
        raise TypeError("invalid provider footprint (wrong class)")
    fromFootPrint = classmethod(fromFootPrint)

    def getRecord(self):
        if not self.__freedbrecord:
            self.initRecord()
        return self.__freedbrecord
    
    freedbrecord = property(getRecord)
    
    def getFreedbDiscID(self):
        return self.__freedbdiscid

    freedbdiscid = property(getFreedbDiscID)
    
    def getFreedbGenre(self):
        return self.__freedbgenre

    freedbgenre = property(getFreedbGenre)

    def setCDDBConnection(self, cddbobj):
        self.__cddb = cddbobj

    cddb = property(setCDDBConnection)

    def __getattribute__(self, name):
        if name in ("year", "genre", "artist", "title", "tracks"):
            # Read properties from freedb on demand
            if not self.__readingrecord and not self.__freedbrecord:
                self.__readingrecord = True
                self.initRecord()
                self.__readingrecord = False
        return super(FreeDBAlbumInfo, self).__getattribute__(name)
    
    def initRecord(self):
        if not self.__cddb:
            raise NamingMuseError("FreeDBAlbumInfo bug: missing cddb connection object")
        discid = self.__freedbdiscid
        genre = self.__freedbgenre
        if not (discid and genre):
            raise NamingMuseError("FreeDBAlbumInfo: requested lookup without genre and discid")
        freedbrecord = self.__cddb.getRecord(genre, discid)
        self.parseFreedbRecord(freedbrecord)
        
    def footprint(self):
        footprint = {
            'TTPR': self.tagprovider,
            'TCID': self.__freedbdiscid,
            'TGID': self.__freedbgenre
        }
        return footprint

    def parseFreedbRecord(self, freedbrecord):

        self.__freedbrecord = freedbrecord
        
        dbdict = {}
        linesep = "\r\n"
        lines = freedbrecord.split(linesep)[:-2]
        
        if not re.match("^# xmcd", lines[0]):
            raise NamingMuseError("invalid dbrecord signature: " + lines[0])

        # Convert freedb record to dictionary
        for line in lines:
            if not '#' == line[0]:
                key, value = line.split('=', 1)
                dbdict.setdefault(key, "")
                dbdict[key] += value

        # Set album fields from dbdict
        self.year = dbdict["DYEAR"]
        self.genre = dbdict["DGENRE"] # not limited to the 11 cddb genres
        if " / " in dbdict["DTITLE"]:
            self.artist, self.title = dbdict["DTITLE"].split(" / ", 1)
        else:
            self.title = self.artist = dbdict["DTITLE"]
            
        # Set track fields from dbdict
        secs = self.extractTrackLengths(freedbrecord)
        tracks = []
        self.isVarious = False
        for key, value in dbdict.items():
            if key.startswith("TTITLE"):
                number = key[len("TTITLE"):]
                title = value
                number = int(number)
                t = TrackInfo()
                t.number = number + 1
                t.playLength = secs[number]
                if " / " in title:
                    self.isVarious = True
                    t.artist, t.title = title.split(" / ", 1)
                else:
                    # inherit track artist from album
                    t.artist = self.artist
                    t.title = title
                tracks.append(t)
        self.tracks = tracks

    def extractTrackLengths(self, cddbrecord):
        'Parse cddb record and calculate track lengths in seconds'

        pattern = '''
        # Match the header
        \#\ Track\ frame\ offsets:\s*

        # Match all the frame lines
        ((?:\#\s*[0-9]*\s*)+)

        # Eat blank comment lines
        [\s\#]*

        # Match total length
        Disc\ length:\ ([0-9]+)
        '''
        
        match = re.search(pattern, cddbrecord, re.X)
        if match:
            framestub = match.group(1)
            totalsecs = int(match.group(2))
        else:
            print cddbrecord
            raise NamingMuseError("invalid freedb record: " + \
                                  "couldn't parse frame offsets")
        
        # Convert frame comments to python list
        frames = re.split("\s*#\s*", framestub)
        frames = [int(x) for x in frames if x != '']

        # Convert frame offsets to track playlengths
        secs = []
        for i in range(1, len(frames)):
            secs.append(int(round((frames[i] - frames[i - 1]) / 75.0)))
        secs.append(totalsecs - sum(secs)) # last song

        return secs
