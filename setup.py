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
The setup.py script allows to install Imagizer regardless to the 
"""

from distutils.core import setup
import os,sys,glob,distutils.sysconfig

#here we detect the OS runnng the program so that we can call exftran in the right way
installdir=os.path.join(distutils.sysconfig.get_python_lib(),"imagizer")
if os.name == 'nt': #sys.platform == 'win32':
	execexiftran=os.path.join(os.getcwd(),"bin","exiftran.exe")
	ConfFile=[os.path.join(os.getenv("ALLUSERSPROFILE"),"imagizer.conf"),os.path.join(os.getenv("USERPROFILE"),"imagizer.conf")]
	os.rename('selector','selector.py')
	os.rename('generator','generator.py')
	scripts= ['selector.py',"generator.py"]

elif os.name == 'posix':
	execexiftran=os.path.join(os.getcwd(),"bin","exiftran")
	ConfFile=["/etc/imagizer.conf",os.path.join(os.getenv("HOME"),".imagizer")]
	scripts= ['selector',"generator"]
else:
	raise "Your platform does not seem to be an Unix nor a M$ Windows.\nI am sorry but the exiftran binary is necessary to run selector, and exiftran is probably not available for you plateform. If you have exiftran installed, please contact the developper to correct that bug, kieffer at terre-adelie dot org"
	sys.exit(1)

setup(name= 'Imagizer',
	version= '1.0',
	author= 'Jerome Kieffer',
	author_email= 'Jerome.Kieffer@terre-adelie.org',
	url= 'http://wiki.terre-adelie.org/Imagizer',
	description= "Imagizer is a manager for a repository of photos",
	license= 'GNU GPL v2',
	scripts= scripts,
	data_files= [
		(installdir, ["selector.glade",execexiftran]+
		glob.glob(os.path.join("pixmaps","*.png"))+
		glob.glob(os.path.join("pixmaps","*.ico"))),
		(os.path.split(ConfFile[0])[0],['imagizer.conf'])
	],
	packages= ['imagizer'],
	package_dir= {'imagizer': ''},
	)
