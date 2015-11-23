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

Module to handle matplotlib and the Qt backend

"""

__author__ = "Jerome Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "21/11/2015"
__status__ = "production"


import os
import sys
import matplotlib
from .utils import get_ui_file

has_Qt = True
if ('PySide' in sys.modules):
    from PySide import QtGui, QtCore, QtUiTools, QtWebKit
    from PySide.QtCore import SIGNAL, Signal

#TODO: see https://github.com/lunaryorn/snippets/blob/master/qt4/designer/pyside_dynamic.py

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

transformations = (QtCore.Qt.FastTransformation, QtCore.Qt.SmoothTransformation)

def flush():
    """
    Enforce the flush of the graphical application
    """
    if QtCore.QCoreApplication.hasPendingEvents():
        QtCore.QCoreApplication.flush ()
#         for evt in QtCore.QCoreApplication.p
#     QtCore.QCoreApplication.processEvents()

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

def buildUI(ui_file):
    """
    Retrun a class from a ui descrition file
    """
    return loadUi(get_ui_file(ui_file))


def icon_on(target="right", button=None, icon_name=None,):
    """Put the icon of the button on the right side of the text
    @param target: "right" or "left"
    @param button: QPushButton Instance
    @param icon_name: path to the filename ... optional
    """
    if not button:
        return
    text = button.text()
    if icon_name is None:
        pixmap = button.icon().pixmap(QtCore.QSize(22, 22))
    else:
        pixmap = QtGui.QPixmap(icon_name)
    button.setText("")
    button.setIcon(QtGui.QIcon())
    layout1 = QtGui.QHBoxLayout(button)
    layout1.setContentsMargins(0, 0, 0, 0)
    layout1.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
    button.setLayout(layout1)
    widget = QtGui.QWidget(button)
    button.layout().addWidget(widget)
    layout2 = QtGui.QFormLayout(widget)
    layout2.setContentsMargins(0, 0, 0, 0)
    layout2.setSpacing(2)
    widget.setLayout(layout2)
    lab_txt = QtGui.QLabel(text, widget)
    lab_txt.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    lab_ico = QtGui.QLabel(widget)
    lab_ico.setPixmap(pixmap)
    if target == "right":
        widget.layout().addRow(lab_txt, lab_ico)
    else:
        widget.layout().addRow(lab_ico, lab_txt)

class ExtendedQLabel(QtGui.QLabel):
    zoom = Signal(QtGui.QWheelEvent, name="zoom")
    def __init(self, parent):
        QtGui.QLabel.__init__(self, parent)


    def mouseReleaseEvent(self, ev):
#        print("Released %s" % ev)
        self.emit(SIGNAL('clicked()'))

    def mousePressEvent(self, ev):
#        print("Pressed %s" % ev)
        self.emit(SIGNAL('clicked()'))

    def wheelEvent(self, ev):
#        print("Scroll %s at %s,%s %s" % (ev, ev.x(), ev.y(), ev.delta()))
        self.zoom.emit(ev)

def get_matrix(orientation):
    """Return the rotation matrix corresponding to the exif orientation

    @param orientation: value from 1 to 8
    @return: rotation matrix
    """
    if orientation == 2:
        matrix = QtGui.QMatrix(-1, 0, 0, 1, 0, 0)
    elif orientation == 3:
        matrix = QtGui.QMatrix(-1, 0, 0, -1, 0, 0)
    elif orientation == 4:
        matrix = QtGui.QMatrix(1, 0, 0, -1, 0, 0)
    elif orientation == 5:
        matrix = QtGui.QMatrix(0, 1, 1, 0, 0, 0)
    elif orientation == 6:
        matrix = QtGui.QMatrix(0, 1, -1, 0, 0, 0)
    elif orientation == 7:
        matrix = QtGui.QMatrix(0, -1, -1, 0, 0, 0)
    elif orientation == 8:
        matrix = QtGui.QMatrix(0, -1, 1, 0, 0, 0)
    else:
        matrix = QtGui.QMatrix(1, 0, 0, 1, 0, 0)
    return matrix
