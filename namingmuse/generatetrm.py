#!/usr/bin/env python

# this file is almost a verbatim copy from a python-musicbrainz distribution example

import mad          # get this from http://spacepants.org/src/pymad/
import musicbrainz  # get this from http://www.musicbrainz.org
import ogg.vorbis   # get this from http://www.andrewchatham.com/pyogg/
import os
import sys
import wave         # should come with python

def getSignature(filename):
    (path, ext) = os.path.splitext(filename)
    if ext.lower() == '.ogg':
        ff = ogg.vorbis.VorbisFile(filename)
    elif ext.lower() == '.mp3':
        ff = MadWrapper(filename)
    elif ext.lower() == '.wav':
        ff = WavWrapper(filename)
    else:
        raise SystemError, "Unsupported audio file."

    info = ff.info()
    trm = musicbrainz.trm()
    trm.SetPCMDataInfo(info.rate, info.channels, 16)
    while 1:
        (buff, bytes, bit) = ff.read()
        if bytes == 0:
            break
        if trm.GenerateSignature(buff):
            break

    sig = trm.FinalizeSignature()

    return sig

class WavWrapper:
    """
    Make the wave module act more like ogg.vorbis.VorbisFile
    """
    def __init__(self, filename):
        self.ff = wave.open(filename, 'r')
    
    def read(self):
        """
        These docs are from ogg.vorbis.VorbisFile.read()
        
        @returns: Returns a tuple: (x,y,y) where x is a buffer object of the
            data read, y is the number of bytes read, and z is whatever the
            bitstream value means (no clue).
        @returntype: tuple
        """
        buff = self.ff.readframes(4096)
        return (buff, len(buff), None)

    def info(self):
        return AudioInfo(self.ff.getframerate(), self.ff.getnchannels())

class MadWrapper:
    """
    Make the mad module act more like ogg.vorbis.VorbisFile
    """
    def __init__(self, filename):
        self.ff = mad.MadFile(filename)
    
    def read(self):
        """
        These docs are from ogg.vorbis.VorbisFile.read()
        
        @returns: Returns a tuple: (x,y,y) where x is a buffer object of the
            data read, y is the number of bytes read, and z is whatever the
            bitstream value means (no clue).
        @returntype: tuple
        """
        buff = self.ff.read()
        if buff:
            return (buff, len(buff), None)
        else:
            return ('', 0, None)
            
    def info(self):
        if self.ff.mode() == mad.MODE_SINGLE_CHANNEL:
            channels = 1
        else:
            channels = 2
        return AudioInfo(self.ff.samplerate(), channels)


class AudioInfo:
    def __init__(self, rate, channels):
        self.rate = rate
        self.channels = channels

def main():
    for filename in sys.argv[1:]:
        print getSignature(filename)

if __name__ == '__main__':
    main()

