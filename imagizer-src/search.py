#!/usr/bin/env python
# coding: utf8
#
#******************************************************************************\
# * Copyright (C) 2006 - 2014,  Jérôme Kieffer <kieffer@terre-adelie.org>
# * Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
# * Licence GPL v2
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# *
#*****************************************************************************/

from __future__ import with_statement, division, print_function, absolute_import

"""
Dialog Graphical interfaces for selector.
"""
__author__ = "Jérôme Kieffer"
__version__ = "2.0.0"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "28/07/2019"
__license__ = "GPL"

import os
import logging
import time
import sys
import subprocess
logger = logging.getLogger(__name__)
from .config import config
from . import qt
from .parser import AttrFile
from .photo import Photo
from .encoding import unicode2ascii
from .imagecache import title_cache
from .tree import TreeRoot, TreeModel
PY3 = sys.version_info[0] > 2

if PY3:
    unicode = str
    to_unicode = str
else:
    def to_unicode(text):
        if isinstance(text, str):
            return text.decode(config.Coding)
        else:
            return unicode(text)

class SearchTitle(qt.QObject):
    def __init__(self, callback=None):
        """
        The callback is called when an image is double-clicked.
        """
        qt.QObject.__init__(self)
        self.gui = qt.buildUI("search_title")
        self.callback = callback
        root = TreeRoot()
        self.model = TreeModel(root, self.gui)
        self.gui.treeView.setModel(self.model)
        self.gui.treeView.callback = self.goto
        self.gui.treeView.doubleClicked.connect(self.goto)
        self.gui.searchButton.clicked.connect(self.search_clicked)
        self.gui.treeView.setColumnWidth(0, 300)
        self.gui.treeView.setAlternatingRowColors(True)

    def show(self):
        self.gui.show()

    def search_clicked(self, *args):
        value = unicode2ascii(self.gui.lineEdit.text()).lower()
        logger.info("Searching for %s", value)
        results = self.search(value)
        logger.info("found %s", results)
        self.model = TreeModel(results, self.gui)
        self.gui.treeView.setModel(self.model)

    def search(self, value):
        results = TreeRoot()
        for key, val in title_cache.items():
            try:
                dec = unicode2ascii(val).lower()
            except UnicodeEncodeError as err:
                dec = val.lower()
                logger.error("Unicode error for %s: %s (%s) ... %s", key, val, type(val), err)
            if value in dec:
                results.add_leaf(key, val)
        return results

    def goto(self, midx):
        """
        Return the name of the image clicked.
        """
        leaf = midx.internalPointer()
        if leaf.order == 4:
            value = leaf.name
        else:
            value = leaf.first().name
        logger.info("Clicked on %s", value)
        if self.callback:
            self.callback(value)
        return value
