""" A module for naming policies """

import os, re, sys, string

def filename(original, ext, title, track, trackartist, albumname, year, genre, albumartist):
    if trackartist:
        if albumartist == "Various":
            # Track number first
            tofile = "%.2u %s - %s%s" % (track, trackartist, title, ext)
        else:
            # Track number behind artist 
            tofile = "%s - %.2u %s%s" % (trackartist, track, title, ext)
    else:
        # No artist
        tofile = "%.2u %s%s" % (track, title, ext)
        
    tofile = tofile.replace("/", " ")
    return tofile

def albumdirname(original, artist, albumname, year, genre):
    albumname = albumname.replace("/", " ")
    if int(year) > 1800:
        newdirname = "%s %s %s" % (artist, year, albumname)
    else:
        newdirname = "%s %s" % (artist,albumname)
    newdirname = newdirname.replace("/", " ")
    return newdirname
    # return original # no change

# Overwrite global functions defined above with local ones
home = os.getenv("HOME")
homeconf = os.path.join(home, ".namingmuse")
modnamingpolicy = os.path.join(homeconf, "namingpolicy.py")
if os.access(homeconf, os.R_OK):
    sys.path.append(homeconf)
    if os.access(modnamingpolicy, os.R_OK):
        from namingpolicy import *
