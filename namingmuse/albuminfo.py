""" A module that defines the base albuminfo class.
An albuminfo class is a class that contains metdata about an album.
"""
import os
import re
import sys
from namingmuse.constants import TAGVER
from namingmuse.musexceptions import *

#__all__ = [ 'TrackInfo', 'AlbumInfo' ]

class debugdumper(type):
    def __init__(cls, name, bases, dct):
        super(debugdumper, cls).__init__(name, bases, dct)
        def xrepr(self):
            s = "OBJECT DUMP of %s:\n" % name
            for key in dir(self):
                if key != "__init__":
                    value = getattr(self, key)
                    if not callable(value):
                        if isinstance(value, unicode):
                            value = value.encode(sys.stdout.encoding)
                        s += "%s = %s\n" % (key, value)
            return s
        cls.dump = xrepr

class TagSafety(type):
    'A metaclass for adding helper methods guaranteeing tag completeness'
    
    def __init__(cls, name, bases, dct):
        super(TagSafety, cls).__init__(name, bases, dct)

        def strictGetString(self, prop):
            try:
                ret = getattr(self, "_%s__%s" % (name, prop))
            except AttributeError:
                ret = getattr(self, "_%s__%s" % (bases[0].__name__, prop))
                
            if isinstance(ret, basestring):
                ret = ret.strip()
            else:
                ret = ""
            if ret == "":
                raise TagIncompleteWarning(name + "." + prop)
            return ret

        def strictGetInt(self, prop):
            try:
                ret = getattr(self, "_%s__%s" % (name, prop))
            except AttributeError:
                ret = getattr(self, "_%s__%s" % (bases[0].__name__, prop))

            try:
                ret = int(ret)
            except ValueError:
                ret = 0
            if ret == 0:
                raise TagIncompleteWarning(name + "." + prop)
            return ret
        
        def weakGetString(self, prop):
            try:
                return strictGetString(self, prop)
            except TagIncompleteWarning:
                return ""

        def weakGetInt(self, prop):
            try:
                return strictGetInt(self, prop)
            except TagIncompleteWarning:
                return 0

        def ignoreMissing(self, truth):
            if truth: # be lenient
                self._getString = self._weakGetString
                self._getInt = self._weakGetInt
            else: # throw exceptions
                self._getString = self._strictGetString
                self._getInt = self._strictGetInt

        cls._getString = strictGetString
        cls._getInt = strictGetInt
        cls._strictGetString = strictGetString
        cls._strictGetInt = strictGetInt
        cls._weakGetString = weakGetString
        cls._weakGetInt = weakGetInt

        cls.ignoreMissing = ignoreMissing

class debugTagSafe(debugdumper, TagSafety): pass
#class debugTagSafe(TagSafety): pass

class TrackInfo(object):

    __metaclass__ = debugTagSafe
    
    __artist = ""
    __title = ""
    __number = 0
    __playLength = 0
    
    # XXX: generate set/get methods from dict
    def __init__(self):
        return

    def validate(self):
        props = "artist", "title", "number", "playLength"
        missing = []
        for prop in props:
            try:
                getattr(self, prop)
            except TagIncompleteWarning, warn:
                missing.append(warn.getMissing())
        return missing
    
    def getArtist(self):
        return self._getString("artist")
    
    def setArtist(self, artist):
        self.__artist = artist

    def getTitle(self):
        return self._getString("title")

    def setTitle(self, title):
        self.__title = title

    def getPlayLength(self):
        return self._getInt("playLength")

    def setPlayLength(self, playlength):
        self.__playLength = playlength

    def getNumber(self):
        return self._getInt("number")
        
    def setNumber(self, number):
        self.__number = number
    
    artist = property(getArtist, setArtist)
    title = property(getTitle, setTitle)
    playLength = property(getPlayLength, setPlayLength)
    number = property(getNumber, setNumber)

class AlbumInfo(object):
    __tagversion = TAGVER
    tagprovider = 'none'

    __metaclass__ = debugTagSafe

    def __init__(self):
        self.__year = 0
        self.__genre = ""
        self.__artist = ""
        self.__title = ""
        self.__tracks = []
        self.__isVarious = False

    def readFootPrint(self, localalbum):
        'Read footprint common to all providers'
        self.__tagversion = localalbum.footprint('TNMU')

    def validate(self):
        props = ("year", "genre", "artist", "title", "tracks")
        self.ignoreMissing(False)
        missing = []
        for prop in props:
            try:
                getattr(self, prop)
            except TagIncompleteWarning, warn:
                missing.append(warn.getMissing())
        for track in self.tracks:
            missing.extend(track.validate())
        self.ignoreMissing(True)
        return missing
    
    def getYear(self):
        year = self._getInt("year")
        #if year < 1800 or year > 3000:
        #    raise TagIncompleteWarning("album year")
        return year

    def setYear(self, year):
        self.__year = year

    def getGenre(self):
        return self._getString("genre")
    
    def setGenre(self, genre):
        # XXX: apply normalizing function
        # example: Alt Rock and Alt. Rock -> Alternative Rock
        self.__genre = genre

    def getArtist(self):
        return self._getString("artist")
    
    def setArtist(self, artist):
        self.__artist = artist

    def getTitle(self):
        return self._getString("title")

    def setTitle(self, title):
        self.__title = title

    def getTracks(self):
        for track in self.__tracks:
            assert isinstance(track, TrackInfo)
        return self.__tracks
    
    def setTracks(self, tracks):
        self.__tracks = tracks

    def getTagVersion(self):
        return self.__tagversion
        
    def getIsVarious(self):
        return self.__isVarious
    
    def setIsVarious(self, isvarious):
        assert isinstance(isvarious, bool)
        self.__isVarious = isvarious

    year = property(getYear, setYear)
    genre = property(getGenre, setGenre)
    artist = property(getArtist, setArtist)
    title = property(getTitle, setTitle)
    tracks = property(getTracks, setTracks)
    tagversion = property(getTagVersion)
    isVarious = property(getIsVarious, setIsVarious)
