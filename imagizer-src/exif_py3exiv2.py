#!/usr/bin/env python
# coding: utf8

# compatibility with py3exiv2

__author__ = "Jérôme Kieffer"
__contact = "imagizer@terre-adelie.org"
__date__ = "20201222"
__license__ = "GPL"

import pyexiv2


class Exif(pyexiv2.ImageMetadata):

    def __init__(self, filename):
        pyexiv2.ImageMetadata.__init__(self, filename)
        self.read()

    def interpretedExifValue(self, key):
        """
        Get the interpreted value of an EXIF tag as presented by the exiv2 tool.
        @param key: the EXIF key of the requested metadata tag
        """
        return self[key].human_value

    def dumpThumbnailToFile(self, thumbFile):
            self.exif_thumbnail.write_to_file(thumbFile)

    def _get_comment(self):
        if "Exif.Photo.UserComment" in self:
            e = self["Exif.Photo.UserComment"]
#             print("raw_value", type(e.raw_value), e.raw_value, "\n",
#                   "value", e.value, e._value, "\n",
#                   "human", e.human_value, "\n",
#                    str(e))
            if e.raw_value in ("charset=Ascii binary comment", 'binary comment'):
                ecomment = ""
            else:
                ecomment = e.value
        else:
            ecomment = ""
        jcomment = pyexiv2.ImageMetadata._get_comment(self)
        comment = jcomment or ecomment
        return comment

    def _set_comment(self, comment):
        if comment:
            try:
                pyexiv2.ImageMetadata._set_comment(self, comment)
            except ValueError:
                pass
            pyexiv2.ImageMetadata.__setitem__(self, "Exif.Photo.UserComment",
                                              "charset=Unicode " + comment)
        else:
            try:
                self._del_comment()
            except ValueError:
                pass
            pyexiv2.ImageMetadata.__setitem__(self, "Exif.Photo.UserComment", "charset=Ascii  ")

    def _del_comment(self):
        pyexiv2.ImageMetadata._del_comment(self)

    comment = property(fget=_get_comment, fset=_set_comment, fdel=_del_comment,
                       doc='The image comment.')

    def get_largest_preview(self):
        return self.previews[-1]

    @property
    def orientation(self):
        "return the orientation value for the image"
        return pyexiv2.ImageMetadata.get_orientation(self)
