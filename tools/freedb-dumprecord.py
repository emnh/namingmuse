#!/usr/bin/env python

import os, re, sys
from namingmuse.filepath import FilePath
from namingmuse.albumtag import *
from namingmuse.cddb import CDDBP

if len(sys.argv) < 2:
    sys.exit("usage: %s <album>" % sys.argv[0])
    sys.exit(1)
    
dirname = sys.argv[1]

fpath = FilePath(dirname)
filelist = getfilelist(fpath)
if len(filelist) == 0:
    sys.exit("no files")
albuminfo = getNmuseTag(filelist)
if not albuminfo:
    sys.exit("not tagged")

cddb = CDDBP()
cddb.encoding = sys.stdout.encoding
albuminfo.setCDDBConnection(cddb)
title = albuminfo.title

#filename = title + ".cddb"
filename = "%s %s.cddb" % (albuminfo.freedbgenre, albuminfo.freedbdiscid)
fd = file(filename, "w")
fd.write(albuminfo.freedbrecord)
fd.close()
print "Wrote " + filename
print "This filename is needed when submitting with freedb-submit.py"
