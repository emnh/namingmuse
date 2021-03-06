"""
CLI frontend for the various namingmuse modules.
It has three main modes, a searcher (useful if an album doesn't match in freedb)
, a discmatcher which tries to match an album in freedb and
a namefixer module which just tries to prettify filenames.

$Id: 
"""
import copy
import os
import stat
import sys
import re
import time
from sys import exit
from optparse import OptionParser, OptionGroup, make_option
from ConfigParser import *

from namingmuse import albumtag
from namingmuse import providers
from namingmuse import searchfreedb
from namingmuse import terminal
from cddb import CDDBP, CDDBPException, CDDB_CONNECTION_TIMEOUT, \
        CDDB_ALREADY_READ
from discmatch import DiscMatch
from filepath import FilePath
from musexceptions import *
from providers import LocalAlbumInfo, FreeDBAlbumInfo, MusicBrainz2AlbumInfo
from providers.mbrainz2 import searchMBAlbum

def makeOptionParser():
    op = OptionParser()
    op.set_usage("%prog <actionopt> [options] <albumdir>")

    
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
    
    op.add_option("",
                  "--ignore",
                  action = "append",
                  dest = 'ignore',
                  help = "ignore paths matching regex. useful with -r")

    op.add_option("-A",
                  "--artistdir",
                  action = "store_true",
                  dest = "artistdir",
              help = "place albumdir in artist/albumdir if not already there")

    op.add_option("-v",
                  "--verbose",
                  action = "store_true",
                  help = "be more verbose")
    
    op.add_option("",
                  "--dry-run",
                  action = "store_true",
                  dest = "dryrun",
                  help= "don't modify anything, just pretend")

    op.add_option("",
                  "--loose",
                  dest = "strict",
                  action = "store_false",
                  default = True,
                  help = "allow nmuse to work with missing tag information")

    op.add_option("",
                  "--doc",
                  action = "store_true",
                  help = "print module documentation")

    op.add_option("",
                  "--namebinder",
                  action = "store",
                  dest = "namebinder",
                  help = "select namebinder: trackorder/filenames/" +
                         "filenames+time/manual")
    op.add_option("",
                  "--mb-accurate",
                  action = "store_false",
                  dest = 'mb_fast',
                  help = '''default is to speed up musicbrainz search by assuming that the first track is on the right album.
                            use this option to look up album for all tracks.
                          ''')

    actionopts = OptionGroup(op,
                             "action options",
                             "you need one of these to get something done")

    op.add_option_group(actionopts)

    actionopts.add_option("-d",
                          "--discmatch",
                          const = "discmatch",
                          action = "store_const",
                          dest = "cmd",
                          help = "tag and rename files using discid" +
                                 " toc match (default)")
                                
    actionopts.add_option("-c",
                  "--cddb",
                  action = "store",
                  dest = "cddb",
                  help = "use explicitly specified cddb disc to name files." + 
                         " ex: data/7a0a2f0a")

    actionopts.add_option("-m",
                          "--musicbrainz2",
                          const = "musicbrainz2",
                          action = "store_const",
                          dest = "cmd",
                          help = "tag and rename files using musicbrainz")

    actionopts.add_option("",
                  "--mb-album",
                  action = "store",
                  dest = "releaseid",
                  help = "use explicitly specified musicbrainz release id to name files. " +
                         "ex: 77d9e53d-f6d3-4a13-bf39-fb63d02a7f94")
     
    actionopts.add_option("-s", 
                          "--search",
                          action = "append",
                          dest = "words",
                          help = "tag and rename files using fulltext search")

    actionopts.add_option("-n",
                  "--namefix",
                  action = "store_const",
                  const = "namefix",
                  dest = "cmd",
                  help = "rename files according to predefined rules")

    actionopts.add_option("-l",
                  "--local",
                  action = "store_const",
                  const = "local",
                  dest = "cmd",
          help = "use locally existing metadata instead of doing remote lookup")

    actionopts.add_option("",
                          "--stats",
                          action = "store_const",
                          const = "stats",
                          dest = "cmd",
                          help = "print out statistics on local files"
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
    """ Return documentation in the various modules. """
    from namingmuse import albuminfo
    import cddb, policy, coverfetcher
    doc = "\n"
    doc += "ALBUMTAG\n"
    doc += albumtag.__doc__ + "\n"
    doc += "ALBUMINFO\n"
    doc += albuminfo.__doc__ + "\n"
    doc += "CDDB\n"
    doc += cddb.__doc__ + "\n"
    doc += "COVERFETCHER\n"
    doc += coverfetcher.__doc__ + "\n"
    doc += "SEARCH" + "\n"
    doc += searchfreedb.__doc__ + "\n"
    doc += "DISCMATCH" + "\n"
    doc += DiscMatch.__doc__ + "\n"
    doc += "NAMEFIX" + "\n"
    doc += namefix.__doc__ + "\n"
    doc += "STATS" + "\n"
    doc += stats.__doc__ + "\n"
    doc += "POLICY" + "\n"
    doc += policy.__doc__ + "\n"
    return doc

defaultconfig = {
'tagencoding': 'iso-8859-15',
'sysencoding': 'utf-8',
'autoselect': 'False',
'mb_fast': 'True',
'ignore': []
}

def readconfig(options):
    home = os.getenv("HOME")
    homeconfdir = FilePath(home, ".namingmuse")
    configfile = homeconfdir + "config"
    cp = ConfigParser(defaultconfig)
    if os.access(str(configfile), os.R_OK):
        cp.read([str(configfile)])
    defitems = cp.items("DEFAULT")
    for key, value in dict(defitems).items():
        if str(value).lower() == "true":
            value = True
        elif str(value).lower() == "false":
            value = False
        options.ensure_value(key, value)
    if options.sysencoding == 'terminal':
        options.sysencoding = sys.stdout.encoding
    if options.tagencoding == 'terminal':
        options.tagencoding = sys.stdout.encoding
    if isinstance(options.ignore, basestring):
        options.ignore = [options.ignore]

def cli():
    op = makeOptionParser()
    options, args = op.parse_args()

    readconfig(options)

    if options.doc:
        print getDoc()
        exit()

    if len(args) == 0:
        op.print_help()
        exit(0)

    if not options.cmd and len(args) >= 1:
        options.cmd = "discmatch"

    if options.cmd and len(args) == 0:
        op.print_help()
        exit("error: <albumdir> not specified")

    if options.words:
        options.cmd = "search"

    if options.cddb:
        options.cmd = 'cddb'

    if options.releaseid:
        options.cmd = 'releaseid'

    albumdir = FilePath(args[0])

    try:
        os.listdir(str(albumdir))
    except OSError, (errno, strerror):
        exit(strerror + ": " + str(albumdir))

    exitstatus = 0

    try:
        cddb = CDDBP()
        if options.cmd == "discmatch":
            discmatch = DiscMatch()
            if options.recursive:
                walk(albumdir, cddb, options)
            else:
                doDiscmatch(options, albumdir, cddb)
        elif options.cmd == "search":
            doFullTextSearch(albumdir, options, cddb)
        elif options.cmd == "cddb":
            match = re.search(r'([^/]+)/([^/]+)$', options.cddb)
            genre, discid = match.group(1), match.group(2)
            albuminfo = checkAlreadyTagged(albumdir, options)
            if not albuminfo:
                albuminfo = FreeDBAlbumInfo(cddb, genre, discid)
                albumtag.tagfiles(albumdir, albuminfo, options)
        elif options.cmd == 'musicbrainz2':
            if options.recursive:
                walk2(albumdir, options)
            else:
               doMusicbrainz(options, albumdir)
        elif options.cmd == 'releaseid':
            albuminfo = MusicBrainz2AlbumInfo(options.releaseid)
            albumtag.tagfiles(albumdir, albuminfo, options)
        elif options.cmd == "local":
            if options.recursive:
                for root, dirs, files in albumdir.walk():
                    if len(dirs) > 0:
                        for dir in dirs:
                            try:
                                doLocal(FilePath(root, dir), options)
                            except NoFilesException:
                                pass
                            except NamingMuseInfo, err:
                                print err
                            except NamingMuseWarning, strerr:
                                print strerr
            #the recursive function doesn't run doLocal on the root
            #so we have to do it either way
            doLocal(albumdir, options)
        elif options.cmd == "namefix":
            namefix(albumdir, options)
        elif options.cmd == "stats":
            stats(albumdir, options)
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
    except CDDBPException, strerr:
        print strerr
        exitstatus = 4
        
    exit(exitstatus)

def walk2(top, options):
    ''''I assume this walk method is here (as opposed to using os.walk) because
    we modify the directory tree by renaming directories?'''

    try:
        names = os.listdir(str(top))
    except os.error:
        return
    try:
        if not isIgnored(options, top):
            doMusicbrainz(options, top)
    except NoFilesException:
        pass
    except NamingMuseException,(errstr):
        print errstr
    for name in names:
        name = FilePath(top, name)
        if name.isdir():
            walk2(name, options)

def walk(top, cddb, options):
    ''''I assume this walk method is here (as opposed to using os.walk) because
    we modify the directory tree by renaming directories?'''

    try:
        names = os.listdir(str(top))
    except os.error:
        return
    try:
        if not isIgnored(options, top):
            doDiscmatch(options, top, cddb)
    except CDDBPException, err:
        if err.code == CDDB_CONNECTION_TIMEOUT:
            print "Connection timed out, reconnecting.."
            cddb.reconnect()
        elif err.code == CDDB_ALREADY_READ:
            print '%s: %s is probably a duplicate album' % (str(err), top)
            # freedb shuts us down if we try to reread a record
            # XXX: this only happens on duplicate albums AFAIK, but we should
            # probably cache the records anyway.
            cddb.reconnect()
        else:
            print err
            cddb = CDDBP()
    except NoFilesException:
        pass
    except NamingMuseException,(errstr):
        print errstr
    for name in names:
        name = FilePath(top, name)
        if name.isdir():
            walk(name, cddb, options)

def isIgnored(options, fp):
    ignoreThis = False
    for ign in options.ignore:
        if re.search(ign, str(fp)):
            ignoreThis = True
            break
    return ignoreThis

def stats(albumdir, options):
    """
    Prints out statistics.
    """
    import statistics

    stats = statistics.Stats()

    if options.recursive:
        for root, dirs, files in albumdir.walk():
            if len(dirs) > 0:
                for dir in dirs:
                    fp = FilePath(root, dir)
                    if isIgnored(options, fp):
                        continue
                    try:
                        stats = statistics.dirstat(fp, stats, options.verbose)
                    except NamingMuseException, strerr:
                        print strerr
        #print '\n' + str(stats)
    else:
        print "This mode only makes sense in recursive mode (-r)"

def namefix(albumdir, options):
    """
    Prettifies filenames, see doc in the namefix module.
    """
    from namefix import namefix
    from terminal import colorize
    filelist = getFilelist(albumdir)
    
    renamesign = "->"
    if options.dryrun:
        renamesign = "-dry->" 
    
    for filepath in filelist:
        tofile = albumdir + namefix(filepath.getName())
        print filepath
        print "\t", colorize(renamesign), tofile
        if not options.dryrun:
            os.rename(str(filepath), str(tofile))

    todir = namefix(albumdir.getName())
    print "\n", albumdir.getName()
    print "\t", colorize(renamesign), todir
    if not options.dryrun:
        os.rename(str(albumdir), str(FilePath(albumdir.getParent(), todir)))

def doLocal(albumdir, options):
    filelist = getFilelist(albumdir)
    checkAlreadyTagged(albumdir, options)
    albuminfo = LocalAlbumInfo(albumdir)
    albumtag.tagfiles(albumdir, albuminfo, options)

def getFilelist(albumdir):
    lalb = LocalAlbumInfo(albumdir)
    filelist = lalb.getfilelist()
    return filelist

def checkAlreadyTagged(albumdir, options):
    albuminfo = None
    if not options.force:
        localalbum = LocalAlbumInfo(albumdir)
        albuminfo = providers.getRemoteAlbumInfo(localalbum)
        if albuminfo:
            # may have used --loose to get the album
            options = copy.copy(options)
            options.strict = False
    if albuminfo \
       and albuminfo.getTagVersion() == albumtag.TAGVER \
       and not options.updatetags:
        raise NamingMuseInfo(\
                '%s already tagged with %s %s, not retagging.' \
                   %(albumdir, "namingmuse", albumtag.TAGVER))
    return albuminfo

#XXX: merge common stuff of fulltextsearch and discmatch
def doFullTextSearch(albumdir, options, cddb):
    """
    Searches the cddb database given an albumdir and searchstrings.
    """
    filelist = getFilelist(albumdir)

    if not options.words:
        raise NamingMuseError("no search words specified")
    if options.all:
        searchfields = searchfreedb.allfields
    else:
        optfilter = lambda key, o = options: getattr(o, key)
        searchfields = filter(optfilter, searchfreedb.allfields)
    searchwords = options.words

    print "Searching for albums.."
    albums = searchfreedb.searchalbums(\
            albumdir, searchwords, searchfields, cddb)

    if len(albums) == 0:
        raise NamingMuseError(\
                "No match for search %s in %s" % (searchwords, albumdir))
    
    albuminfo = terminal.choosealbum(albums, albumdir, options, lambda: cddb.flush())

    if not albuminfo:
        raise NamingMuseWarning('Not tagging %s' \
                   %(albumdir))

    albumtag.tagfiles(albumdir, albuminfo, options)

def doMusicbrainz(options, albumdir):
    
    filelist = getFilelist(albumdir)

    albuminfo = checkAlreadyTagged(albumdir, options)

    if not albuminfo:
        # search
        releases = searchMBAlbum(albumdir, options.mb_fast)
        albuminfos = []
        ok = True
        if releases:
            for release in releases:
                mb = MusicBrainz2AlbumInfo(release)
                if len(getFilelist(albumdir)) == len(mb.tracks):
                    albuminfos.append(mb)

            if albuminfos:
                albuminfo = terminal.choosealbum(albuminfos, albumdir, options, None )

                if not albuminfo:
                    raise NamingMuseWarning('Not tagging %s' \
                               %(albumdir))
            else:
                ok = False
        else:
            ok = False
        if not ok:
            raise NamingMuseError("No musicbrainz album match for folder %s" % (albumdir))
        albumtag.tagfiles(albumdir, albuminfo, options)

def doDiscmatch(options, albumdir, cddb):
    """Takes a dir with a album inside and a cddb module.
    It then computes the cddb-info and queries a remote cddb server.
    Last, it renames and tags the album.
    """

    filelist = getFilelist(albumdir)
    
    if options.printtoc:
        DiscMatch.printTOC(filelist)
        exit()


    # Check/retrieve already tagged
    albuminfo = checkAlreadyTagged(albumdir, options)

    if not albuminfo:
        query = DiscMatch.files2discid(filelist)
        statusmsg, albums = DiscMatch.freedbTOCMatchAlbums(cddb, query)
        if len(albums) == 0:
            raise NamingMuseError("No freedb match for id %08x in folder %s" \
                                    %(query[0], albumdir))
        albuminfos = []
        for album in albums:
            albuminfo = FreeDBAlbumInfo(cddb, album['genreid'], album['cddbid'])
            albuminfos.append(albuminfo)
            
        albuminfo = terminal.choosealbum(albuminfos, albumdir, options, lambda: cddb.flush())
        if not albuminfo:
            raise NamingMuseWarning('Not tagging %s' \
                       %(albumdir))
    else:
        # update
        # we might be updating musicbrainz album
        if hasattr(albuminfo, 'setCDDBConnection'):
            albuminfo.setCDDBConnection(cddb)

    # Trackorder is the only one that makes sense here
    # (if they weren't in track order we wouldn't have matched)
    options.ensure_value('namebinder', 'trackorder')
    albumtag.tagfiles(albumdir, albuminfo, options)

if __name__ == "__main__": cli()
