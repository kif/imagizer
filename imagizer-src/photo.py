# !/usr/bin/env python
# coding: utf-8
# ******************************************************************************\
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
# *****************************************************************************/
"""
Module containing most classes for handling images
"""

from __future__ import print_function, absolute_import, division


__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "19/08/2022"
__license__ = "GPL"

from math import ceil
import os
import logging
import shutil
import time
import subprocess
import shutil
import os.path as op
import tempfile
from io import BytesIO
installdir = op.dirname(__file__)
logger = logging.getLogger("imagizer.photo")

try:
    from PIL import Image, ImageStat, ImageChops, ImageFile
except ImportError:
    try:
        import Image, ImageStat, ImageChops, ImageFile
    except ImportError:
        logger.error("""Selector needs PIL: Python Imaging Library or pillow""")
        raise error

Image.MAX_IMAGE_PIXELS = None
from .config import config
from .imagecache import image_cache, title_cache
kpix = 3 * config.ScaledImages["Size"] ** 2 / 4000
if kpix > 64:
    ImageFile.MAXBLOCK = 2 ** 26  # Thats 66 Mpix

from .exif       import Exif
from .           import pyexiftran
from .fileutils  import mkdir, makedir, smartSize
from .encoding   import unicode2ascii
from .           import blur


# #########################################################
# # # # # # Début de la classe photo # # # # # # # # # # #
# #########################################################
class Photo(object):
    """class photo that does all the operations available on photos"""
    _gaussian = blur.Gaussian()

    EXIF_KEYS = {'Exif.Image.Make':'make',
                 'Exif.Image.Model':'model',
                 'Exif.Photo.DateTimeOriginal':'time',
                 'Exif.Photo.ExposureTime':'speed',
                 'Exif.Photo.FNumber':'aperture',
                 'Exif.Photo.ExposureBiasValue':'bias',
                 'Exif.Photo.Flash':'flash',
                 'Exif.Photo.FocalLength':'focal',
                 'Exif.Photo.ISOSpeedRatings':'iso'
                }


    def __init__(self, filename, dontCache=False):
        """
        @param filename: Name of the image file, starting from the repository root
        """
        self.ext = os.path.splitext(filename)[-1].lower()
        self.is_raw = self.ext in config.RawExtensions
        if filename.startswith(config.DefaultRepository):
            self.fn = filename
            if config.DefaultRepository.endswith("/"):
                self.filename = filename[len(config.DefaultRepository):]
            else:
                self.filename = filename[len(config.DefaultRepository) + 1:]
        else:
            self.filename = filename
            self.fn = op.join(config.DefaultRepository, self.filename)
        if not op.isfile(self.fn):
            logger.error("No such photo %s" % self.fn)
        if title_cache and self.filename in title_cache:
            self.metadata = {"title": title_cache[self.filename]}
        else:
            self.metadata = {}
        self._pixelsX = None
        self._pixelsY = None
        self._pil = None
        self._exif = None
#         self._pixbuf = None
        self.scaledPixbuffer = None
        self._orientation = 0

        if image_cache:
            if filename in image_cache:
                logger.debug("Image %s found in Cache", filename)
                fromCache = image_cache[filename]
                self.metadata = fromCache.metadata
                self._pixelsX = fromCache.pixelsX
                self._pixelsY = fromCache.pixelsY
                self._pil = fromCache.pil
                self._exif = fromCache.exif
                self.scaledPixbuffer = fromCache.scaledPixbuffer
                self._orientation = fromCache.orientation
            elif not dontCache:
                logger.debug("Image %s not in Cache", filename)
                image_cache[filename] = self

    def __repr__(self):
        return "Photo object on filename %s" % self.filename

    @property
    def pil(self):
        if self._pil is None:
            if not self.is_raw:
                self._pil = Image.open(self.fn)
            else:
                largest =self.exif.get_largest_preview()
                try:
                    data = largest.get_data()
                except:
                    logger.warning("No preview data for %s", self.filename)
                else:
                    self._pil = Image.open(BytesIO(data), mode="r")
        return self._pil

    @pil.setter
    def pil(self, value):
        self._pil = value

    @pil.deleter
    def pil(self):
        del self._pil
        self.pil = None

    @property
    def pixelsX(self):
        if not self._pixelsX:
            try:
                # Enforce the reading of the metadata
                exif = self.exif
            except Exception as err:
                logger.error("Exception %s in PixelsX: %s", type(err), err)
                self._pixelsX = max(1, self.pil.size[0])

        return self._pixelsX

    @pixelsX.setter
    def pixelsX(self, value):
        self._pixelsX = value

    @property
    def pixelsY(self):
        if not self._pixelsY:
            try:
                # Enforce the reading of the metadata
                exif = self.exif
            except:
                self._pixelsY = max(1, self.pil.size[1])
        return self._pixelsY

    @pixelsY.setter
    def pixelsY(self, value):
        self._pixelsY = value

    @property
    def exif(self):
        if self._exif is None:
            try:
                self._exif = Exif(self.fn)
            except Exception as e:
                print(f"Unable to parse metadata for {self.fn}")
                self._exif = None
                self._pixelsY = max(1, self.pil.size[1])
                self._pixelsX = max(1, self.pil.size[0])
                raise e
            else:
                self._pixelsX, self._pixelsY = self._exif.dimensions
                if self.is_raw and self.get_orientation(True) > 4:
                    self._pixelsX, self._pixelsY = self._pixelsY, self._pixelsX
        return self._exif

    # No property as get_orientation may be used as a function wich check=True to avoid caching the actual value
    def get_orientation(self, check=False):
        if not self._orientation or check:
            try:
                orientation = self.exif.orientation
            except Exception as err:
                logger.warning("No orientation in %s: %s", self.filename, err)
                orientation = 1
            if check:
                return orientation
            self._orientation = orientation
        return self._orientation

    def set_orientation(self, value):
        self._orientation = value

    orientation = property(get_orientation, set_orientation)


    def larg(self):
        """width-height of a jpeg file"""
        return self.pixelsX - self.pixelsY


    def taille(self):
        """Deprecated method to taille data"""
        import traceback
        logger.warning("Use of taille is deprecated!!!")
        traceback.print_stack()
        self.getPIL()

    def as_jpeg(self, dest):
        """
        Save the photo as JPEG file in the given destination.

        :parm dest: destination file
        :return: image Photo instance
        """
        dirname = os.path.dirname(dest)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        if not self.is_raw:
            shutil.copy(self.fn, dest)
            rescaled = self.__class__(dest, dontCache=True)
        else:
            metadata = self.read_exif()
            prev = self.exif.get_largest_preview()
            ext = prev.extension
            if ext.lower() == ".jpg":
                if dest.endswith(".jpg"):
                    prev.write_to_file(dest[:-4])
                else:
                    prev.write_to_file(dest)
            else:
                pil = Image.open(BytesIO(prev.data), mode="r")
                pil.save(dest)
            rescaled = self.__class__(dest, dontCache=True)
            rescaled_exif = rescaled.exif
            rescaled._exif = None
            self.exif.copy(rescaled_exif)
            # print(rescaled_exif.get_exposure_data())
            rescaled_exif.write()
            rescaled.orientation = self.orientation
            rescaled.autorotate(check=False)
            title, rate = metadata.get("title", ""), metadata.get("rate", 0)
            rescaled._exif = None
            rescaled.set_title(title, rate, reset_orientation=True)
            return rescaled


    def saveThumb(self, strThumbFile, Size=160, Interpolation=1, Quality=75, Progressive=False,
                  Optimize=False, ExifExtraction=False):
        """save a thumbnail of the given name, with the given size and the interpolation methode (quality)
        resampling filters :
        NONE = 0
        NEAREST = 0
        ANTIALIAS = 1 # 3-lobed lanczos
        LINEAR = BILINEAR = 2
        CUBIC = BICUBIC = 3
        Optimized/parallel 3-lobed lanczos = 4

        @return: rescaled image Photo instance
        """
        rescaled = None
        if  op.isfile(strThumbFile):
            logger.warning("Thumbnail %s exists" % strThumbFile)
        else:
            extract = False
            logger.info("Rescale image to %s" % strThumbFile)
            if ExifExtraction:
                try:
                    self.exif.dumpThumbnailToFile(strThumbFile[:-4])
                    extract = True
                except (OSError, IOError, RuntimeError):
                    extract = False

                if extract and op.isfile(strThumbFile):
                    thumbImag = Photo(strThumbFile, dontCache=True)
                    if self.larg() * thumbImag.larg() < 0:  # Check if the thumbnail is correctly oriented
                        logger.warning("Thumbnail was not with the same orientation as original: %s" % self.filename)
                        os.remove(strThumbFile)
                        extract = False
                    else:
                        # crop thumbnail to remove black borders
                        orig_ratio = float(self.pixelsY) / self.pixelsX
                        box = None
                        if self.larg() > 0:  # image in lanscape, maybe crop horizontal bands
                            new_height = thumbImag.pixelsX * orig_ratio
                            if abs(new_height - thumbImag.pixelsY) > 2:  # Not the good format
                                offset = int(ceil((thumbImag.pixelsY - new_height) / 2.0))
                                box = (0, offset,
                                       thumbImag.pixelsX, thumbImag.pixelsY - offset)
                        else:  # image in portrait, maybe crop verical bands
                            new_width = thumbImag.pixelsY / orig_ratio
                            if abs(new_width - thumbImag.pixelsX) > 2:  # Not the good format
                                offset = int(ceil((thumbImag.pixelsX - new_width) / 2.0))
                                box = (offset, 0,
                                       thumbImag.pixelsX - offset, thumbImag.pixelsY)
                        if box is not None:
                            thumbImag.pil.crop(box).save(strThumbFile)

            if not extract:
                if Interpolation < 4:
                    copyOfImage = self.pil.copy()
                    copyOfImage.thumbnail((Size, Size), Interpolation)
                else:
                    ary = numpy.asarray(self.pil).copy()
                    scale = min([float(i) / Size for i in ary.shape[:2]])
                    out = self.DS.scale(ary, scale)
                    copyOfImage = Image.fromarray(out)
                copyOfImage.save(strThumbFile, quality=Quality, progressive=Progressive, optimize=Optimize)
                rescaled = self.__class__(strThumbFile, dontCache=True)
                rescaled.pil = copyOfImage
            try:
                os.chmod(strThumbFile, config.DefaultFileMode)
            except OSError:
                logger.warning("Unable to chmod %s" % strThumbFile)
        return rescaled

    def rotate(self, angle=0):
        """does a lossless rotation of the given jpeg file"""
        from . import qt
        if os.name == 'nt' and self.pil != None:
            del self.pil
        x = self.pixelsX
        y = self.pixelsY
        logger.debug("Before rotation %i, x=%i, y=%i, scaledX=%i, scaledY=%i" % (angle, x, y, self.scaledPixbuffer.width(), self.scaledPixbuffer.height()))

        if angle == 90:
            if image_cache is not None:
                pyexiftran.rotate90(self.fn, config.Coding)
                trans = qt.QTransform().rotate(90)
                newPixbuffer = self.scaledPixbuffer.transformed(trans, mode=qt.transformations[config.Interpolation])
                logger.debug("rotate 90 of %s" % newPixbuffer)
                self.pixelsX = y
                self.pixelsY = x
                if self.metadata.get("resolution") is not None:
                    self.metadata["resolution"] = "%i x % i" % (y, x)
            else:
                pyexiftran.rotate90(self.fn, config.Coding)
                self.pixelsX = None
                self.pixelsY = None
        elif angle == 270:
            if image_cache is not None:
                pyexiftran.rotate270(self.fn, config.Coding)
                trans = qt.QTransform().rotate(270)
                newPixbuffer = self.scaledPixbuffer.transformed(trans, mode=qt.transformations[config.Interpolation])
                logger.debug("rotate 270 of %s" % newPixbuffer)
                self.pixelsX = y
                self.pixelsY = x
                if self.metadata is not None:
                    self.metadata["resolution"] = "%i x % i" % (y, x)
            else:
                pyexiftran.rotate270(self.fn, config.Coding)
                self.pixelsX = None
                self.pixelsY = None
        elif angle == 180:
            if image_cache is not None:
                pyexiftran.rotate180(self.fn, config.Coding)
                trans = qt.QTransform().rotate(180)
                newPixbuffer = self.scaledPixbuffer.transformed(trans, mode=qt.transformations[config.Interpolation])
                logger.debug("rotate 270 of %s" % newPixbuffer)
            else:
                pyexiftran.rotate180(self.fn, config.Coding)
                self.pixelsX = None
                self.pixelsY = None
        else:
            logger.error("Il n'est pas possible de faire une rotation de ce type sans perte de donnée.")
        if image_cache is not None:
            self.scaledPixbuffer = newPixbuffer
            image_cache[self.filename] = self
        logger.debug("After   rotation %i, x=%i, y=%i, scaledX=%i, scaledY=%i" %
                     (angle, self.pixelsX, self.pixelsY,
                      self.scaledPixbuffer.width(), self.scaledPixbuffer.height()))

    def removeFromCache(self):
        """remove the curent image from the Cache .... for various reasons"""
        if image_cache is not None and self.filename in image_cache.ordered:
            image_cache.pop(self.filename)
        if title_cache is not None and self.filename in title_cache:
            title_cache.pop(self.filename)

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


    def read_exif(self):
        """
        @return: metadata dict (exif data + title from the photo)
        """
        exif = self.exif
        if self.metadata.get("size") is None:
            self.metadata["size"] = "%.2f %s" % smartSize(op.getsize(self.fn))
            title = exif.comment or u""
            title = title.strip()
            self.metadata["title"] = title
            if title_cache:
                title_cache[self.filename] = title

            rate = exif["Exif.Image.Rating"].value if "Exif.Image.Rating" in exif else 0
            self.metadata["rate"] = rate

            self.metadata["resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            for key, name in self.EXIF_KEYS.items():
                try:
                    value = self.exif[key].human_value or u""
                except (IndexError, KeyError):
                    value = u""
                finally:
                    self.metadata[name] = value.strip()
        return self.metadata.copy()

    def load_pixbuf(self):
        """
        Load the image using QPixmap, either directly or from preview for RAW.

        @return: QPixmap
        """
        from . import qt
        if self.is_raw:
            if self.metadata.get("size") is None:
                self.read_exif()
            largest = self._exif.get_largest_preview()
            dimentions = largest.dimensions
            pixbuf = qt.QPixmap(*dimentions)

            if not pixbuf.loadFromData(largest.data):
                logger.warning("Unable to load raw preview (size: %s): %s" %
                                (dimentions, self.fn))
            orientation = self.get_orientation(True)
            if orientation != 1:
                matrix = qt.get_matrix(orientation)
                pixbuf = pixbuf.transformed(matrix, mode=qt.Qt.FastTransformation)
                self.orientation = 1
        else:
            pixbuf = qt.QPixmap(self.fn)
        return pixbuf


    def get_pixbuf(self, Xsize=600, Ysize=600, Xcenter=None, Ycenter=None):
        """
        Generate a pixbuffer from size and center

        @param Xsize: Width of the image buffer
        @param Ysize: Height of the image buffer
        @param Xcenter: fraction of image to center on in x
        @param Ycenter: fraction of image to center on in Y
        @return: a pixbuf to shows the image in a window
        """
        from . import qt

        scaled_buf = None
        if Xsize > config.ImageWidth :
            config.ImageWidth = Xsize
        if Ysize > config.ImageHeight:
            config.ImageHeight = Ysize

#        Prepare the big image to be put in cache
        Rbig = min(float(config.ImageWidth) / self.pixelsX,
                   float(config.ImageHeight) / self.pixelsY)
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
            pixbuf = self.load_pixbuf()
            logger.debug("self.scaledPixbuffer is empty")

            if Rbig < 1:

                self.scaledPixbuffer = pixbuf.scaled(nxBig, nyBig, aspectRatioMode=qt.Qt.KeepAspectRatio,
                                                     transformMode=qt.transformations[config.Interpolation])
            else :
                self.scaledPixbuffer = pixbuf
            logger.debug("To Cached  %s, size (%i,%i)" % (self.filename, nxBig, nyBig))
        if Xcenter and Ycenter:
            logger.debug("zooming to ")
            Xcenter *= self.pixelsX
            Ycenter *= self.pixelsY
            xmin = int(Xcenter - Xsize / 2.0)
            ymin = int(Ycenter - Ysize / 2.0)
            width = min(Xsize, self.pixelsX)
            height = min(Ysize, self.pixelsY)
            ymax = int(Ycenter + Ysize / 2.0)
            if xmin < 0:
                xmin = 0
            if ymin < 0:
                ymin = 0
            if xmin + Xsize > self.pixelsX:
                xmin = max(0, self.pixelsX - Xsize)
            if ymin + Ysize > self.pixelsY:
                ymin = max(0, self.pixelsY - Ysize)
            pixbuf = self.load_pixbuf()
            return pixbuf.copy(xmin, ymin, width, height)
        elif (self.scaledPixbuffer.width() == nx) and \
             (self.scaledPixbuffer.height() == ny):
            scaled_buf = self.scaledPixbuffer
            logger.debug("In cache No resize %s" % self.filename)
        else:
            logger.debug("In cache To resize %s" % self.filename)
            scaled_buf = self.scaledPixbuffer.scaled(nx, ny, qt.Qt.KeepAspectRatio,
                                                     qt.transformations[config.Interpolation])
        return scaled_buf

    def is_entitled(self):
        """return: true if the image is entitled
        """
        return bool(self.get_title())

    def get_title(self):
        "retrieve the name set inside the file using either the database, either by reading the file"
        if self._exif is None:
            name = self.metadata.get("title")
            if name is None:
                name = self.read_exif().get("title")
        else:
            name = self.metadata.get("title")
        return name

    def set_title(self, title=None, rate=None, reset_orientation=False):
        """
        write the title of the photo inside the description field, in the JPEG header

        @param title: entitled name of the image (string)
        @param  rate: rating of the image (int between 0 and 5)
        """
        if (title is None) and (rate is None):
            return
        if (os.name == 'nt') and (self.pil is not None):
            self.pil = None
        if self.exif.filename != self.filename:
            self._exif = None

        if rate is not None:
            if self.metadata is not None:
                self.metadata["rate"] = rate
            self.exif["Exif.Image.Rating"] = int(rate)

        if title is not None:
            if self.metadata is not None:
                self.metadata["title"] = title
#             if self.is_raw:
#                 self.exif["Exif.Photo.UserComment"] = title
#             else:
            self.exif.comment = title
        if reset_orientation:
            self.exif['Exif.Image.Orientation'] = 1
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
        if (image_cache is not None) and (oldname in image_cache):
            image_cache.rename(oldname, newname)


    def store_original_name(self, originalName):
        """
        Save the original name of the file into the Exif.Image.DocumentName tag.
        This tag is usually not used, people prefer the JPEG tag for entitling images.

        @param  originalName: name of the file before it was processed by selector
        @type   originalName: python string
        """
        self.exif["Exif.Image.DocumentName"] = originalName
        self.exif.write(preserve_timestamps=True)

    def retrieve_original_name(self):
        """Retrives the original name of the file into the Exif.Photo.DocumentName tag.

        @return: name of the file before it was processed by selector
        """
        exif = self.exif
        try:
            original_name = exif["Exif.Image.DocumentName"].human_value
        except (KeyError, IndexError) as err:
            original_name = None
            logger.error("in retrieve_original_name: reading Exif for %s. %s", self.fn, err)
        return original_name

    def autorotate(self, check=True):
        """does autorotate the image according to the EXIF tag.
        Works only for JPEG images
        :param check: set to False to use the strored 
        """
        if self.is_raw:
            return
        if os.name == 'nt' and self.pil is not None:
            del self.pil
        orientation = self.get_orientation(check)
        if orientation != 1:
            pyexiftran.autorotate(self.fn, config.Coding)
            if orientation > 4:
                self.pixelsX, self.pixelsY = self.pixelsY, self.pixelsX
                if self.metadata is not None:
                    self.metadata["resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
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
        img_array = numpy.frombuffer(self.pil.tobytes(), dtype="uint8").astype("float32")
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
        dst_filename = op.join(config.DefaultRepository, outfile)
        F.save(dst_filename, quality=80, progressive=True, Optimize=True)
        try:
            os.chmod(dst_filename, config.DefaultFileMode)
        except IOError:
            logger.error("Unable to chmod %s" % outfile)
        exifJpeg = Exif(dst_filename)
        exifJpeg.read()
        self.exif.copy(exifJpeg)
        # TODO: use settitle !
        exifJpeg.comment = self.exif.comment
        logger.debug("Write metadata to %s", dst_filename)
        exifJpeg.write()
        logger.info("The whoole contrast mask took %.3f" % (time.time() - t0))
        res = Photo(outfile)
        res.autorotate()
        return res


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
        # rgb1 = numpy.fromstring(self.pil.tostring(), dtype="uint8")
        rgb1 = numpy.array(self.pil).copy()
        inshape = rgb1.shape
        rgb1.shape = (-1, 3)
        rgb = rgb1.astype("float32")
        rgb1.sort(axis=0)
        pos_min = int(round(rgb1.shape[0] * position))
        pos_max = rgb1.shape[0] - pos_min
        rgb_min = rgb1[pos_min]
        rgb_max = rgb1[pos_max]
        rgb[:, 0] = 255.0 * (rgb[:, 0].clip(rgb_min[0], rgb_max[0]) - rgb_min[0]) / (rgb_max[0] - rgb_min[0])
        rgb[:, 1] = 255.0 * (rgb[:, 1].clip(rgb_min[1], rgb_max[1]) - rgb_min[1]) / (rgb_max[1] - rgb_min[1])
        rgb[:, 2] = 255.0 * (rgb[:, 2].clip(rgb_min[2], rgb_max[2]) - rgb_min[2]) / (rgb_max[2] - rgb_min[2])
        rgb.shape = inshape
        out = Image.fromarray(rgb.round().clip(0, 255).astype("uint8"), mode="RGB")
        dst_filename = op.join(config.DefaultRepository, outfile)
        out.save(dst_filename, quality=80, progressive=True, Optimize=True)
        try:
            os.chmod(dst_filename, config.DefaultFileMode)
        except IOError:
            logger.error("Unable to chmod %s" % outfile)
        exifJpeg = Exif(dst_filename)
        exifJpeg.read()
        self.exif.copy(exifJpeg)
        logger.debug("Write metadata to %s", dst_filename)
        exifJpeg.write(preserve_timestamps=True)
        logger.info("The whoole Auto White-Balance took %.3f" % (time.time() - t0))
        res = Photo(outfile)
        res.autorotate()
        return res


# #######################################################
# # # # # # fin de la classe photo # # # # # # # # # # #
# #######################################################

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
                    self.exif["Exif.Photo.DateTimeOriginal"].replace(" ", os.sep).replace(":", "-", 2).replace(":", "h", 1).replace(":", "m", 1),
                    self.exif["Exif.Image.Model"].strip().split(",")[-1].replace("/", "").replace(" ", "_")
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

            exifJpeg.write()

        else:  # in config.Extensions, i.e. a JPEG file
            shutil.copy(self.strRawFile, strJpegFullPath)
            pyexiftran.autorotate(strJpegFullPath, config.Coding)

        os.chmod(strJpegFullPath, config.DefaultFileMode)
