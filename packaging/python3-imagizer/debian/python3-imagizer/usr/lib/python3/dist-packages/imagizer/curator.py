# !/usr/bin/env python3
# coding: utf-8

__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "23/03/2023"
__license__ = "GPL"

import os
import json
import logging
import stat
import urllib.parse
from collections import namedtuple
SplitName = namedtuple("SplitName", "dir base repn ext")
logger = logging.getLogger(__name__)


class Entry(object):

    def __init__(self, fn, mtime, size, info):
        self.fn = fn
        self.mtime = int(mtime)
        self.size = int(size)
        self.info = info

    def __repr__(self):
        return '"%s" %d %d: %s\n' % (self.fn, self.mtime, self.size, self.info)

    def as_tuple(self):
        return (self.fn, self.mtime, self.size, self.info)


class FCache:
    "A class which handles the cache for the image size "

    def __init__(self, filename=None):
        "Initialize the fcache, reading the given file."
        self.cachefn = None
        self.entries = {}
        if (filename is not None) and os.path.exists(filename):
            self.load(filename)

    def load(self, filename):
        "Initialize the cache from disk"
        self.cachefn = filename
        if os.path.exists(filename):
            try:
                with open(filename) as fp:
                    data = json.load(fp)
            except Exception as error:
                logger.error("Unable to parse saved JSON data: discarding them")
                os.unlink(filename)
            else:
                for entry in data:
                    self.entries[entry[0]] = Entry(*entry)

    def store(self, fn, info):
        s = os.stat(fn)
        self.entries[fn] = Entry(fn, s[stat.ST_MTIME], s[stat.ST_SIZE], info)

        if self.cachefn is not None:
            # write out cache
            try:
                with open(self.cachefn, 'w') as fp:
                    json.dump([e.as_tuple() for e in self.entries.values()], fp)
            except IOError as err:
                logger.error("Error writing-out cache: %s" % err)

    def lookup(self, fn):
        try:
            e = self.entries[fn]
        except KeyError:
            return None

        s = os.stat(fn)
        if e.mtime != s[stat.ST_MTIME] or e.size != s[stat.ST_SIZE]:
            return None

        return e.info

    def dump(self):
        print("Cache filename: %s", self.cachefn)
        print()
        for e in self.entries.values():
            print("filename: %s" % e.fn)
            print("mtime: %s" % e.mtime)
            print("size: %s" % e.size)
            print("info: %s" % e.info)
            print()


def urlquote(text):
    """same as urllib.quote but windows compliant"""
    if os.path.sep == "\\":
        return urllib.parse.quote(text.replace("\\", "/"))
    else:
        return urllib.parse.quote(text)


def full_split_path(path):
    """Splits a path into a list of components.

    In a sense it it similar to path.split(os.sep)
    This function works around a quirk in string.split().

    :param path: a string
    :return: a list of directory names.

    """
    if not path:
        return []

    first, second = os.path.split(path)
    result = [second]
    while first:
        first, second = os.path.split(first)
        result.insert(0, second)
    return result


def relative_path(dest, curdir):
    """Relative path to curdir

    :param dest: a path
    :param curdir: the current path
    :return: relative path of dest to curdir.
    """

    sc = full_split_path(curdir)
    sd = full_split_path(dest)

    while sc and sd:
        if sc[0] != sd[0]:
            break
        sc = sc[1:]
        sd = sd[1:]

    if len(sc) == 0 and len(sd) == 0:
        out = ""
    elif len(sc) == 0:
        out = os.path.join(*sd)
    elif len(sd) == 0:
        out = os.path.join(* ([os.pardir] * len(sc)))
    else:
        out = os.path.join(*([os.pardir] * len(sc) + list(sd)))

    # make sure the path is suitable for html consumption
    return out


def split_filename(filename, separator):
    """Returns a NamedTuple (dir, base, repn, ext).

    The repn is split using separator.
    The separator should not be present more than once.
    Repn is '' if not present.

    :param filename: the path for a filename
    :param separator: the separator for the representation, usually "--"
    :return: SplitName namedtuple which contains (dir, base, repn, ext)
    """

    (directory, basename) = os.path.split(filename)

    fidx = basename.find(separator)
    if fidx != -1:
        # found separator, add as an alt repn
        base = basename[:fidx ]
        (repn, ext) = os.path.splitext(basename[fidx + len(separator):])
    else:
        # didn't find separator, split using extension
        (base, ext) = os.path.splitext(basename)
        repn = ''
    return SplitName(directory, base, repn, ext)


def check_thumbnail_size(image_size, thumbnail_size, desired):
    """Returns true if the sizepair fits the size.

    :param image_size: Size of the image as 2-tuple
    :param thumbnail_size: size of the thumbnail as 2-tuple
    :param desired: maximum dimention size of the image
    :return: True if the size match expectation, else 0 or False
    """

    # tolerate 2% error
    try:
        if abs(float(image_size[0]) / image_size[1] - float(thumbnail_size[0]) / thumbnail_size[1]) > 0.02:
            # Extra checks for panoramic images
            if abs(desired - thumbnail_size[0]) <= 1:
                expected = float(image_size[1] * thumbnail_size[0]) / float(image_size[0])
                return abs(expected - thumbnail_size[1]) <= 1
            elif abs(desired - thumbnail_size[1]) <= 1:
                expected = float(image_size[0] * thumbnail_size[1]) / float(image_size[1])
                return abs(expected - thumbnail_size[0]) <= 1
            else:
                return 0  # aspect has changed, or image_size rotated
    except:
        return 0
    return abs(desired - thumbnail_size[0]) <= 1 or abs(desired - thumbnail_size[1]) <= 1
