import os
import inspect
from glob import glob

from namingmuse.albuminfo import AlbumInfo

__all__ = []

def getModules():
    'Dynamically determine available modules.'
    modfile = os.path.abspath(__file__)
    modpath = os.path.dirname(modfile)
    modpattern = os.path.join(modpath, '*.py')
    modlist = glob(modpattern)
    modlist.sort()

    modules = {}
    for modfile in modlist:
        if modfile.endswith('__init__.py'):
            continue
        modname = os.path.basename(modfile)
        modname = os.path.splitext(modname)[0]
        mod = __import__(modname, globals())
        modules[modname] = mod
    return modules

def getProviders(modules):
    'Determine available providers.'
    providerclasses = {}
    for module in modules.values():
        for subname in vars(module):
            if '_' in subname: continue
            subobj = getattr(module, subname, None)
            if inspect.isclass(subobj) and issubclass(subobj, AlbumInfo):
                providerclasses[subname] = subobj
    return providerclasses

def lookup(tagprovider):
    'Translate provider name to actual class'
    for cls in providerclasses.values():
        if cls.tagprovider == tagprovider:
            return cls
    raise NamingMuseError("unknown provider: " + tagprovider)

modules = getModules()
providerclasses = getProviders(modules)
globals().update(providerclasses)
__all__ = modules.keys()

# Delete stuff we don't want to export
del glob, os, inspect
del modules, getModules, getProviders

if __name__ == "__main__":
    print 'all:', __all__
    print 'providers:', providerclasses
