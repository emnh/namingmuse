"""
Statistics
"""
import sys,re,os
import albumtag
from exceptions import *

def dirstat(dir, stats): 
    filelist = albumtag.getfilelist(dir)
    if len(filelist) > 0:
        stats.total += 1
        print stats,
        nmusetag = albumtag.getNmuseTag(filelist)
        if nmusetag:
            stats.nmusetagged += 1
            try:
                year = nmusetag.year
            except NamingMuseWarning:
                stats.missingyear += 1
            try:
                genre = nmusetag.genre
            except NamingMuseWarning:
                stats.missinggenre += 1
    return stats

class Stats:

    nmusetagged = 0
    total = 0
    missingyear = 0
    missinggenre = 0

    def __str__(self):
        return "\rAlbums: %s, " %self.total +\
        "Tagged: %s, " %self.nmusetagged +\
        "Untagged: %s, " %(self.total-self.nmusetagged) +\
        "Missing year: %s, " %self.missingyear +\
        "Missing genre: %s" %self.missinggenre
