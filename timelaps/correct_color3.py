#!/usr/bin/python
# coding: utf-8

import os
import glob
import numpy
from scipy.misc import imread,imsave
from PIL import Image

#name of the directory with the processed images
dst = "color3"

#position of the discontinuity in the image
disc=1776

#arrays to convert images back & forth from RGB to YUV space.
RGB2YUV = numpy.array([[0.299,0.587,0.114],[-0.14713,-0.28886,0.436],[0.615,-0.51498,-0.10001]])
YUV2RGB = numpy.array([[1,0,1.13983],[1,-0.39465,-0.58060],[1,2.03211,0]])
RGB2YUV = numpy.ascontiguousarray(RGB2YUV.T)
YUV2RGB = numpy.ascontiguousarray(YUV2RGB.T)




def corr_img(img, disc=1776):
    "Pump up the luminosity for all pixels below the discontinuity"
    d = img[disc,:,:].std(axis=0)
    if d == 0:
       m = 1
    else:
       m = img[disc-1,:,:].std(axis=0) / d
    p = img[disc-1,:,:].mean(axis=0) - m*img[disc,:,:].mean(axis=0)
    cor = img[...]
    numpy.around(img[disc:,:,:]*m+p, out=cor[disc:,:,:])
    return cor


def corr_img2(img, disc=1776):
    cor = img.copy()
    sl = cor[disc-1:,:,:]
    yuv = sl.dot(RGB2YUV)
    y = yuv[0:2,:,0]
    mean = y.mean(axis=-1)
    std = y.std(axis=-1)
    if std[1] == 0:
        m = 1
    else:
        m = std[0] / std[1]
    p = mean[0] - m * mean[1]
    yuv[:,:,0] = yuv[:,:,0] * m + p
    rgb = yuv[1:].dot(YUV2RGB).clip(0,255)
    numpy.around(rgb, out=cor[disc:,:,:])
    return cor


if __name__ == "__main__":

    images = glob.glob("*.jpg")
    images.sort()
    print(len(images))

    fn = images[000]
    img = imread(fn)
    print(img.shape)

    if not os.path.exists(dst):
        os.mkdir(dst)

    for fn in images:
        img = Image.open(fn)
        #img = imread(fn)
        cor = corr_img2(numpy.asarray(img))
        df = os.path.join(dst,fn)
        Image.fromarray(cor, 'RGB').save(df, quality=95)
        #imsave(df, Image(cor)
        print(df)





