""" A module for naming policies """

import re

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
    if re.search("^[0-9]{4}", year):
        newdirname = "%s %s %s" % (artist, year, albumname)
    else:
        newdirname = "%s %s" % (artist,albumname)
    newdirname = newdirname.replace("/", " ")
    return newdirname
    # return original # no change
