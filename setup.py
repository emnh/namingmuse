#!/usr/bin/env python

"""Setup script"""

from distutils.core import setup
import os

authors = [
           {'name': 'Tor Hveem',
            'mail': 'torh at bash dot no'},
           {'name': 'Eivind Magnus Hvidevold', 
            'mail': 'emh at hvidevold dot cjb dot net'}
          ]

name = 'namingmuse'
author = authors[-1]['name']
author_email = 'namingmuse-devel@lists.berlios.de'
version = "0.9.0"
description = "A toolkit for dealing with music tags."
license = "GPL"
url = 'http://namingmuse.berlios.de/' 
download_url = url + name + "-" + version + ".tar.gz"
packages = [ 'namingmuse', 'namingmuse.providers' ]
platforms = ['OS Independent']
scripts = ['nmuse']

long_description = """A toolkit for cleaning up audio filenames,
settings tags and renaming, using freedb to get metainfo.
The freedb modules supports discid generation
and full text search with string approximation
in binding the freedb metainfo to files."""

classifiers = [
'Development Status :: 5 - Production/Stable',
'Environment :: Console',
'Intended Audience :: End Users/Desktop',
'License :: OSI Approved :: GNU General Public License (GPL)',
'Natural Language :: English'
'Operating System :: Linux',
'Programming Language :: Python',
'Topic :: Multimedia :: Sound/Audio',
]

os.umask(022)

setup(
    author = author,
    author_email = author_email,
    classifiers = classifiers,
    download_url = download_url,
    license = license,
    long_description = long_description,
    platforms = platforms,
    url = url,
    description = description,
    name = name,
    scripts = scripts,
    packages = packages,
    version = version
)
