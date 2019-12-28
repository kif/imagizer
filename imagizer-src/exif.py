#!/usr/bin/env python
# coding: utf8
__author__ = "Jérôme Kieffer"
__contact = "imagizer@terre-adelie.org"
__date__ = "20191222"
__license__ = "GPL"

import os
import gi
gi.require_version('GExiv2', '0.10')
from gi.repository import GExiv2

class Exif:

    def __init__(self, filename):
        """Constructor of the class
        
        :param filename: name of the image file
        """
        self.filename = filename
        if not os.path.exists(filename):
            raise RuntimeError("File does not exist: %s"%filename)
        self._gi = None
        self._tags = [] # cached tags
        self.read()

    def read(self):
        """Read the metadata embedded in the associated image. 
        It is necessary to call this method once before attempting 
        to access the metadata (an exception will be raised if 
        trying to access metadata before calling this method).
        
        Should do nothing: left for compatibility
        """
        self._gi = GExiv2.Metadata(self.filename)
        # Work around for bug about comment being the camera make by resetting the tag
        description = self._gi.get_tag_raw("Exif.Image.ImageDescription")
        camera = self._gi.get_tag_raw("Exif.Image.Make")
        if camera and description and description.get_data() == camera.get_data():
            self._gi.set_tag_long("Exif.Image.ImageDescription", 0) and self._gi.clear_tag("Exif.Image.ImageDescription")
        return self

    def write(self, preserve_timestamps=False):
        """Write the metadata back to the image.
        
        :param bool preserve_timestamps: Whether to preserve the file’s 
                original timestamps (access time and modification time)
        """
        if preserve_timestamps:
            stats = os.stat(self.filename)
        self._gi.save_file(self.filename)
        if preserve_timestamps:
            os.utime(self.filename, (stats.st_atime, stats.st_mtime))
    
    @property
    def previews(self):
        "return a list of preview"
        props = self._gi.get_preview_properties()
        return [self._gi.get_preview_image(i) for i in props]

    @property
    def size(self):
        "Calculate the size of the image"
        return (self._gi.get_pixel_width(), self._gi.get_pixel_height())

    @property
    def orientation(self):
        "return the orientation value for the image"
        return self._gi.get_orientation().real

    @property
    def comment(self):
        return self._gi.get_comment()

    @comment.setter
    def comment(self, comment):
        return self._gi.set_comment(comment)

    @property
    def exif_keys(self):
        "return list of exif keys"
        if not self._tags:
            res = []
            if self._gi.has_exif():
                res = self._gi.get_exif_tags()
            if self._gi.has_xmp():
                res += self._gi.get_xmp_tags()
            if self._gi.has_iptc():
                res += self._gi.get_iptc_tags()
            self._tags = res
        return self._tags
    
    def get_largest_preview(self):
        props = self._gi.get_preview_properties()
        best = None
        best_size = 0
        for p in props:
            ext = p.get_extension()
            size = p.get_size()
            if "jp" in ext.lower():
                if size > best_size:
                    best_size = size
                    best = p
        if best is None: # DOn't check for jpeg
            for p in props:
                size = p.get_size()
                if size > best_size:
                    best_size = size
                    best = p
        if best is None:
            raise RuntimeError("No Thumbnail found in file %s"%self.filename)
        return self._gi.get_preview_image(best)

    def dumpThumbnailToFile(self, thumb_filename):
        "Save the best resolution thumbnail to another file ... probably deprecated"
        preview = self.get_largest_preview()
        ext = preview.get_extension()
        if thumb_filename.lower().endswith(ext.lower()):
            thumb_filename = thumb_filename[:-len(ext)]
        preview.write_file(thumb_filename)

    def interpretedExifValue(self, key):
        "This is legacy, use the [] to access interpreted value"
        return self._gi.get_tag_interpreted_string(key)

    def copy(self, other):
        """
        Copy the metadata to another image.
        The metadata in the destination is overridden. In particular, if the
        destination contains e.g. EXIF data and the source doesn't, it will be
        erased in the destination, unless explicitly omitted.

        :param other: the destination metadata to copy to 
        :return: other (updated)
        """
        self._gi.save_file(other.filename)
        other._tags = []
        other.read()
        return other

    def get(self, key, default=None, type=None):
        if key in self.exif_keys:
            if type is str:
                return self._gi.get_tag_string(key)
            elif type is int:
                return self._gi.get_tag_long(key)
            elif type is bytes:
                return self._gi.get_tag_raw(key).get_data()
            else:
                return self._gi.get_tag_raw(key)
        else:
            return default

    def pop(self, key):
        "Remove a key and return the value if present"
        value = None
        if key in self.exif_keys:
            value = self._gi.get_tag_raw(key)
            self._gi.clear_tag(key)
            self._tags.pop(key)
        return value

    def __iter__(self):
        "Implements the dictionnary interface"
        for x in self.exif_keys:
            yield x

    def __contains__(self, key):
        "Implements the dictionnary interface ... TODO"
        return self._gi.has_tag(key)

    def items(self):
        "Implements the dictionnary interface"
        for tag in self.exif_keys:
            yield (tag, self._gi.get_tag_interpreted_string(tag))

    keys = __iter__

    def values(self):
        "Implements the dictionnary interface"
        for tag in self.exif_keys:
            yield self._gi.get_tag_interpreted_string(tag)

    def __setitem__(self, key, value):
        if isinstance(value, str):
            self._gi.set_tag_string(key, value)
        elif isinstance(value, int):
            self._gi.set_tag_long(key, value)
        else:
            try:
                self._gi.set_tag_multiple(key, value)
            except Exception as e:
                logger.error(e)

    def __getitem__(self, key):
        return self._gi.get_tag_interpreted_string(key)

    def __repr__(self):
        return "\n".join(("%50s:\t%s" % (key, self._gi.get_tag_interpreted_string(key)) for key in self.exif_keys))

    def __len__(self):
        return len(self.exif_keys)

