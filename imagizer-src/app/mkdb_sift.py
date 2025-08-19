#!/usr/bin/python
import pyopencl
import sift
import Image
import imagizer, imagizer.config, imagizer.imagizer
import hashlib
import time
import os
import json
import sys
import numpy
import base64
import h5py

root = imagizer.config.config.DefaultRepository
lst = imagizer.imagizer.rangeTout(fast=True)[0]
siftplans = {}
ctx = pyopencl.create_some_context(interactive=True)

if len(sys.argv)==2 and os.path.exists(sys.argv[1]):
    database = h5py.File(sys.argv[1])
else:
    database = h5py.File("db.h5")
sha1 = database.require_group("sha1")
for idx, fn in enumerate(lst):
    print("%10i\t%60s"%(idx,fn))
    if fn in database:
        continue
    img = Image.open(os.path.join(root, fn))
    try:
        data = img.tostring()
    except IOError:
        print("Error while reading %s" % fn)
        continue
    hsh = hashlib.sha1(data).hexdigest()
    if hsh in sha1:
        database[fn]=sha1[hsh]
        continue
    ary = numpy.array(img)
    if not ary.shape in siftplans:
        siftplans = {}
        siftplans[ary.shape] = sift.SiftPlan(template=ary, context=ctx)
    try:
        kp =  siftplans[ary.shape].keypoints(ary)
    except pyopencl.MemoryError:
        print("Not enough memory")
    else:
        sha1.create_dataset(hsh, data=kp, compression="gzip", compression_opts=9)
        database[fn]=sha1[hsh]