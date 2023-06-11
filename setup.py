#!/usr/bin/env python
# -*- coding: UTF8 -*-
#******************************************************************************\
# * $Source$
# * $Id$
# *
# * Copyright (C) 2006,  Jérome Kieffer <kieffer@terre-adelie.org>
# * Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
# * Licence GPL v2
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# *
#*****************************************************************************/

"""
The setup.py script allows to install Imagizer regardless to the operating system
"""
import glob
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.extension import Extension
import os, sys, distutils.sysconfig, shutil, locale
sys.path.insert(0, os.path.dirname(__file__))

def get_version():
    """
    return the version string
    """
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "imagizer-src", "__init__.py")) as f:
        for line in f:
            if line.strip().startswith("__version__"):
                return eval(line.split("=")[1])

version = get_version()

SCRIPTS = "scripts"

# here we detect the OS runnng the program so that we can call exftran in the right way
installdir = os.path.join(distutils.sysconfig.get_python_lib(), "imagizer")
EXIFTRAN = "pyexiftran"
# JPEG_VERSION = "80"  # "62"
JPEG_VERSION = "62"
JPEG_DIR = os.path.join(EXIFTRAN, "jpeg", JPEG_VERSION)

sources = glob.glob(os.path.join(EXIFTRAN, "*.c")) + glob.glob(os.path.join(JPEG_DIR, "*.c"))


if os.name == 'nt':  # sys.platform == 'win32':
    execexiftran = os.path.join("bin", "exiftran.exe")
    ConfFile = [os.path.join(os.getenv("ALLUSERSPROFILE"), "imagizer.conf"), os.path.join(os.getenv("USERPROFILE"), "imagizer.conf")]
    shutil.copy('selector', 'selector.py')
    shutil.copy('generator', 'generator.py')
    shutil.copy('imagizer.conf-windows', 'imagizer.conf')


elif os.name == 'posix':
#    shutil.copy(os.path.join(os.getcwd(),"bin","exiftran"+str(int(1+log(os.sys.maxint+1)/log(2)))),os.path.join(os.getcwd(),"bin","exiftran"))
    ConfFile = ["/etc/imagizer.conf", os.path.join(os.getenv("HOME"), ".imagizer")]
#    scripts = ['selector', "generator", "NommeVideo.py", "NommeVideo2.py"]
    execexiftran = os.path.join("bin", "exiftran")
    os.chmod(execexiftran, 509)  # 509 = 775 in octal
    shutil.copy('imagizer.conf-unix', 'imagizer.conf')
else:
    raise "Your platform does not seem to be an Unix nor a M$ Windows.\nI am sorry but the exiftran binary is necessary to run selector, and exiftran is probably not available for you plateform. If you have exiftran installed, please contact the developper to correct that bug, kieffer at terre-adelie dot org"


rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
scripts = [os.path.join(SCRIPTS, scriptname) for scriptname in os.listdir(os.path.join(rootdir, "scripts"))]

configured = False
for i in ConfFile:
    if os.path.isfile(i):
        configured = True

# ## trick to make an auto-install under windows :
if len(sys.argv) == 1:
    sys.argv.append("install")

binary_modules = []
binary_modules.append({"name":'pyexiftran',
                       "sources":sources,
                       "define_macros":[],
                       "include_dirs":[JPEG_DIR],
                       "libraries":["jpeg", "exif", "m"]})
binary_modules.append({"name":'down_sampler',
                       "sources": ["src/down_sampler.c"],
                       "extra_compile_args": ["-fopenmp"],
                       "extra_link_args":["-fopenmp"]})
binary_modules.append({"name":'_tree',
                       "sources": ["src/_tree.c"],
                       "extra_compile_args": [],
                       "extra_link_args":[]})

print("execexiftran", execexiftran)
setup(name='imagizer',
    version=version,
    author='Jérôme Kieffer',
    author_email='Jerome.Kieffer@terre-adelie.org',
    url='http://wiki.terre-adelie.org/Imagizer',
    description="image repository management tools",
    long_description="manager for a repository of images with complete metadata management",
    license='GNU GPL v2',
    scripts=scripts,
    data_files=[
        (installdir, ["selector.glade", execexiftran]),
        (os.path.join(installdir, "gui"), glob.glob("gui/*.ui")),
        (os.path.join(installdir, "pixmaps"), glob.glob("pixmaps/*.png") + glob.glob("pixmaps/*.ico")),
        (os.path.split(ConfFile[0])[0], ['imagizer.conf']),
        ("/usr/lib/xscreensaver", ["screensaver/imagizer", "screensaver/imagizer_qt", "screensaver/imagizer_qt5"])
    ],
    packages=['imagizer'],
    package_dir={'imagizer': 'imagizer-src'},
    ext_package="imagizer",
    ext_modules=[Extension(**mode) for mode in binary_modules],
    classifiers=[
          'Development Status :: 5 - production',
          'Environment :: Graphic',
          'Environment :: Qt',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Photographs',
          'License :: OSI Approved :: GPL',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          ],)
os.remove("imagizer.conf")

if not configured:
    sys.path.insert(0, "imagizer-src")
    from config import config
    config.load(ConfFile)
    while True:
        print("Enter le chemin du repertoire racine du serveur WEB :")
        config.WebRepository = input("[%s] :" % config.WebRepository)
        if(os.path.isdir(config.WebRepository)):
            break
        print("No Such Directory")
    config.Locale, config.Coding = locale.getdefaultlocale()
    LANG = os.getenv("LANG")
    if LANG:
        config.Locale = LANG
    config.printConfig()
    config.save("/etc/imagizer.conf")
    print("Configuration finished .... Saving it\nYou can modify it in /etc/imagizer.conf")

    try:
        import exif
    except ImportError:
        raise ImportError("You should install exiv2 by: #aptitude install python-gi libgexiv2-2")

    try:
        import Image, ImageStat, ImageChops, ImageFile
    except ImportError:
        raise ImportError("Selector needs PIL: Python Imaging Library\n PIL is available from http://www.pythonware.com/products/pil/\ninstall it by # aptitude install python-imaging")

