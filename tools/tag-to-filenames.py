#!/usr/bin/env python

import os, re, sys
from namingmuse.provider import LocalAlbumInfo
from namingmuse.filepath import FilePath
from namingmuse.policy import genfilename,genalbumdirname
from namingmuse.terminal import colorize

if len(sys.argv) < 2:
    sys.exit(1)

dirname = sys.argv[1]
fp = FilePath(dirname)
album = LocalAlbumInfo(fp)

for track in album.tracks:
    fpath = track.fpath
    newfilename = genfilename(fpath, album, track)
    newfpath = fpath.getParent() + newfilename
    print fpath.getName()
    print "\t", colorize("->"), newfilename
    os.rename(str(fpath), unicode(newfpath))
