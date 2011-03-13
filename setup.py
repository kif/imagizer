#!/usr/bin/env python 
# -*- coding: UTF8 -*-
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
The setup.py script allows to install Imagizer regardless to the operating system
"""

from distutils.core import setup
from distutils.extension import Extension
import os, sys, glob, distutils.sysconfig, shutil, locale

#here we detect the OS runnng the program so that we can call exftran in the right way
installdir = os.path.join(distutils.sysconfig.get_python_lib(), "imagizer")
if os.name == 'nt': #sys.platform == 'win32':
    execexiftran = os.path.join(os.getcwd(), "bin", "exiftran.exe")
    ConfFile = [os.path.join(os.getenv("ALLUSERSPROFILE"), "imagizer.conf"), os.path.join(os.getenv("USERPROFILE"), "imagizer.conf")]
    shutil.copy('selector', 'selector.py')
    shutil.copy('generator', 'generator.py')
    shutil.copy('imagizer.conf-windows', 'imagizer.conf')
    scripts = ['selector.py', "generator.py", "NommeVideo.py", "NommeVideo2.py"]

elif os.name == 'posix':
#    shutil.copy(os.path.join(os.getcwd(),"bin","exiftran"+str(int(1+log(os.sys.maxint+1)/log(2)))),os.path.join(os.getcwd(),"bin","exiftran"))
    ConfFile = ["/etc/imagizer.conf", os.path.join(os.getenv("HOME"), ".imagizer")]
    scripts = ['selector', "generator", "NommeVideo.py", "NommeVideo2.py"]
    execexiftran = os.path.join(os.getcwd(), "bin", "exiftran")
    os.chmod(execexiftran, 509) #509 = 775 in octal
    shutil.copy('imagizer.conf-unix', 'imagizer.conf')

else:
    raise "Your platform does not seem to be an Unix nor a M$ Windows.\nI am sorry but the exiftran binary is necessary to run selector, and exiftran is probably not available for you plateform. If you have exiftran installed, please contact the developper to correct that bug, kieffer at terre-adelie dot org"
    sys.exit(1)

configured = False
for i in ConfFile:
    if os.path.isfile(i):configured = True


### trick to make an auto-install under windows :
if len(sys.argv) == 1:
    sys.argv.append("install")



setup(name='Imagizer',
    version='1.1.0',
    author='Jerome Kieffer',
    author_email='Jerome.Kieffer@terre-adelie.org',
    url='http://wiki.terre-adelie.org/Imagizer',
    description="Imagizer is a manager for a repository of photos",
    license='GNU GPL v2',
    scripts=scripts,
    data_files=[
        (installdir, ["selector.glade", execexiftran] +
        [os.path.join("pixmaps", i) for i in os.listdir("pixmaps") if (i.endswith(".png") or i.endswith(".ico"))]),
        (os.path.split(ConfFile[0])[0], ['imagizer.conf'])
    ],
    packages=['imagizer'],
    package_dir={'imagizer': 'imagizer'},
    ext_package="imagizer",
    ext_modules=[
         Extension(
             name='libexiftran',
             sources=[os.path.join("libexiftran", i) for i in os.listdir("libexiftran") if i.endswith(".c")],
#             glob.glob(os.path.join("libexiftran", "*.c")),
             define_macros=[],
             libraries=["jpeg", "exif", "m"],
    #               include_dirs=["/usr/include/libexif"]
         ),
    ],
    )
os.remove("imagizer.conf")

if not configured:
    import config
    config = config.Config()
    config.load(ConfFile)
#    textinterface = True
#    try:
#        import pygtk ; pygtk.require('2.0')
#        import gtk, gtk.glade
        #textinterface = False
#    except ImportError:

#        textinterface = True
#    if textinterface:
    while True:
        print "Enter le chemin du repertoire racine du serveur WEB :"
        config.WebRepository = raw_input("[%s] :" % config.WebRepository)
        if os.path.isdir(config.WebRepository):
            break
        print "No Such Directory"
#    else:
#        from dirchooser import WarningSc
#        W = WarningSc(config.WebRepository, window="WWW-root")
#        config.WebRepository = W.directory
#        del W
    config.Locale, config.Coding = locale.getdefaultlocale()
    LANG = os.getenv("LANG")
    if LANG:
        config.Locale = LANG
    config.printConfig()
    config.saveConfig("/etc/imagizer.conf")
    print "Configuration finished .... Saving it\nYou can modify it in /etc/imagizer.conf"

    try:
        import pyexiv2
    except:
        raise ImportError("You should install pyexiv2 by: #aptitude install python-pyexiv2")

    try:
        import Image, ImageStat, ImageChops, ImageFile
    except:
        raise ImportError("Selector needs PIL: Python Imaging Library\n PIL is available from http://www.pythonware.com/products/pil/\ninstall it by # aptitude install python-imaging")
    try:
        import pygtk ; pygtk.require('2.0')
        import gtk, gtk.glade
    except ImportError:
        raise ImportError("Selector needs pygtk and glade-2 available from http://www.pygtk.org/\nPLease install it with # aptitude install python-glade2")

