"""
Contains filepath, a path representation class
$Id: 
"""

import os

class FilePath(object):
    """A class that represents a file path. 
       It also provides some useful and common methods regarding paths.
       """ 

    def __init__(self, path, *filep):
        if isinstance(path, FilePath):
            path = path.fullpath
        else:
            path = os.path.abspath(path)
        if len(filep) > 0:
            for f in filep:
                path = os.path.join(path, f)
        self.fullpath = path
    
    def getName(self):
        return os.path.basename(self.fullpath)
    
    def getParent(self):
        return FilePath(os.path.dirname(self.fullpath))

    def getExt(self):
        return os.path.splitext(self.fullpath)[1]

    def getFileType(self):
        return self.getExt()[1:].lower()

    def __add__(self, other):
        return FilePath(self, other)
        
    def __len__(self):
        return len(self.fullpath)
        
    def __str__(self):
        return self.fullpath
    
    def __repr__(self):
        return self.__str__()
    
    def __cmp__(self, other):
        if not isinstance(other, (FilePath, basestring)): 
            raise TypeError(\
                    "can't compare FilePath with non-FilePath/string object")
        if isinstance(other, FilePath):
            other = other.fullpath
        return cmp(self.fullpath, other)
