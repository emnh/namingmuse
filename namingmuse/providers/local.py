#!/usr/bin/env python
'Classes for getting metainfo from local albums.'

import os
import re
import sys
import tagpy
import tagpy.mpeg
import tagpy.ogg.vorbis
from tagpy import id3v1
from tagpy import id3v2
from tagpy import ogg
from tagpy import ape
from tagpy import flac
from tagpy import mpc
from tagpy import _tagpy
import tagpy.ogg.flac

from namingmuse.albuminfo import *
from namingmuse.filepath import FilePath

def decodeFrame(tag, getfield):
    fval = ''
    if isinstance(tag, id3v2.Tag):
        framelistmap = tag.frameListMap()
        if getfield in framelistmap:
            frame = framelistmap[getfield][0]
            if frame.textEncoding() == tagpy.StringType.UTF8:
                fval = frame.toString().decode('UTF-8')
            elif frame.textEncoding() == tagpy.StringType.Latin1:
                fval = frame.toString().decode('ISO-8859-15')
    elif isinstance(tag, ogg.XiphComment):
        fields = tag.fieldListMap()
        if getfield in fields:
            frame = fields[getfield][0]
            # Xiph is always UTF-8
            fval = str(frame).decode('UTF-8')
    elif isinstance(tag, ape.Tag):
        fields = tag.itemListMap()
        if getfield in fields:
            stlist = fields[getfield].toStringList()
            if len(stlist) > 0:
                frame = stlist[0]
                # APE is always UTF-8
                fval = str(frame).decode('UTF-8')
    # XXX: replace _tagpy.id3v1_Tag by good name once available
    elif isinstance(tag, _tagpy.id3v1_Tag): 
        # this function is only used for fingerprint
        # fingerprint is not supported in ID3v1
        pass
        #if funcname:
        #    # ID3v1 is always ISO-8859-1
        #    fval = str(getattr(tag, funcname)())
        #    if isinstance(fval, basestring):
        #        fval = fval.decode('ISO-8859-1')
    else:
        raise NamingMuseError("unsupported tag: " + str(tag))
            
    return fval

class LocalTrackInfo(TrackInfo):

    _readingtag = False
    _gettingPlayLength = False
    _tag = None
    _gotPlayLength = False

    def __init__(self, fpath):
        super(LocalTrackInfo, self).__init__()
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
            fpath = str(self.fpath)

            if fpath.lower().endswith('mp3'):
                fileref = tagpy.mpeg.File(fpath)
                tag = fileref.ID3v2Tag()
                if not tag:
                    tag = fileref.ID3v1Tag()
            elif fpath.lower().endswith('ogg'):
                fileref = tagpy.ogg.vorbis.File(fpath)
                tag = fileref.tag()
            elif fpath.lower().endswith('flac'):
                fileref = flac.File(fpath)
                tag = fileref.xiphComment()
            elif fpath.lower().endswith('mpc'):
                fileref = mpc.File(fpath)
                tag = fileref.APETag()
            else:
                fileref = tagpy.FileRef(fpath)
                tag = fileref.tag()

            #fileref = tagpy.FileRef(fpath)
            #tag = fileref.tag()

            if not tag or tag.isEmpty():
                return None

            self._fileref = fileref # must save, or destroys tag
            self._tag = tag

        self.artist = self._tag.artist
        self.title = self._tag.title
        self.number = self._tag.track
        return tag

    def _getLength(self):
        return getIntLength(self.fpath)
        
    playLength = property(_getLength)


def getIntLength(fpath):
    "Get length of a music file via tagpy"
    filename = str(fpath)
    #tagfile = TagLib.FileRef(filename, True, TagLib.AudioProperties.Accurate)
    tagfile = tagpy.FileRef(filename)
    audioproperties = tagfile.audioProperties()
    
    if not audioproperties:
        raise NamingMuseError("failed to get audioproperties: broken file?")
        
    length = audioproperties.length
    
    # XXX: try various fallback methods
    if length == 0:
        print NamingMuseWarning("using fallback: getMP3Length(%s)" % filename)
        if fpath.getExt().lower() == ".mp3":
            length = getMP3Length(filename)

    # raise exception; or discid generation will fail
    # and user doesn't know why
    if length == 0:
        raise NamingMuseError("taglib audioproperties " \
            "failed to get length of: %s" % filename)

    return length

def getMP3Length(filename):
    mp3info = "/usr/bin/mp3info"
    strlength = "0"
    if os.access(mp3info, os.X_OK):
        pread,pwrite = os.pipe()
        childid = os.fork()
        if childid:
            os.waitpid(childid, 0)
        else:
            os.dup2(pwrite, sys.stdout.fileno())
            args = [ "mp3info" ]
            args.append("-F")
            args.append('-p%S\n')
            args.append(filename)
            os.execv(mp3info, args)
        pread = os.fdopen(pread)
        strlength = pread.readline()
        pread.close()
    try:
        strlength = int(strlength)
    except:
        return 0
    return strlength
                    
class LocalAlbumInfo(AlbumInfo):

    _readtagshort = False
    _readtaglong = False
    
    def __getattribute__(self, name):
        if name in ('year', 'genre', 'title', 'tagprovider', 'footprint'):
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
        self.albumdir = albumdir
        filelist = self.getfilelist()
        if len(filelist) == 0:
            raise NoFilesException("Warning: %s contains no music files !" \
                    %albumdir)
        for fpath in filelist:
            tr = LocalTrackInfo(fpath)
            self.tracks.append(tr)

    def _readTagShort(self):
        'Uses tag from first track to get year, genre and title'
        # assume all tracks have same album info
        tag = self.tracks[0].readTag()
        if not tag: return
        self.year = tag.year
        self.genre =  tag.genre
        self.title = tag.album
        tagprovider = ""
        def tagValue(key):
            ret = decodeFrame(tag, key)
            return ret
        self.tagValue = tagValue
        tagprovider = tagValue('TTPR')
        if not tagprovider or tagprovider == '':
            tagprovider = 'local'
        self.tagprovider = tagprovider

    def _readTagLong(self):
        'Uses tag from all tracks to get artist/isVarious'
        # Check artist on all tracks; if they aren't all equal use Various
        tag = self.tracks[0].readTag()
        if not tag: return
        oldartist = tag.artist
        self.artist = oldartist
        self.isVarious = False
        for track in self.tracks:
            tag = track.readTag()
            artist = tag.artist
            if artist != oldartist:
                self.artist = "Various"
                self.isVarious = True
                break
            oldartist = artist

    def getfilelist(self, encoding='ascii'):
        """Get sorted list of files supported by taglib 
           from specified directory"""
        path = str(self.albumdir)
        rtypes = re.compile(r'\.((mp3)|(ogg)|(mpc)|(flac))$', re.I)
        if os.access(path, os.X_OK):
            filelist = filter(lambda x: rtypes.search(str(x)), os.listdir(path))
            filelist = map(lambda x: FilePath(path, x, encoding=encoding), filelist)
            filelist.sort()
            return filelist
        else:
            raise NamingMuseError('Read access denied to path: %s' %path)

    def footprint(self):
        footprint = {}
        footprint["TTPR"] = self.tagprovider
        return footprint

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: %s <album>" % sys.argv[0])
    l = LocalAlbumInfo(sys.argv[1])
    l.ignoreMissing(True)
    for i in l.tracks:
        i.ignoreMissing(True)
        print i.dump()
