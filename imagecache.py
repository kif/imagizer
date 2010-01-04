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

################################################################################################
###############  Class ImageCache for storing the bitmaps in a Borg ############################
################################################################################################
class ImageCache(dict):
    """this class is a Borg : always returns the same values regardless to the instance of the object
    it is used as data storage for bitmaps ... with a limit of max_len
    """
    __shared_state = {}
    __data_initialized = False
    def __init__(self, maxSize=1000000):
        self.__dict__ = self.__shared_state
        if  not ImageCache.__data_initialized :
            ImageCache.__data_initialized = True
            self.ordered = []
            self.imageDict = {}
            self.maxSize = maxSize
            self.size = 0
    def __setitem__(self, key, value):
        """x.__setitem__(i, y) <==> x[i]=y"""
        self.imageDict[ key ] = value
        if key in self.ordered:
            index = self.ordered.index(key)
            self.ordered.pop(index)
            pixBuf = self.imageDict[ key ]
            self.size -= 3 * pixBuf.get_width() * pixBuf.get_height()
        self.size += 3 * value.get_width() * value.get_height()
        if self.size > self.maxSize:
            firstKey = self.ordered[ 0 ]
            if config.DEBUG: print "Removing file %s from cache" % firstKey
            firstPixBuf = self.imageDict.pop(firstKey)
            self.size -= 3 * firstPixBuf.get_width() * firstPixBuf.get_height()
            self.ordered = self.ordered[1:]
        self.ordered.append(key)

    def __getitem__(self, key):
        """x.__getitem__(y) <==> x[y]"""
        index = self.ordered.index(key)
        self.ordered.pop(index)
        self.ordered.append(key)
        return self.imageDict[ key ]
