"""A module for searching the freedb albums using
a full text search interface, and tagging an album
with the resulting information. Fields that can be
searched are artist, title, track and rest.
"""

import sys, os ,re
import htmllib
import urllib
import albumtag
import terminal
from sys import exit
from HTMLParser import HTMLParser
from optparse import make_option

from provider import LocalAlbumInfo
from provider import FreeDBAlbumInfo

from musexceptions import *

DEBUG = False
#DEBUG = True

baseurl = "http://www.freedb.org/"
allfields = ("artist", "title", "track", "rest")
defaultfields = ('artist', 'title')

class FreedbSearchParser(HTMLParser):
    "Class for parsing the search page"

    def __init__(self):
        HTMLParser.__init__(self)
        self.albums = {}
        adr = baseurl + "freedb_search_fmt.php"
        self.rexadr = re.compile(adr + "\?cat=(?P<genreid>[^\s]+)\&id=(?P<cddbid>[a-f0-9]+)")

    def handle_starttag(self, tag, attrs):
        if tag == "a": 
            dattrs = dict(attrs)
            match = self.rexadr.match(dattrs["href"])
            if match:
                album = match.groups()
                self.albums[album] = True
    
    def getAlbums(self):
        return self.albums.keys()
    
    albums = property(getAlbums)

def searchalbums(albumdir, searchwords, searchfields, cddb):
    if len(searchfields) == 0:
        searchfields = defaultfields

    doc = baseurl + "freedb_search.php"
    query = [
             ("words", "+".join(searchwords)),
             ("allcats", "YES"),
             ("grouping", "none"),
             ("x", 0),
             ("y", 0)
            ] + [ 
             ("fields", f) for f in searchfields
            ]
    querystr = urllib.urlencode(query)
    url = doc + "?" + querystr

    searchres = urllib.urlopen(url)
    htmldata = searchres.read()
    searchres.close()

    if DEBUG:
        fd = file("search.html", "w")
        fd.write(htmldata)
        fd.close()

    # Parse HTML for album links
    parser = FreedbSearchParser()
    parser.feed(htmldata)
    
    # Filter and make FreeDBAlbumInfos
    songcount = len(LocalAlbumInfo(albumdir).tracks)
    albums = filterBySongCount(parser.albums, songcount)
    albums = [FreeDBAlbumInfo(cddb, genre, cddbid) for genre, cddbid in albums]
    return albums

def filterBySongCount(albums, songcount):
    retalbums = []
    for album in albums: 
        genre, cddbid = album
        try:
            cddbid = int(cddbid, 16)
        except ValueError:
            raise NamingMuseError("invalid cddbid " + cddbid)
        sct = cddbid % 0x100
        if sct == songcount:
            retalbums.append(album)
        elif DEBUG:
            print "%s filtered, had %u tracks, wanted %u" % (cddbid, sct, songcount)
           
    return retalbums
