#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
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

"""
Library used by selector and the installer to select the working directories.
"""

import os, sys, logging
logger = logging.getLogger("imagizer.dirchooser")
try:
    import pygtk ; pygtk.require('2.0')
    import gtk, gtk.glade
except:
        raise "Selector needs pygtk and glade-2 available from http://www.pygtk.org/"

from config import Config
config = Config()

unifiedglade = os.path.join(os.path.dirname(__file__), "selector.glade")

class WarningSc:
    """
    Print a warning before starting the program and allows to change the working directory
    """
    def __init__(self, directory, window="dialog-warning", manageGTK=True, callBack=None):
        """
        Print a small dialog screen
        
        @param callBack: method to be called with the directory chosen 
        @type callBack: method or function
        """
        logger.debug("WarningSc.init")
        self.directory = directory
        self.window = window
        self.manageGTK = manageGTK
        self.quit = True
        self.callBack = callBack
        self.guiFiler = None
        self.gui = gtk.glade.XML(unifiedglade, root=self.window)
        self.gui.signal_connect('on_dialog_destroy', self.destroy)
        self.gui.signal_connect('on_Select_clicked', self.filer)
        self.gui.signal_connect('on_cancel_clicked', self.destroy)
        self.gui.signal_connect('on_ok_clicked', self.continu)
        self.gui.signal_connect('on_dirname_editing_done', self.continu)
        self.gui.get_widget("dirname").set_text(directory)

        if self.manageGTK:
            gtk.main()
        else:
            while gtk.events_pending():
                gtk.main_iteration()

    def continu(self, *args):
        """
        Just destroy the window and goes on ....
        """
        logger.debug("WarningSc.continue")
        self.directory = self.gui.get_widget("dirname").get_text().strip()
        if self.manageGTK:
            gtk.main_quit()
        self.quit = False
        self.gui.get_widget(self.window).destroy()
        while gtk.events_pending():
            gtk.main_iteration()
        if self.callBack is not None:
            self.callBack(self.directory)

    def destroy(self, *args):
        """
        Destroy clicked by user -> quit the program
        """
        logger.debug("WarningSc.destroy called")
        if self.manageGTK:
            if self.quit:
                sys.exit(0)
        else:
            self.gui.get_widget(self.window).destroy()
            while gtk.events_pending():
                gtk.main_iteration()


    def filer(self, *args):
        """
        Launch the filer GUI to choose the root directory
        """
        logger.debug("WarningSc.dirchooser.filer called")
        self.guiFiler = gtk.glade.XML(unifiedglade, root="filer")
        self.guiFiler.get_widget("filer").set_current_folder(self.directory)
        self.guiFiler.signal_connect('on_Open_clicked', self.filerSelect)
        self.guiFiler.signal_connect('on_Cancel_clicked', self.filerDestroy)


    def filerSelect(self, *args):
        """
        Close the filer GUI and update the data
        """
        logger.debug("WarningSc.filerSelect called")
        self.directory = self.guiFiler.get_widget("filer").get_current_folder()
        self.gui.get_widget("dirname").set_text(self.directory)
        self.guiFiler.get_widget("filer").destroy()

    def filerDestroy(self, *args):
        """
        Close the filer GUI
        """
        logger.debug("WarningSc.filerDestroy called")
        self.guiFiler.get_widget("filer").destroy()

    def getDirectory(self):
        """
        Return the directory chosen
        """
        logger.debug("WarningSc.getDirectory")
        self.directory = self.gui.get_widget("dirname").get_text().strip()
        return self.directory
