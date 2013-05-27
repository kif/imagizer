#!/usr/bin/env python
# -*- coding: UTF8 -*-
#******************************************************************************\
# * $Source$
# * $Id$
# *
# * Copyright (C) 2006 - 2011,  Jérôme Kieffer <imagizer@terre-adelie.org>
# * Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
# * Licence GPL v2
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
"""
Module containing most classes for handling images
"""

__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20120530"
__license__ = "GPL"

import os, logging, shutil, time, subprocess
import os.path as op
installdir = op.dirname(__file__)
logger = logging.getLogger("imagizer.photo")

try:
    import Image, ImageStat, ImageChops, ImageFile
except:
    raise ImportError("Selector needs PIL: Python Imaging Library\n PIL is available from http://www.pythonware.com/products/pil/")
try:
    import pygtk ; pygtk.require('2.0')
    import gtk
    import gtk.glade as GTKglade
except ImportError:
    raise ImportError("Selector needs pygtk and glade-2 available from http://www.pygtk.org/")
# Variables globales qui sont des CONSTANTES !
gtkInterpolation = [gtk.gdk.INTERP_NEAREST, gtk.gdk.INTERP_TILES, gtk.gdk.INTERP_BILINEAR, gtk.gdk.INTERP_HYPER]
# gtk.gdk.INTERP_NEAREST    Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
# gtk.gdk.INTERP_TILES    This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
# gtk.gdk.INTERP_BILINEAR    Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
# gtk.gdk.INTERP_HYPER    This is the slowest and highest quality reconstruction function. It is derived from the hyperbolic filters in Wolberg's "Digital Image Warping", and is formally defined as the hyperbolic-filter sampling the ideal hyperbolic-filter interpolated image (the filter is designed to be idempotent for 1:1 pixel mapping).


from config import Config
config = Config()
if config.ImageCache > 1:
    import imagecache
    imageCache = imagecache.ImageCache(maxSize=config.ImageCache)
else:
    imageCache = None

from exif       import Exif
import pyexiftran
from fileutils  import mkdir, makedir, smartSize
from encoding   import unicode2ascii
import blur

##########################################################
# # # # # # Début de la classe photo # # # # # # # # # # #
##########################################################
class Photo(object):
    """class photo that does all the operations available on photos"""
    _gaussian = blur.Gaussian()

    def __init__(self, filename, dontCache=False):
        """
        @param filename: Name of the image file, starting from the repository root
        """
        self.filename = filename
        self.fn = op.join(config.DefaultRepository, self.filename)
        if not op.isfile(self.fn):
            logger.error("No such photo %s" % self.fn)
        self.metadata = None
        self._pixelsX = None
        self._pixelsY = None
        self._pil = None
        self._exif = None
        self.scaledPixbuffer = None
        self.orientation = 1
        if (imageCache is not None) and (filename in imageCache):
            logger.debug("Image %s found in Cache", filename)
            fromCache = imageCache[filename]
            self.metadata = fromCache.metadata
            self._pixelsX = fromCache.pixelsX
            self._pixelsY = fromCache.pixelsY
            self._pil = fromCache.pil
            self._exif = fromCache.exif
            self.scaledPixbuffer = fromCache.scaledPixbuffer
            self.orientation = fromCache.orientation
        else:
            logger.debug("Image %s not in Cache", filename)
            if dontCache is False:
                imageCache[filename] = self
        return None


    def getPIL(self):
        if self._pil is None:
            self._pil = Image.open(self.fn)
        return self._pil
    def setPIL(self, value):self._pil = value
    def delPIL(self):
        del self._pil
        self.pil = None
    pil = property(getPIL, setPIL, delPIL, doc="property: PIL object")

    def loadPIL(self):
        """Deprecated method to load PIL data"""
        import traceback
        logger.warning("Use of loadPIL is deprecated!!!")
        traceback.print_stack()
        self.getPIL()

    def getPixelsX(self):
        if self._pixelsX is None:
            self._pixelsX = self.pil.size[0]
        return self._pixelsX
    def setPixelsX(self, value): self._pixelsX = value
    pixelsX = property(getPixelsX, setPixelsX, doc="Property to get the size in pixels via PIL")

    def getPixelsY(self):
        if self._pixelsY is None:
            self._pixelsY = self.pil.size[1]
        return self._pixelsY
    def setPixelsY(self, value): self._pixelsY = value
    pixelsY = property(getPixelsY, setPixelsY, doc="Property to get the size in pixels via PIL")


    def getExif(self):
        if self._exif is None:
            self._exif = Exif(self.fn)
            self._exif.read()
        return self._exif
    exif = property(getExif, doc="property for exif data")

    def larg(self):
        """width-height of a jpeg file"""
        return self.pixelsX - self.pixelsY


    def taille(self):
        """Deprecated method to taille data"""
        import traceback
        logger.warning("Use of taille is deprecated!!!")
        traceback.print_stack()
        self.getPIL()


    def saveThumb(self, strThumbFile, Size=160, Interpolation=1, Quality=75, Progressive=False, Optimize=False, ExifExtraction=False):
        """save a thumbnail of the given name, with the given size and the interpolation methode (quality)
        resampling filters :
        NONE = 0
        NEAREST = 0
        ANTIALIAS = 1 # 3-lobed lanczos
        LINEAR = BILINEAR = 2
        CUBIC = BICUBIC = 3
        """
        if  op.isfile(strThumbFile):
            logger.warning("Thumbnail %s exists" % strThumbFile)
        else:
            extract = False
            print "process file %s exists" % strThumbFile
            if ExifExtraction:
                try:
                    self.exif.dumpThumbnailToFile(strThumbFile[:-4])
                    extract = True
                except (OSError, IOError):
                    extract = False
                # Check if the thumbnail is correctly oriented
                if op.isfile(strThumbFile):
                    thumbImag = Photo(strThumbFile)
                    if self.larg() * thumbImag.larg() < 0:
                        print("Warning: thumbnail was not with the same orientation as original: %s" % self.filename)
                        os.remove(strThumbFile)
                        extract = False
            if not extract:
                copyOfImage = self.pil.copy()
                copyOfImage.thumbnail((Size, Size), Interpolation)
                copyOfImage.save(strThumbFile, quality=Quality, progressive=Progressive, optimize=Optimize)
            try:
                os.chmod(strThumbFile, config.DefaultFileMode)
            except OSError:
                print("Warning: unable to chmod %s" % strThumbFile)


    def rotate(self, angle=0):
        """does a looseless rotation of the given jpeg file"""
        if os.name == 'nt' and self.pil != None:
            del self.pil
        x = self.pixelsX
        y = self.pixelsY
        logger.debug("Before rotation %i, x=%i, y=%i, scaledX=%i, scaledY=%i" % (angle, x, y, self.scaledPixbuffer.get_width(), self.scaledPixbuffer.get_height()))

        if angle == 90:
            if imageCache is not None:
                pyexiftran.rotate90(self.fn)
                newPixbuffer = self.scaledPixbuffer.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
                logger.debug("rotate 90 of %s" % newPixbuffer)
                self.pixelsX = y
                self.pixelsY = x
                if self.metadata is not None:
                    self.metadata["Resolution"] = "%i x % i" % (y, x)
            else:
                pyexiftran.rotate90(self.fn)
                self.pixelsX = None
                self.pixelsY = None
        elif angle == 270:
            if imageCache is not None:
                pyexiftran.rotate270(self.fn)
                newPixbuffer = self.scaledPixbuffer.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
                logger.debug("rotate 270 of %s" % newPixbuffer)
                self.pixelsX = y
                self.pixelsY = x
                if self.metadata is not None:
                    self.metadata["Resolution"] = "%i x % i" % (y, x)
            else:
                pyexiftran.rotate270(self.fn)
                self.pixelsX = None
                self.pixelsY = None
        elif angle == 180:
            if imageCache is not None:
                pyexiftran.rotate180(self.fn)
                newPixbuffer = self.scaledPixbuffer.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
                logger.debug("rotate 270 of %s" % newPixbuffer)
            else:
                pyexiftran.rotate180(self.fn)
                self.pixelsX = None
                self.pixelsY = None
        else:
            print "Erreur ! il n'est pas possible de faire une rotation de ce type sans perte de donnée."
        if imageCache is not None:
            self.scaledPixbuffer = newPixbuffer
            imageCache[self.filename] = self
        logger.debug("After   rotation %i, x=%i, y=%i, scaledX=%i, scaledY=%i" % (angle, self.pixelsX, self.pixelsY, self.scaledPixbuffer.get_width(), self.scaledPixbuffer.get_height()))


    def removeFromCache(self):
        """remove the curent image from the Cache .... for various reasons"""
        if imageCache is not None:
            if self.filename in imageCache.ordered:
                imageCache.pop(self.filename)


    def trash(self):
        """Send the file to the trash folder"""
        self.removeFromCache()
        Trashdir = op.join(config.DefaultRepository, config.TrashDirectory)
        td = op.dirname(op.join(Trashdir, self.filename))
        if not op.isdir(td):
            makedir(td)
        shutil.move(self.fn, op.join(Trashdir, self.filename))
        logger.debug("sent %s to trash" % self.filename)
        self.removeFromCache()


    def readExif(self):
        """
        return exif data + title from the photo
        """
        clef = {'Exif.Image.Make':'Marque',
 'Exif.Image.Model':'Modele',
 'Exif.Photo.DateTimeOriginal':'Heure',
 'Exif.Photo.ExposureTime':'Vitesse',
 'Exif.Photo.FNumber':'Ouverture',
# 'Exif.Photo.DateTimeOriginal':'Heure2',
 'Exif.Photo.ExposureBiasValue':'Bias',
 'Exif.Photo.Flash':'Flash',
 'Exif.Photo.FocalLength':'Focale',
 'Exif.Photo.ISOSpeedRatings':'Iso' ,
# 'Exif.Image.Orientation':'Orientation'
}

        if self.metadata is None:
            self.metadata = {}
            self.metadata["Taille"] = "%.2f %s" % smartSize(op.getsize(self.fn))
            self.metadata["Titre"] = self.exif.comment
            try:
                self.metadata["Titre"].encode(config.Coding)
            except Exception as error:
                logger.error("%s in comment: %s" % (error, self.metadata["Titre"]))
                try:
                    self.metadata["Titre"] = self.metadata["Titre"].decode("latin1")
                except Exception as error2:
                    logger.error("%s Failed as well in latin1, resetting" % (error2))
                    self.metadata["Titre"] = u""
            try:
                rate = self.exif["Exif.Image.Rating"]
            except KeyError:
                self.metadata["Rate"] = 0
                self.exif["Exif.Image.Rating"] = 0
            else:
                if "value" in dir(rate):  # pyexiv2 v0.2+
                    self.metadata["Rate"] = int(rate.value)
                else:  # pyexiv2 v0.1
                    self.metadata["Rate"] = int(float(rate))

            if self._pixelsX and self._pixelsY:
                self.metadata["Resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            else:
                try:
                    self.pixelsX = self.exif["Exif.Photo.PixelXDimension"]
                    self.pixelsY = self.exif["Exif.Photo.PixelYDimension"]
                except (IndexError, KeyError):
                    pass
                else:
                    if "human_value" in dir(self.pixelsX):
                        self.pixelsX = self.pixelsX.value
                        self.pixelsY = self.pixelsY.value
                self.metadata["Resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            if "Exif.Image.Orientation" in self.exif.exif_keys:
                self.orientation = self.exif["Exif.Image.Orientation"]
                if "human_value" in dir(self.orientation):
                    self.orientation = self.orientation.value
            for key in clef:
                try:
                    value = self.exif.interpretedExifValue(key)
                    if value:
                        self.metadata[clef[key]] = value.decode(config.Coding).strip()
                    else:
                        self.metadata[clef[key]] = u""
                except (IndexError, KeyError):
                    self.metadata[clef[key]] = u""
        return self.metadata.copy()


    def has_title(self):
        """
        return true if the image is entitled
        """
        if self.metadata == None:
            self.readExif()
        if  self.metadata["Titre"]:
            return True
        else:
            return False


    def show(self, Xsize=600, Ysize=600):
        """
        return a pixbuf to shows the image in a Gtk window
        """

        scaled_buf = None
        if Xsize > config.ImageWidth :
            config.ImageWidth = Xsize
        if Ysize > config.ImageHeight:
            config.ImageHeight = Ysize

#        Prepare the big image to be put in cache
        Rbig = min(float(config.ImageWidth) / self.pixelsX, float(config.ImageHeight) / self.pixelsY)
        if Rbig < 1:
            nxBig = int(round(Rbig * self.pixelsX))
            nyBig = int(round(Rbig * self.pixelsY))
        else:
            nxBig = self.pixelsX
            nyBig = self.pixelsY

        R = min(float(Xsize) / self.pixelsX, float(Ysize) / self.pixelsY)
        if R < 1:
            nx = int(round(R * self.pixelsX))
            ny = int(round(R * self.pixelsY))
        else:
            nx = self.pixelsX
            ny = self.pixelsY

#       Put in Cache the "BIG" image
        if self.scaledPixbuffer is None:
            logger.debug("self.scaledPixbuffer is empty")
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.fn)
            if Rbig < 1:
                self.scaledPixbuffer = pixbuf.scale_simple(nxBig, nyBig, gtkInterpolation[config.Interpolation])
            else :
                self.scaledPixbuffer = pixbuf
            logger.debug("To Cached  %s, size (%i,%i)" % (self.filename, nxBig, nyBig))
        if (self.scaledPixbuffer.get_width() == nx) and (self.scaledPixbuffer.get_height() == ny):
            scaled_buf = self.scaledPixbuffer
            logger.debug("In cache No resize %s" % self.filename)
        else:
            logger.debug("In cache To resize %s" % self.filename)
            scaled_buf = self.scaledPixbuffer.scale_simple(nx, ny, gtkInterpolation[config.Interpolation])
        return scaled_buf


    def name(self, titre, rate=None):
        """write the title of the photo inside the description field, in the JPEG header"""
        if os.name == 'nt' and self.pil != None:
            self.pil = None
        self.metadata["Titre"] = titre
        if rate is not None:
            self.metadata["Rate"] = rate
            self.exif["Exif.Image.Rating"] = int(rate)
        self.exif.comment = titre
        try:
            self.exif.write()
        except IOError as error:
            logger.warning("Got IO exception %s: file has probably changed:\n photo.name=%s\n exif.name=%s\n pil.name=%s" %
                           (error, self.filename, self.exif.filename, self.pil.filename))


    def renameFile(self, newname):
        """
        rename the current instance of photo:
        -Move the file
        -update the cache
        -change the name and other attributes of the instance
        -change the exif metadata.
        """
        oldname = self.filename
        newfn = op.join(config.DefaultRepository, newname)
        os.rename(self.fn, newfn)
        self.filename = newname
        self.fn = newfn
        self._exif = None
        if (imageCache is not None) and (oldname in imageCache):
            imageCache.rename(oldname, newname)


    def storeOriginalName(self, originalName):
        """
        Save the original name of the file into the Exif.Photo.UserComment tag.
        This tag is usually not used, people prefer the JPEG tag for entiteling images.

        @param  originalName: name of the file before it was processed by selector
        @type   originalName: python string
        """
        self.exif["Exif.Photo.UserComment"] = originalName
        self.exif.write()


    def autorotate(self):
        """does autorotate the image according to the EXIF tag"""
        if os.name == 'nt' and self.pil is not None:
            del self.pil
        self.readExif()
        if self.orientation != 1:
            pyexiftran.autorotate(self.fn)
            if self.orientation > 4:
                self.pixelsX = self.exif["Exif.Photo.PixelYDimension"]
                self.pixelsY = self.exif["Exif.Photo.PixelXDimension"]
                self.metadata["Resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            self.orientation = 1


    def contrastMask(self, outfile):
        """Ceci est un filtre de debouchage de photographies, aussi appelé masque de contraste,
        il permet de rattrapper une photo trop contrasté, un contre jour, ...
        Écrit par Jérôme Kieffer, avec l'aide de la liste python@aful,
        en particulier A. Fayolles et F. Mantegazza avril 2006
        necessite numpy et PIL.

        @param: the name of the output file (JPEG)
        @return: filtered Photo instance
        """

        try:
            import numpy
#            import scipy.signal as signal
        except:
            logger.error("This filter needs the numpy library available on https://sourceforge.net/projects/numpy/files/")
            return

        t0 = time.time()
        dimX, dimY = self.pil.size

        ImageFile.MAXBLOCK = dimX * dimY
        img_array = numpy.fromstring(self.pil.tostring(), dtype="UInt8").astype("float32")
        img_array.shape = (dimY, dimX, 3)
        red, green, blue = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        # nota: this is faster than desat2=(ar.max(axis=2)+ar.min(axis=2))/2
        desat_array = (numpy.minimum(numpy.minimum(red, green), blue) + numpy.maximum(numpy.maximum(red, green), blue)) / 2.0
        inv_desat = 255. - desat_array
        blured_inv_desat = self._gaussian.blur(inv_desat, config.ContrastMaskGaussianSize)
        bisi = numpy.round(blured_inv_desat).astype("uint8")
        k = Image.fromarray(bisi, "L").convert("RGB")
        S = ImageChops.screen(self.pil, k)
        M = ImageChops.multiply(self.pil, k)
        F = ImageChops.add(ImageChops.multiply(self.pil, S), ImageChops.multiply(ImageChops.invert(self.pil), M))
        exitJpeg = op.join(config.DefaultRepository, outfile)
        F.save(exitJpeg, quality=80, progressive=True, Optimize=True)
        try:
            os.chmod(exitJpeg, config.DefaultFileMode)
        except IOError:
            logger.error("Unable to chmod %s" % outfile)
        exifJpeg = Exif(exitJpeg)
        exifJpeg.read()
        self.exif.copy(exifJpeg)
        exifJpeg.comment = self.exif.comment
#
#        for metadata in [ 'Exif.Image.Make', 'Exif.Image.Model', 'Exif.Photo.DateTimeOriginal',
#                         'Exif.Photo.ExposureTime', 'Exif.Photo.FNumber', 'Exif.Photo.ExposureBiasValue',
#                         'Exif.Photo.Flash', 'Exif.Photo.FocalLength', 'Exif.Photo.ISOSpeedRatings',
#                         "Exif.Image.Orientation", "Exif.Photo.UserComment"
#                         ]:
#            if metadata in self.exif:
#                logger.debug("Copying metadata %s", metadata)
#                try:
#                    exifJpeg[metadata] = self.exif[metadata]
#                except KeyError:
#                    pass #'Tag not set'-> unable to copy it
#                except:
#                    logger.error("Unable to copying metadata %s in file %s, value: %s" % (metadata, self.filename, self.exif[metadata]))
        logger.debug("Write metadata to %s", exitJpeg)
        exifJpeg.write()
        logger.info("The whoole contrast mask took %.3f" % (time.time() - t0))
        return Photo(outfile)

    def autoWB(self, outfile):
        """
        apply Auto White - Balance to the current image

        @param: the name of the output file (JPEG)
        @return: filtered Photo instance

        """
        try:
            import numpy
        except:
            logger.error("This filter needs the numpy library available on http://numpy.scipy.org/")
            return
        t0 = time.time()
        position = 5e-4
        rgb1 = numpy.fromstring(self.pil.tostring(), dtype="uint8")
        rgb1.shape = -1, 3
        rgb = rgb1.astype("float32")
        rgb1.sort(axis=0)
        pos_min = int(round(rgb1.shape[0] * position))
        pos_max = rgb1.shape[0] - pos_min
        rgb_min = rgb1[pos_min]
        rgb_max = rgb1[pos_max]
        rgb[:, 0] = 255.0 * (rgb[:, 0].clip(rgb_min[0], rgb_max[0]) - rgb_min[0]) / (rgb_max[0] - rgb_min[0])
        rgb[:, 1] = 255.0 * (rgb[:, 1].clip(rgb_min[1], rgb_max[1]) - rgb_min[1]) / (rgb_max[1] - rgb_min[1])
        rgb[:, 2] = 255.0 * (rgb[:, 2].clip(rgb_min[2], rgb_max[2]) - rgb_min[2]) / (rgb_max[2] - rgb_min[2])
        out = Image.fromstring("RGB", (self.pixelsX, self.pixelsY), rgb.round().astype("uint8").tostring())
        exitJpeg = op.join(config.DefaultRepository, outfile)
        out.save(exitJpeg, quality=80, progressive=True, Optimize=True)
        try:
            os.chmod(exitJpeg, config.DefaultFileMode)
        except IOError:
            logger.error("Unable to chmod %s" % outfile)
        exifJpeg = Exif(exitJpeg)
        exifJpeg.read()
        self.exif.copy(exifJpeg)
        logger.debug("Write metadata to %s", exitJpeg)
        exifJpeg.write()
        logger.info("The whoole Auto White-Balance took %.3f" % (time.time() - t0))
        return Photo(outfile)


########################################################
# # # # # # fin de la classe photo # # # # # # # # # # #
########################################################

class Signature(object):
    def __init__(self, filename):
        """
        this filter allows add a signature to an image
        """
        self.img = None
        self.sig = Image.open(filename)
        self.sig.convert("RGB")
        (self.xs, self.ys) = self.sig.size
        self.bigsig = self.sig
        # The signature file is entented to be white on a black background, this inverts the color if necessary
        if ImageStat.Stat(self.sig)._getmean() > 127:
            self.sig = ImageChops.invert(self.sig)

        self.orientation = -1  # this is an impossible value
        (self.x, self.y) = (self.xs, self.ys)

    def mask(self, orientation=5):
        """
        x and y are the size of the initial image
        the orientation correspond to the position on a clock :
        0 for the center
        1 or 2 upper right
        3 centered in heith right side ...."""
        if orientation == self.orientation and (self.x, self.y) == self.bigsig.size:
            # no need to change the mask
            return
        self.orientation = orientation
        self.bigsig = Image.new("RGB", (self.x, self.y), (0, 0, 0))
        if self.x < self.xs or self.y < self.ys :
            # the signature is larger than the image
            return
        if self.orientation == 0:
            self.bigsig.paste(self.sig, (self.x / 2 - self.xs / 2, self.y / 2 - self.ys / 2, self.x / 2 - self.xs / 2 + self.xs, self.y / 2 - self.ys / 2 + self.ys))
        elif self.orientation in [1, 2]:
            self.bigsig.paste(self.sig, (self.x - self.xs, 0, self.x, self.ys))
        elif self.orientation == 3:
            self.bigsig.paste(self.sig, (self.x - self.xs, self.y / 2 - self.ys / 2, self.x, self.y / 2 - self.ys / 2 + self.ys))
        elif self.orientation in [ 5, 4]:
            self.bigsig.paste(self.sig, (self.x - self.xs, self.y - self.ys, self.x, self.y))
        elif self.orientation == 6:
            self.bigsig.paste(self.sig, (self.x / 2 - self.xs / 2, self.y - self.ys, self.x / 2 - self.xs / 2 + self.xs, self.y))
        elif self.orientation in [7, 8]:
            self.bigsig.paste(self.sig, (0, self.y - self.ys, self.xs, self.y))
        elif self.orientation == 9:
            self.bigsig.paste(self.sig, (0, self.y / 2 - self.ys / 2, self.xs, self.y / 2 - self.ys / 2 + self.ys))
        elif self.orientation in [10, 11]:
            self.bigsig.paste(self.sig, (0, 0, self.xs, self.ys))
        elif self.orientation == 12:
            self.bigsig.paste(self.sig, (self.x / 2 - self.xs / 2, 0, self.x / 2 - self.xs / 2 + self.xs, self.ys))
        return

    def substract(self, inimage, orientation=5):
        """apply a substraction mask on the image"""
        self.img = inimage
        self.x, self.y = self.img.size
        ImageFile.MAXBLOCK = self.x * self.y
        self.mask(orientation)
        k = ImageChops.difference(self.img, self.bigsig)
        return k


class RawImage:
    """ class for handling raw images
    - extract thumbnails
    - copy them in the repository
    """
    def __init__(self, strRawFile):
        """
        Contructor of the class

        @param strRawFile: path to the RawImage
        @type strRawFile: string
        """
        self.strRawFile = strRawFile
        self.exif = None
        self.strJepgFile = None
        logger.info("Importing [Raw|Jpeg] image %s" % strRawFile)

    def getJpegPath(self):

        if self.exif is None:
            self.exif = Exif(self.strRawFile)
            self.exif.read()
        if self.strJepgFile is None:
            self.strJepgFile = unicode2ascii("%s-%s.jpg" % (
                    self.exif.interpretedExifValue("Exif.Photo.DateTimeOriginal").replace(" ", os.sep).replace(":", "-", 2).replace(":", "h", 1).replace(":", "m", 1),
                    self.exif.interpretedExifValue("Exif.Image.Model").strip().split(",")[-1].replace("/", "").replace(" ", "_")
                    ))
            while op.isfile(op.join(config.DefaultRepository, self.strJepgFile)):
                number = ""
                idx = None
                listChar = list(self.strJepgFile[:-4])
                listChar.reverse()
                for val in listChar:
                    if val.isdigit():
                        number = val + number
                    elif val == "-":
                        idx = int(number)
                        break
                    else:
                        break
                if idx is None:
                    self.strJepgFile = self.strJepgFile[:-4] + "-1.jpg"
                else:
                    self.strJepgFile = self.strJepgFile[:-5 - len(number)] + "-%i.jpg" % (idx + 1)
        dirname = op.dirname(op.join(config.DefaultRepository, self.strJepgFile))
        if not op.isdir(dirname):
            makedir(dirname)

        return self.strJepgFile

    def extractJPEG(self):
        """
        extract the raw image to its right place
        """
        extension = op.splitext(self.strRawFile)[1].lower()
        strJpegFullPath = op.join(config.DefaultRepository, self.getJpegPath())
        if extension in config.RawExtensions:

            process = subprocess.Popen("%s %s" % (config.Dcraw, self.strRawFile), shell=True, stdout=subprocess.PIPE)
            ret = process.wait()
            if ret != 0:
                logger.error("'%s %s' ended with error %s" % (config.Dcraw, self.strRawFile, ret))
            data = process.stdout.readlines()
            img = Image.fromstring("RGB", tuple([int(i) for i in data[1].split()]), "".join(tuple(data[3:])))
            img.save(strJpegFullPath, format='JPEG')
            # Copy all metadata useful for us.
            exifJpeg = Exif(strJpegFullPath)
            exifJpeg.read()
            exifJpeg['Exif.Image.Orientation'] = 1
            exifJpeg["Exif.Photo.UserComment"] = self.strRawFile
            for metadata in [ 'Exif.Image.Make', 'Exif.Image.Model', 'Exif.Photo.DateTimeOriginal', 'Exif.Photo.ExposureTime', 'Exif.Photo.FNumber', 'Exif.Photo.ExposureBiasValue', 'Exif.Photo.Flash', 'Exif.Photo.FocalLength', 'Exif.Photo.ISOSpeedRatings']:
                try:
                    exifJpeg[metadata] = self.exif[metadata]
                except:
                    logger.error("Unable to copying metadata %s in file %s, value: %s" % (metadata, self.strRawFile, self.exif[metadata]))
            # self.exif.copyMetadataTo(self.strJepgFile)

            exifJpeg.write()

        else:  # in config.Extensions, i.e. a JPEG file
            shutil.copy(self.strRawFile, strJpegFullPath)
            pyexiftran.autorotate(strJpegFullPath)

        os.chmod(strJpegFullPath, config.DefaultFileMode)
