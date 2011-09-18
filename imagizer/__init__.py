# coding: utf8
#
#
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2011,  Jérôme Kieffer <kieffer@terre-adelie.org>
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
General library used by selector and generator.
It handles images, progress bars and configuration file.
"""

__author__ = "Jérôme Kieffer"
__contact__ = "jerome.kieffer@terre-adelie.org"
__version__ = "1.2.1"

import os, logging, sys
logger = logging.Logger("imagizer", logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
#formatter = logging.Formatter("%(name)s/%(levelname)s: %(message)s")
#ch.setFormatter(formatter)
logger.addHandler(ch)

if os.name == 'nt': #sys.platform == 'win32':
    listConfigurationFiles = [os.path.join(os.getenv("ALLUSERSPROFILE"), "imagizer.conf"), os.path.join(os.getenv("USERPROFILE"), "imagizer.conf")]
elif os.name == 'posix':
    listConfigurationFiles = ["/etc/imagizer.conf", os.path.join(os.getenv("HOME"), ".imagizer")]

from config import Config
config = Config()
config.load(listConfigurationFiles)

from exiftran import Exiftran
from imagecache import ImageCache
from parser import AttrFile
from signals import Signal
from encoding import unicode2html, unicode2ascii
from html import Html
installdir = os.path.dirname(__file__)
