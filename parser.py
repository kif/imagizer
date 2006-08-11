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

import re

class AttrFile:

	"""Attributes file representation and trivial parser."""

	#---------------------------------------------------------------------------
	#
	def __init__( self, path ):

		"""Constructor."""

		self._path = path
		self._attrmap = {}
		self._dirty = 0

	#---------------------------------------------------------------------------
	#
	def read( self ):

		"""Read the file and parse it."""

		try:
			f = open( self._path, "r" )
			self._lines = f.read()
			f.close()
		except IOError, e:
			print >> sys.stderr, \
				  "Error: cannot open attributes file", self._path
			self._lines = ''

		self.parse( self._lines )
		self._dirty = 0

	#---------------------------------------------------------------------------
	#
	def resetDirty( self ):

		"""Resets the dirty flag. Why would you want to do this?"""

		self._dirty = 0

	#---------------------------------------------------------------------------
	#
	def write( self ):

		"""Write the file to disk, if dirty."""

		# If not dirty, don't write anything.
		if self._dirty == 0:
			return

		try:
			# if there are no field, delete the file.
			if len( self._attrmap ) == 0:
				os.unlink( self._path )
				return

			f = open( self._path, "w" )
			for k in self._attrmap.keys():
				f.write( k )
				f.write( ": " )
				f.write( self._attrmap[k] )
				f.write( "\n\n" )
			f.close()
			os.chmod(self._path,config.DefaultFileMode)
		except IOError, e:
			print >> sys.stderr, "Error: cannot open attributes file", \
				  self._path
			self._lines = ''

	#---------------------------------------------------------------------------
	#
	def parse( self, lines ):

		"""Parse attributes file lines into a map."""

		mre1 = re.compile( "^([^:\n]+)\s*:", re.M )
		mre2 = re.compile( "^\s*$", re.M )

		pos = 0
		while 1:
			mo1 = mre1.search( lines, pos )

			if not mo1:
				break

			txt = None
			mo2 = mre2.search( lines, mo1.end() )
			if mo2:
				txt =  lines[ mo1.end() : mo2.start() ].strip()
			else:
				txt =  lines[ mo1.end() : ] .strip()

			self._attrmap[ mo1.group( 1 ) ] = txt

			if mo2:
				pos = mo2.end()
			else:
				break

	#---------------------------------------------------------------------------
	#
	def get( self, field ):

		"""Returns an attribute field content extracted from this attributes
		file."""

		if self._attrmap.has_key( field ):
			return self._attrmap[ field ]
		else:
			raise KeyError()

	#---------------------------------------------------------------------------
	#
	def get_def( self, field, default=None ):

		"""Returns an attribute field content extracted from this attributes
		file."""

		if self._attrmap.has_key( field ):
			return self._attrmap[ field ]
		else:
			return default

	#---------------------------------------------------------------------------
	#
	def set( self, field, value ):

		"""Sets a field of the description file. Returns true if the value has
		changed.  Set a field value to None to remove the field."""

		if value == None:
			if self._attrmap.has_key( field ):
				del self._attrmap[ field ]
				self._dirty = 1
				return 1
			else:
				return 0

		# remove stupid dos chars (\r) added by a web browser
		value = value.replace( '\r', '' )
		value = value.strip()

		# remove blank lines from the field value
		mre2 = re.compile( "^\s*$", re.M )
		while 1:
			mo = mre2.search( value )
			if mo and mo.end() != len(value):
				outval = value[:mo.start()]
				id = mo.end()
				while value[id] != '\n': id += 1
				outval += value[id+1:]
				value = outval
			else:
				break

		if '\n' in value:
			value = '\n' + value

		if self._attrmap.has_key( field ):
			if self._attrmap[ field ] == value:
				return 0

		self._attrmap[ field ] = value
		self._dirty = 1
		return 1

	#---------------------------------------------------------------------------
	#
	def __getitem__(self, key):
		return self.get( key )

	#---------------------------------------------------------------------------
	#
	def __setitem__(self, key, value):
		return self.set( key, value)
	


	#---------------------------------------------------------------------------
	#
	def keys(self):
		return self._attrmap.keys()

	#---------------------------------------------------------------------------
	#
	def has_key(self, key):
		return self._attrmap.has_key(key)

	#---------------------------------------------------------------------------
	#
	def __len__(self):
		return len( self._attrmap )

	#---------------------------------------------------------------------------
	#
	def __repr__( self ):

		"""Returns contents to a string for debugging purposes."""

		txt = ""
		for a in self._attrmap.keys():
			txt += a + ":\n" + self._attrmap[a] + "\n\n"
		return txt
