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

"""

Module to handle matplotlib and the Qt backend

"""

__author__ = "Jerome Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "20/10/2014"
__status__ = "production"


import os
import sys
import matplotlib
installdir = os.path.dirname(os.path.abspath(__file__))

has_Qt = True
if ('PySide' in sys.modules):
    from PySide import QtGui, QtCore, QtUiTools, QtWebKit
    from PySide.QtCore import SIGNAL, Signal


    #we need to handle uic !!!
    """
    loadUi(uifile, baseinstance=None, package='') -> widget

Load a Qt Designer .ui file and return an instance of the user interface.

uifile is a file name or file-like object containing the .ui file.
baseinstance is an optional instance of the Qt base class.  If specified
then the user interface is created in it.  Otherwise a new instance of the
base class is automatically created.
package is the optional package which is used as the base for any relative
imports of custom widgets.

    """
    class uic(object):
        @staticmethod
        def loadUi(uifile, baseinstance=None, package=''):
            """Load a Qt Designer .ui file and return an instance of the user interface.

            uifile is a file name or file-like object containing the .ui file.
            baseinstance is an optional instance of the Qt base class.  If specified
            then the user interface is created in it.  Otherwise a new instance of the
            base class is automatically created.
            package is the optional package which is used as the base for any relative
            imports of custom widgets.

            Totally untested !
            """
            loader = QtUiTools.QUiLoader()
            file = QtCore.QFile(uifile)
            file.open(QtCore.QFile.ReadOnly)
            myWidget = loader.load(file, self)
            file.close()
            if baseinstance is not None:
                baseinstance = myWidget
            else:
                return myWidget

    sys.modules["PySide.uic"] = uic
    matplotlib.rcParams['backend.qt4'] = 'PySide'
else:
    try:
        from PyQt4 import QtGui, QtCore, uic, QtWebKit
        from PyQt4.QtCore import SIGNAL, pyqtSignal as Signal
    except ImportError:
        has_Qt = False
    else:
        loadUi = uic.loadUi
if has_Qt:
    matplotlib.use('Qt4Agg')
    from matplotlib.backends import backend_qt4 as backend
    from matplotlib import pyplot
    from matplotlib import pylab
else:
    from matplotlib import pyplot
    from matplotlib import pylab
    from matplotlib.backends import backend
    QtGui = QtCore = QtUiTools = QtWebKit = loadUi = None
    SIGNAL = Signal = None


def flush():
    QtCore.QCoreApplication.processEvents()

def update_fig(fig=None):
    """
    Update a matplotlib figure with a Qt4 backend

    @param fig: pylab figure
    """
    if fig and "canvas" in dir(fig) and fig.canvas:
        fig.canvas.draw()
        if "Qt4" in pylab.get_backend():
            QtGui.qApp.postEvent(fig.canvas,
                                 QtGui.QResizeEvent(fig.canvas.size(),
                                                    fig.canvas.size()))
            flush()

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
    print(filename)
    resources = [os.environ.get("IMAGIZER_DATA"), installdir, os.path.dirname(installdir)]

    for resource in resources:
        if not resource:
            continue
        real_filename = os.path.join(resource, filename)
        print(real_filename)
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

def buildUI(ui_file):
    """
    Retrun a class from a ui descrition file
    """
    return loadUi(get_ui_file(ui_file))
