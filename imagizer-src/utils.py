#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Imagizer
#             https://github.com/kif/imagizer
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import with_statement, division, print_function, absolute_import

"""

Module to handle various data files (user interface, images, ...)

"""

__author__ = "Jerome Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "29/11/2014"
__status__ = "production"


import os, time, logging
installdir = os.path.dirname(os.path.abspath(__file__))
timelog = logging.getLogger("timeit")

def timeit(func):
    def wrapper(*arg, **kw):
        '''This is the docstring of timeit:
        a decorator that logs the execution time'''
        t1 = time.time()
        res = func(*arg, **kw)
        t2 = time.time()
        if "func_name" in dir(func):
            name = func.func_name
        else:
            name = str(func)
        timelog.warning("%s took %.3fs" % (name, t2 - t1))
        return res
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

def _get_data_path(filename):
    """
    @param filename: the name of the requested data file.
    @type filename: str

    Can search root of data directory in:
    - Environment variable PYFAI_DATA
    - path hard coded into pyFAI.directories.data_dir
    - where this file is installed.

    In the future ....
    This method try to find the requested ui-name following the
    xfreedesktop recommendations. First the source directory then
    the system locations

    For now, just perform a recursive search
    """
    resources = [os.environ.get("IMAGIZER_DATA"), installdir, os.path.dirname(installdir)]

    for resource in resources:
        if not resource:
            continue
        real_filename = os.path.join(resource, filename)
        if os.path.exists(real_filename):
            return real_filename
    else:
        raise RuntimeError("Can not find the [%s] resource, "
                        " something went wrong !!!" % (real_filename,))


def get_ui_file(filename):
    """get the full path of a user-interface file

    @return: the full path of the ui
    """
    if filename[-3:] != ".ui":
        filename = filename + ".ui"
    return _get_data_path(os.path.join("gui", filename))


def get_pixmap_file(filename):
    """get the full path of a pixmap image for the user interface

    @return: the full path of the pixmap
    """
    if filename[-4:] != ".png":
        filename = filename + ".png"
    return _get_data_path(os.path.join("pixmaps", filename))

