#!/usr/bin/env python
# coding: utf-8
"""Unit tests for the _get_date build helper (used to stamp __date__).

Verify the git-commit-date primary path and the filesystem-mtime fallback used
when git or the repository is unavailable (e.g. building from a tarball).
"""
import os
import sys
import datetime
import tempfile
import unittest
import importlib.util


def _load_get_date():
    """Load _get_date.py by path (it has no imagizer-internal imports)."""
    pkgdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(
        "imagizer_get_date_under_test", os.path.join(pkgdir, "_get_date.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


get_date = _load_get_date()


class TestGetDate(unittest.TestCase):

    def test_mtime_date_matches_filesystem(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            expected = datetime.date.fromtimestamp(
                os.path.getmtime(path)).strftime("%d/%m/%Y")
            self.assertEqual(get_date.mtime_date(path), expected)
        finally:
            os.unlink(path)

    def test_mtime_date_format_is_dd_mm_yyyy(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            value = get_date.mtime_date(path)
            # DD/MM/YYYY -> re-parsing must succeed
            datetime.datetime.strptime(value, "%d/%m/%Y")
        finally:
            os.unlink(path)

    def test_git_date_outside_repo_returns_none(self):
        # A file in a bare temp directory is not tracked by any git repo.
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "untracked.txt")
        with open(path, "w") as handle:
            handle.write("x")
        try:
            self.assertIsNone(get_date.git_date(path))
        finally:
            os.unlink(path)
            os.rmdir(directory)

    def test_file_date_falls_back_to_mtime(self):
        # Outside a git repo, file_date must equal the filesystem mtime.
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "f.txt")
        with open(path, "w") as handle:
            handle.write("x")
        try:
            self.assertEqual(get_date.file_date(path), get_date.mtime_date(path))
        finally:
            os.unlink(path)
            os.rmdir(directory)


if __name__ == "__main__":
    unittest.main()
