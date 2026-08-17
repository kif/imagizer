#!/usr/bin/env python3
"""Print the last-modification date of the given file as DD/MM/YYYY.

Build helper used by meson to stamp __date__ into _version.py. It prefers the
git commit date of the file (robust to filesystem mtime resets on clone /
checkout / tarball extraction) and falls back to the filesystem modification
time when git or the repository is unavailable (e.g. building from a release
tarball).
"""
import os
import sys
import subprocess
import datetime

DATE_FORMAT = "%d/%m/%Y"


def git_date(path):
    """Return the last git commit date of *path* (DD/MM/YYYY), or None."""
    directory = os.path.dirname(os.path.abspath(path))
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=format:" + DATE_FORMAT,
             "--", os.path.basename(path)],
            cwd=directory, capture_output=True, text=True, check=True,
        ).stdout.strip()
        return out or None
    except Exception:
        return None


def mtime_date(path):
    """Return the filesystem modification date of *path* (DD/MM/YYYY)."""
    return datetime.date.fromtimestamp(os.path.getmtime(path)).strftime(DATE_FORMAT)


def file_date(path):
    """Return the git commit date of *path*, or its filesystem mtime as fallback."""
    return git_date(path) or mtime_date(path)


def main():
    print(file_date(sys.argv[1]))


if __name__ == "__main__":
    main()
