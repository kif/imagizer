#!/usr/bin/env python
# coding: utf-8
#
#******************************************************************************\
#*
#* Copyright (C) 2006-2009,  Jérome Kieffer <kieffer@terre-adelie.org>
#* Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
#* Licence GPL v2
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

from __future__ import with_statement, division, print_function, absolute_import

"""
Library used by selector and the installer to select the working directories.
"""
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "29/11/2014"
__license__ = "GPL"

import os, sys, logging
logger = logging.getLogger("imagizer.dirchooser")

from .config import config
from .qt import buildUI, flush, SIGNAL, QtGui


class WarningSc(object):
    """
    Print a warning before starting the program and allows to change the working directory
    """
    def __init__(self, directory, window="dialog_warning", callBack=None):
        """
        Print a small dialog screen

        @param callBack: method to be called with the directory chosen
        @type callBack: method or function
        """
        logger.debug("WarningSc.init")
        self.window = window
        self.quit = True
        self.callBack = callBack
        self.guiFiler = None
        self.gui = buildUI(self.window)
        for widget, signal, method in (#(self.gui, "destroyed()", self.destroy),
                                        (self.gui.select, "clicked()", self.filer),
                                        (self.gui, "rejected()", self.destroy),
                                        (self.gui, "accepted()", self.continu),
#                                        'on_dirname_editing_done': self.continu}()
                                       ):
            self.gui.connect(widget, SIGNAL(signal), method)
        self.gui.dirname.setText(directory)
        flush()

    def continu(self, *args):
        """
        Just destroy the window and goes on ....
        """
        logger.debug("WarningSc.continue")
        self.destroy()
        if self.callBack is not None:
            self.callBack(self.get_directory())

    def destroy(self, *args):
        """
        Destroy clicked by user -> quit the program
        """
        logger.debug("WarningSc.destroy called")
        self.gui.close()

    def filer(self, *args):
        """
        Close the filer GUI and update the data
        """
        logger.debug("WarningSc.filer called")
        self.directory = QtGui.QFileDialog.getExistingDirectory(self.gui, "Select Directory")

    def get_directory(self):
        """
        Return the directory chosen
        """
        logger.debug("WarningSc.get_directory")
        return str(self.gui.dirname.text()).strip()

    def set_directory(self, value):
        """
        set the directory
        """
        logger.debug("WarningSc.set_directory")
        self.gui.dirname.setText(value)
    directory = property(get_directory, set_directory)

    def show(self):
        self.gui.show()


def test():
    def callback(dirname):
        print("Got dirname %s" % dirname)

    app = QtGui.QApplication([])
    w = WarningSc("/home", callBack=callback)
    w.show()
    res = app.exec_()
    print(res)
    sys.exit(res)

if __name__ == "__main__":
    test()
