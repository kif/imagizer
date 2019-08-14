#!/usr/bin/env python
# coding: utf8
#******************************************************************************\
# *
# * Copyright (C) 2001, Martin Blais <blais@furius.ca>
# * Copyright (C) 2012, Jerome Kieffer <imagizer@terre-adelie.org>
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
from __future__ import with_statement, division, print_function, absolute_import

"""CLASS AttrFile Attributes file representation and trivial parser."""

__authors__ = ["Martin Blais", "Jérôme Kieffer"]
__contact = "imagizer@terre-adelie.org"
__date__ = "20120415"
__license__ = "GPL"

import re, os, sys, logging
from collections import OrderedDict
logger = logging.getLogger("imagizer.parser")
from .config import config

PY2 = sys.version_info[0] == 2

class AttrFile(object):
    """Attributes file representation and trivial parser."""


    def __init__(self, path):
        """Constructor."""
        self._path = path
        self._attrmap = OrderedDict()
        self._dirty = False
        self._attrmap["coding"] = config.Coding


    def read(self):
        """Read the file and parse it."""
        logger.debug("AttrFile.read file %s" % self._path)
        try:
            with  open(self._path, "rb") as f:
                self._lines = f.read()
        except IOError as error:
            logger.error("Cannot open attributes file %s: %s", self._path, error)
            self._lines = ''

        self.parse(self._lines)
        self._dirty = False


    def resetDirty(self):
        """Resets the dirty flag. Why would you want to do this?"""
        self._dirty = False


    def write(self):
        """Write the file to disk, if dirty."""
        logger.debug("AttrFile.write file %s" % self._path)
        # If not dirty, don't write anything.
        if not self._dirty:
            return
        try:
            coding = self._attrmap["coding"]
        except:
            coding = config.Coding

        try:
            # if there are no field, delete the file.
            if len(self._attrmap) == 0:
                os.unlink(self._path)
                return

            with open(self._path, "wb") as f:
                for k in self._attrmap.keys():
                    f.write(k)
                    f.write(": ")
                    f.write(self._attrmap[k].encode(coding))
                    f.write("\n\n")
        except IOError as e:
            sys.stderr.write("Error: cannot open attributes file %s: %s%s"\
                             % (self._path, e, os.linesep))
            self._lines = ''
        try:
            os.chmod(self._path, config.DefaultFileMode)
        except:
            logger.warning("Unable to chmod %s" % self._path)


    def parse(self, lines):
        """
        Parse attributes file lines into a map.
        """
        logger.debug("AttrFile.parse")
        mre1 = re.compile("^([^:\n]+)\s*:", re.M)
        mre2 = re.compile("^\s*$", re.M)

        pos = 0
        while 1:
            mo1 = mre1.search(lines, pos)

            if not mo1:
                break

            txt = None
            mo2 = mre2.search(lines, mo1.end())
            if mo2:
                txt = lines[ mo1.end() : mo2.start() ].strip()
            else:
                txt = lines[ mo1.end() : ] .strip()

            self._attrmap[ mo1.group(1) ] = txt

            if mo2:
                pos = mo2.end()
            else:
                break
        try:
            coding = self._attrmap["coding"]
        except:
            coding = config.Coding

        for key in self._attrmap.keys():
            txt = self._attrmap[ key ]
            try:
                self._attrmap[key] = txt.decode(coding)
            except:
                self._attrmap[key] = txt


    def get(self, field, default=None):
        """
        Returns an attribute field content extracted from this attributes
        file.
        """
        logger.debug("AttrFile.get(%s)" % field)
        if field in self._attrmap:
            return self._attrmap[ field ]
        else:
            logger.debug("AttrFile.get(%s), returned default:%s" % (field, default))
            return default


    def set(self, field, value):
        """
        Sets a field of the description file. Returns true if the value has
        changed.
        Set a field value to None to remove the field.
        """
        logger.debug("AttrFile.set(%s,value: %s)" % (field, type(value)))
        if value == None:
            if field in self._attrmap:
                self._attrmap.pop(field)
                self._dirty = True
                return 1
            else:
                return 0

        # remove stupid dos chars (\r) added by a web browser
        value = value.strip()

        # remove blank lines from the field value
        mre2 = re.compile("^\s*$", re.M)
        while 1:
            mo = mre2.search(value)
            if mo and mo.end() != len(value):
                outval = value[:mo.start()]
                id = mo.end()
                while value[id] != '\n': id += 1
                outval += value[id + 1:]
                value = outval
            else:
                break

        if '\n' in value:
            value = '\n' + value

        if field in self._attrmap:
            if self._attrmap[ field ] == value:
                return 0

        self._attrmap[ field ] = value
        self._dirty = True
        return 1


    def __getitem__(self, key):
        """
        Returns an attribute field content extracted from this attributes
        file.
        """
        logger.debug("AttrFile.__getitem__(%s)" % key)
        if key in self._attrmap:
            return self._attrmap[ key ]
        else:
            logger.error("AttrFile.__getitem__(%s): No such field in %s" % (key, self._path))
            raise KeyError("AttrFile.__getitem__(%s): No such field in %s" % (key, self._path))


    def __setitem__(self, key, value):
        return self.set(key, value)


    def keys(self):
        return self._attrmap.keys()


    def __contains__(self, key):
        return key in self._attrmap
    has_key = __contains__


    def __len__(self):
        return len(self._attrmap)


    def __repr__(self):
        """
        Returns contents to a string for debugging purposes.
        """
        lsttxt = ["AttrFile for %s" % self._path]
        if PY2:
            lsttxt += ["%s: %s" % (a, b.encode(config.Coding)) for a, b in self._attrmap.items()]
        else:
            lsttxt += ["%s: %s" % (a, b) for a, b in self._attrmap.items()]
        return os.linesep.join(lsttxt)
