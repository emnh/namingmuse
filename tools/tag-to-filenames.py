#!/usr/bin/env python

import os, re, sys
from namingmuse.provider import LocalAlbumInfo
from namingmuse.filepath import FilePath
from namingmuse.policy import genfilename,genalbumdirname
from namingmuse.terminal import colorize
from namingmuse.musexceptions import *

if len(sys.argv) < 2:
    sys.exit(1)

dirname = sys.argv[1]
fp = FilePath(dirname)
album = LocalAlbumInfo(fp)

for track in album.tracks:
    fpath = track.fpath
    try:
        newfilename = genfilename(fpath, album, track)
    except TagIncompleteWarning, e:
        print e, "\nCan't rename", fpath.getName()
        continue
    newfpath = fpath.getParent() + newfilename
    print fpath.getName()
    print "\t", colorize("->"), newfilename
    os.rename(str(fpath), unicode(newfpath))
