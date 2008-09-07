# -*- coding: utf-8 -*-

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

# stdlib imports
import sys, os, re, logging, StringIO, time
from os.path import *
from collections import defaultdict
from operator import itemgetter
import operator

# musicdns imports
import musicdns, musicdns.cache

# mutagen imports
from mutagen import File

# musicbrainz imports
import musicbrainz2
from musicbrainz2.webservice import Query, TrackFilter, WebServiceError, ReleaseIncludes
from musicbrainz2.model import Release

from namingmuse.filepath import FilePath

DEBUG = os.getenv('DEBUG')

from namingmuse.albuminfo import *

musicdns_key = '3d9af7bb4f9ed16dbb80b03a94a2735e'

valid_extensions = ('.mp3', '.m4a', '.m4p', '.ogg', '.wav', '.flac')

# XXX: should be in more general module
def commonPrefix(strs):
    'return the longest common prefix of strings'
    prefix = ''
    if len(strs) == 0:
        return prefix
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
    lstfiles.sort()

    nums = []
    prefix = commonPrefix(lstfiles)
    for i, fname in enumerate(lstfiles):
        fname = fname[len(prefix):]
        root, ext = os.path.splitext(fname)
        match = re.search('([0-9]+)', root)
        if match:
            val = int(match.group(1))
            nums.append(val)

    if len(nums) == len(lstfiles) and \
            len(nums) > 1 and \
            reduce(operator.and_, (nums[i] > nums[i - 1] for i in range(1, len(nums)))):
        isOrdered = True
    else:
        isOrdered = False

    return isOrdered

def process_dir(dn, musicdns_key, fast=False):
    dn = abspath(dn)
    files = [join(dn, x) for x in sorted(os.listdir(dn)) \
            if splitext(x)[1].lower() in valid_extensions]

    ordered = isOrdered(files)
    if not ordered:
        fast = False

    def getPuids(files):
        'Create a list of (track, filename, puid).'
        track = 0
        print 'Looking up puids (takes a few seconds per file):',
        sys.stdout.flush()
        for fn in files:
            try:
                sys.stdout.write('.')
                sys.stdout.flush()
                puid, _ = cache.getpuid(fn, musicdns_key)
            except IOError:
                puid = None
            track += 1
            #track = filename_track_number(fn)
            if DEBUG:
                print 'file %d, puid: %s, %s' % (track, fn, puid)

            yield (track, fn, puid)

    # For each track, filter the releases by including only those whose track
    # number matches the filename track number.
    matchrel = defaultdict(int)
    for no, fn, puid in getPuids(files):
        if puid is None:
            continue
        
        for _ in xrange(5): # Retry a few times
            try:
                freleases = find_releases(puid)
                if DEBUG:
                    print 'puid releases for %s:' % puid
                    print freleases
                break
            except WebServiceError, e:
                logging.error("Can't access releases for song, retrying: %s" % e)
                time.sleep(1)
        else:
            logging.error("Gave up on MusicBrainz.")
            return None, None

        for tno, track, release in freleases:
            # If the track numbers match, include the release in matches.
            included = 0
            if DEBUG:
                print '%s vs %s: fno %d, trackno %d' % (fn, release.title.encode(sys.stdout.encoding), no, tno)
            if (ordered and no == tno) or not ordered:
                matchrel[release.id] += 1
                included = 1

        if fast and len(matchrel.values()) > 0:
            break
    print

    if DEBUG:
        print matchrel

#     Select the most appropriate one.
#    if releases:
#        maxfreq = max(freq for rel, freq in releases)
#        mreleases = [rel for rel, freq in releases if freq == maxfreq]

#        ntmatches = [rel for rel in mreleases if len(rel.getTracks()) == len(nfiles)]
#        chosen = ntmatches[0] if ntmatches else mreleases[0]
#    else:
#        chosen = None

    releaseids = sorted(matchrel.iteritems(), key=itemgetter(1), reverse=1)
    releaseids = [x[0] for x in releaseids]
    return releaseids


def filename_track_number(fn):
    """Given filename, attempt to find the track numbers from the filenames."""
    mo = re.search('([0-9]+)', basename(fn))
    if mo:
        return int(mo.group(1))
        
def find_releases(puid):
    """Given a track's puid, return a list of
      (track-no, track, release)
    for each release that the song appeared on on."""
    q = Query()
    f = TrackFilter(puid=puid)
    results = q.getTracks(f)

    out = []
    for r in results:
        track = r.track
        rels = track.getReleases()
        assert len(rels) == 1
        rel = rels[0]
        out.append((rel.getTracksOffset()+1, track, rel))
    return out

class MusicBrainz2AlbumInfo(AlbumInfo):

    tagprovider = 'musicbrainz2'

    # XXX: get rid of the overcomplicated validation scheme that makes for these ugly hacks
    # overriding to avoid strict warnings
    def getGenre(self):
        return self.__genre
    def setGenre(self, genre):
        self.__genre = genre
    genre = property(getGenre, setGenre)

    def __init__(self, releaseId):
        #self.ignoreMissing(True)
        super(MusicBrainz2AlbumInfo, self).__init__()
        if isinstance(releaseId, basestring):
            self.__releaseId = releaseId
            q = Query()
            include = ReleaseIncludes(artist=True, tracks=True, releaseEvents=True)
            release = q.getReleaseById(releaseId, include)
        elif isinstance(releaseId, Release):
            release = releaseId
            self.__releaseId = release.id
        else:
            raise Exception("incorrect type parameter for MusicBrainz2AlbumInfo %s" % releaseId)

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
            # XXX: get rid of the overcomplicated validation scheme that makes for these ugly hacks
            class MBTrackInfo(TrackInfo):
                def getPlayLength(self):
                    return self.__playLength
                def setPlayLength(self, playLength):
                    self.__playLength = playLength
                def __init__(self):
                    super(MBTrackInfo, self).__init__()
                playLength = property(getPlayLength, setPlayLength)

            t = MBTrackInfo()
            del t.validateProps[t.validateProps.index('playLength')]
            t.number = number
            if track.duration:
                t.playLength = track.duration / 1000.0
            else:
                # XXX: make sure we don't use namebinder relying on track length
                t.playLength = 0
            musicbrainz2.model
            if track.artist:
                t.artist = track.artist.name
                self.isVarious = True
            else:
                t.artist = release.artist.name
            t.title = track.title
            tracks.append(t)
        self.tracks = tracks

    def fromFootPrint(cls, localalbum):
        if localalbum.tagValue('TTPR') == cls.tagprovider:
            releaseId = localalbum.tagValue('TRID')
            self = cls(releaseId)
            return self
        raise TypeError("invalid provider footprint (wrong class)")
    fromFootPrint = classmethod(fromFootPrint)

    def footprint(self):
        footprint = {
            'TTPR': self.tagprovider,
            'TRID': self.__releaseId,
        }
        return footprint

def searchMBAlbum(albumdir, fast=False):

    musicdns.initialize()
    global cache; cache = musicdns.cache.MusicDNSCache()

    releases = process_dir(str(albumdir), musicdns_key, fast)

    if DEBUG:
        for x in releases:
            print 'Release: %s' % (x)

    musicdns.finalize()

    del cache

    return releases

if __name__ == '__main__':
    #m = MusicBrainz2AlbumInfo('6c6c976b-9e1c-42f2-abe3-ef89ad3d3da2') # slagsmaalsklubben hit me hard
    rids = searchMBAlbum('/media/data1/musikk/mp3/Slagsmålsklubben/a/2004 Hit Me Hard')
    m = MusicBrainz2AlbumInfo(rids[0])
    #m = MusicBrainz2AlbumInfo('6c6c976b-9e1c-42f2-abe3-ef89ad3d3da2') # slagsmaalsklubben hit me hard
    #m = MusicBrainz2AlbumInfo('77d9e53d-f6d3-4a13-bf39-fb63d02a7f94') # various natural born killers
    #m.ignoreMissing(True)
    from namingmuse.policy import genfilename, genalbumdirname
    print genalbumdirname(FilePath('blah'), m)
    for t in m.tracks:
        print genfilename(FilePath('.mp3'), m, t)
    sys.exit()
