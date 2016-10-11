#!/usr/bin/python

import numpy

# coding: utf-8

# In[1]:

#get_ipython().magic(u'pylab inline')


# In[2]:

import glob
images = glob.glob("*.jpg")
print(len(images))


# In[14]:

from scipy.misc import imread,imsave
fn = images[000]
img = imread(fn)
print(img.shape)


# In[15]:

#imshow(img)


# In[5]:

#looking for the discontinuity
#green_mean_line = img[:,:,1].mean(axis=-1)
#clf()
#plot(green_mean_line[1770:1780])


# In[6]:

disc=1776
#clf()
#plot(img[1775,:,1],label="1775")
#plot(img[1776,:,1],label="1776")
#plot(img[1776,:,1]*m+p,label="1776_cor")
#legend()


# In[7]:

def corr_img(img, disc=1776):
    d = img[disc,:,:].std(axis=0)
    if d == 0:
       m = 1
    else:
       m = img[disc-1,:,:].std(axis=0) / d
    p = img[disc-1,:,:].mean(axis=0) - m*img[disc,:,:].mean(axis=0)
    cor = img[...]
    numpy.around(img[disc:,:,:]*m+p, out=cor[disc:,:,:])
    return cor


# In[8]:

RGB2YUV = numpy.array([[0.299,0.587,0.114],[-0.14713,-0.28886,0.436],[0.615,-0.51498,-0.10001]])
YUV2RGB = numpy.array([[1,0,1.13983],[1,-0.39465,-0.58060],[1,2.03211,0]])
RGB2YUV = numpy.ascontiguousarray(RGB2YUV.T)
YUV2RGB = numpy.ascontiguousarray(YUV2RGB.T)

def corr_img2(img, disc=1776):
    cor = img[...]
    sl = cor[disc-1:,:,:]
    yuv = sl.dot(RGB2YUV)
    y = yuv[0:2,:,0]
    m = y[0].std() / y[1].std()
    p = y[0].mean() - m*y[1].mean()
    yuv[:,:,0] = yuv[:,:,0]*m+p
    rgb = yuv[1:].dot(YUV2RGB).clip(0,255)
    numpy.around(rgb, out=cor[disc:,:,:])
    return cor


# In[16]:

#clf()
#subplot(2,1,1)
#imshow(img)
#subplot(2,1,2)
#imshow(corr_img2(img))


# In[17]:

import os
dst = "color2"
if not os.path.exists(dst):
    os.mkdir(dst)

for fn in images:
    img = imread(fn)
    cor = corr_img2(img)
    df = os.path.join(dst,fn)
    imsave(df, cor)
    print(df)


# In[ ]:




