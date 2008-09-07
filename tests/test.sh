#!/bin/bash

function createalbum {
    dir="$1"
    songs="$2"
    format="$3"
    mkdir -p "$dir"
    for i in `seq -w 1 $songs`; do
        cp $testfname.$format $dir/$i.$format
    done
}

function die {
    exit 1
}

nmuse=$PWD/../nmuse
prefix=$PWD/testdir
testfname=$PWD/test

rm -rf $prefix
mkdir -p $prefix

formats="mp3 ogg mpc flac"

# basic cddb tests
for format in $formats; do
    album="$prefix/moon-safari/$format/test"
    createalbum "$album" 10 $format
    $nmuse -c jazz/870a3d0a "$album" || die
done

# basic cddb update test, force local test
for format in $formats; do
    album="$prefix/moon-safari/$format/1998 Moon Safari"
    $nmuse -u "$album" || die
    $nmuse -f -l "$album" || die
    $nmuse -n "$album" || die
done

# encoding test, bjork
for format in $formats; do
    album="$prefix/bjork/$format/test"
    createalbum "$album" 15 $format
    $nmuse --loose -A -c newage/cb0ff50f "$album" || die
done

# musicbrainz test, with encoding
for format in $formats; do
    album="$prefix/hellsing/$format/test"
    createalbum "$album" 19 $format
    $nmuse --mb-album a38e20a5-ec66-4f4d-80ce-3d6eb0ee4bb2 "$album" || die
done

# TODO more tests:
# namebinders
# recursion
# read back tags and verify
# verify that tags are encoded as specified by the user
