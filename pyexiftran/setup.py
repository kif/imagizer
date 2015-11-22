#!/usr/bin/env python
# -*- coding: utf8 -*-
"""Setup script for the exiftran python module distribution."""

import glob
import os
from distutils.core import setup
from distutils.extension import Extension

JPEG_VERSION = "80" #"62"
JPEG_DIR = os.path.join("jpeg", JPEG_VERSION)

sources = glob.glob("*.c") + glob.glob(os.path.join(JPEG_DIR, "*.c"))

print sources

define_macros = []
setup (
    name="exiftran python library",
    version="2.0",
    description="Wrapping as C library of the exiftran program using cython",
    author="Jerome Kieffer",

    # Description of the modules and packages in the distribution
    ext_modules=[
         Extension(
         name='pyexiftran',
         sources=sources,
         define_macros=define_macros,
         include_dirs=[JPEG_DIR],
         libraries=["jpeg", "exif", "m"],
         ),
    ],
)
