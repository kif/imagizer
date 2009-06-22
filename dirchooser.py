#!/usr/bin/env python 
# -*- coding: Latin1 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006,  Jérome Kieffer <kieffer@terre-adelie.org>
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
Library used by selector and the installer to select the working directories.
"""

import distutils.sysconfig,os,sys

try:
	import pygtk ; pygtk.require('2.0')
	import gtk,gtk.glade
except:
		raise "Selector needs pygtk and glade-2 available from http://www.pygtk.org/"

from config import Config
config=Config()


unifiedglade=os.path.join(distutils.sysconfig.get_python_lib(),"imagizer","selector.glade")


class WarningSc:
	"""print a warning before starting the program and allows to chang the working directory"""
	def __init__(self,directory,window="dialog-warning"):
		self.directory=directory
		self.window=window
		self.quit=True
		self.xml=gtk.glade.XML(unifiedglade,root=self.window)
		self.xml.signal_connect('on_dialog_warning_destroy',self.destroy)
		self.xml.signal_connect('on_Select_clicked',self.filer)
		self.xml.signal_connect('on_cancel_clicked',self.destroy)
		self.xml.signal_connect('on_ok_clicked',self.continu)
		self.xml.signal_connect('on_dirname_editing_done',self.continu)
		while gtk.events_pending():gtk.main_iteration()
		self.xml.get_widget("dirname").set_text(directory)		
		gtk.main()
	def continu(self,*args):
		"""just distroy the window and goes on ...."""
		self.directory=self.xml.get_widget("dirname").get_text().strip()
		gtk.main_quit()
		self.quit=False
		self.xml.get_widget(self.window).destroy()
		while gtk.events_pending():gtk.main_iteration()
	def destroy(self,*args):
		"""destroy clicked by user -> quit the program"""
		if self.quit:
			sys.exit(0)
	def filer(self,*args):	
		"""Lauch the filer GUI to choose the root directory"""
		self.xml2=gtk.glade.XML(unifiedglade,root="filer")
		self.xml2.get_widget("filer").set_current_folder(self.directory)
		self.xml2.signal_connect('on_Open_clicked',self.filerselect)
		self.xml2.signal_connect('on_Cancel_clicked',self.filerdestroy)
	def filerselect(self,*args):	
		"""Close the filer GUI and update the data"""
		self.directory=self.xml2.get_widget("filer").get_current_folder()
		self.xml.get_widget("dirname").set_text(self.directory)		
		self.xml2.get_widget("filer").destroy()
	def filerdestroy(self,*args):	
		"""Close the filer GUI"""
		self.xml2.get_widget("filer").destroy()
