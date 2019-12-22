# cython: profile=False
# cython: language_level=3
# -*- coding: utf-8 -*-
#
#    Project: Image downsampler
#             https://github.com/kif/imagizer
#
#    Copyright (C) 2014
#
#    Principal author:
#                        Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Implementation of a separable 2D convolution"""
__authors__ = ["Jerome Kieffer"]
__contact__ = "Jerome.kieffer@terre-adelie.org"
__date__ = "22/12/2019"
__status__ = "stable"
__license__ = "GPLv3+"
import cython
import numpy
cimport numpy
from cython.parallel import prange
from cython cimport view
from libc.math cimport round, fabs, floor
import time

def timeit(func):
    def wrapper(*arg, **kw):
        '''This is the docstring of timeit:
        a decorator that logs the execution time'''
        t1 = time.time()
        res = func(*arg, **kw)
        t2 = time.time()
        if "func_name" in dir(func):
            name = func.func_name
        else:
            name = str(func)
        print("%s took %.3fs" % (name, t2 - t1))
        return res
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def horizontal_convolution(float[:, :] img, float[:] filter):
    """
    Implements a 1D horizontal convolution with a filter.
    The only implemented mode is "reflect" (default in scipy.ndimage.filter)

    @param img: input image
    @param filter: 1D array with the coefficients of the array
    @return: array of the same shape as image with
    """
    cdef:
        int FILTER_SIZE, HALF_FILTER_SIZE
        int IMAGE_H, IMAGE_W
        int x, y, pos, fIndex, newpos, c
        float sum, err, val, tmp
        numpy.ndarray[numpy.float32_t, ndim = 2] output

    FILTER_SIZE = filter.shape[0]
    if FILTER_SIZE % 2 == 1:
        HALF_FILTER_SIZE = (FILTER_SIZE) // 2
    else:
        HALF_FILTER_SIZE = (FILTER_SIZE + 1) // 2

    IMAGE_H = img.shape[0]
    IMAGE_W = img.shape[1]
    output = numpy.zeros((IMAGE_H, IMAGE_W), dtype=numpy.float32)
    for y in prange(IMAGE_H, nogil=True):
        for x in range(IMAGE_W):
            sum = 0.0
            err = 0.0
            for fIndex in range(FILTER_SIZE):
                newpos = x + fIndex - HALF_FILTER_SIZE
                if newpos < 0:
                    newpos = - newpos - 1
                elif newpos >= IMAGE_W:
                    newpos = 2 * IMAGE_W - newpos - 1
                # sum += img[y,newpos] * filter[fIndex]
                # implement Kahan summation
                val = img[y, newpos] * filter[fIndex] - err
                tmp = sum + val
                err = (tmp - sum) - val
                sum = tmp
            output[y, x] += sum
    return output


@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
def vertical_convolution(float[:, :] img, float[:] filter):
    """
    Implements a 1D vertical convolution with a filter.
    The only implemented mode is "reflect" (default in scipy.ndimage.filter)

    @param img: input image
    @param filter: 1D array with the coefficients of the array
    @return: array of the same shape as image with
    """
    cdef:
        int FILTER_SIZE, HALF_FILTER_SIZE
        int IMAGE_H, IMAGE_W
        int x, y, pos, fIndex, newpos, c
        float sum, err, val, tmp
        numpy.ndarray[numpy.float32_t, ndim=2] output

    FILTER_SIZE = filter.shape[0]
    if FILTER_SIZE % 2 == 1:
        HALF_FILTER_SIZE = (FILTER_SIZE) // 2
    else:
        HALF_FILTER_SIZE = (FILTER_SIZE + 1) // 2

    IMAGE_H = img.shape[0]
    IMAGE_W = img.shape[1]
    output = numpy.zeros((IMAGE_H, IMAGE_W), dtype=numpy.float32)
    for y in prange(IMAGE_H, nogil=True):
        for x in range(IMAGE_W):
            sum = 0.0
            err = 0.0
            for fIndex in range(FILTER_SIZE):
                newpos = y + fIndex - HALF_FILTER_SIZE
                if newpos < 0:
                    newpos = - newpos - 1
                elif newpos >= IMAGE_H:
                    newpos = 2 * IMAGE_H - newpos - 1
                # sum += img[y,newpos] * filter[fIndex]
                # implement Kahan summation
                val = img[newpos, x] * filter[fIndex] - err
                tmp = sum + val
                err = (tmp - sum) - val
                sum = tmp
            output[y, x] += sum
    return output


def gaussian(sigma, width=None, half=True):
    """
    Return a Gaussian window of length "width" with standard-deviation "sigma".

    @param sigma: standard deviation sigma
    @param width: length of the windows (int) By default 6*sigma+1,

    Width should be odd for half==False.

    The FWHM is 2*sqrt(2 * pi)*sigma

    """
    if width is None:
        if half:
            width = int(3 * sigma)
        else:
            width = int(6 * sigma + 1)
            if width % 2 == 0:
                width += 1
    sigma = float(sigma)
    if half:
        x = numpy.linspace(0, 3 * sigma, width)
    else:
        x = numpy.linspace(-3 * sigma, 3 * sigma, width)
    g = numpy.exp(-(x / sigma) ** 2 / 2.0)
    return g


def lanczos(order=3, width=32, half=True):
    """
    Returns the lanczos function
    """
    if half:
        x = numpy.linspace(0, order, width)
    else:
        x = numpy.linspace(-order, order, width)
    l = numpy.sinc(x)*numpy.sinc(x/order)
    return l


def gaussian_filter(img, sigma):
    """
    Performs a gaussian bluring using a gaussian kernel.

    @param img: input image
    @param sigma:
    """
    raw = numpy.ascontiguousarray(img, dtype=numpy.float32)
    gauss = gaussian(sigma).astype(numpy.float32)
    res = vertical_convolution(horizontal_convolution(raw, gauss), gauss)
    return res

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef inline void _point_horizontal(int x, int y, numpy.uint8_t[:,:,:] img, numpy.uint8_t[:,:,:] output, float factor, float order, float[:] data) nogil:
    cdef:
        float[4] sum
        int c = 0
        float norm = 0.0
        int fIndex = 0
        int newpos = 0
        int pos_coef = 0
        float coef = 0.0
        int HALF_FILTER_SIZE = <int> round(factor * order)
        int IMAGE_H = img.shape[0]
        int IMAGE_W = img.shape[1]
        int COLORS = img.shape[2]
        int OUTPUT_H = output.shape[0]
        int OUTPUT_W = output.shape[1]
        int SIZE = data.shape[0]

    for c in range(COLORS):
        sum[c] = 0.0

    for fIndex in range(-HALF_FILTER_SIZE + 1, HALF_FILTER_SIZE):
        newpos = <int> round(factor * x + fIndex)

        pos_coef = <int> round(fabs(fIndex) / factor / order * SIZE)
        if pos_coef>=SIZE:
            continue
        else:
            coef = data[pos_coef]

        #mirror
        if newpos < 0:
            newpos = - newpos - 1
        elif newpos >= IMAGE_W:
            newpos = 2 * IMAGE_W - newpos - 1

        norm += coef
        for c in range(COLORS):
            sum[c] += img[y,newpos,c] * coef

    for c in range(COLORS):
        coef = round(sum[c]/norm)
        if coef >= 255.0:
            output[y, x, c] = 255
        else:
            output[y, x, c] = <numpy.uint8_t> coef

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
cdef inline void _point_vertical(int x, int y, numpy.uint8_t[:,:,:] img, numpy.uint8_t[:,:,:] output, float factor, float order, float[:] data) nogil:
    cdef:
        float[4] sum
        int c = 0
        float norm = 0.0
        int fIndex = 0
        int newpos = 0
        int pos_coef = 0
        float coef = 0.0
        int HALF_FILTER_SIZE = <int> round(factor * order)
        int IMAGE_H = img.shape[0]
        int IMAGE_W = img.shape[1]
        int COLORS = img.shape[2]
        int OUTPUT_H = output.shape[0]
        int OUTPUT_W = output.shape[1]
        int SIZE = data.shape[0]

    for c in range(COLORS):
        sum[c] = 0.0

    for fIndex in range(-HALF_FILTER_SIZE + 1,HALF_FILTER_SIZE):
        newpos = <int> round(factor * y + fIndex)

        pos_coef = <int> round(fabs(fIndex) / factor / order * SIZE)
        if pos_coef >= SIZE:
            continue
        else:
            coef = data[pos_coef]

        if newpos < 0:
            continue
            #newpos = - newpos - 1
        elif newpos >= IMAGE_H:
            continue
            #newpos = 2 * IMAGE_H - newpos - 1

        norm += coef
        for c in range(COLORS):
            sum[c] = sum[c] + img[newpos, x, c] * coef

    for c in range(COLORS):
        coef = round(sum[c]/norm)
        if coef >= 255.0:
            output[y, x, c] = 255
        else:
            output[y, x, c] = <numpy.uint8_t> coef


class DownScaler(object):
    """
    Anti-aliased down-sampler
    """
    def __init__(self, func="lanczos", order=3, size=32 ):
        self.order = order
        self.size = size
        self.func = func
        if func == "lanczos":
            self.data = lanczos(order, size, half=True).astype("float32")
        else:
            self.data = gaussian(order/3.0, size, half=True).astype("float32")

    @timeit
    def scale(self, raw not None, float factor=3):
        """
        Scale should be greater than 1 for downscaling
        """
        if raw.ndim==3:
            colors = raw.shape[2]
            in_shape = raw.shape[:2]
        else:
            in_shape = raw.shape
            colors = 1
            raw = raw.reshape(in_shape[0], in_shape[1], 1)
        out_shape = tuple([int(floor(i//factor)) for i in in_shape])
        tmp = numpy.zeros(shape=(in_shape[0],out_shape[1],colors), dtype=numpy.uint8)
        out = numpy.zeros(shape=(out_shape[0],out_shape[1],colors), dtype=numpy.uint8)
        self._horizontal_scale(raw,  tmp, factor)
        self._vertical_scale(tmp,  out, factor)
        if colors==1:
            return out.reshape(out_shape[0], out_shape[1])
        else:
            return out

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    def _horizontal_scale(self, numpy.uint8_t[:,:,:] img, numpy.uint8_t[:,:,:] output, float factor):
        """
        scale an image dim0, dim1 -> dim0, dim1/factor
        note dim2 is the color channel
        """
        cdef:
            int x, y
            float ORDER = float(self.order)
            float[:] data=self.data
            int IMAGE_H = img.shape[0]
            int OUTPUT_W = output.shape[1]
        for y in prange(IMAGE_H, nogil=True):
            for x in range(OUTPUT_W):
                _point_horizontal(x, y, img, output, factor, ORDER, data)
#                for c in range(COLORS):
#                    sum[c] = 0.0
#                norm = 0.0
#                for fIndex in range(-HALF_FILTER_SIZE + 1, HALF_FILTER_SIZE):
#                    newpos = <int> round(factor * x + fIndex)
#
#                    pos_coef = <int> round(fabs(fIndex) / factor / ORDER * SIZE)
#                    if pos_coef>=SIZE:
##                        with gil:
##                            print("Warning H: idx=%s, hfs=%s, w=%s, order=%s"%(fIndex,HALF_FILTER_SIZE,SIZE,ORDER))
#                        coef = 0
#                    else:
#                        coef = data[pos_coef]
#
#                    if newpos < 0:
#                        newpos = - newpos - 1
#                    elif newpos >= IMAGE_W:
#                        newpos = 2 * IMAGE_W - newpos - 1
#
#                    norm = norm + coef
#                    for c in range(COLORS):
#                        sum[c] = sum[c] + img[y,newpos,c] * coef
#                for c in range(COLORS):
#                    coef = round(sum[c]/norm)
#                    if coef>255.0:
##                        with gil:
##                            print("Warning V: sum=%s, norm=%s"%(coef,norm))
#                        coef=255.0
#                    output[y, x, c] += <numpy.uint8_t> coef
        return output

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.cdivision(True)
    def _vertical_scale(self, numpy.uint8_t[:,:,:] img, numpy.uint8_t[:,:,:] output, float factor):
        """
        scale an image dim0, dim1 -> dim0/factor
        note dim2 is the color channel
        """
        cdef:
            int x, y
            float ORDER = float(self.order)
            float[:] data=self.data
            int IMAGE_H = img.shape[0]
            int IMAGE_W = img.shape[1]
            int OUTPUT_H = output.shape[0]
        for y in prange(OUTPUT_H, nogil=True):
            for x in range(IMAGE_W):
                _point_vertical(x, y, img, output, factor, ORDER, data)
#                for c in range(COLORS):
#                    sum[c] = 0.0
#                norm = 0.0
#                for fIndex in range(-HALF_FILTER_SIZE + 1,HALF_FILTER_SIZE):
#                    newpos = <int> round(factor * y + fIndex)
#
#                    pos_coef = <int> round(fabs(fIndex) / factor / ORDER * SIZE)
#                    if pos_coef>=SIZE:
##                        with gil:
##                            print("Warning V: idx=%s, hfs=%s, w=%s, order=%s"%(fIndex,HALF_FILTER_SIZE,SIZE,ORDER))
#                        coef = 0
#                    else:
#                        coef = data[pos_coef]
#
#                    if newpos < 0:
#                        newpos = - newpos - 1
#                    elif newpos >= IMAGE_H:
#                        newpos = 2 * IMAGE_H - newpos - 1
#
#                    norm = norm + coef
#                    for c in range(COLORS):
#                        sum[c] = sum[c] + img[newpos, x, c] * coef
#                for c in range(COLORS):
#                    coef = round(sum[c]/norm)
#                    if coef>255.0:
##                        with gil:
##                            print("Warning V: sum=%s, norm=%s"%(coef,norm))
#                        coef=255.0
#                    output[y, x, c] += <numpy.uint8_t> coef
        return output





