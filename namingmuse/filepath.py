"""
Contains filepath, a path representation class
$Id: 
"""

import os
from types import StringTypes

class FilePath(object):
    """A class that represents a file path. 
       It also provides some useful and common methods regarding paths.
       """ 

    def __init__(self, path, *filep):
        path = os.path.abspath(str(path))
        if len(filep) > 0:
            for f in filep:
                path = os.path.join(path, str(f))
        self.fullpath = path
    
    def getName(self):
        return os.path.basename(self.fullpath)
    
    def getParent(self):
        return os.path.dirname(self.fullpath)

    def getExt(self):
        return os.path.splitext(self.fullpath)[1]

    def getFileType(self):
        return self.getExt()[1:].lower()

    def __add__(self, other):
        return FilePath(str(self), str(other))
        
    def __len__(self):
        return len(str(self))
        
    def __str__(self):
        return self.fullpath
    
    def __repr__(self):
        return str(self)
    
    def __cmp__(self, other):
        if not isinstance(other, (FilePath, StringTypes)): 
            raise TypeError(\
                    "can't compare FilePath with non-FilePath/string object")
        return cmp(str(self), str(other))
