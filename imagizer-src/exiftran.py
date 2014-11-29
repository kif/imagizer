#!/usr/bin/env python
# coding: utf-8
#******************************************************************************\
#*
#* Copyright (C) 2006-2014,  Jérôme Kieffer <kieffer@terre-adelie.org>
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

#
# Liste des dépendances : python, PIL, Glade-2
# Exiftran existe en version windows maintenant ... nous utilisons une verison modifiée ...!!!!
#
#todo liste des fonctions a implemanter ....
# - se passer de exiftran
# - la version windows et la version mac
# - faire une doc décente.
# - proposer d'exporter toutes les photos dans un seul répertoire (pas de jour)


"""
exiftran.py a wrapper for the original exiftran provided by Gerd Korn
http://linux.bytesex.org/fbida/

Needs libexif-dev, libjepg-dev and python-dev to be installed on the system.
"""
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20111016"
__license__ = "GPL"

import os, threading, logging

installdir = os.path.dirname(__file__)

try:
    import libexiftran
    exiftranExe = None
    print "Successfully imported libexiftran"
except:
    print "Failed to import libexiftran: use old fashion"
    if os.name == 'nt': #sys.platform == 'win32':
        exiftranExe = os.path.join(installdir, "exiftran.exe ")
    elif os.name == 'posix':
        exiftranPath = os.path.join(installdir, "exiftran ")
        if not os.path.isfile(exiftranPath):
            for oneExeDir in os.environ["PATH"].split(os.pathsep):
                if os.path.isfile(os.path.join(oneExeDir, "exiftran")):
                    exiftranPath = os.path.join(oneExeDir, "exiftran ")
        MaxJPEGMem = 1000000 # OK up to 100 Mpix
        exiftranExe = "JPEGMEM=%i %s " % (MaxJPEGMem, exiftranPath)




class Exiftran(object):
    """
    This is static class implementing libexiftran in a more pythonic way
    """
    semaphore = threading.Semaphore()


    @staticmethod
    def _exiftranThread(action, filename):
        """
        actual exiftran launcher
        @param action: 0 for autorotate, 1 for 180 deg, 2 for 270 deg and 9 for 90 deg reotation clockwise
        @type action: integer
        @param filename: name of the jpeg file to process
        @type filename: string
        """
        logging.debug("Exiftran._exiftranThread %s %s" % (action, filename))
        if exiftranExe is None:
            libexiftran.run(action, filename)
        else:
            if action == 0:action = "a"
            os.system('%s -ip -%s "%s" ' % (exiftranExe, action, filename))
        Exiftran.semaphore.release()


    @staticmethod
    def rotate90(filename):
        """
        rotate the given file by 90 degrees clockwise
        @param filename: name of the JPEG file to rotate
        @type filename: python string
        """
        logging.debug("Exiftran.rotate90 %s" % (filename))
        Exiftran.semaphore.acquire()
        myThread = threading.Thread(target=Exiftran._exiftranThread, args=(9, filename))
        myThread.start()


    @staticmethod
    def rotate180(filename):
        """
        rotate the given file by 180 degrees
        @param filename: name of the JPEG file to rotate
        @type filename: python string
        """
        logging.debug("Exiftran.rotate180 %s" % (filename))
        Exiftran.semaphore.acquire()
        myThread = threading.Thread(target=Exiftran._exiftranThread, args=(1, filename))
        myThread.start()


    @staticmethod
    def rotate270(filename):
        """
        rotate the given file by 90 degrees counter-clockwise (270deg clockwise)
        @param filename: name of the JPEG file to rotate
        @type filename: python string
        """
        logging.debug("Exiftran.rotate270 %s" % (filename))
        Exiftran.semaphore.acquire()
        myThread = threading.Thread(target=Exiftran._exiftranThread, args=(2, filename))
        myThread.start()


    @staticmethod
    def autorotate(filename):
        """
        auto rotate the given file
        @param filename: name of the JPEG file to rotate
        @type filename: python string
        """
        logging.debug("Exiftran.autorotate %s" % (filename))
        Exiftran.semaphore.acquire()
        myThread = threading.Thread(target=Exiftran._exiftranThread, args=(0, filename))
        myThread.start()


    @staticmethod
    def getSemaphoreValue():
        """return the value of the semaphore, either 0 or 1"""
        return Exiftran.semaphore._Semaphore__value

