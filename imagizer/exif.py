# coding: utf8
__author__ = "Jérôme Kieffer"
__contact = "imagizer@terre-adelie.org"
__date__ = "20111016"
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


#class Exif(dict):
#    """Wrapper for pyexiv2"""
#    def __init__(self, filename):
#        """
#        Wrapper for various version of pyexiv2
#        @param  filename: name of the image file
#        @type filename: string or unicode
#        """
#        dict.__init__(self)
#        self.filename = filename
#        try:
#            self.version_info = pyexiv2.version_info
#        except AttributeError:
#            self.version_info = (0, 1, 0)
#
#        if self.version_info >= (0, 2, 0):
#            self.metadata = pyexiv2.ImageMetadata(filename)
#        else:
#            self.metadata = pyexiv2.Image(filename)
#
#    def __getitem__(self, key):
#        "Get a metadata tag for a given key."
#        return self.metadata.__getitem__(key)
#
#    def __setitem__(self, key, value):
#        """Set a metadata tag for a given key. If the tag was previously set, it is overwritten. As a handy shortcut, a value may be passed instead of a fully formed tag. The corresponding tag object will be instantiated.
#Parameters:    
#
#    * key (string) – metadata key in the dotted form familyName.groupName.tagName where familyName may be one of exif, iptc or xmp.
#    * tag_or_value (pyexiv2.exif.ExifTag or pyexiv2.iptc.IptcTag or pyexiv2.xmp.XmpTag or any valid value type) – an instance of the corresponding family of metadata tag, or a value
#
#Raises KeyError:
#     
#
#if the key is invalid"""
#        self.metadata.__setitem__(key, value)
#
#    def __delitem__(self, key):
#        """Delete a metadata tag for a given key.
#    Parameter:    key (string) – metadata key in the dotted form familyName.groupName.tagName where familyName may be one of exif, iptc or xmp.
#    Raises KeyError:
#         if the tag with the given key doesn’t exist
#    """
#        self.metadata.__delitem__(key)
#
#
#
#    def read(self):
#        if self.version_info >= (0, 2, 0):
#            return self.metadata.read()
#        else:
#            return self.metadata.readMetadata()
#    def write(self):
#        if self.version_info >= (0, 2, 0):
#            return self.metadata.write()
#        else:
#            return self.metadata.writeMetadata()
#
#    def dumpThumbnailToFile(self, thumbFile):
#        if self.version_info >= (0, 2, 0):
#            self.metadata.exif_thumbnail.write_to_file(thumbFile)
#        else:
#            self.metadata.dumpThumbnailToFile(thumbFile)
#
#    def exifKeys(self):
#        """
#        List of the keys of the available EXIF tags.
#        """
#        if self.version_info >= (0, 2, 0):
#            return self.metadata.exif_keys
#        else:
#            return self.metadata.exifKeys()
#    exif_keys = property(exifKeys)
#
#
#    def getComment(self):
#        if self.version_info >= (0, 2, 0):
#            return self.metadata.comment
#        else:
#            return self.metadata.getComment()
#    def setComment(self, comment):
#        if self.version_info >= (0, 2, 0):
#            self.metadata.comment = comment
#        else:
#            return self.metadata.setComment(comment)
#    comment = property(getComment, setComment)
#
#
#    def interpretedExifValue(self, key):
#        """Get the interpreted value of an EXIF tag as presented by the exiv2 tool.
# 
#For EXIF tags, the exiv2 command-line tool is capable of displaying
#user-friendly interpreted values, such as 'top, left' for the
#'Exif.Image.Orientation' tag when it has value '1'. This method always
#returns a string containing this interpreted value for a given tag.
#Warning: calling this method will not cache the value in the internal
#dictionary.
# 
#Keyword arguments:
#key -- the EXIF key of the requested metadata tag
#        """
#        if self.version_info >= (0, 2, 0):
#            return self.metadata[key].human_value
#        else:
#            return self.metadata.interpretedExifValue(key)


