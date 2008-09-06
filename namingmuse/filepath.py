"""
Contains filepath, a path representation class
$Id: 
"""

import os
from musexceptions import *

class FilePath(object):
    """A class that represents a file path. 
       It also provides some useful and common methods regarding paths.
       """ 

    def __init__(self, path, *filep, **kwargs):
        if 'encoding' in kwargs:
            self.encoding = kwargs['encoding']
        else:
            self.encoding = 'ascii'
        if isinstance(path, FilePath):
            path = path.fullpath
        else:
            path = os.path.abspath(path)
        if len(filep) > 0:
            path = os.path.join(path, *filep)
        self.fullpath = path
    
    def getName(self, unicode=False):
        s = os.path.basename(self.fullpath)
        if unicode:
            s = self.decode(s)
        return s
    
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
        s = self.fullpath
        return s

    def decode(self, s):
        try:
            s = s.decode(self.encoding)
        except Exception, e:
            print NamingMuseWarning('failed to decode path %s with encoding %s' % (s, self.encoding))
            s = s.decode(self.encoding, 'ignore')
        return s

    def __unicode__(self):
        return self.decode(self.fullpath)
    
    def __repr__(self):
        return self.__str__()
    
    def __cmp__(self, other):
        if not isinstance(other, (FilePath, basestring)): 
            raise TypeError(\
                    "can't compare FilePath with non-FilePath/string object")
        if isinstance(other, FilePath):
            other = other.fullpath
        return cmp(self.fullpath, other)
    
    def rename(self, dst):
        os.rename(str(self), str(dst))

    def mkdir(self):
        os.mkdir(str(self))

    def rmdir(self):
        os.rmdir(str(self))

    def exists(self):
        os.path.exists(str(self))
