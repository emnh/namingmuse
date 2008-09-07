"""A module for renaming and setting tags on music albums 
using the online music database freedb to retrieve the
information.
"""

import os
import shutil
import tempfile
import trackorder

from difflib import SequenceMatcher
import tagpy
from tagpy import id3v2
import tagpy.mpeg

import policy
#import providers
from cddb import *
from constants import *
from filepath import FilePath
from musexceptions import *
from terminal import colorize
from providers import LocalAlbumInfo

DEBUG = os.getenv('DEBUG')

def distwrap(a, b):
    "Wraps a string distance function"
    a, b = a.lower(), b.lower()
    isjunk = lambda x: not x.islower()
    rat = SequenceMatcher(isjunk, a, b).ratio()
    return 1.0 - rat

def namebinder_strapprox_time(filelist, album, encoding):
    '''Bind tracks to filelist by a function of string distance
       and playlength offset. I'm not sure what the best
       function is, or what the magic numbers are. We'll
       just have to play with it until it is good.
    '''
    tracks = album.tracks
    newtracks = []
    for i in range(0, len(filelist)):
        from namingmuse.providers import local
        filePlayLength = local.getIntLength(filelist[i])
        file = filelist[i].getName(True)
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

def namebinder_strapprox(filelist, album, encoding):
    "Bind tracks to filelist by string approximation"
    tracks = album.tracks
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

def namebinder_trackorder(filelist, album, encoding):
    "Bind tracks to filelist by track order"
    tracks = album.tracks
    tracks.sort(lambda a, b:cmp(a.number, b.number))
    return tracks

def namebinder_manual(filelist, album, encoding):
    tracks = album.tracks

    tracks = trackorder.display(filelist, album, encoding)
    
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
    'filenames': namebinder_strapprox,
    'manual': namebinder_manual
    }
    if options.namebinder:
        if bindfunctions.has_key(options.namebinder):
            return bindfunctions[options.namebinder]
        else:
            raise NamingMuseError("Error: invalid namebinder: %s" % options.namebinder)
    
    for i, filename in enumerate(filelist):
        if not unicode(i+1) in unicode(filename):
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

    localalbum = LocalAlbumInfo(albumdir)
    filelist = localalbum.getfilelist(options.sysencoding)

    namebinder = get_namebinder(options, filelist)
    
    tracks = namebinder(filelist, album, options.sysencoding)
    if not sortedcmp(tracks, album.tracks):
        options.dryrun = True
        print NamingMuseError("binding was not exact, forcing dry run")

    print "Tagging album: %s, %s - %s, %s.\n" % \
          (album.year, album.artist, album.title, album.genre)

    # Process files
    renamealbum = True

    renameTempDir = FilePath(albumdir, 'rename-tmp')

    if renameTempDir.exists():
        raise NamingMuseError('%s exists!' % renameTempDir)

    renameTempDir.mkdir()

    # a list of tuples (from, to)
    # we use temporary renames to avoid filename collision on filename swaps
    # this holds the list of final renames to be executed
    finalrenames = []

    # a list of tuples (from, to)
    # used to rollback renames in case of error
    rollback = []

    renamesign = "->"
    rollbacksign = '<-'
    if options.tagonly:
        renamesign = "-tag->"
    if options.dryrun:
        renamesign = "-dry->" 

    try:
        for i in range(0, len(filelist)):
            fpath = filelist[i]
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

            tofile = policy.genfilename(filelist[i], album, track)
            tofile = tofile.encode(options.sysencoding)
            totmpfile = FilePath(renameTempDir, tofile, encoding=options.sysencoding)
            tofinalfile = FilePath(albumdir, tofile, encoding=options.sysencoding)
        
            # Tag and rename file
            print fpath.getName()
            print "\t", colorize(renamesign), tofinalfile.getName()

            if not options.dryrun:

                # Tag file

                #preserve stat
                fd = tempfile.NamedTemporaryFile()
                tmpfilename = fd.name
                shutil.copystat(str(fpath), tmpfilename)
                
                # tag the file
                tagfile(fpath, album, track, options)

                # restore filestat
                shutil.copystat(tmpfilename, str(fpath))

                # deletes tempfile
                fd.close()

                # Rename file to temporary name
                
                if not options.tagonly:
                    if totmpfile.exists():
                        raise NamingMuseError('tried to rename file over existing: %s' % str(totmpfile))
                    if fpath != totmpfile:
                        fpath.rename(totmpfile)
                        rollback.append((fpath, totmpfile))
                        finalrenames.append((totmpfile, tofinalfile))

    except Exception, e:
        print
        print colorize('Error: an error occurred. rolling back %d renames.' % len(rollback))
        for frompath, topath in reversed(rollback):
            print frompath.getName()
            print "\t", colorize(rollbacksign), topath.getName()
            topath.rename(frompath)
        renameTempDir.rmdir()
        raise e

    # Rename files to final names
    for frompath, topath in finalrenames:
        frompath.rename(topath)
    renameTempDir.rmdir()
                        
    # Get new albumdir name
    newalbum = policy.genalbumdirname(albumdir, album)
    newalbum = newalbum.encode(options.sysencoding)
    artistdir = ""
    # Check if parent dir name matches fairly well with
    # artistname. If it does, we ignore options.artistdir
    parent = albumdir.getParent().getName()
    artistdirdiff = distwrap(parent, album.artist.encode(options.sysencoding))
    if DEBUG: print "Distance between %s and %s is : %s" \
            %(parent, album.artist, artistdirdiff)
    needartistdirmove = options.artistdir and \
            (artistdirdiff > 0.25) #XXX sane value?
    if needartistdirmove:
        newalbumdir = FilePath(albumdir.getParent(), album.artist.encode(options.sysencoding), newalbum, encoding=options.sysencoding)
    else:
        newalbumdir = FilePath(albumdir.getParent(), newalbum, encoding=options.sysencoding)

    # Make parent directory of albumdir if needed
    parent = str(newalbumdir.getParent())
    if not os.path.isdir(parent):
        os.mkdir(parent)

    # Rename album (if no "manual" mp3 files in that dir)
    rollbacksign = '<-'
    renamesign = "->"
    if options.dryrun or options.tagonly:
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
    if needartistdirmove:
        print os.path.join(unicode(album.artist), unicode(newalbumdir.getName()))
    else:
        print newalbumdir.getName()

def tagfile(fpath, album, track, options):
    """ Tag the file with metadata """

    if not hasattr(tagpy.FileRef, 'create'):
        print 'warning: using generic tagging. upgrade to tagpy 0.94.5 or later.'
        fileref = tagpy.FileRef(str(fpath))
        tag = fileref.tag()
        tag.year = album.year
        tag.genre = album.genre
        tag.artist = track.artist
        tag.album = album.title
        tag.title = track.title
        tag.track = track.number
        #TODO comment
        #tag.setComment(comment)
        return fileref.save()

    if fpath.getFileType() == 'mp3':
        #fileref = tagpy.FileRef(str(fpath))
        fileref = tagpy.mpeg.File(str(fpath))

        hadID3v2Tag = fileref.ID3v2Tag()
       
        # Preserve old idv1 comments
        oldcomment = None
        if not hadID3v2Tag:
            id1tag = fileref.ID3v1Tag()
            if id1tag and not id1tag.isEmpty():
                oldcomment = id1tag.comment
                if oldcomment == "":
                    oldcomment = None

        # strip id3v1tag, bool freeMemory = False 
        fileref.strip(tagpy.mpeg.TagTypes.ID3v1)

        ## Have to make new fileref, since the old one still contains an ID3v1
        ## tag (in memory) which we do not want to merge into our new tag
        ## TODO: Is this true for new bindings?
        #del fileref
        #fileref = tagpy.mpeg.File(str(fpath))

        tag = fileref.ID3v2Tag(True)

        # Insert old id3v1 comment in id3v2tag
        if oldcomment:
            cf = id3v2.CommentsFrame()
            cf.setText(oldcomment)
            tag.addFrame(cf)
        
        
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

        if 'UTF' in options.tagencoding.upper():
            tagpyenc = tagpy.StringType.UTF8
        else:
            tagpyenc = tagpy.StringType.Latin1
        id3v2.FrameFactory.instance().setDefaultTextEncoding(tagpyenc)

        # append namingmuse footprint
        for key, text in framedict.items():
            tag.removeFrames(key)
            if not text == "":
                #if isinstance(text, unicode):
                #    print 'uni', text
                #    text = text.encode(options.tagencoding) #,'ignore')
                #else:
                #    print 'not uni', text
                tf = id3v2.TextIdentificationFrame(key, tagpyenc)
                tf.setText(text)
                tag.addFrame(tf)

        retval = fileref.save(tagpy.mpeg.TagTypes.ID3v2)
        if not retval:
            print NamingMuseWarning('Failed to save tag in %s' % fpath)
        return retval

    elif fpath.getFileType() == 'ogg':
        fileref = tagpy.ogg.vorbis.File(str(fpath))
        tag = fileref.tag()
        
        # Clean old comment
        if 'namingmuse' in tag.comment:
            tag.removeField('DESCRIPTION')

        oggencoding = 'UTF-8'
        fields = {
            'ALBUM': album.title,
            'ARTIST': track.artist,
            'DATE': str(album.year),
            'GENRE': album.genre,
            'TITLE': track.title,
            'TRACKNUMBER': str(track.number)
        }
        footprintdict = album.footprint()
        footprintdict['TNMU'] = TAGVER
        fields.update(footprintdict)
        for key, value in fields.items():
            key = key.encode(oggencoding)
            value = value.encode(oggencoding)
            tag.addField(key, value, True) # replace = True
        fileref.save()

    elif fpath.getFileType() == 'mpc':
        raise Exception("Not converted to new code yet")
        fileref = MPCFile(str(fpath))
        tag = fileref.APETag(True) # create = True
        ape_encoding = 'UTF-8'
        fields = {
            'ALBUM': album.title,
            'ARTIST': track.artist,
            'GENRE': album.genre,
            'TITLE': track.title,
            'TRACK': str(track.number),
            'YEAR': str(album.year)
        }
        footprintdict = album.footprint()
        footprintdict['TNMU'] = TAGVER
        fields.update(footprintdict)
        for key, value in fields.items():
            key = key.decode(album.encoding).encode(ape_encoding)
            value = value.decode(album.encoding).encode(ape_encoding)
            tag.addValue(key, value, True) # replace = True
        fileref.save()
        
    else:
        fileref = tag.pyFileRef(str(fpath))
        tag = fileref.tag()
        tag.year = album.year
        tag.genre = album.genre
        tag.artist = track.artist
        tag.album = album.title
        tag.title = track.title
        tag.track = track.number
        #TODO comment
        #tag.setComment(comment)
        fileref.save()

