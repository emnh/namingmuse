
from terminal import colorize

class NamingMuseException(Exception):
    "Base class for namingmuse exceptions"
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        return colorize(self.value)

class NamingMuseError(NamingMuseException):
    def __init__(self, msg):
        super = NamingMuseError.__bases__[0]
        super.__init__(self, "Error: " + msg)

class NamingMuseWarning(NamingMuseException):
    def __init__(self, msg):
        super = NamingMuseWarning.__bases__[0]
        super.__init__(self, "Warning: " + msg)

class TagIncompleteWarning(NamingMuseWarning):
    "Warning for incomplete tag info"
    def __init__(self, missingtag):
        super = TagIncompleteWarning.__bases__[0]
        super.__init__(self, missingtag + " is missing")

class NoFilesException(NamingMuseException): pass

class HTTPServerError(NamingMuseError): pass

class NotImplementedError(NamingMuseError): pass
