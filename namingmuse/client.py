"""Frontend for the namingmuse tools.
"""
import sys,os
import albumtag
import discmatch
import searchfreedb
import terminal
from sys import exit
from optparse import OptionParser, make_option
from optparse import OptionGroup

from exceptions import *

def makeOptionParser():
    op = OptionParser()
    op.set_usage("%prog <actionopt> [options] <albumdir>")

    op.add_option("-n", 
                  "--dry-run",
                  action = "store_true",
                  dest = "dryrun",
                  help= "don't modify anything, just pretend"
                  )

    op.add_option("-t",
                  "--tag-only",
                  action = "store_true",
                  dest = "tagonly",
                  help = "do not rename files, only set tags")
                  
    op.add_option("-f",
                  "--force",
                  action = "store_true",
                  help = "force new lookup and retagging")

    op.add_option("-u",
                  "--update-tags",
                  action = "store_true",
                  dest = "updatetags",
                  help = "update files already tagged, using stored discid")

    op.add_option("", 
                  "--strict",
                  action = "store_true",
                  help = "bail out if any tag information is missing")

    op.add_option("",
                  "--doc",
                  action = "store_true",
                  help = "print module documentation"
                  )

    actionopts = OptionGroup(op,
                             "action options",
                             "you need one of these to get something done")

    op.add_option_group(actionopts)

    actionopts.add_option("-d", "--discmatch",
                                const = "discmatch",
                                action = "store_const",
                                dest = "cmd",
                                help = "tag and rename files using discid toc match (default)"
                                )
                                
    actionopts.add_option("-s", "--search",
                                action = "append",
                                dest = "words",
                                help = "tag and rename files using fulltext search"
                                )

    dopts = OptionGroup(op, "discmatch options")
    op.add_option_group(dopts)
    dopts.add_option("-p",
                     "--print-toc",
                     action = "store_true",
                     dest = "printtoc",
                     help = "print calculated TOC of the album, then exit")

    sopts = OptionGroup(op, "search options")

    sopts.add_option("-a", 
                     "--all",
                     action = "store_true",
                     help = "enable searching of all fields (default: artist+title)")

    for field in searchfreedb.allfields:
        sopts.add_option("",
                         "--" + field,
                         action = "store_true",
                         help = "enable searching of " + field + " field")

    op.add_option_group(sopts)
    return op

def getDoc():
    doc = "\n"
    doc += "ALBUMTAG\n"
    doc += albumtag.__doc__ + "\n"
    doc += "SEARCH" + "\n"
    doc += searchfreedb.__doc__ + "\n"
    doc += "DISCMATCH" + "\n"
    doc += discmatch.__doc__ + "\n"
    return doc

def cli():
    op = makeOptionParser()
    options,args = op.parse_args()

    if options.doc:
        print getDoc()
        exit()

    if len(args) == 0:
        op.print_help()
        exit("error: <albumdir> not specified")
    elif not options.cmd and len(args) >= 1:
        options.cmd = "discmatch"

    if options.words:
        options.cmd = "search"

    albumdir = args[0]

    try: 
        os.listdir(albumdir)
    except OSError, (errno, strerror):
        exit(strerror + ": " + albumdir)

    try:
        if options.cmd == "discmatch":
            doDiscmatch(albumdir,options)
        elif options.cmd == "search":
            searchfreedb.search(albumdir, options)
        else:
            exit("error: no action option specified")
    except NamingMuseException, strerr:
        exit(strerr)
    except NamingMuseWarning, strerr:
        exit(strerr)
    except NoFilesException, strerr:
        exit(strerr)
    
def doDiscmatch(albumdir, options):
    filelist = albumtag.getfilelist(albumdir)
    if len(filelist)== 0:
        raise NoFilesException("Warning: %s contains no music files !" %albumdir)
    
    if options.printtoc:
        discmatch.printTOC(filelist)
        exit()

    # Check if it is already tagged
    if not albumtag.needTag(filelist) \
       and not options.updatetags \
       and not options.force:
        raise NamingMuseWarning('%s already tagged with %s %s, not retagging...' \
                   %(albumdir, albumtag.tagname, albumtag.tagver))

    albumdict = None
    if options.updatetags:
        identifier = albumtag.getStoredCDDBId(filelist)
        albumdict = discmatch.getalbuminfo(identifier['genreid'], identifier['cddbid'])
    if options.force:
        albumdict = None
    if not albumdict:
        query = discmatch.files2discid(filelist)
        statusmsg, albums = discmatch.freedbTOCMatchAlbums(query)
        if len(albums) == 0:
            raise NamingMuseError("No freedb match for id %08x in folder %s" % (query[0], albumdir))
        albumdicts = []
        for album in albums:
            albumdicts.append(discmatch.getalbuminfo(album['genreid'],album['cddbid']))
        albumdict = terminal.choosealbum(albumdicts, albumdir)
        if not albumdict:
            raise NamingMuseWarning('Not tagging %s' \
                       %(albumdir))

    albumtag.tagfiles(albumdir, albumdict, options, \
            albumtag.namebinder_trackorder)

if __name__ == "__main__": cli()
