# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2004-2016 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""Common wrapper over Python Qt bindings:

- `PyQt5 <http://pyqt.sourceforge.net/Docs/PyQt5/>`_,
- `PyQt4 <http://pyqt.sourceforge.net/Docs/PyQt4/>`_ or
- `PySide <http://www.pyside.org>`_.

If a Qt binding is already loaded, it will use it, otherwise the different
Qt bindings are tried in this order: PyQt4, PySide, PyQt5.

The name of the loaded Qt binding is stored in the BINDING variable.

This module provides a flat namespace over Qt bindings by importing
all symbols from **QtCore** and **QtGui** packages and if available
from **QtOpenGL** and **QtSvg** packages.
For **PyQt5**, it also imports all symbols from **QtWidgets** and
**QtPrintSupport** packages.

Example of using :mod:`silx.gui.qt` module:

>>> from silx.gui import qt
>>> app = qt.QApplication([])
>>> widget = qt.QWidget()

For an alternative solution providing a structured namespace,
see `qtpy <https://pypi.python.org/pypi/QtPy/>`_ which
provides the namespace of PyQt5 over PyQt4 and PySide.
"""

__authors__ = ["V.A. Sole - ESRF Data Analysis"]
__license__ = "MIT"
__date__ = "17/09/2017"


import logging
import sys
import traceback


_logger = logging.getLogger(__name__)


BINDING = None
"""The name of the Qt binding in use: 'PyQt5', 'PyQt4' or 'PySide'."""

QtBinding = None  # noqa
"""The Qt binding module in use: PyQt5, PyQt4 or PySide."""

HAS_SVG = False
"""True if Qt provides support for Scalable Vector Graphics (QtSVG)."""

HAS_OPENGL = False
"""True if Qt provides support for OpenGL (QtOpenGL)."""

# First check for an already loaded wrapper
if 'PySide.QtCore' in sys.modules:
    BINDING = 'PySide'

elif 'PyQt5.QtCore' in sys.modules:
    BINDING = 'PyQt5'

elif 'PyQt4.QtCore' in sys.modules:
    BINDING = 'PyQt4'

else:  # Then try Qt bindings
    try:
        import PyQt4  # noqa
    except ImportError:
        try:
            import PySide  # noqa
        except ImportError:
            try:
                import PyQt5  # noqa
            except ImportError:
                raise ImportError(
                    'No Qt wrapper found. Install PyQt4, PyQt5 or PySide.')
            else:
                BINDING = 'PyQt5'
        else:
            BINDING = 'PySide'
    else:
        BINDING = 'PyQt4'


if BINDING == 'PyQt4':
    _logger.debug('Using PyQt4 bindings')

    if sys.version < "3.0.0":
        try:
            import sip

            sip.setapi("QString", 2)
            sip.setapi("QVariant", 2)
        except:
            _logger.warning("Cannot set sip API")

    import PyQt4 as QtBinding  # noqa

    from PyQt4.QtCore import *  # noqa
    from PyQt4.QtGui import *  # noqa

    try:
        from PyQt4.QtOpenGL import *  # noqa
    except ImportError:
        _logger.info("PyQt4.QtOpenGL not available")
        HAS_OPENGL = False
    else:
        HAS_OPENGL = True

    try:
        from PyQt4.QtSvg import *  # noqa
    except ImportError:
        _logger.info("PyQt4.QtSvg not available")
        HAS_SVG = False
    else:
        HAS_SVG = True

    from PyQt4.uic import loadUi  # noqa

    Signal = pyqtSignal

    Property = pyqtProperty

    Slot = pyqtSlot

elif BINDING == 'PySide':
    _logger.debug('Using PySide bindings')

    import PySide as QtBinding  # noqa

    from PySide.QtCore import *  # noqa
    from PySide.QtGui import *  # noqa

    try:
        from PySide.QtOpenGL import *  # noqa
    except ImportError:
        _logger.info("PySide.QtOpenGL not available")
        HAS_OPENGL = False
    else:
        HAS_OPENGL = True

    try:
        from PySide.QtSvg import *  # noqa
    except ImportError:
        _logger.info("PySide.QtSvg not available")
        HAS_SVG = False
    else:
        HAS_SVG = True

    pyqtSignal = Signal

    # Import loadUi wrapper for PySide
    from ._pyside_dynamic import loadUi  # noqa

    # Import missing classes
    if not hasattr(locals(), "QIdentityProxyModel"):
        from ._pyside_missing import QIdentityProxyModel  # noqa

elif BINDING == 'PyQt5':
    _logger.debug('Using PyQt5 bindings')

    import PyQt5 as QtBinding  # noqa

    from PyQt5.QtCore import *  # noqa
    from PyQt5.QtGui import *  # noqa
    from PyQt5.QtWidgets import *  # noqa
    from PyQt5.QtPrintSupport import *  # noqa

    try:
        from PyQt5.QtOpenGL import *  # noqa
    except ImportError:
        _logger.info("PySide.QtOpenGL not available")
        HAS_OPENGL = False
    else:
        HAS_OPENGL = True

    try:
        from PyQt5.QtSvg import *  # noqa
    except ImportError:
        _logger.info("PyQt5.QtSvg not available")
        HAS_SVG = False
    else:
        HAS_SVG = True

    from PyQt5.uic import loadUi  # noqa

    Signal = pyqtSignal

    Property = pyqtProperty

    Slot = pyqtSlot

else:
    raise ImportError('No Qt wrapper found. Install PyQt4, PyQt5 or PySide')

# provide a exception handler but not implement it by default
def exceptionHandler(type_, value, trace):
    """
    This exception handler prevents quitting to the command line when there is
    an unhandled exception while processing a Qt signal.

    The script/application willing to use it should implement code similar to:

    .. code-block:: python

        if __name__ == "__main__":
            sys.excepthook = qt.exceptionHandler

    """
    _logger.error("%s %s %s", type_, value, ''.join(traceback.format_tb(trace)))
    msg = QMessageBox()
    msg.setWindowTitle("Unhandled exception")
    msg.setIcon(QMessageBox.Critical)
    msg.setInformativeText("%s %s\nPlease report details" % (type_, value))
    msg.setDetailedText(("%s " % value) + ''.join(traceback.format_tb(trace)))
    msg.raise_()
    msg.exec_()

def supportedImageFormats():
    """Return a set of string of file format extensions supported by the
    Qt runtime."""
    if sys.version_info[0] < 3:
        convert = str
    else:
        convert = lambda data: str(data, 'ascii')
    formats = QImageReader.supportedImageFormats()
    return set([convert(data) for data in formats])

transformations = (Qt.FastTransformation, Qt.SmoothTransformation)


def flush():
    """
    Enforce the flush of the graphical application
    """
    if QCoreApplication.hasPendingEvents():
        QCoreApplication.flush()


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
                     ev, ev.x(), ev.y(), ev.angleDelta())
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
