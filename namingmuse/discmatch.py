"""A module for tagging and renaming files.
It generates a discid from album toc to acquire
matching metainfo for an album from freedb.
"""

import re,sys,os,string
import albumtag, terminal, exceptions
from cddb import *

QUERY_EXACT = 200
QUERY_NONE = 202
QUERY_MULTIPLE = 211
SERVER_ERROR=450
READ_OK = 210

DEBUG = False

def printTOC(filelist):
    'print nicely formatted toc, mostly for debugging'
    toc = files2discid(filelist)
    discid,filect,framelist,totsecs = toc[0],toc[1],toc[2:-1],toc[-1]
    print "cddbid: %08x" % discid
    print "filecount: %s" % filect
    print "album length: %us = %um %us" % (totsecs, totsecs / 60, totsecs % 60)
    oldlength = 0
    framelist.append(totsecs * 75)
    for i in range(len(framelist)):
        frameidx = framelist[i]
        if i == 0:
            filen = "lead in"
            length = frameidx / 75 - oldlength
        else:
            filen = filelist[i - 1]
            length = frameidx / 75 - oldlength
            #length = albumtag.getlength(filen)
        print "length: %4us = %2um %2us, frameidx: %8u: %s" % \
            (length, length / 60, length % 60, framelist[i], filen)
        oldlength += length
    print "nb! last frameidx not sent to server (just totsecs * 75)"

def cddb_sum(n):
    ret = 0
    
    while n > 0:
	ret = ret + (n % 10)
	n = n / 10

    return ret

def files2discid(filelist):
    """Calculate discid from an _ordered_ set of files
       Supported filetypes are those supported by TagLib"""

    filect = len(filelist)
    leadin = 2
    checksum = cddb_sum(leadin)  # sum leadin too
    totalsecs = leadin
    framelist = []

    roundsecs = lambda x: int(x + 0.5)

    floatrest = 0
    for file in filelist:
        secs = albumtag.getIntLength(file)
        #secs = albumtag.getFloatLength(file)
        if type(secs) is int:
            checksum += cddb_sum(secs)
        elif type(secs) is float:
            floatrest += secs - roundsecs(secs)
            checksum += cddb_sum(roundsecs(secs))
            
        # on CDs an audio frame is 1/75 of a second
        # the framelist contains the offset of the songs on a CD,
        # measured in frames
        framelist.append(int(totalsecs * 75))
        totalsecs += secs

    # discid howto: subtract leadin from totalsecs in chksum
    #totalsecs -= leadin

    if type(totalsecs) is float:
        totalsecs = roundsecs(totalsecs)

    # testing code
    checksum = 0
    for frame in framelist:
        checksum += cddb_sum(frame / 75)

    # the checksum is a 32bit integer structured as follows
    # first byte: sum(all digits in all song lengths(seconds)) mod 255
    # this is the one that is hardest to get right
    # second and third byte: total length of all songs (no leadin, no leadout)
    # fourth byte: the number of songs

    discid = (long((checksum % 0xFF)) << 24 | totalsecs << 8 | filect)
    if DEBUG:
        print "floatrest: %f" % floatrest
        print "cddbid: %08x" % discid

    return [discid, filect] + framelist + [totalsecs]

def getalbuminfo(genreid, cddbid):
    "Get album info from cddb server"

    if DEBUG: 
        "Fetching albuminfo..." 

    cddb = CDDBP()
    cddb.connect()
    read_stat,read_info = cddb.read(genreid, cddbid)

    if DEBUG: 
        print "read_stat, read_info:",read_stat,read_info

    if read_stat == READ_OK:
        year = read_info["DYEAR"].strip()
        genre = read_info["DGENRE"].strip() # not limited to the 11 cddb genres
        albumartist = read_info["DTITLE"].split("/")[0].strip()
        album = string.join(read_info["DTITLE"].split("/")[1:], "/").strip()

        if re.search("various", albumartist, re.I):
            albumartist = "Various"
        
        namelist = []
        for key in read_info.keys():
            if key[:6] == "TTITLE":
                track = int(key[6:]) + 1
                title = read_info[key]
                dict = {"track": track, "title": title}
                namelist.append(dict)
    else:
        raise NotImplementedException("cddb read: code " + str(read_stat))

    return {"year":year, 
            "genre":genre, 
            "genreid":genreid,
            "cddbid":cddbid,
            "albumartist":albumartist, 
            "album":album, 
            "namelist":namelist}

def freedbTOCMatchAlbums(query):
    """Search freedb for album matches for music files in
       an album(directory) in track order, using discid
       calculation."""
    
    if query:
        cddb = CDDBP()
        cddb.connect()
        query_stat,query_info = cddb.query(query)
        if query_stat == QUERY_MULTIPLE:
            statusmsg = "multiple matches." 
        elif query_stat == QUERY_EXACT: 
            statusmsg = "exact match!"
            pass
        elif query_stat == QUERY_NONE:
            statusmsg = "no matches!"
            query_info = []
        else:
            raise NotImplementedError("Unknown freedb status code: %d" % query_stat)
        albums = query_info
        for album in albums:
            album["title"] = re.sub("\s+", " ", album["title"])
        return (statusmsg, query_info)
    else:
        return (None, None)
