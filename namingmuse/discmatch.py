import re, sys, os, string
import albumtag, terminal, exceptions
from cddb import *

QUERY_EXACT = 200
QUERY_NONE = 202
QUERY_MULTIPLE = 211
QUERY_MULTIPLE_EXACT = 210 # protocol 4
READ_OK = 210 # deleteme
DEBUG = False

class DiscMatch:
    """A module for tagging and renaming files.
    It generates a discid from album toc to acquire
    matching metainfo for an album from freedb.
    """
    def __init__(self):
        self.cddb = CDDBP()
        if DEBUG:
            print "Connecting to CDDB server"
        self.cddb.connect()

    def printTOC(filelist):
        'print nicely formatted toc, mostly for debugging'
        toc = files2discid(filelist)
        discid,filect,framelist,totsecs = toc[0],toc[1],toc[2:-1],toc[-1]
        print "cddbid: %08x" % discid
        print "filecount: %s" % filect
        print "album length: %us = %um %us" % (totsecs, totsecs / 60, totsecs % 60)
        oldlength = 0
        framelist.append(totsecs * 75)
        for i in range(len(framelist)):
            frameidx = framelist[i]
            if i == 0:
                filen = "lead in"
                length = frameidx / 75 - oldlength
            else:
                filep = filelist[i - 1]
                length = frameidx / 75 - oldlength
                #length = albumtag.getlength(filen)
            print "length: %4us = %2um %2us, frameidx: %8u: %s" % \
                (length, length / 60, length % 60, framelist[i], str(filep))
            oldlength += length
        print "nb! last frameidx not sent to server (just totsecs * 75)"

    def cddb_sum(n):
        ret = 0
        
        while n > 0:
            ret = ret + (n % 10)
            n = n / 10

        return ret

    def files2discid(filelist):
        """Calculate discid from an _ordered_ set of files
           Supported filetypes are those supported by TagLib"""

        filect = len(filelist)
        leadin = 2
        checksum = DiscMatch.cddb_sum(leadin)  # sum leadin too
        totalsecs = leadin
        framelist = []

        roundsecs = lambda x: int(x + 0.5)

        floatrest = 0
        for filep in filelist:
            secs = albumtag.getIntLength(filep)
            #secs = albumtag.getFloatLength(filep)
            if type(secs) is int:
                # i'm pretty confident this is the correct way to calculate checksum
                # because it seems to be what both the freedb reference implementation
                # does for CD and the "entagged" application does for MP3
                # but i'm not sure whether it works best in practice
                # alternatives: secs, totalsecs[x]
                checksum += DiscMatch.cddb_sum(totalsecs)
            elif type(secs) is float:
                floatrest += secs - roundsecs(secs)
                checksum += DiscMatch.cddb_sum(roundsecs(secs))
                
            # on CDs an audio frame is 1/75 of a second
            # the framelist contains the offset of the songs on a CD,
            # measured in frames
            framelist.append(int(totalsecs * 75))
            totalsecs += secs

        # this is what the freedb reference implementation does
        # in practice it doesn't seem to make a big difference
        totalsecs -= leadin

        if type(totalsecs) is float:
            totalsecs = roundsecs(totalsecs)

        # the checksum is a 32bit integer structured as follows
        # first byte: sum(all digits in all song lengths(seconds)) mod 255
        # this is the one that is hardest to get right
        # second and third byte: total length of all songs (no leadin, no leadout)
        # fourth byte: the number of songs

        discid = (long((checksum % 0xFF)) << 24 | totalsecs << 8 | filect)
        if DEBUG:
            print "floatrest: %f" % floatrest
            print "cddbid: %08x" % discid

        return [discid, filect] + framelist + [totalsecs]

    printTOC = staticmethod(printTOC)
    cddb_sum = staticmethod(cddb_sum)
    files2discid = staticmethod(files2discid)

    def freedbTOCMatchAlbums(self, query):
        """Search freedb for album matches for music files in
           an album(directory) in track order, using discid
           calculation."""
        
        if query:
            query_stat,query_info = self.cddb.query(query)
            if query_stat == QUERY_MULTIPLE:
                statusmsg = "multiple matches." 
            elif query_stat == QUERY_MULTIPLE_EXACT:
                # this happens mostly on albums with very few songs
                statusmsg = "multiple exact matches"
            elif query_stat == QUERY_EXACT: 
                statusmsg = "exact match!"
                pass
            elif query_stat == QUERY_NONE:
                statusmsg = "no matches!"
                query_info = []
            else:
                raise NotImplementedError("Unknown freedb status code: %d" % query_stat)
            albums = query_info
            for album in albums:
                album["title"] = re.sub("\s+", " ", album["title"])
            return (statusmsg, query_info)
        else:
            return (None, None)
