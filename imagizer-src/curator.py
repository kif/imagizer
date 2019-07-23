# !/usr/bin/env python
# coding: utf-8

__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "23/07/2019"
__license__ = "GPL"

import os
import json
import logging
import stat
import urllib

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
            with open(filename) as fp:
                data = json.load(fp)
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
        return urllib.quote(text.replace("\\", "/"))
    else:
        return urllib.quote(text)
