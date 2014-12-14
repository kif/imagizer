#!/usr/bin/env python
# coding: utf-8
#******************************************************************************\
#*
#* Copyright (C) 2006 - 2014,  Jérôme Kieffer <imagizer@terre-adelie.org>
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
from __future__ import with_statement, division, print_function, absolute_import

"""
Module containing most classes for handling files
"""

__author__ = "Jérôme Kieffer"
__date__ = "14/12/2014"
__licence__ = "GPLv2"
__contact__ = "imagizer@terre-adelie.org"


import os, logging
import os.path as op
installdir = op.dirname(__file__)
logger = logging.getLogger("imagizer.fileutils")
from .config import config

def makedir(filen):
    """creates the tree structure for the file"""
    dire = os.path.dirname(filen)
    if os.path.isdir(dire):
        mkdir(filen)
    else:
        makedir(dire)
        mkdir(filen)


def mkdir(filename):
    """create an empty directory with the given rights is not yet existing"""
    if not os.path.exists(filename):
        os.mkdir(filename)
        try:
            os.chmod(filename, config.DefaultDirMode)
        except OSError:
            logger.warning("Unable to chmod %s" % filename)


def findFiles(strRootDir, lstExtentions=None, bFromRoot=False):
    """
    Equivalent to:
    files=os.system('find "%s"  -iname "*.%s"'%(RootDir,suffix)).readlines()

    @param strRootDir: path of the root of the search
    @type strRootDir: string
    @param lstExtentions: list of string representing interesting extensions
    @param bFromRoot: start the return path from / instead of the strRootDir
    @return: the list of the files with the given suffix in the given dir
    @rtype: list of strings
    """
    if lstExtentions is None:
        lstExtentions = config.Extensions
    listFiles = []
    if strRootDir.endswith(os.sep):
        lenRoot = len(strRootDir)
    else:
        lenRoot = len(strRootDir) + 1
    for root, dirs, files in os.walk(strRootDir):
        for oneFile in  files:
            if os.path.splitext(oneFile)[1].lower() in lstExtentions:
                fullPath = os.path.join(root, oneFile)
                if bFromRoot:
                    listFiles.append(fullPath)
                else:
                    assert len(fullPath) > lenRoot
                    listFiles.append(fullPath[lenRoot:])
    return listFiles


def smartSize(size):
    """
    Print the size of files in a pretty way
    """
    unit = "o"
    fsize = float(size)
    if len(str(size)) > 3:
        size = size // 1024
        fsize /= 1024.0
        unit = "ko"
        if len(str(size)) > 3:
            size = size // 1024
            fsize /= 1024.0
            unit = "Mo"
            if len(str(size)) > 3:
                size = size // 1024
                fsize /= 1024.0
                unit = "Go"
    return fsize, unit


def recursive_delete(strDirname):
    """
    Delete everything reachable from the directory named in "top",
    assuming there are no symbolic links.
    CAUTION:  This is dangerous!  For example, if top == '/', it
    could delete all your disk files.
    @param strDirname: top directory to delete
    @type strDirname: string
    """
    for root, dirs, files in os.walk(strDirname, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(strDirname)


def list_files_in_named_dir(root, dirname, filename):
    """
    @param root:name of the root of the repository, a string
    @param dirname: name of the directory, a string
    @param filename: name of the file, a string
    @return: None is so such file exists or the list of filenames
    """
    ret = []
    for adir in os.listdir(root):
        if adir.startswith(dirname):
            fullpath = os.path.join(root, adir)
            if os.path.isdir(fullpath):
                fullname = os.path.join(fullpath, filename)
                if os.path.isfile(fullname):
                    ret.append(fullname)
    return ret
