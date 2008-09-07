#!/usr/bin/python

import os, re, sys
import tagpy
import tagpy.mpeg
import tagpy.ogg
import tagpy.ogg.vorbis
import tagpy.mpc
import tagpy.ogg.flac
import tagpy.flac
from sys import exit

MPEGFile = tagpy.mpeg.File
VorbisFile = tagpy.ogg.vorbis.File
MPCFile = tagpy.mpc.File
FlacFile = tagpy.flac.File

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
            #cd = CommentsFrame(frame)
            cd = frame
            print "Comment Description:", cd.description()
            print "Comment:", cd.toString()
        else:
            print i, frame.frameID() + ":", frame.toString()
            i += 1

def flacdumptag(flacfile):
    ref = FlacFile(flacfile)
    tag = ref.xiphComment()
    if not tag or tag.isEmpty():
        print "empty tag"
        return
    fields = tag.fieldListMap()
    for fieldname, stringlist in zip(fields.keys(), 
            [fields[x] for x in fields.keys()]):
        for value in stringlist:
            print str(fieldname).ljust(20), str(value)

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

def mpcdumptag(fname):
    ref = MPCFile(fname)
    if ref.ID3v1Tag(False):
        print 'Has ID3v1Tag'
    if ref.APETag(False):
        print 'Has APETag'
    tag = ref.APETag()
    if not tag:
        print 'no APETag'
        return
    fields = tag.itemListMap()

    try:
        for fieldname, item in fields.items():
            stringlist = item.toStringList()
            for value in stringlist:
                print str(fieldname).ljust(20), str(value)
    except Exception, e:
        raise

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
            elif ext == 'mpc':
                print 'Dumping tag for:', fname
                mpcdumptag(fname)
                print
            elif ext == 'flac':
                print 'Dumping tag for:', fname
                flacdumptag(fname)
                print
        else:
            print "Error: couldn't read:", fname
else:
    print "usage: %s <mp3-files>"
