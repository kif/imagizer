#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Project: Imagizer
#             https://github.com/kif/imagizer
#
#    Copyright (C) Jerome Kieffer
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@terre-adelie.org)
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

"""Imagizer specific stuff from Qt"""

__author__ = "Jerome Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "01/01/2016"
__status__ = "production"


import os
import sys
import matplotlib
from .utils import get_ui_file
import logging
logger = logging.getLogger("imagizer.qt")

transformations = (QtCore.Qt.FastTransformation, QtCore.Qt.SmoothTransformation)


def flush():
    """
    Enforce the flush of the graphical application
    """
    if QtCore.QCoreApplication.hasPendingEvents():
        QtCore.QCoreApplication.flush()


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
    """Extenstion for Qlabel with pan and zoom function used to display images
    """
    zoom = Signal(QtGui.QWheelEvent, name="zoom")
    pan = Signal(QtGui.QMoveEvent, name="pan")
    DELTA2 = 100
    def __init__(self, parent):
        QtGui.QLabel.__init__(self, parent)
        self.old_pos = None

    def mouseReleaseEvent(self, ev):
        logger.debug("Released %s %s", ev, ev)
        if self.old_pos is not None:
            lastx, lasty = self.old_pos
            x = ev.x()
            y = ev.y()
            dx = x - lastx
            dy = y - lasty
            delta2 = dx * dx + dy * dy
            if delta2 > self.DELTA2:
                move_ev = QtGui.QMoveEvent(ev.pos(),
                                           QtCore.QPoint(*self.old_pos))
#                 logger.info("move image %s", move_ev)
                self.pan.emit(move_ev)
            self.old_pos = None
        else:
            print("last ev is None !!!")

    def mousePressEvent(self, ev):
        logger.debug("Pressed %s %s %s ", ev, ev.x(), ev.y())
        self.old_pos = (ev.x(), ev.y())

    def wheelEvent(self, ev):
        logger.debug("Scroll %s at %s,%s %s",
                     ev, ev.x(), ev.y(), ev.delta())
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
