"""A module for renaming and setting tags on music albums 
using the online music database freedb to retrieve the
information.
"""

import difflib
import os, re, sys, shutil
import random
from TagLib import * # get this from http://namingmuse.berlios.de
import policy
import tempfile
import provider

from difflib import SequenceMatcher

from terminal import colorize
from cddb import *
from filepath import FilePath
from constants import *
from musexceptions import *


DEBUG = False

def getNmuseTag(filelist):
    import types
    fpath = filelist[0]
    tagprovider, fdict = None, {}
    if fpath.getFileType() == "mp3":
        fileref = MPEGFile(str(fpath))
        tag = fileref.ID3v2Tag()
        if type(tag) == types.StringType:
            raise NamingMuseError("Error, old TagLib bindings: " + tag)
        if not tag or tag.isEmpty():
            return None
        framelistmap = tag.frameListMap()

        if framelistmap.has_key("TTPR"):
            tagprovider = str(framelistmap["TTPR"][0])
            for frame in tag.frameList():
                key = str(frame.frameID())
                if key.startswith('T'):
                    fdict[key] = str(frame)
    elif fpath.getFileType() == "ogg":
        fileref = VorbisFile(str(fpath))
        tag = fileref.tag()
        if type(tag) == types.StringType:
            raise NamingMuseError("Error, old TagLib bindings: " + tag)
        if not tag or tag.isEmpty():
            return None
        fields = tag.fieldListMap()
        if fields.has_key("TTPR"):
            tagprovider = str(fields["TTPR"][0])
            for fieldname, stringlist in fields.items():
                fieldname = str(fieldname)
                # Our fields are singletons
                if fieldname.startswith('T'):
                    fdict[fieldname] = str(stringlist[0])
    if tagprovider:
        providerclass = provider.lookup(tagprovider)
        providerobj = providerclass(fdict)
        return providerobj
    else:
        return None

# XXX: currently duplicate, make use of local provider
def getfilelist(path):
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
    try:
        strlength = int(strlength)
    except:
        return 0
    return strlength

def getIntLength(fpath):
    "Get length of a music file via taglib"
    filename = str(fpath)
    tagfile = FileRef(filename, True, AudioProperties.Accurate)
    audioproperties = tagfile.audioProperties()
    
    if not audioproperties:
        raise NamingMuseError("failed to get audioproperties: broken file?")
        
    length = audioproperties.length()
    
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


def distwrap(a, b):
    "Wraps a string distance function"
    a, b = a.lower(), b.lower()
    str
    isjunk = lambda x: not x.islower()
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
            if timedist < 2 or strdist < 0.3:
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

def get_namebinder(options, filelist):
    '''Automatically determine which namebinding algorithm to use,
    if one was not specified explicitly by the user.

    It checks if every track in the filelist has a tracknumber,
    and they are in sequence, without gaps. If so, it chooses 
    namebinder_trackorder. Else, namebinder_strapprox_time.
    '''

    bindfunctions = {
    'trackorder': namebinder_trackorder,
    'filenames+time': namebinder_strapprox_time,
    'filenames': namebinder_strapprox
    }
    if options.namebinder:
        if bindfunctions.has_key(options.namebinder):
            return bindfunctions[options.namebinder]
        else:
            raise NamingMuseError("Error: invalid namebinder: %s" % options.namebinder)
    
    for i, filename in enumerate(filelist):
        if not str(i+1) in str(filename):
            if DEBUG: print 'Using strapprox_time as namebinder'
            return namebinder_strapprox_time

    if DEBUG: print 'Using namebinder_trackorder as namebinder'
    return namebinder_trackorder

def tagfiles(albumdir, album, options):
    '''Rename and tag files using freedb information for
       the specified album.'''

    # XXX: doesn't really belong here
    missing = album.validate()
    if len(missing) > 0:
        if options.strict:
            amiss = ",".join(missing)
            raise TagIncompleteWarning(amiss)
        else:
            for miss in missing:
                print TagIncompleteWarning(miss)
            print
    album.ignoreMissing(True)

    filelist = getfilelist(albumdir)

    namebinder = get_namebinder(options, filelist)
    
    tracks = namebinder(filelist, album.tracks)
    if not sortedcmp(tracks, album.tracks): 
        options.dryrun = True
        print NamingMuseError("binding was not exact, forcing dry run")

    print "Tagging album: %s, %s - %s, %s.\n" % \
          (album.year, album.artist, album.title, album.genre)

    # Process files
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
        print fpath.getName()
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
                        
    # Get new albumdir name
    newalbum = policy.genalbumdirname(albumdir, album)
    artistdir = ""
    if options.artistdir:
        newalbumdir = FilePath(albumdir.getParent(), album.artist, newalbum)
    else:
        newalbumdir = FilePath(albumdir.getParent(), newalbum)

    # Make parent directory of albumdir if needed
    parent = newalbumdir.getParent()
    if not os.path.isdir(parent):
        os.mkdir(parent)

    # Rename album (if no "manual" mp3 files in that dir)
    renamesign = "->"
    if options.dryrun:
        renamesign = "-dry->"
    if not (options.dryrun or options.tagonly) and renamealbum \
        and str(albumdir) != str(newalbumdir):
        if os.path.exists(str(newalbumdir)):
            raise NamingMuseWarning("Directory already exists (dup album?): " +
                  str(newalbumdir))
        try:
            os.rename(str(albumdir), str(newalbumdir))
        except OSError, err:
            raise NamingMuseWarning(str(err))

    # Print rename message
    print "\n", albumdir.getName()
    print "\t", colorize(renamesign),
    if options.artistdir:
        print os.path.join(album.artist, newalbumdir.getName())
    else:
        print newalbumdir.getName()

def tagfile(fpath, album, track):
    """ Tag the file with metadata """

    if fpath.getFileType() == 'mp3':
        fileref = MPEGFile(str(fpath))

        hadID3v2Tag = fileref.ID3v2Tag(False) and True
       
        # Preserve old idv1 comments
        oldcomment = None
        if not hadID3v2Tag:
            id1tag = fileref.ID3v1Tag(False)
            if id1tag and not id1tag.isEmpty():
                oldcomment = id1tag.comment()
                if oldcomment == "":
                    oldcomment = None

        # strip id3v1tag, bool freeMemory = False 
        fileref.strip(MPEGFile.ID3v1, False)

        # Have to make new fileref, since the old one still contains an ID3v1
        # tag (in memory) which we do not want to merge into our new tag
        del fileref
        fileref = MPEGFile(str(fpath))

        tag = fileref.ID3v2Tag(True)

        # Insert old id3v1 comment in id3v2tag
        if oldcomment:
            cf = CommentsFrame()
            cf.setText(oldcomment)
            tag.addFrame(cf)
        
        if 'UTF' in album.encoding.upper():
            taglibencoding = String.UTF8 
        else:
            taglibencoding = String.Latin1
        
        # gather frame values
        framedict = {}
        footprintdict = album.footprint()
        footprintdict["TNMU"] = TAGVER 
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

        # append namingmuse footprint
        for key,text in framedict.items():
            tag.removeFrames(key)
            if not text == "":
                tf = TextIdentificationFrame(key, taglibencoding)
                tf.setText(text)
                tag.addFrame(tf)

        return fileref.save()
    elif fpath.getFileType() == 'ogg':
        fileref = VorbisFile(str(fpath))
        tag = fileref.tag()
        
        # Clean old comment
        if 'namingmuse' in tag.comment():
            tag.removeField("DESCRIPTION")

        oggencoding = 'UTF-8'
        fields = {
            "DATE": str(album.year),
            "GENRE": album.genre,
            "ARTIST": track.artist,
            "ALBUM": album.title,
            "TITLE": track.title,
            "TRACKNUMBER": str(track.number)
        }
        footprintdict = album.footprint()
        footprintdict["TNMU"] = TAGVER 
        fields.update(footprintdict)
        for key, value in fields.items():
            key = key.decode(album.encoding).encode(oggencoding)
            value = value.decode(album.encoding).encode(oggencoding)
            tag.addField(key, value, True) # replace = True
        fileref.save()
        
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

