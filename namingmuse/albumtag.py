"""A module for renaming and setting tags on music albums 
using the online music database freedb to retrieve the
information.
"""

TAGVER = "0.03"

import difflib
import os,re,sys,string,shutil
import random
from TagLib import *
import policy
import tempfile
from terminal import colorize
from cddb import *
from string import lower
from difflib import SequenceMatcher
from filepath import FilePath
from albuminfo import *

from exceptions import *


DEBUG = False

# XXX: move
providers = {
"default": AlbumInfo,
"freedb": FreeDBAlbumInfo
}

def getNmuseTag(filelist):
    fpath = filelist[0]
    if fpath.getFileType() == "mp3":
        fileref = MPEGFile(str(fpath))
        tag = fileref.ID3v2Tag()
        if not tag or tag.isEmpty():
            return None
        framelistmap = tag.frameListMap()

        if framelistmap.has_key("TTPR"): #new school
            tagprovider = str(framelistmap["TTPR"][0])
            fdict = {}
            for frame in tag.frameList():
                key = str(frame.frameID())
                if key.startswith('T'):
                    fdict[key] = str(frame)
        else: #old school
            comms = framelistmap["COMM"]
            fdict = {}
            for comm in comms:
                cf = CommentsFrame(comm)
                key = cf.description()
                value = cf.text()
                fdict[key] = value
            if not fdict.has_key("namingmuse"):
                return None
            if fdict.has_key("tagprovider"):
                tagprovider = fdict["tagprovider"]
            else:
                tagprovider = "default"
        providerclass = providers[tagprovider]
        providerobj = providerclass(fdict)
        return providerobj
    return None

def getfilelist(path):
    """Get sorted list of files supported by taglib 
       from specified directory"""
    path = str(path)
    rtypes = re.compile("\.(mp3|ogg|flac)$", re.I)
    filelist = filter(lambda x: rtypes.search(str(x)), os.listdir(path))
    filelist = map(lambda x: FilePath(path, x), filelist)
    filelist.sort()
    return filelist

def getMP3Length(filename):
    mp3info = "/usr/bin/mp3info"
    strlength = "0"
    if os.access(mp3info, os.X_OK):
        pread,pwrite = os.pipe()
        childid = os.fork()
        if childid:
            os.waitpid(childid, 0)
        else:
            # set stdout to pwrite 
            os.dup2(pwrite, 1)
            args = [ "mp3info" ]
            args.append("-F")
            args.append('-p%S\n')
            args.append(filename)
            os.execv(mp3info, args)
        pread = os.fdopen(pread)
        strlength = pread.readline()
        pread.close()
    return int(strlength)

def getFloatLength(filename):
    #p = os.popen("/tmp/build/mp3info-0.8.4/playtime.sh " + filename)
    pread,pwrite = os.pipe()
    childid = os.fork()
    if childid:
        os.waitpid(childid, 0)
    else:
        os.dup2(pwrite, 1) #stdout
        os.execv("/tmp/build/mp3info-0.8.4/playtime.sh", ["playtime.sh", filename])
    pread = os.fdopen(pread)
    strlength = pread.readline()
    pread.close()
    return float(strlength)

def getIntLength(filename):
    "Get length of a music file via taglib"
    filename = str(filename)
    tagfile = FileRef(filename, True, AudioProperties.Accurate)
    audioproperties = tagfile.audioProperties()
    
    if not audioproperties:
        raise NamingMuseError("failed to get audioproperties: broken file?")
        
    length = audioproperties.length()
    
    # XXX: try various fallback methods
    if length == 0:
        print NamingMuseWarning("using fallback: getMP3Length(%s)" % filename)
        if string.lower(filename[-4:]) == ".mp3":
            length = getMP3Length(filename)

    # raise exception; or discid generation will fail
    # and user doesn't know why
    if length == 0: 
        raise NamingMuseError("taglib audioproperties " \
            "failed to get length of: %s" % filename)

    return length


def distwrap(a, b):
    "Wraps a string distance function"
    a, b = a.lower(), b.lower()
    isjunk = lambda x: not x in string.lowercase
    rat = SequenceMatcher(isjunk, a, b).ratio()
    return 1.0 - rat

def namebinder_strapprox_time(filelist, tracks):
    '''Bind tracks to filelist by a function of string distance
       and playlength offset. I'm not sure what the best
       function is, or what the magic numbers are. We'll
       just have to play with it until it is good.
    '''
    newtracks = []
    for i in range(0, len(filelist)):
        filePlayLength = getIntLength(filelist[i])
        file = filelist[i].getName()
        least = (distwrap(file, tracks[0].title), 0)
        for j in range(0, len(tracks)):
            
            # make a guess at title format
            if "-" in file:
                title = tracks[j].artist + " " + tracks[j].title
            else:
                title = tracks[j].title
            
            strdist = distwrap(file, title)
            timedist = abs(filePlayLength - tracks[j].playLength)
            if timedist < 5 or strdist < 0.3:
                # greatly favour close proximity matches
                dist = strdist / 10
            else:
                dist = strdist
            #print "dist: ", dist, file, title
            if dist < least[0]:
                least = (dist, j)
        newtracks.append(tracks[least[1]])
    return newtracks

def namebinder_strapprox(filelist, tracks):
    "Bind tracks to filelist by string approximation"
    newtracks = []
    for i in range(0, len(filelist)):
        file = filelist[i].getName()
        least = (distwrap(file, tracks[0].title), 0)
        for j in range(0, len(tracks)):
            title = tracks[j].title
            dist = distwrap(file, title)
            if dist < least[0]:
                least = (dist, j)
        newtracks.append(tracks[least[1]])
    return newtracks

def namebinder_trackorder(filelist, tracks):
    "Bind tracks to filelist by track order"
    tracks.sort(lambda a,b:cmp(a.number, b.number))
    return tracks

def sortedcmp(a, b):
    a = a[:]
    b = b[:]
    trackcmp = lambda x, y: cmp(x.number, y.number)
    a.sort(trackcmp)
    b.sort(trackcmp)
    return a == b

def tagfiles(albumdir, album, options, namebinder = namebinder_trackorder):
    '''Rename and tag files using freedb information for
       the specified album.'''

    # XXX: doesn't really belong here
    missing = album.validate()
    if len(missing) > 0:
        if options.strict:
            amiss = string.join(missing, ",")
            raise TagIncompleteWarning(amiss)
        else:
            for miss in missing:
                print TagIncompleteWarning(miss)
            print
    album.ignoreMissing(True)

    filelist = getfilelist(albumdir)
    tracks = namebinder(filelist, album.tracks)
    if not sortedcmp(tracks, album.tracks): 
        options.dryrun = True
        print NamingMuseError("binding was not exact, forcing dry run")

    print "Tagging album: %s, %s - %s, %s.\n" % \
          (album.year, album.artist, album.title, album.genre)

    todir = policy.genalbumdirname(albumdir, album)
    newalbumdir = FilePath(albumdir.getParent(), todir)

    # Process files
    longestfilename = max(map(lambda x: len(x), filelist))
    renamealbum = True

    for i in range(0, len(filelist)):
        fpath = filelist[i]
        ext = fpath.getExt()
        # XXX: move bug check to freedbalbuminfo parser

        #if album.isVarious:
        #    if not "/" in title and "-" in title:
        #        # workaround: this is a bug in the freedb entry
        #        # (according to submission guidelines)
        #        trackartist, title = title.split("-")
        #        print NamingMuseWarning("bugged database entry with - instead of /")
        #    else:
        #        trackartist, title = title.split("/")
        #    trackartist, title = trackartist.strip(), title.strip()
        #else:
        #    trackartist = albumartist
        track = tracks[i]

        tofile = policy.genfilename(fpath, album, track)
        tofile = FilePath(albumdir, tofile)
    
        # Tag and rename file
        renamesign = "->"
        if options.tagonly:
            renamesign = "-tag->"
        if options.dryrun:
            renamesign = "-dry->" 
        #if "manual" in comment:
        #   renamesign = "-skip->"
        #    renamealbum = False
        print fpath.getName().ljust(longestfilename)
        print "\t", colorize(renamesign), tofile.getName()
        if not options.dryrun:
            #preserve stat
            fd = tempfile.NamedTemporaryFile()
            tmpfilename = fd.name
            shutil.copystat(str(fpath), tmpfilename)
            
            # tag the file
            tagfile(fpath, album, track)
            # restore filestat
            shutil.copystat(tmpfilename, str(fpath))
            # deletes tempfile
            fd.close()
            if not options.tagonly:
                os.rename(str(fpath), str(tofile))
                        
    # Rename album (if no "manual" mp3 files in that dir)
    renamesign = (renamealbum and "->" or "-skip->")
    if renamealbum and options.dryrun: renamesign = "-dry->"
    if not (options.dryrun or options.tagonly) and renamealbum:
        os.rename(str(albumdir), str(newalbumdir))
        albumdir = newalbumdir
        if options.artistdir:
            artistdir = FilePath(albumdir.getParent(), album.artist)
            if not os.path.isdir(str(artistdir)):
                os.mkdir(str(artistdir))
            todir = artistdir + albumdir.getName()
            shutil.move(str(albumdir), str(todir))
    print "\n", albumdir.getName()
    print "\t", colorize(renamesign), todir

def tagfile(fpath, album, track):
    """ Tag the file with metadata """

    if fpath.getFileType() == 'mp3':
        fileref = MPEGFile(str(fpath))

        hadID3v2Tag = fileref.ID3v2Tag(False) and True
        tag = fileref.ID3v2Tag(True)
       
        # Preserve old idv1 comments
        oldcomment = None
        if not hadID3v2Tag:
            id1tag = fileref.ID3v1Tag(False)
            if id1tag and not id1tag.isEmpty():
                oldcomment = id1tag.comment()
                if oldcomment == "":
                    oldcomment = None
                if oldcomment and 'namingmuse' in oldcomment:
                    oldComment = None

        #strip id3v1tag, bool freeMemory = False 
        fileref.strip(MPEGFile.ID3v1,False)

        
        #fetch footprintdict
        footprintdict = album.footprint()
        # Add namingmuse tag with version
        footprintdict["TNMU"] = TAGVER 

        # Preserve ID3v2Tag comments other than our generated ones
        oldcommentlist = []
        for frame in tag.frameList():
            if frame.frameID() == "COMM":
                cf = CommentsFrame(frame)
                if not 'namingmuse' in cf.text() and not cf.description() in ["namingmuse", "genreid", "cddbid", "tagprovider"]:
                    newcf = CommentsFrame()
                    newcf.setDescription(cf.description())
                    newcf.setText(cf.text())
                    oldcommentlist.append(newcf)

        #remove old comment frames
        tag.removeFrames("COMM")

        # Add preserved ID3v2 comments 
        for frame in oldcommentlist:
            tag.addFrame(frame)
            
        # Insert old id3v1 comment in id3v2tag
        if oldcomment:
            cf = CommentsFrame()
            cf.setText(oldcomment)
            tag.addFrame(cf)

        framedict = {}
        framedict.update(footprintdict)
        del footprintdict
        framedict.update({
                "TDRC": str(album.year),
                "TCON": album.genre,
                "TPE1": track.artist,
                "TALB": album.title,
                "TIT2": track.title,
                "TRCK": "%s/%s" % (track.number, len(album.tracks))
                })
                    
        if 'UTF' in album.encoding.upper():
            taglibencoding = String.UTF8 
        else:
            taglibencoding = String.Latin1
        
        # append namingmuse footprint
        for key,text in framedict.items():
            tag.removeFrames(key)
            if not text == "":
                tf = TextIdentificationFrame(key, taglibencoding)
                tf.setText(text)
                tag.addFrame(tf)

        return fileref.save()
        
    else:
        fileref = FileRef(str(fpath))
        tag = fileref.tag()
        tag.setYear(album.year)
        tag.setGenre(album.genre)
        tag.setArtist(track.artist)
        tag.setAlbum(album.title)
        tag.setTitle(track.title)
        tag.setTrack(track.number)
        #TODO comment
        #tag.setComment(comment)
        fileref.save()

