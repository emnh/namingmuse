"""Frontend for the namingmuse tools.
"""
import sys,os,stat
import albumtag
from discmatch import DiscMatch
import searchfreedb
import terminal
from sys import exit
from optparse import OptionParser, make_option
from optparse import OptionGroup
from albuminfo import *
from filepath import FilePath

from exceptions import *
import cddb

def makeOptionParser():
    op = OptionParser()
    op.set_usage("%prog <actionopt> [options] <albumdir>")

    op.add_option("", 
                  "--dry-run",
                  action = "store_true",
                  dest = "dryrun",
                  help= "don't modify anything, just pretend"
                  )

    op.add_option("-n",
                  "--namefix",
                  action = "store_const",
                  const = "namefix",
                  dest = "cmd",
                  help = "Namefix given files"
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
                  "--force-update",
                  action = "store_true",
                  dest = "updatetags",
                  help = "update files already tagged with same version")
    op.add_option("-r",
                  "--recursive",
                  action = "store_true",
                  help = "recurse directories")

    op.add_option("-A",
                  "--artistdir",
                  action = "store_true",
                  dest = "artistdir",
                  help = "place albumdir in artist/albumdir")

    op.add_option("", 
                  "--loose",
                  dest = "strict",
                  action = "store_false",
                  default = True,
                  help = "allow nmuse to work with missing tag information")

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
    doc += DiscMatch.__doc__ + "\n"
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

    albumdir = FilePath(args[0])

    try: 
        os.listdir(str(albumdir))
    except OSError, (errno, strerror):
        exit(strerror + ": " + str(albumdir))

    exitstatus = 0

    try:
        if options.cmd == "discmatch":
            discmatch = DiscMatch()
            if options.recursive:
                def walk(top):
                    try:
                        names = os.listdir(str(top))
                    except os.error:
                        return
                    try:
                        if top.getName() != "nonalbum":
                            doDiscmatch(options, top, discmatch)
                    except cddb.CDDBPException, err:
                        if err.code == cddb.CDDB_CONNECTION_TIMEOUT:
                            print "Connection timed out, reconnecting.."
                            discmatch.cddb.connect()
                    except NoFilesException:
                        pass
                    except NamingMuseException,(errstr):
                        print errstr
                    for name in names:
                        name = FilePath(top, name)
                        try:
                            st = os.lstat(str(name))
                        except os.error:
                            continue
                        if stat.S_ISDIR(st.st_mode):
                            walk(name)
                walk(albumdir)
            else:
               doDiscmatch(options, albumdir, discmatch)
        elif options.cmd == "search":
            doFullTextSearch(albumdir, options)
        elif options.cmd == "namefix":
            namefix(albumdir,options)
        else:
            exit("error: no action option specified")
    except NamingMuseException, strerr:
        print strerr 
        exitstatus = 1
    except NamingMuseWarning, strerr:
        print strerr
        exitstatus = 2
    except NoFilesException, strerr:
        print strerr 
        exitstatus = 3
    except cddb.CDDBPException, strerr:
        print strerr
        exitstatus = 4
        
    exit(exitstatus)

def namefix(albumdir, options):
    from namefix import namefix
    from terminal import colorize
    filelist = albumtag.getfilelist(albumdir)
    for filepath in filelist:
        tofile = albumdir + namefix(filepath.getName())
        renamesign = "->"
        if options.dryrun:
            renamesign = "-dry->" 
        print filepath
        print "\t", colorize(renamesign), tofile
        if not options.dryrun:
            os.rename(filename, str(tofile))

    todir = namefix(albumdir.getName())
    print "\n", albumdir.getName()
    print "\t", colorize(renamesign), todir
    if not options.dryrun:
        os.rename(str(albumdir), str(FilePath(albumdir.getParent(), todir)))

#XXX: merge common stuff of fulltextsearch and discmatch
def doFullTextSearch(albumdir, options):
    discmatch = DiscMatch()
    filelist = albumtag.getfilelist(albumdir)
    if len(filelist) == 0:
        raise NoFilesException("Warning: %s contains no music files !" %albumdir)

    if not options.words:
        raise NamingMuseError("no search words specified")
    if options.all:
        searchfields = searchfreedb.allfields
    else:
        optfilter = lambda key, options = options: eval("options." + key)
        searchfields = filter(optfilter, searchfreedb.allfields)
    searchwords = options.words

    print "Searching for albums.."
    if len(searchfields) > 0:
        albums = searchfreedb.searchalbums(searchwords, searchfields)
    else:
        albums = searchfreedb.searchalbums(searchwords)

    if len(albums) == 0:
        raise NamingMuseError("No match for text search %s" % (searchwords))

    albums = searchfreedb.filterBySongCount(albums, len(filelist))

    albuminfos, haveread = [], {}
    for album in albums:
        haveread.setdefault(album['cddbid'], [])
        if not album['genreid'] in haveread.get(album['cddbid']):
            freedbrecord = discmatch.cddb.getRecord(album['genreid'], 
                                                    album['cddbid'])
            albuminfo = FreeDBAlbumInfo(discmatch.cddb,
                                        album['genreid'], album['cddbid'])
            albuminfos.append(albuminfo)
            haveread[album['cddbid']].append(album['genreid'])

    if len(albuminfos) == 0:
        raise NamingMuseError("No matches in folder %s" % albumdir)
    
    albuminfo = choosealbum(albuminfos, albumdir, options)

    if not albuminfo:
        raise NamingMuseWarning('Not tagging %s' \
                   %(albumdir))

    albumtag.tagfiles(albumdir, albuminfo, options, \
            albumtag.namebinder_strapprox_time)


def doDiscmatch(options, albumdir, discmatch):
    filelist = albumtag.getfilelist(albumdir)
    if len(filelist)== 0:
        raise NoFilesException("Warning: %s contains no music files !" \
                %albumdir)
    
    if options.printtoc:
        discmatch.printTOC(filelist)
        exit()

    cddb = discmatch.cddb

    # Check/retrieve already tagged
    albuminfo = None
    if not options.force:
        albuminfo = albumtag.getNmuseTag(filelist)
    if albuminfo \
       and albuminfo.getTagVersion() == albumtag.TAGVER \
       and not options.updatetags: 
        raise NamingMuseWarning(\
                '%s already tagged with %s %s, not retagging.' \
                   %(albumdir, "namingmuse", albumtag.TAGVER))

    if not albuminfo:
        query = discmatch.files2discid(filelist)
        statusmsg, albums = discmatch.freedbTOCMatchAlbums(query)
        if len(albums) == 0:
            raise NamingMuseError("No freedb match for id %08x in folder %s" \
                                    %(query[0], albumdir))
        albuminfos = []
        for album in albums:
            albuminfo = FreeDBAlbumInfo(cddb, album['genreid'], album['cddbid'])
            albuminfos.append(albuminfo)
            
        albuminfo = terminal.choosealbum(albuminfos, albumdir, options)
        if not albuminfo:
            raise NamingMuseWarning('Not tagging %s' \
                       %(albumdir))
    else:
        albuminfo.setCDDBConnection(cddb)

    albumtag.tagfiles(albumdir, albuminfo, options, \
            albumtag.namebinder_trackorder)

if __name__ == "__main__": cli()
