
import os
from glob import glob

__all__ = []

def getModules():
    'dynamically determine available modules'
    modfile = os.path.abspath(__file__)
    modpath = os.path.dirname(modfile)
    modpattern = os.path.join(modpath, '*.py')
    modlist = glob(modpattern)

    modules = []
    for module in modlist:
        module = os.path.basename(module)
        module = os.path.splitext(module)[0]
        modules.append(module)
    return modules

__all__ = getModules()
try:
    __all__.remove('__init__')
except ValueError:
    pass

if __name__ == "__main__":
    print __all__
