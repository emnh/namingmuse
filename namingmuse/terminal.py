""" A module for functions closely knit to terminal io """

import sys, os, re, string
import struct, fcntl, termios
from sys import stdout
from difflib import SequenceMatcher
import curses

DEBUG = False

def termcolor(color, msg):
    colornum = eval("curses.COLOR_" + string.upper(color))
    return "\033[1;3%dm%s\033[0;39m" % (colornum, msg)

def colorize(msg):
    "All-in-one place string coloring (potentially smart)"
    tr = {
    "->": "blue",        # blue means write
    "-tag->": "blue",
    "-skip->": "green",  # green means dry-run
    "-dry->": "green",
    }
    color = (msg in tr.keys() and tr[msg] or "")
    msg = re.sub("Warning",termcolor('yellow',"Warning"),msg)
    msg = re.sub("Error",termcolor('red',"Error"),msg)
    if color != "": msg = termcolor(color, msg)
    return msg

def gettermsize():
    s = struct.pack("HHHH", 0, 0, 0, 0)
    rows,cols = struct.unpack("HHHH", fcntl.ioctl(sys.stdout.fileno(),
                           termios.TIOCGWINSZ, s))[:2]
    return rows, cols

def alphadiff(a, b):
    a, b = a.lower(), b.lower()
    isjunk = lambda x: not x in string.lowercase
    return SequenceMatcher(isjunk, a, b).ratio()

def choosealbum(albums, matchto):
    rows,cols = gettermsize()

    # XXX: do this elsewhere
    matchto = os.path.basename(os.path.abspath(matchto))

    if len(albums) == 1: return albums[0]
    #import pprint
    #pprint.pprint(albums)

    mlen = max(map(lambda x: len(x.title), albums)) + 3
    mlen = min(mlen, cols - 30)
    #fmat = lambda x,y,z: "%10s   %-10s%s\n" % (x, y, z.rjust(mlen))
    fmat = lambda u,v,w,x,y,z: "%3s%6s%5s %-15s%-15s %-10s\n" \
                % (u, v, w, x, y, z)
    pagerapp = os.getenv("PAGER") or "less"
    pager = (len(albums) < rows and sys.stdout or os.popen(pagerapp, "w"))
    
    try:
        pager.write("\n")
        pager.write("Pick a number that matches '%s':\n" % matchto)
        pager.write(fmat("Nr", "Match", "Year", "Genre", "Artist", "Title"))
        pager.write(fmat(str(0) + ":","", "", "", "Don't tag this album", ""))
        for i in range(0, len(albums)):
            album = albums[i]
            album.ignoreMissing(True)
            similarity = alphadiff(album.title, matchto)
            similarity = "%3.1f%%" % (similarity * 100)
            pager.write(fmat(str(i + 1) + ":",similarity, 
                        album.year, album.genre, album.artist,album.title))
        if (pager != stdout): pager.close()
    except IOError, (nr, strerr):
        if strerr != "Broken pipe": 
            raise

    idx = -1 
    while idx < 0 or idx > len(albums)+1:
        print "Pick an album (number):",
        try:
            idx = int(raw_input())
        except ValueError:
            pass
    print
    if idx == 0: #we dont want any of the suggested
        return None
    return albums[idx - 1]
