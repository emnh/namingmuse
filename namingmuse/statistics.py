"""
Statistics
"""
import os
import re
import sys

from namingmuse import albumtag
from musexceptions import *
from providers import LocalAlbumInfo, getRemoteAlbumInfo

def dirstat(dirn, stats, verbose = False): 
    try:
        album = LocalAlbumInfo(dirn)
    except NoFilesException:
        return stats
    filelist = album.getfilelist()
    if len(filelist) > 0:
        stats.total += 1
        albuminfo = getRemoteAlbumInfo(album)
        if albuminfo:
            missing = []
            stats.nmusetagged += 1
            try:
                year = album.year
            except NamingMuseWarning:
                stats.missingyear += 1
                missing.append('year')
            try:
                genre = album.genre
            except NamingMuseWarning:
                stats.missinggenre += 1
                missing.append('genre')
            if verbose and len(missing) > 0:
                print "\n%s is missing %s" % (dirn, ", ".join(missing))
        else:
            if verbose:
                print "\n%s is untagged" % (dirn)
        if verbose:
            print str(stats)
        else:
            print "\r" + str(stats),
    return stats

class Stats:

    nmusetagged = 0
    total = 0
    missingyear = 0
    missinggenre = 0

    def __str__(self):
        return "Albums: %s, " %self.total +\
        "Tagged: %s, " %self.nmusetagged +\
        "Untagged: %s, " %(self.total-self.nmusetagged) +\
        "Missing year: %s, " %self.missingyear +\
        "Missing genre: %s" %self.missinggenre
