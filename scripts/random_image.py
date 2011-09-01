#!/usr/bin/env python
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006-2011,  Jérôme Kieffer <kieffer@terre-adelie.org>
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

"""
Create a symbolic link to any file in the repository

"""
__author__ = "Jérôme Kieffer"
__date__ = "201100901"
__licence__ = "GPLv2"

import os, sys, logging, random
from imagizer.fileutils import findFiles
from imagizer.config    import Config
from imagizer.photo     import Photo
config = Config()
logger = logging.getLogger("imagizer.random_image")


if (len(sys.argv) < 2):
    logger.error("You need to give the name of the link to create ! One argument is expected")
    sys.exit(1)
linkName = sys.argv[1]
if (os.path.islink(linkName)):
    try:
        os.unlink(linkName)
    except IOError:
        raise IOError("Unable to remove initial link file. Check rights")

if linkName.startswith("-"):
    logger.error("You need to give the name of the link to create ! One argument is expected")
    sys.exit(0)

listImages = findFiles(config.DefaultRepository)
random.shuffle(listImages)
for imFile in listImages:
    photo = Photo(imFile)
    metadata = photo.readExif()
    rate = metadata.get("Rate", 0)
    rating = 0.01 + 0.2 * rate
    if random.random() < rating:
        print("%s[%s] ---> %s" % (imFile, rate, linkName))
        os.symlink(photo.fn, linkName)
        break
