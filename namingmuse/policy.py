""" A module for naming policies """

import os, re, sys, string

def genfilename(original, album, track):
    ext = original.getExt()
    if album.isVarious:
        # Track number first
        tofile = "%.2u %s - %s%s" % \
                (track.number, track.artist, track.title, ext)
    else:
        # Track number behind artist 
        tofile = "%s - %.2u %s%s" % \
                (track.artist, track.number, track.title, ext)
    tofile = tofile.replace("/", " ")
    return tofile

def genalbumdirname(original, album):
    if album.year != 0:
        newdirname = "%s %s" % (album.year, album.title)
    else:
        newdirname = "%s" % (album.title)
    newdirname = newdirname.replace("/", " ")
    return newdirname

# Overwrite global functions defined above with local ones
home = os.getenv("HOME")
homeconf = os.path.join(home, ".namingmuse")
modnamingpolicy = os.path.join(homeconf, "namingpolicy.py")
if os.access(homeconf, os.R_OK):
    sys.path.append(homeconf)
    if os.access(modnamingpolicy, os.R_OK):
        from namingpolicy import *
