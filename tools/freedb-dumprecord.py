#!/usr/bin/env python

import os
import sys
from namingmuse import providers
from namingmuse.cddb import CDDBP
from namingmuse.filepath import FilePath
from namingmuse.musexceptions import *
from namingmuse.providers import LocalAlbumInfo

if len(sys.argv) < 2:
    sys.exit("usage: %s <album>" % sys.argv[0])
    sys.exit(1)
    
dirname = sys.argv[1]

fpath = FilePath(dirname)
try:
    localalbum = LocalAlbumInfo(fpath)
except NoFilesException, e:
    print e
    sys.exit(1)
    
albuminfo = providers.getRemoteAlbumInfo(localalbum)
if not albuminfo:
    sys.exit("not tagged")

cddb = CDDBP()
cddb.encoding = sys.stdout.encoding
albuminfo.setCDDBConnection(cddb)
title = albuminfo.title

#filename = title + ".cddb"
filename = "%s %s.cddb" % (albuminfo.freedbgenre, albuminfo.freedbdiscid)
fd = file(filename, "w")
fd.write(albuminfo.freedbrecord.encode('UTF-8'))
fd.close()
print "Wrote " + filename
print "This filename is needed when submitting with freedb-submit.py"
