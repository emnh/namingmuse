#!/usr/bin/env python
'Classes for getting metainfo from local albums.'

import os, re, sys
import TagLib

from albuminfo import *
from namingmuse.filepath import FilePath

# XXX: move somewhere? make better bindings to do this stuff?
def decodeFrame(tag, getfield):
    'Return unicode string (or int) representing the field'
    id3fields = [
    ('TDRC', 'year'), # int
    ('TCON', 'genre'),
    ('TPE1', 'artist'),
    ('TALB', 'albumtitle'),
    ('TIT2', 'tracktitle'),
    ('TRCK', 'number') # int
    ]
    xiphfields = [
    ('DATE', 'year'),
    ('GENRE', 'genre'),
    ('ARTIST', 'artist'),
    ('ALBUM', 'albumtitle'),
    ('TITLE', 'tracktitle'),
    ('TRACKNUMBER', 'number')
    ]
    id3dict = {}
    xiphdict = {}
    for tagfield, common_name in id3fields:
        id3dict[common_name] = tagfield
    for tagfield, common_name in xiphfields:
        xiphdict[common_name] = tagfield
    
    fval = ''
    if isinstance(tag, TagLib.ID3v2Tag):
        framelistmap = tag.frameListMap()
        tagfield = id3dict[getfield]
        if framelistmap.has_key(tagfield):
            frame = framelistmap[tagfield][0]
            frame = TagLib.TextIdentificationFrame(frame)
            if frame.textEncoding() == TagLib.String.UTF8:
                fval = str(frame).decode('UTF-8')
            elif frame.textEncoding() == TagLib.String.Latin1:
                fval = str(frame).decode('ISO-8859-1')
    elif isinstance(tag, TagLib.XiphComment):
        fields = tag.fieldListMap()
        tagfield = xiphdict[getfield]
        if fields.has_key(tagfield):
            frame = fields[tagfield][0]
            fval = str(frame).decode('UTF-8')
            
    if getfield == 'year':
        try:
            fval = int(fval)
        except ValueError:
            fval = 0
    elif getfield == 'number':
        try:
            fval = int(fval.split("/")[0])
        except ValueError:
            fval = 0
    
    return fval

class LocalTrackInfo(TrackInfo):

    _readingtag = False
    _tag = None

    def __init__(self, fpath):
        super(TrackInfo, self).__init__()
        if not os.access(str(fpath), os.R_OK):
            raise NamingMuseError('Read access denied to path: %s' % str(fpath))
        self.fpath = fpath
    
    def __getattribute__(self, name):
        if name in ('artist', 'title', 'number'):
            if not self._readingtag and not self._tag:
                self._readingtag = True
                self.readTag()
                self._readingtag = False
        return super(LocalTrackInfo, self).__getattribute__(name)

    def readTag(self):
        if self._tag:
            tag = self._tag
        else:    
            if self.fpath.getFileType() == "mp3":
                fileref = TagLib.MPEGFile(str(self.fpath))
                tag = fileref.ID3v2Tag()
                if not tag or tag.isEmpty():
                    return None
            elif self.fpath.getFileType() == "ogg":
                fileref = TagLib.VorbisFile(str(self.fpath))
                tag = fileref.tag()
                if not tag or tag.isEmpty():
                    return None
            self._fileref = fileref # must save, or destroys tag
            self._tag = tag

        self.artist = decodeFrame(tag, 'artist')
        self.title = decodeFrame(tag, 'tracktitle')
        self.number = decodeFrame(tag, 'number')
        # XXX: bind playLength property to getIntLength
        #      but move those functions over here first

        return tag
                    
class LocalAlbumInfo(AlbumInfo):

    tagprovider = 'local'
    _readtagshort = False
    _readtaglong = False
    
    def __getattribute__(self, name):
        if name in ('year', 'genre', 'title'):
            if not self._readtagshort:
                self._readtagshort = True
                self._readTagShort()
        if name in ('artist', 'isVarious'):
            if not self._readtaglong:
                self._readtaglong = True
                self._readTagLong()
        return super(LocalAlbumInfo, self).__getattribute__(name)

    def __init__(self, albumdir):
        super(LocalAlbumInfo, self).__init__()
        filelist = self.getfilelist(albumdir)
        for fpath in filelist:
            tr = LocalTrackInfo(fpath)
            self.tracks.append(tr)

    def _readTagShort(self):
        'Uses tag from first track to get year, genre and title'
        # assume all tracks have same album info
        tag = self.tracks[0].readTag()
        self.year = decodeFrame(tag, 'year')
        self.genre = decodeFrame(tag, 'genre')
        self.title = decodeFrame(tag, 'albumtitle')

    def _readTagLong(self):
        'Uses tag from all tracks to get artist/isVarious'
        # Check artist on all tracks; if they aren't all equal use Various
        tag = self.tracks[0].readTag()
        oldartist = decodeFrame(tag, 'artist')
        self.artist = oldartist
        self.isVarious = False
        for track in self.tracks:
            tag = track.readTag()
            artist = decodeFrame(tag, 'artist')
            if artist != oldartist:
                self.artist = "Various"
                self.isVarious = True
                break
            oldartist = artist

    def getfilelist(self, path):
        """Get sorted list of files supported by taglib 
           from specified directory"""
        path = str(path)
        rtypes = re.compile("\.(mp3)$|\.(ogg)$", re.I)
        if os.access(path, os.X_OK):
            filelist = filter(lambda x: rtypes.search(str(x)), os.listdir(path))
            filelist = map(lambda x: FilePath(path, x), filelist)
            filelist.sort()
            return filelist
        else:
            raise NamingMuseError('Read access denied to path: %s' %path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: %s <album>" % sys.argv[0])
    l = LocalAlbumInfo(sys.argv[1])
    l.ignoreMissing(True)
    for i in l.tracks:
        i.ignoreMissing(True)
        print i.dump()
