"""A module for searching the freedb albums using
a full text search interface, and tagging an album
with the resulting information. Fields that can be
searched are artist, title, track and rest.
"""

import sys,os,re,string
import htmllib
import urllib
import albumtag
import terminal
from string import join
from sys import exit
from HTMLParser import HTMLParser
from optparse import make_option

#DEBUG = False
DEBUG = True

baseurl = "http://www.freedb.org/"
allfields = ["artist", "title", "track", "rest"]

class searchparser(HTMLParser):
    "Class for parsing the search page"

    album = None
    albums = []
    adr = baseurl + "freedb_search_fmt.php"
    rexadr = re.compile(adr + "\?cat=(?P<genreid>.*)\&id=(?P<cddbid>[a-f0-9]*)")

    def getalbums(self):
        return self.albums

    def handle_starttag(self, tag, attrs):
        self.album = None
        if tag == "a": 
            attrs = dict(attrs)
            match = self.rexadr.match(attrs["href"])
            if match:
                self.album = match.groupdict()

    def handle_data(self, data):
        if self.album:
            self.album["title"] = string.strip(data)
            self.album["genreid"] = self.album["genreid"].strip()
            self.album["cddbid"] = self.album["cddbid"].strip()
            self.albums.append(self.album)
            album = None

def searchalbums(searchwords, searchfields = ("artist", "title")):
    doc = baseurl + "freedb_search.php"
    query = [("words", join(searchwords, "+")),
                     ("allfields", "NO"),
                     ("allcats", "YES"),
                     ("grouping", "none"),
                     ("x", 0),
                     ("y", 0)]
    for field in searchfields:
        query.append(("fields", field))
    querystr = urllib.urlencode(query)
    url = doc + "?" + querystr

    if DEBUG: print querystr
    searchres = urllib.urlopen(url)
    htmldata = searchres.read()
    searchres.close()

    if DEBUG:
        fd = file("search.html", "w")
        fd.write(htmldata)
        fd.close()

    parser = searchparser()
    parser.feed(htmldata)
    albums = parser.getalbums()
    return albums

def getoptions():
    opts = []
    opts.append(make_option("-a", "--all", action="store_true",
                                help="enable searching of all fields (default: artist+title)"))
    for field in allfields:
        opts.append(make_option("", "--" + field, action="store_true",
                                    help="enable searching of " + field + " field"))
    return opts

def search(albumdir, options):
    if not options.words:
        exit("error: no search words specified")
    if options.all:
        searchfields = allfields
    else:
        searchfields = filter(lambda key, options = options: eval("options." + key), allfields)
    searchwords = options.words
    print "Searching for albums.."
    if searchfields != []:
        albums = searchalbums(searchwords, searchfields)
    else:
        albums = searchalbums(searchwords)

    album = terminal.choosealbum(albums, albumdir)
    albumtag.tagfiles(albumdir, album, options, albumtag.namebinder_strapprox)
