#!/usr/bin/python

import os, re, sys
from TagLib import *
from sys import exit

def mp3dumptag(mpfile):
    ref = MPEGFile(mpfile)
    #ref.strip(MPEGFile.ID3v1)
    if ref.ID3v1Tag(False):
        print "Has ID3v1Tag"
    if ref.ID3v2Tag(False):
        print "Has ID3v2Tag"
    tag = ref.ID3v2Tag()
    if not tag:
        print "no tag"
        return
    frames = tag.frameList()
    i = 0
    for frame in frames:
        if frame.frameID() == "COMM":
            cd = CommentsFrame(frame)
            print "Comment Description:", cd.description()
            print "Comment:", cd
        else:
            print i, frame.frameID() + ":", frame
            i += 1

def oggdumptag(oggfile):
    ref = VorbisFile(oggfile)
    tag = ref.tag()
    if not tag or tag.isEmpty():
        print "empty tag"
        return
    fields = tag.fieldListMap()
    for fieldname, stringlist in fields.items():
        for value in stringlist:
            print str(fieldname).ljust(20), str(value)

if len(sys.argv) > 1:
    for fname in sys.argv[1:]:
        if os.access(fname, os.R_OK):
            ext = os.path.splitext(fname)[1].lower()
            ext = ext.lstrip('.')
            if ext == "mp3":
                print "Dumping tag for:", fname
                mp3dumptag(fname)
                print
            elif ext == "ogg":
                print "Dumping tag for:", fname
                oggdumptag(fname)
                print
        else:
            print "Error: couldn't read:", fname
else:
    print "usage: %s <mp3-files>"
