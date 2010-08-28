#!/usr/bin/env python

"""Setup script for the libexiftran module distribution."""

import glob
from distutils.core import setup
from distutils.extension import Extension

sources = glob.glob("*.c")
#["python-exiftran.c"]
print sources
define_macros = []
setup (
        name="Python-exiftran interface",
        version="1.0",
        description="Input Output helper module",
        author="Jerome Kieffer",

        # Description of the modules and packages in the distribution
        ext_modules=[
                       Extension(
                            name='libexiftran',
                            sources=sources,
                            define_macros=define_macros,
                            libraries=["jpeg", "exif", "m"],
#                            include_dirs=["/usr/include/libexif"]
                       ),
       ],
)
