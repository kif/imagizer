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
__date__ = "06/01/2015"
__licence__ = "GPLv2"

import os, sys, logging, random, glob
from imagizer.config    import config
from imagizer.photo     import Photo
logger = logging.getLogger("imagizer.random_image")

def scan():
    """
    Scan the repository for all valid files
    """
    if config.DefaultRepository.endswith(os.sep):
        l = len(config.DefaultRepository)
    else:
        l = len(config.DefaultRepository) + 1
    all_jpg = [i[l:] for i in glob.glob(os.path.join(config.DefaultRepository, "*", "*.jpg"))]
    logger.debug("Scanned directory %s and found %i images" % (config.DefaultRepository, len(all_jpg)))
    return all_jpg


def create_link(linkName, lst=None):
    if (os.path.islink(linkName)):
        try:
            os.unlink(linkName)
        except IOError:
            raise IOError("Unable to remove initial link file. Check rights")
    if linkName.startswith("-"):
        logger.error("You need to give the name of the link to create ! One argument is expected")
        return
    while True:
        if not lst:
            lst = scan()
            random.shuffle(lst)
        imFile = lst.pop()
        photo = Photo(imFile, dontCache=True)
        data = photo.readExif()
        rate = data.get("rate", 0)
        # 0 for x=5, 0.5 for x=3 and 0.99 for x=0
        treshold = -0.01733333 * rate * rate + -0.11133333 * rate + 0.99
        found = (photo.pixelsX > photo.pixelsY) and (random.random() >= treshold)
        if found:
            print("%s[%s] ---> %s" % (imFile, rate, linkName))
            os.symlink(photo.fn, linkName)
            break

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        logger.error("You need to give the name of the link to create ! One argument is expected")
        sys.exit(1)
    lst = scan()
    random.shuffle(lst)
    for oneFile in sys.argv[1:]:
        create_link(oneFile, lst)

