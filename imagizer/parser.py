#!/usr/bin/env python
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2001, Martin Blais <blais@furius.ca>
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

"""CLASS AttrFile Attributes file representation and trivial parser."""

import re, os, sys, logging
logger = logging.getLogger("imagizer.parser")
import config
config = config.Config()

class AttrFile:
    """Attributes file representation and trivial parser."""


    def __init__(self, path):
        """Constructor."""
        self._path = path
        self._attrmap = {}
        self._dirty = False
        self._attrmap["coding"] = config.Coding


    def read(self):
        """Read the file and parse it."""
        logger.debug("AttrFile.read file %s" % self._path)
        try:
            f = open(self._path, "rb")
            self._lines = f.read()
            f.close()
        except IOError, e:
            logger.error("Cannot open attributes file %s" % self._path)
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

            f = open(self._path, "w")
            for k in self._attrmap.keys():
                f.write(k)
                f.write(": ")
                f.write(self._attrmap[k].encode(coding))
                f.write("\n\n")
            f.close()
        except IOError, e:
            print >> sys.stderr, "Error: cannot open attributes file", \
                  self._path
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
                self._attrmap[ key ] = txt.decode(coding)
            except:
                self._attrmap[ key ] = txt


    def get(self, field):
        """
        Returns an attribute field content extracted from this attributes
        file.
        """
        logger.debug("AttrFile.get(%s)" % field)
        if field in self._attrmap:
            return self._attrmap[ field ]
        else:
            logger.error("AttrFile.get(%s): No such field in %s" % (field, self._path))
            raise KeyError("AttrFile.get(%s): No such field in %s" % (field, self._path))


    def get_def(self, field, default=None):
        """
        Returns an attribute field content extracted from this attributes
        file.
        """
        logger.debug("AttrFile.get_def(%s)" % field)
        if field in self._attrmap:
            return self._attrmap[ field ]
        else:
            logger.debug("AttrFile.get_def(%s), returned default:%s" % (field, default))
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
        return self.get(key)


    def __setitem__(self, key, value):
        return self.set(key, value)


    def keys(self):
        return self._attrmap.keys()


    def has_key(self, key):
        return self._attrmap.has_key(key)


    def __len__(self):
        return len(self._attrmap)


    def __repr__(self):
        """
        Returns contents to a string for debugging purposes.
        """
        lsttxt = ["AttrFile for %s" % self._path]
        for a in self._attrmap:
            lsttxt += [a + ":", self._attrmap[a], ""]
        return os.linesep.join(lsttxt)
