
from glob import glob
import os, re, sys

__all__ = []

# dynamically determine available modules
modfile = os.path.abspath(__file__)
modpath = os.path.dirname(modfile)
modpattern = os.path.join(modpath, '*.py')
modlist = glob(modpattern)

for module in modlist:
    module = os.path.basename(module)
    __all__ += [os.path.splitext(module)[0]]

try:
    __all__.remove('__init__')
except ValueError:
    pass

if __name__ == "__main__":
    print __all__
