#!/usr/bin/env python

import commands
import os, re, sys
import time
from optparse import OptionParser

STDIN_FILENO = 1
knownfiletypes = (".mp3", ".ogg", ".flac")

def getoutputv(path, args):
    flist = []
    pread, pwrite = os.pipe()
    childpid = os.fork()
    if not childpid:
        os.dup2(pwrite, STDIN_FILENO)
        os.execv(path, ['locate'] + args)
        os.close(pwrite)
    else:
        os.close(pwrite)
        fread = os.fdopen(pread)
        data = fread.read()
        fread.close()
        return data

def locatealbum(args):
    flist = getoutputv("/usr/bin/locate", args)
    flist = flist.split("\n")

    albumlist = []
    for filename in flist:
        ext = os.path.splitext(filename)[1]
        if ext in knownfiletypes:
            albumtitle = os.path.dirname(filename)
            albumlist.append(albumtitle)

    albumlist.sort()
    oldalbum = ""
    for i in range(len(albumlist) - 1, 0, -1):
        if albumlist[i] == albumlist[i - 1]:
            del albumlist[i]

    return albumlist

op = OptionParser()
op.add_option("-p", 
              "--path",
              action = "store_true",
              help = "print full album paths")
op.add_option("-a",
              "--artist",
              action = "store_true",
              help = "filter by artist")
op.add_option("-t",
              "--title",
              action = "store_true",
              help = "filter by title")
op.add_option("-I", 
              "--case-sensitive",
              action = "store_true",
              help = "be case sensitive (not default)")
options, args = op.parse_args()

if len(args) == 0:
    op.print_help()
    sys.exit(1)

locateargs = args
if not options.case_sensitive:
    locateargs += ['-i']
albumlist = locatealbum(locateargs)

def albumfilter(artist, title, args = args, options = options):
    if not options.case_sensitive:
        search = args[0].lower()
        artist = artist.lower()
        title = title.lower()
    if options.artist:
        return not search in artist
    if options.title:
        return not search in title
    return False

for album in albumlist:
    artist = os.path.basename(os.path.dirname(album))
    title = os.path.basename(album)
    if albumfilter(artist, title):
        continue
    if options.path:
        print album
    else:
        print "%s - %s" % (artist, title)
