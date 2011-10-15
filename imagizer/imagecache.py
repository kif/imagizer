#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006-2009,  Jérome Kieffer <kieffer@terre-adelie.org>
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

"""
ImageCache is a class containing a copy of the bitmap of images .
Technically it is a Borg (design Pattern) so every instance of ImageCache has exactly the same contents.
"""
import logging, os
logger = logging.getLogger("imagizer.imagecache")
from config import Config
config = Config()


################################################################################################
###############  Class ImageCache for storing the bitmaps in a Borg ############################
################################################################################################
class ImageCache(dict):
    """
    this class is a Borg : always returns the same values regardless to the instance of the object
    it is used as data storage for images ... with a limit on the number of images to keep in memory.
    """
    __shared_state = {}
    __data_initialized = False


    def __init__(self, maxSize=100):
        """
        Constructor of ImageCache
        @param maxSize: number of element to keep in memory
        """
        self.__dict__ = self.__shared_state
        if  ImageCache.__data_initialized is False:
            ImageCache.__data_initialized = True
            logger.debug("ImageCache.__init__: initalization of the Borg")
            self.ordered = []
            self.imageDict = {}
            self.maxSize = maxSize
            self.size = 0


    def __repr__(self):
        """
        """
        out = ["{"]
        for key in self.ordered:
            out.append(" '%s': %s," % (key, self.imageDict[key]))
        out.append("}")
        return os.linesep.join(out)


    def __setitem__(self, key, value):
        """
        x.__setitem__(i, y) <==> x[i]=y
        """
        logger.debug("ImageCache.__setitem__: %s" % key)
        self.imageDict[ key ] = value
        if key in self.ordered:
            index = self.ordered.index(key)
            self.ordered.pop(index)
        if len(self.ordered) > self.maxSize:
            firstKey = self.ordered.pop(0)
            logger.debug("Removing from cache: %s" % firstKey)
            self.imageDict.pop(firstKey)
        self.ordered.append(key)


    def __getitem__(self, key):
        """
        x.__getitem__(y) <==> x[y]
        """
        logger.debug("ImageCache.__setitem__: %s" % key)
        index = self.ordered.index(key)
        self.ordered.pop(index)
        self.ordered.append(key)
        return self.imageDict[ key ]


    def __contains__(self, key):
        """
        D.__contains__(k) -> True if D has a key k, else False
        """
        return key in self.imageDict
    has_key = __contains__


    def __len__(self):
        """
        """
        return len(self.ordered)


    def get(self, key, default=None):
        """
        get method with default answer implemented
        """
        if key in self.ordered:
            return self.__getitem__(key)
        elif default is not None:
            self.__setitem__(key, default)
            return default


    def keys(self):
        """ 
        Returns the list of keys, ordered
        """
        logger.debug("ImageCache.keys")
        return self.ordered[:]


    def pop(self, key):
        """
        Remove a key for the dictionary and return it's value
        """
        logger.debug("ImageCache.pop %s" % key)
        try:
            index = self.ordered.index(key)
        except:
            raise KeyError
        self.ordered.pop(index)
        myData = self.imageDict.pop(key)
        return myData

    def rename(self, oldKey, newKey):
        """
        Change the name of a key without affecting anything else
        If the name is not present: do nothing.
        """
        logger.debug("ImageCache.rename %s->%s" % (oldKey, newKey))
        if oldKey not in self.ordered:
            return
        index = self.ordered.index(oldKey)
        self.ordered[index] = newKey
        myData = self.imageDict.pop(oldKey)
        self.imageDict[newKey] = myData

