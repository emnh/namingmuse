#!/usr/bin/env python

# XXX: this module should be integrated in providers/__init__.py

import inspect
from glob import glob

from namingmuse import providers
from namingmuse.providers import *
from namingmuse.providers.albuminfo import AlbumInfo

providerclasses = {}

def getProviders():
    providerclasses = {}
    for modname in providers.__all__:
        obj = eval(modname)
        for subname in dir(obj):
            if '_' in subname: continue
            subobj = getattr(obj, subname, None)
            if inspect.isclass(subobj) and issubclass(subobj, AlbumInfo):
                providerclasses[subname] = subobj
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
