"""
Statistics
"""
import sys,re,os
import albumtag
from musexceptions import *
from provider import LocalAlbumInfo

def dirstat(dir, stats): 
    filelist = albumtag.getfilelist(dir)
    if len(filelist) > 0:
        stats.total += 1
        nmusetag = albumtag.getNmuseTag(filelist)
        if nmusetag:
            stats.nmusetagged += 1
            albuminfo = LocalAlbumInfo(dir)
            try:
                year = albuminfo.year
            except NamingMuseWarning:
                stats.missingyear += 1
            try:
                genre = albuminfo.genre
            except NamingMuseWarning:
                stats.missinggenre += 1
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
