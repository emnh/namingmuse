
"Contains filepath, a path representation class"

import os

class FilePath:
    "Path representation class"
    def __init__(self, path, file = None):
        if file: path = os.path.join(path, file)
        self.fullpath = os.path.abspath(path)
    
    def getName(self):
        return os.path.basename(self.fullpath)
    
    def getParent(self):
        return os.path.dirname(self.fullpath)
        
    def __str__(self):
        return self.fullpath


