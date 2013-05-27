#!/usr/bin/env python
# -*- coding: UTF8 -*-
#******************************************************************************\
#*
#* Copyright (C) 2006-2013,  Jérôme Kieffer <kieffer@terre-adelie.org>
#* Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
#* Licence GPL v2
#*
#* This program is free software; you can redistribute it and/or modify
#* it under the terms of the GNU General Public License as published by
#* the Free Software Foundation; either version 2 of the License, or
#* (at your option) any later version.
#*
#* This program is distributed in the hope that it will be useful,
#* but WITHOUT ANY WARRANTY; without even the implied warranty of
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#* GNU General Public License for more details.
#*
#* You should have received a copy of the GNU General Public License
#* along with this program; if not, write to the Free Software
#* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#*
#*****************************************************************************/

#
"""
pyexiftran.py a wrapper for the original exiftran provided by Gerd Korn
http://linux.bytesex.org/fbida/

Needs libexif-dev, libjepg-dev and python-dev to be installed on the system.
"""
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20130527"
__license__ = "GPL"

import logging

cdef extern from "exiftran.h":
    int pylib(int a, char *name) nogil

logger = logging.getLogger("pyexiftran")


def rotate90(filename):
    """
    Rotate the given image file by 90 degrees clockwise

    @param filename: name of the JPEG file to rotate
    @type filename: python string
    """
    cdef int rc
    cdef char* cfname = filename
    logger.debug("rotate90 %s" % (filename))
    #with nogil:
    rc = pylib(9, cfname)
    if rc:
        logger.warning("rotate90 returned code %s on %s"%(rc,filename))


def rotate180(filename):
    """
    Rotate the given image file by 180 degrees

    @param filename: name of the JPEG file to rotate
    @type filename: python string
    """
    cdef int rc
    cdef char* cfname = filename
    logger.debug("rotate180 %s" % (cfname))
    #with nogil:
    rc = pylib(1, filename)
    if rc:
        logger.warning("rotate180 returned code %s on %s"%(rc,filename))

def rotate270(filename):
    """
    Rotate the given file by 90 degrees counter-clockwise (270deg clockwise)

    @param filename: name of the JPEG file to rotate
    @type filename: python string
    """
    cdef int rc
    cdef char* cfname = filename
    logger.debug("rotate270 %s" % (filename))
    #with nogil:
    rc = pylib(2, cfname)
    if rc:
        logger.warning("rotate270 returned code %s on %s"%(rc,filename))

def autorotate(filename):
    """
    Auto rotate the given image file

    @param filename: name of the JPEG file to rotate
    @type filename: python string
    """
    cdef int rc
    cdef char* cfname = filename
    logger.debug("autorotate %s" % (filename))
#    with nogil:
    rc = pylib(0, cfname)
    if rc:
        logger.warning("autorotate returned code %s on %s"%(rc,filename))
