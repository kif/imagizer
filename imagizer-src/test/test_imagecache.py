#!/usr/bin/env python
# coding: utf-8
"""Unit tests for imagizer.imagecache.ImageCache.

These guard the rename semantics relied upon by Photo.renameFile: after a file
is renamed, the cache entry must point at the up-to-date instance, not keep the
previously cached object (whose paths / pyexiv2 metadata are stale).
"""
import os
import sys
import types
import unittest
import importlib.util


def _load_imagecache():
    """Load imagecache.py in isolation, with stubbed config and sqlitedict.

    Works both from a source checkout (imagizer-src/) and from the installed
    package (imagizer/), since imagecache.py is a sibling of this test package's
    parent directory in both layouts.
    """
    pkgdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stub = "imagizer_imagecache_test_stub"
    pkg = types.ModuleType(stub)
    pkg.__path__ = [pkgdir]
    cfg = types.ModuleType(stub + ".config")

    class _Cfg:
        ImageCache = 100
        DefaultRepository = "/tmp"
        Database_file = "imagizer_test.db"

    cfg.config = _Cfg()
    sqld = types.ModuleType(stub + ".sqlitedict")
    sqld.SqliteDict = lambda *a, **k: {}
    sys.modules[stub] = pkg
    sys.modules[stub + ".config"] = cfg
    sys.modules[stub + ".sqlitedict"] = sqld
    spec = importlib.util.spec_from_file_location(
        stub + ".imagecache", os.path.join(pkgdir, "imagecache.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[stub + ".imagecache"] = mod
    spec.loader.exec_module(mod)
    return mod


imagecache = _load_imagecache()
ImageCache = imagecache.ImageCache


class TestImageCache(unittest.TestCase):

    def setUp(self):
        # ImageCache is a Borg (shared state): start each test from a clean slate.
        self.cache = ImageCache(maxSize=100)
        self.cache.maxSize = 100
        self.cache.ordered.clear()
        self.cache.imageDict.clear()

    def tearDown(self):
        self.cache.ordered.clear()
        self.cache.imageDict.clear()

    def test_setitem_getitem_contains(self):
        self.cache["a"] = 1
        self.assertIn("a", self.cache)
        self.assertEqual(self.cache["a"], 1)
        self.assertEqual(len(self.cache), 1)

    def test_pop_removes_key(self):
        self.cache["a"] = 1
        self.assertEqual(self.cache.pop("a"), 1)
        self.assertNotIn("a", self.cache)
        with self.assertRaises(KeyError):
            self.cache.pop("a")

    def test_rename_keeps_same_object(self):
        # Documents the pitfall Photo.renameFile had to work around: rename()
        # only moves the key, so the cached object (and its stale paths) stays.
        obj = object()
        self.cache["old"] = obj
        self.cache.rename("old", "new")
        self.assertNotIn("old", self.cache)
        self.assertIn("new", self.cache)
        self.assertIs(self.cache["new"], obj)

    def test_pop_then_setitem_replaces_object(self):
        # The Photo.renameFile fix: drop the old key and store the up-to-date
        # instance under the new key, so a stale cached object is discarded.
        stale = object()
        fresh = object()
        self.cache["old"] = stale
        self.cache.pop("old")
        self.cache["new"] = fresh
        self.assertNotIn("old", self.cache)
        self.assertIs(self.cache["new"], fresh)
        self.assertIsNot(self.cache["new"], stale)

    def test_maxsize_eviction(self):
        small = ImageCache(maxSize=100)
        small.ordered.clear()
        small.imageDict.clear()
        small.maxSize = 2
        for i in range(5):
            small["k%d" % i] = i
        # Never grows unboundedly beyond maxSize (+1, matching the impl).
        self.assertLessEqual(len(small), 3)
        self.assertIn("k4", small)
        self.assertNotIn("k0", small)


if __name__ == "__main__":
    unittest.main()
