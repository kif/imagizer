#!/usr/bin/env python
# coding: utf8

# Historical version kept for compatibility with pyexiv2

__author__ = "Jérôme Kieffer"
__contact = "imagizer@terre-adelie.org"
__date__ = "20120530"
__license__ = "GPL"

import pyexiv2
try:
    version_info = pyexiv2.version_info
except AttributeError:
    version_info = (0, 1, 0)

if version_info >= (0, 2, 0):
    class Exif(pyexiv2.ImageMetadata):
        def interpretedExifValue(self, key):
            """
            Get the interpreted value of an EXIF tag as presented by the exiv2 tool.
            @param key: the EXIF key of the requested metadata tag
            """
            return self[key].human_value

        def dumpThumbnailToFile(self, thumbFile):
                self.exif_thumbnail.write_to_file(thumbFile)

else:
    class Exif(pyexiv2.Image):
        """
        Wrapper for pyexiv2 v0.1.x
        """
        def __init__(self, filename):
            """    :
            Constructor of the class Exif for handling Exif metadata
            Wrapper for pyexiv2 v0.1.x

            @param filename: path to an image file
            @type filename: string
            """
            self.filename = filename
            pyexiv2.Image.__init__(self, filename)
        def read(self):
            return self.readMetadata()
        def write(self):
            return self.writeMetadata()
        def getComment(self):
            return pyexiv2.Image.getComment(self)
        def setComment(self, value):
            return pyexiv2.Image.setComment(self, value)
        comment = property(getComment, setComment)
        def getExifKeys(self):
            return self.exifKeys()
        exif_keys = property(getExifKeys)
        def copy(self, other, exif=True, iptc=True, xmp=True, comment=True):
            """
            Copy the metadata to another image.
            The metadata in the destination is overridden. In particular, if the
            destination contains e.g. EXIF data and the source doesn't, it will be
            erased in the destination, unless explicitly omitted.

            @ param other: the destination metadata to copy to (it must have been
              :meth:`.read` beforehand)
            @type other: :class:`pyexiv2.metadata.ImageMetadata`
            @param exif: whether to copy the EXIF metadata
            @type exif: boolean
            @param iptc: whether to copy the IPTC metadata
            @type iptc: boolean
            @param xmp: whether to copy the XMP metadata
            @type xmp: boolean
            @param comment: whether to copy the image comment
            @type comment: boolean

            """
            if comment:
                other.setComment(self.getComment())
            if exif:
                for metadata in [ 'Exif.Image.Make', 'Exif.Image.Model', 'Exif.Photo.DateTimeOriginal',
                         'Exif.Photo.ExposureTime', 'Exif.Photo.FNumber', 'Exif.Photo.ExposureBiasValue',
                         'Exif.Photo.Flash', 'Exif.Photo.FocalLength', 'Exif.Photo.ISOSpeedRatings',
                         "Exif.Image.Orientation", "Exif.Photo.UserComment"
                         ]:
                    if metadata in self.getExifKeys():
                        try:
                            other[metadata] = self[metadata]
                        except:
                            print("Unable to copying metadata %s in file %s, value: %s" % (metadata, self.filename, self.exif[metadata]))

