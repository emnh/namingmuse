#!/usr/bin/env python

import providers.__init__
from providers import *
from providers.albuminfo import *
import inspect

providerclasses = {}

def getProviders():
    providerclasses = {}
    for modname in providers.__init__.__all__:
        obj = eval(modname)
        for subname in dir(obj):
            if '_' in subname: continue
            try:
                subobj = getattr(obj, subname)
                bases = subobj.__bases__
            except AttributeError:
                continue
            if AlbumInfo in bases:
                providerclasses[subname] = subobj
                __import__
    return providerclasses

# XXX: temporary
def lookup(tagprovider):
    for cls in providerclasses.values():
        if cls.tagprovider == tagprovider:
            return cls
    raise NamingMuseError("unknown provider: " + tagprovider)

providerclasses = getProviders()
gdict = globals()
gdict.update(providerclasses)
