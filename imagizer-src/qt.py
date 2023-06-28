# coding: utf-8
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

"""Imagizer specific stuff from Qt"""

__author__ = "Jerome Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__license__ = "GPLv3+"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
__date__ = "28/06/2023"
__status__ = "production"

import PyQt6.QtCore, PyQt6.QtGui  # Pre-load PyQt6
try:
    """Remove the limit in size for images"""
    PyQt6.QtGui.QImageReader.setAllocationLimit(0)
except:
    pass
from ._qt import *  # noqa
# from ._utils import * # noqa

import logging
_logger = logging.getLogger(__name__)

transformations = (Qt.FastTransformation, Qt.SmoothTransformation)


def supportedImageFormats():
    """Return a set of string of file format extensions supported by the
    Qt runtime."""
    if sys.version_info[0] < 3 or qt.BINDING in ('PySide', 'PySide2'):
        convert = str
    else:
        convert = lambda data: str(data, 'ascii')
    formats = qt.QImageReader.supportedImageFormats()
    return set([convert(data) for data in formats])


def flush():
    """
    Enforce the flush of the graphical application
    """
    QCoreApplication.processEvents()


def update_fig(fig=None):
    """
    Update a matplotlib figure with a Qt4 backend

    @param fig: pylab figure
    """
    if fig and "canvas" in dir(fig) and fig.canvas:
        fig.canvas.draw()
        if "Qt4" in pylab.get_backend():
            qApp.postEvent(fig.canvas,
                                 QResizeEvent(fig.canvas.size(),
                                                    fig.canvas.size()))
            flush()


def buildUI(ui_file):
    """
    Retrun a class from a ui descrition file
    """
    from .utils import get_ui_file
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
        pixmap = button.icon().pixmap(QSize(22, 22))
    else:
        pixmap = QPixmap(icon_name)
    button.setText("")
    button.setIcon(QIcon())
    layout1 = QHBoxLayout(button)
    layout1.setContentsMargins(0, 0, 0, 0)
    layout1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
    button.setLayout(layout1)
    widget = QWidget(button)
    button.layout().addWidget(widget)
    layout2 = QFormLayout(widget)
    layout2.setContentsMargins(0, 0, 0, 0)
    layout2.setSpacing(2)
    widget.setLayout(layout2)
    lab_txt = QLabel(text, widget)
    lab_txt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lab_ico = QLabel(widget)
    lab_ico.setPixmap(pixmap)
    if target == "right":
        widget.layout().addRow(lab_txt, lab_ico)
    else:
        widget.layout().addRow(lab_ico, lab_txt)


class ExtendedQLabel(QLabel):
    """Extenstion for Qlabel with pan and zoom function used to display images
    """
    zoom = Signal(QWheelEvent, name="zoom")
    pan = Signal(QMoveEvent, name="pan")
    DELTA2 = 100

    def __init__(self, parent):
        QLabel.__init__(self, parent)
        self.old_pos = None

    def mouseReleaseEvent(self, ev):
        _logger.debug("Released %s %s", ev, ev)
        if self.old_pos is not None:
            lastx, lasty = self.old_pos
            x = ev.x()
            y = ev.y()
            dx = x - lastx
            dy = y - lasty
            delta2 = dx * dx + dy * dy
            if delta2 > self.DELTA2:
                move_ev = QMoveEvent(ev.pos(),
                                           QPoint(*self.old_pos))
#                 _logger.info("move image %s", move_ev)
                self.pan.emit(move_ev)
            self.old_pos = None
        else:
            print("last ev is None !!!")

    def mousePressEvent(self, ev):
        _logger.debug("Pressed %s %s %s ", ev, ev.x(), ev.y())
        self.old_pos = (ev.x(), ev.y())

    def wheelEvent(self, ev):
        _logger.debug("Scroll %s at %s,%s %s",
                          ev, ev.position().x(), ev.position().y(), ev.angleDelta().y())
        self.zoom.emit(ev)


def get_matrix(orientation):
    """Return the rotation matrix corresponding to the exif orientation

    @param orientation: value from 1 to 8
    @return: rotation matrix
    """
    if orientation == 2:
        matrix = QTransform(-1., 0., 0., 1., 0., 0., 0., 1.)
    elif orientation == 3:
        matrix = QTransform(-1., 0., 0., 0., -1., 0., 0., 0., 1.)
    elif orientation == 4:
        matrix = QTransform(1., 0., 0., 0., -1., 0., 0., 0., 1.)
    elif orientation == 5:
        matrix = QTransform(0., 1., 0., 1., 0., 0., 0., 0., 1.)
    elif orientation == 6:
        matrix = QTransform(0., 1., 0., -1., 0., 0., 0., 0., 1.)
    elif orientation == 7:
        matrix = QTransform(0., -1., 0., -1., 0., 0., 0., 0., 1.)
    elif orientation == 8:
        matrix = QTransform(0., -1., 0., 1., 0., 0., 0., 0., 1.)
    else:
        matrix = QTransform(1., 0., 0., 0., 1., 0., 0., 0., 1.)
    return matrix
