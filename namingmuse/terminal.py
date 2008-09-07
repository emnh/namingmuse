""" A module for functions closely knit to terminal io """

import curses
import os
import re
import struct
import sys
from difflib import SequenceMatcher
from sys import stdout
import musexceptions

DEBUG = os.getenv('DEBUG')

def termcolor(color, msg):
    colornum = getattr(curses, "COLOR_" + color.upper())
    return "\033[1;3%dm%s\033[0;39m" % (colornum, msg)

def colorize(msg):
    "All-in-one place string coloring (potentially smart)"
    tr = {
    "<-": "red",        # red means rollback
    "->": "blue",        # blue means write
    "-tag->": "blue",
    "-skip->": "green",  # green means dry-run
    "-dry->": "green",
    }
    color = (msg in tr.keys() and tr[msg] or "")
    msg = re.sub("^Warning",termcolor('yellow', "Warning"), msg)
    msg = re.sub("^Error",termcolor('red', "Error"), msg)
    msg = re.sub("^Info",termcolor('green', "Info"), msg)
    msg = re.sub("^CDDBP exception", termcolor('yellow', "CDDBP Exception"), msg)
    if color != "": msg = termcolor(color, msg)
    return msg

def alphadiff(a, b):
    a, b = a.lower(), b.lower()
    isjunk = lambda x: not x.isalnum()
    return SequenceMatcher(isjunk, a, b).ratio()

def choosealbum(albums, matchto, options, cleanupCallback):

    matchto = matchto.getName()
    matchtou = matchto.decode(options.sysencoding, 'ignore')
    matchto = re.sub("^[0-9]{4} ", "", matchto)

    fmat = lambda u,v,w,x,y,z: ("%3s%6s%5s %-17s%-15s %-10s\n" \
                % (u, v, w, x, y, z)).encode(options.sysencoding)
    
    pager = sys.stdout
    pager.write("\n")
    pager.write("Pick a number that matches '%s':\n" % matchto)
    pager.write(fmat("Nr", "Match", "Year", "Genre", "Artist", "Title"))
    pager.write(fmat(str(0) + ":","", "", "", "Don't tag this album", ""))
    newlist = []

    def showAlbum(album, nr):
        newlist.append(album)
        album.ignoreMissing(True)
        similarity = alphadiff(album.title, matchtou)
        similarity = "%3.1f%%" % (similarity * 100)
        pager.write(fmat(str(nr) + ":",similarity, 
                    album.year, album.genre, album.artist,album.title))
    try:
        nr = 0
        for album in albums:
            if options.strict:
                if not len(album.validate()) == 0:
                    continue
            nr += 1
            showAlbum(album, nr)
        if not newlist:
            # XXX: solve this problem for recursive mode too
            if not options.recursive:
                options.strict = False
            print musexceptions.NamingMuseWarning('no albums satisfy strict requirements, showing all')
            for album in albums:
                nr += 1
                showAlbum(album, nr)
    except KeyboardInterrupt:
        if cleanupCallback != None:
            cleanupCallback()

    # XXX: print all albums if none "validated"
            
    idx = -1 
    if not sys.stdout.isatty():
        idx = 0
    
    # Auto-select album
    if options.autoselect:
        if len(newlist) == 1:
            idx = len(newlist)
            print "Auto-selected:", idx
        elif len(newlist) == 0:
            idx = 0
        
    while idx < 0 or idx > len(newlist):
        print "Pick an album (number):",
        try:
            idx = int(raw_input())
        except ValueError:
            pass
        except KeyboardInterrupt:
            continue
    print
    if idx == 0: #we dont want any of the suggested
        return None
    return newlist[idx - 1]
