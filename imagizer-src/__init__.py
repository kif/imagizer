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
General library used by selector and generator.
It handles images, progress bars and configuration file.
"""

__author__ = "Jérôme Kieffer"
__version__ = "6.0.0"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "23/12/2020"
__license__ = "GPL"

import os, logging, sys
logging.basicConfig()
logger = logging.getLogger("imagizer")
from .imagecache import ImageCache
from .parser import AttrFile
from .encoding import unicode2html, unicode2ascii
from .html import Html
installdir = os.path.dirname(__file__)
