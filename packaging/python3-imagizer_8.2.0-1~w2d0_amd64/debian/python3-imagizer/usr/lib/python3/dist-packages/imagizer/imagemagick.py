# !/usr/bin/env python
# coding: utf-8

"""
Interface to ImageMagick
"""

__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "24/07/2019"
__license__ = "GPL"

import os
import subprocess
import logging
import stat
logger = logging.getLogger(__name__)

class ImageMagick(object):
    def __init__(self, path=None):
        """Constructor

        :param path: path where the different executable are to be found
        """
        self.cache = {}
        self.path = os.path.abspath(path) if path else None

    def set_path(self, path):
        "Reset the cache !"
        self.cache = {}
        self.path = os.path.abspath(path) if path else None


    def get_executable(self, progname):
        """Returns the program name to execute for an ImageMagick command."""

        if progname in self.cache:
            return self.cache[ progname ]
        else:
            if self.path:
                prg = os.path.join(self.path, progname)
            else:
                prg = progname
            prg = normpath(prg)
            self.cache[ progname ] = prg

            # Issue a warning if we can't find the program where specified.
            if self.path and \
                not os.path.exists(prg) and \
                not os.path.exists(prg + '.exe'):
                    logger.warning("Can't stat ImageMagick program %s\nPerhaps try specifying it using --magick-path.", prg)
            return prg

    def run(self, command, *args):
        """Run the given command with the provided arguments

        :param command: the name of the image-magick command
        :param args: the command line argument as a list of strings
        :return: out, err
        """
        executable = self.get_executable(command)
        process = subprocess.Popen([executable] + args,
                              shell=False,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        rc = process.wait()
        out = process.stdout.read()
        err = process.stderr.read()
        if rc:
            logger.warning("Failed executing %s with rc %d", command, rc)
        process.stderr.close()
        process.stdout.close()
        return out, err

