# -*- coding: utf-8 -*-
# pylint: disable-msg=I0011,R0914,R0912
# XXX: fix those ignored pylint warnings

"""

Most of this code comes from pyofa:

    http://furius.ca/pyofa/

    Martin Blais <blais@furius.ca> (using the code of Lukáš Lalinský)

Guess release from audio files in a directory.

Automatically identify an album from some audio files.

Given a list of directories containing all and only the files of a single album,
run the fingerprint on the audio/mp3 files to identify the songs, and then apply
some simple heuristics using the track numbers from the filenames, the PUIDs of
the sound files and the MusicBrainz database to automatically guess what is the
most likely album release that corresponds to the directory. Note that this does
not make use of the header tags.

A file named 'saved.mb.release-id' is saved in each directory, with details on
the process.
"""

import logging
import os
import re
import sys
import tempfile
import time

#from os.path import *
from collections import defaultdict
from operator import itemgetter
import operator

# musicdns imports
import musicdns, musicdns.cache

# musicbrainz imports
from musicbrainz2.webservice import Query, TrackFilter, \
        WebServiceError, ReleaseIncludes

from musicbrainz2.model import Release

from namingmuse.filepath import FilePath
from namingmuse.albuminfo import AlbumInfo, TrackInfo
#from namingmuse.albuminfo import *


DEBUG = os.getenv('DEBUG')

MUSICDNS_KEY = '3d9af7bb4f9ed16dbb80b03a94a2735e'

VALID_EXTENSIONS = ('.mp3', '.ogg', '.wav', '.flac', '.mpc')

# XXX: should be in more general module
def commonPrefix(strs):
    'return the longest common prefix of strings'
    prefix = ''
    if len(strs) == 0:
        return prefix
    i = None
    for i in range(min(len(x) for x in strs)):
        done = False
        for s in strs:
            if s[i] != strs[0][i]:
                done = True
                break
        if done:
            break
    return strs[0][:i]

# XXX: should be in more general module
def isOrdered(lstfiles):
    '''Guess if list of files is ordered by track number.'''
    lstfiles.sort()

    nums = []
    prefix = commonPrefix(lstfiles)
    for fname in lstfiles:
        fname = fname[len(prefix):]
        root = os.path.splitext(fname)[0]
        match = re.search('([0-9]+)', root)
        if match:
            val = int(match.group(1))
            nums.append(val)

    if len(nums) == len(lstfiles) and \
            len(nums) > 1 and \
            reduce(operator.and_, 
                    (nums[i] > nums[i - 1] for i in range(1, len(nums)))):
        ret = True
    else:
        ret = False

    return ret

class MusicDNS(object):
    'Provide music dns key.'
    key = MUSICDNS_KEY

    def __init__(self):
        musicdns.initialize()
        self.cache = musicdns.cache.MusicDNSCache()

        self.debugmsgfd = tempfile.TemporaryFile(suffix='avcodec-debug')
        self.realstderr = os.dup(sys.stderr.fileno())

    def getpuid(self, path):
        'Return puid, length in milliseconds for a file.'

        # Temporarily replace stderr for filtering annoying debug messages from
        # libavcodec.
        os.dup2(self.debugmsgfd.fileno(), sys.stderr.fileno())

        try:
            ret = self.cache.getpuid(path, self.key)
        finally:
            os.dup2(self.realstderr, sys.stderr.fileno())

        return ret

    @staticmethod
    def close():
        'Cleanup: shutdown musicdns.'
        musicdns.finalize()

def getPuids(mdns, files):
    'Yield (track, filename, puid) for each file in files.'
    track = 0
    print 'Looking up puids (takes a few seconds per file):',
    sys.stdout.flush()
    for fn in files:
        try:
            sys.stdout.write('.')
            sys.stdout.flush()
            puid = mdns.getpuid(fn)[0]
        except IOError:
            puid = None
        track += 1
        #track = filename_track_number(fn)
        if DEBUG:
            print 'file %d, puid: %s, %s' % (track, fn, puid)

        yield (track, fn, puid)


def process_dir(mdns, dn, fast=False):
    '''Takes a directory dn and returns matching musicbrainz releases.'''
    dn = os.path.abspath(dn)
    files = [os.path.join(dn, x) for x in sorted(os.listdir(dn)) \
            if os.path.splitext(x)[1].lower() in VALID_EXTENSIONS]

    ordered = isOrdered(files)
    if not ordered:
        fast = False

    # For each track, filter the releases by including only those whose track
    # number matches the filename track number.
    matchrel = defaultdict(int)
    for no, fn, puid in getPuids(mdns, files):
        if puid is None:
            continue

        for _notused in xrange(5): # Retry a few times
            try:
                freleases = find_releases(puid)
                if DEBUG:
                    print 'puid releases for %s:' % puid
                    print freleases
                break
            except WebServiceError, err:
                logging.error(
                        "Can't access releases for song, retrying: %s" % err)
                time.sleep(1)
        else:
            logging.error("Gave up on MusicBrainz.")
            return None, None

        for tno, _notused, release in freleases:
            # If the track numbers match, include the release in matches.
            if DEBUG:
                print '%s vs %s: fno %d, trackno %d' % (
                        fn, release.title.encode(sys.stdout.encoding), no, tno)
            if (ordered and no == tno) or not ordered:
                matchrel[release.id] += 1

        if fast and len(matchrel.values()) > 0:
            break
    print

    if DEBUG:
        print matchrel

#     Select the most appropriate one.
#    if releases:
#        maxfreq = max(freq for rel, freq in releases)
#        mreleases = [rel for rel, freq in releases if freq == maxfreq]

#        ntmatches = [rel for rel in mreleases if 
#        len(rel.getTracks()) == len(nfiles)]
#        chosen = ntmatches[0] if ntmatches else mreleases[0]
#    else:
#        chosen = None

    releaseids = sorted(matchrel.iteritems(), key=itemgetter(1), reverse=1)
    releaseids = [y[0] for y in releaseids]
    return releaseids


def filename_track_number(fn):
    """Given filename, attempt to find the track numbers from the filenames."""
    mo = re.search('([0-9]+)', os.path.basename(fn))
    if mo:
        return int(mo.group(1))

def find_releases(puid):
    """Given a track's puid, return a list of
      (track-no, track, release)
    for each release that the song appeared on on."""
    query = Query()
    trackfilter = TrackFilter(puid=puid)
    results = query.getTracks(trackfilter)

    out = []
    for result in results:
        track = result.track
        rels = track.getReleases()
        assert len(rels) == 1
        rel = rels[0]
        out.append((rel.getTracksOffset()+1, track, rel))
    return out

class MusicBrainz2AlbumInfo(AlbumInfo):
    '''Represent musicbrainz album info.'''

    tagprovider = 'musicbrainz2'

    # XXX: get rid of the overcomplicated validation scheme that makes for
    # these ugly hacks overriding to avoid strict warnings
    def getGenre(self):
        'getter'
        return self.__genre
    def setGenre(self, genre):
        'setter'
        self.__genre = genre
    genre = property(getGenre, setGenre)

    def __init__(self, releaseId):
        #self.ignoreMissing(True)
        super(MusicBrainz2AlbumInfo, self).__init__()
        if isinstance(releaseId, basestring):
            self.__releaseId = releaseId
            query = Query()
            include = ReleaseIncludes(artist=True, tracks=True,
                    releaseEvents=True)
            release = query.getReleaseById(releaseId, include)
        elif isinstance(releaseId, Release):
            release = releaseId
            self.__releaseId = release.id
        else:
            raise Exception(
                    "incorrect type parameter for MusicBrainz2AlbumInfo %s"
                    % releaseId)

        self.title = release.title
        # XXX: musicbrainz doesn't have genre info. what to do?
        #self.genre = 'Musicbrainz'
        self.artist = release.artist.name
        date = release.getEarliestReleaseDate()
        if not date:
            self.year = 0
        else:
            self.year = int(date[0:4])
        self.genre = ''
        tracks = []
        number = 0
        self.isVarious = False
        for track in release.tracks:
            number += 1
            # XXX: get rid of the overcomplicated validation scheme that makes
            # for these ugly hacks
            class MBTrackInfo(TrackInfo):
                '''Represent musicbrainz track information.'''
                def getPlayLength(self):
                    'getter'
                    return self.__playLength
                def setPlayLength(self, playLength):
                    'setter'
                    self.__playLength = playLength
                def __init__(self):
                    super(MBTrackInfo, self).__init__()
                playLength = property(getPlayLength, setPlayLength)

            track_info = MBTrackInfo()
            del track_info.validateProps[
                    track_info.validateProps.index('playLength')]
            track_info.number = number
            if track.duration:
                track_info.playLength = track.duration / 1000.0
            else:
                # XXX: make sure we don't use namebinder relying on track length
                track_info.playLength = 0
            if track.artist:
                track_info.artist = track.artist.name
                self.isVarious = True
            else:
                track_info.artist = release.artist.name
            track_info.title = track.title
            tracks.append(track_info)
        self.tracks = tracks

    def fromFootPrint(cls, localalbum):
        'Lookup release from information in footprint.'
        if localalbum.tagValue('TTPR') == cls.tagprovider:
            releaseId = localalbum.tagValue('TRID')
            self = cls(releaseId)
            return self
        raise TypeError("invalid provider footprint (wrong class)")
    fromFootPrint = classmethod(fromFootPrint)

    def footprint(self):
        'Return footprint dictionary.'
        footprint = {
            'TTPR': self.tagprovider,
            'TRID': self.__releaseId,
        }
        return footprint

def searchMBAlbum(albumdir, fast=False):
    '''Return matching releases for albumdir.'''

    mdns = MusicDNS()

    releases = process_dir(mdns, str(albumdir), fast)

    if DEBUG:
        for release in releases:
            print 'Release: %s' % (release)

    mdns.close()

    return releases

def test():
    'Testing code used in development.'

    # slagsmaalsklubben hit me hard
    #m = MusicBrainz2AlbumInfo('6c6c976b-9e1c-42f2-abe3-ef89ad3d3da2') 

    rids = searchMBAlbum(
            '/media/data1/musikk/mp3/Slagsmålsklubben/a/2004 Hit Me Hard')
    mb_album_info = MusicBrainz2AlbumInfo(rids[0])

    # slagsmaalsklubben hit me hard
    #m = MusicBrainz2AlbumInfo('6c6c976b-9e1c-42f2-abe3-ef89ad3d3da2')

    # various natural born killers
    #m = MusicBrainz2AlbumInfo('77d9e53d-f6d3-4a13-bf39-fb63d02a7f94') 

    #m.ignoreMissing(True)
    from namingmuse.policy import genfilename, genalbumdirname
    print genalbumdirname(FilePath('blah'), mb_album_info)
    for track in mb_album_info.tracks:
        print genfilename(FilePath('.mp3'), mb_album_info, track)
    sys.exit()

if __name__ == '__main__':
    test()

