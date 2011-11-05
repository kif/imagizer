#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2011,  Jérôme Kieffer <imagizer@terre-adelie.org>
#* Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
#* Licence GPL v2
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
"""
Module contains a class for gaussian blur
"""

__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20111023"
__license__ = "GPL"

import numpy, logging, sys, threading
logger = logging.getLogger("imagizer.blur")
from numpy import ceil, floor

if sys.platform != "win32":
    WindowsError = RuntimeError

try:
    import fftw3
except (ImportError, WindowsError) as e:
    logger.warning("Exception %s: FFTw3 not available. Falling back on Numpy" % e)
    fftw3 = None

try:
    import scipy.signal as scipy_signal
except (ImportError, WindowsError) as e:
    scipy_signal = None


def gaussian(M, std):
    """
    Return a Gaussian window of length M with standard-deviation std.
      
    @param M: size of the function 
    @param std: sigma value
    """
    if scipy_signal is not None:
        return scipy_signal.gaussian(M, std)
    else:
        return numpy.exp(-(((numpy.arange(M, dtype="float32") - (M / 2.0)) / std) ** 2) / 2.0)



def expand(data, sigma, mode="constant", cval=0.0):
    """Expand array a with its reflection on boundaries
    
    @param a: 2D array
    @param sigma: float or 2-tuple of floats
    @param mode:"constant","nearest" or "reflect"
    @param cval: filling value used for constant, 0.0 by default
    """
    s0, s1 = data.shape
    dtype = data.dtype
    if isinstance(sigma, (list, tuple)):
        k0 = int(ceil(float(sigma[0])))
        k1 = int(ceil(float(sigma[1])))
    else:
        k0 = k1 = int(ceil(float(sigma)))
    if k0 > s0 or k1 > s1:
        raise RuntimeError("Makes little sense to apply a kernel (%i,%i)larger than the image (%i,%i)" % (k0, k1, s0, s1))
    output = numpy.zeros((s0 + 2 * k0, s1 + 2 * k1), dtype=dtype) + float(cval)
    output[k0:k0 + s0, k1:k1 + s1] = data
    if mode in  ["reflect", "mirror"]:
    #4 corners
        output[s0 + k0:, s1 + k1:] = data[-1:-k0 - 1:-1, -1:-k1 - 1:-1]
        output[:k0, :k1] = data[k0 - 1::-1, k1 - 1::-1]
        output[:k0, s1 + k1:] = data[k0 - 1::-1, s1 - 1: s1 - k1 - 1:-1]
        output[s0 + k0:, :k1] = data[s0 - 1: s0 - k0 - 1:-1, k1 - 1::-1]
    #4 sides
        output[k0:k0 + s0, :k1] = data[:s0, k1 - 1::-1]
        output[:k0, k1:k1 + s1] = data[k0 - 1::-1, :s1]
        output[-k0:, k1:s1 + k1] = data[:s0 - k0 - 1:-1, :]
        output[k0:s0 + k0, -k1:] = data[:, :s1 - k1 - 1:-1]
    elif mode == "nearest":
    #4 corners
        output[s0 + k0:, s1 + k1:] = data[-1, -1]
        output[:k0, :k1] = data[0, 0]
        output[:k0, s1 + k1:] = data[0, -1]
        output[s0 + k0:, :k1] = data[-1, 0]
    #4 sides
        output[k0:k0 + s0, :k1] = numpy.outer(data[:, 0], numpy.ones(k1))
        output[:k0, k1:k1 + s1] = numpy.outer(numpy.ones(k0), data[0, :])
        output[-k0:, k1:s1 + k1] = numpy.outer(numpy.ones(k0), data[-1, :])
        output[k0:s0 + k0, -k1:] = numpy.outer(data[:, -1], numpy.ones(k1))
    return output



class Gaussian(object):
    """
    A class that tries to do gaussian blur as fast as possible
    """
    def __init__(self):
        self.dictGaussian = {}
        self.lock = threading.Semaphore()

    def blur(self, data, sigma, mode="reflect", cval=0.0):
        """
        2-dimensional Gaussian filter implemented with FFTw

        @param data:    data array to filter
        @type data: array-like
        @param sigma: standard deviation for Gaussian kernel. 
            The standard deviations of the Gaussian filter are given for each axis as a sequence,
            or as a single number, in which case it is equal for all axes. 
        @type sigma: scalar or sequence of scalars
        @param mode: {'reflect','constant','nearest','mirror', 'wrap'}, optional
            The ``mode`` parameter determines how the array borders are
            handled, where ``cval`` is the value when mode is equal to
            'constant'. Default is 'reflect'
        @param cval: scalar, optional
            Value to fill past edges of data if ``mode`` is 'constant'. Default is 0.0
        """
        if mode != "wrap":
            data = expand(data, sigma, mode, cval)
        s0, s1 = data.shape
        if isinstance(sigma, (list, tuple)):
            k0 = int(ceil(float(sigma[0])))
            k1 = int(ceil(float(sigma[1])))
        else:
            k0 = k1 = int(ceil(float(sigma)))
        if fftw3 is None:
            #Numpy implenentation
            if (s0, s1, k0, k1) not in self.dictGaussian:
                g0 = gaussian(s0, k0)
                g1 = gaussian(s1, k1)
                g0 = numpy.concatenate((g0[s0 // 2:], g0[:s0 // 2]))
                g1 = numpy.concatenate((g1[s1 // 2:], g1[:s1 // 2]))
                g2 = numpy.outer(g0, g1)
                self.dictGaussian[(s0, s1, k0, k1) ] = numpy.fft.fft2(g2 / g2.sum()).conjugate()
            blured = numpy.fft.ifft2(numpy.fft.fft2(data) * self.dictGaussian[(s0, s1, k0, k1) ]).real
        else:
            sum_init = data.astype("float32").sum()
            fftOut = numpy.zeros((s0, s1), dtype=complex)
            fftIn = numpy.zeros((s0, s1), dtype=complex)
            fft = fftw3.Plan(fftIn, fftOut, direction='forward')
            ifft = fftw3.Plan(fftOut, fftIn, direction='backward')

            if (s0, s1, k0, k1) not in self.dictGaussian:
                g0 = gaussian(s0, k0)
                g1 = gaussian(s1, k1)
                g0 = numpy.concatenate((g0[s0 // 2:], g0[:s0 // 2]))
                g1 = numpy.concatenate((g1[s1 // 2:], g1[:s1 // 2]))
                g2 = numpy.outer(g0, g1)
                g2fft = numpy.zeros((s0, s1), dtype=complex)
                fftIn[:, :] = g2.astype(complex) / g2.sum()
                fft()
                g2fft[:, :] = fftOut.conjugate()
                self.dictGaussian[(s0, s1, k0, k1) ] = g2fft

            fftIn[:, :] = data.astype(complex)
            fft()
            fftOut *= self.dictGaussian[(s0, s1, k0, k1) ]
            ifft()
            out = fftIn.real.astype("float32")
            sum_out = out.sum()
            res = out * sum_init / sum_out
            if mode == "wrap":
                blured = res
            else:
                blured = res[k0:-k0, k1:-k1]
        return  blured

