import os
import re
import sys
#from albuminfo import AlbumInfo
from time import sleep
from tunepimp import tunepimp, metadata, track

trackStatus = [
    "Unrecognized",
    "Recognized",
    "Pending",
    "TRM Lookup",
    "TRM Collision",
    "File Lookup",
    "User Selection",
    "Verified",
    "Saved",
    "Deleted",
    "Error"]


class MusicbrainzAlbumInfo:
    'Provides metainfo from musicbrainz.org'

    tagprovider = "musicbrainz"
    client = 'namingmuse'
    version = '0.0.1' 
    
    def __init__(self, directory):
        self.directory = directory
        #self.tp = tunepimp.tunepimp(self.client, self.version, tunepimp.tpThreadNone)
        self.tp = tunepimp.tunepimp(self.client, self.version)
        
    def footprint(self):
        footprint = {}
        footprint["TTPR"] = self._tagprovider
        footprint["TTRM"] = self._trmid
        return footprint

    def getTRMs(self):
        """Iterates the filenames and produces a list of TRMs
        @returns the list of TRMs.
        """
        trms = []
        
        self.tp.addFile(self.directory)

        self.filenumber = self.tp.getNumFiles()
        done = 0
        while done < self.filenumber:

            ret, type, fileId = self.tp.getNotification();
            if not ret:
                sleep(0.1)
                continue
            print "ret:",ret,"type:",type,"fileId",fileId
            status = self.tp.getStatus()[0]
            print "status",self.tp.getStatus()
            if type == tunepimp.eFileChanged and status == tunepimp.eUnrecognized:
                tr = self.tp.getTrack(fileId);
                tr.lock()
                trstatus = tr.getStatus()
                trm = tr.getTRM()
                metadata = tr.getServerMetadata()
                localdata = tr.getLocalMetadata()
                tr.unlock()
                self.tp.releaseTrack(tr)
                print "artist:",metadata.artist,"track:",metadata.track,"year:",metadata.releaseYear
        return trms

    def getSongInfo(self, trms):

if __name__ == '__main__':
    mbi = MusicbrainzAlbumInfo('/home/xt/film/Cake/01.mp3')
    trms = mbi.getTRMs()
    print trms
