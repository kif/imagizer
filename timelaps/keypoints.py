#!/usr/bin/python
import numpy
import glob
import feature
from scipy.misc import imread,imsave
import h5py
import sift_pyocl as sift

images = glob.glob("*.jpg")
print(len(images))
images.sort()
fn = images[0]
img = imread(fn)
print(img.shape)
plan = sift.SiftPlan(template=img, devicetype="gpu")
match = sift.MatchPlan(devicetype='GPU')
kp = plan.keypoints(img)
print(len(kp))
pos = {"dx":[], "dy":[], "dt":[], "dr":[]}
last = kp
h5 = h5py.File("keypoints.h5")
for fn in images:
    img = imread(fn)
    kp = plan.keypoints(img)
    h5[fn] = kp
    m = match.match(kp,last)
    dx = dy = dt = dr = 0
    if len(m):
        n = feature.sift_orsa(m)
        #cutof = m[:,:].scale.mean() + m[:,:].scale.std()
        #(m[:,0].scale - m[:,1].scale)/m[:,0].scale < 0.2
        #keep = numpy.logical_and((abs(m[:,0].scale - m[:,1].scale)/m[:,0].scale < 0.2), m[:,:].scale.max(axis=-1)<cutof)
        #n = m[keep]
        if len(n):
            dx = float(numpy.median(n[:,0].x-n[:,1].x))
            dy = float(numpy.median(n[:,0].y-n[:,1].y))
            dt = float(numpy.median((n[:,0].angle-n[:,1].angle+numpy.pi)%(2*numpy.pi)-numpy.pi))
            x = n[:,0].x - n[:,0].x.mean()
            y = n[:,0].y - n[:,0].y.mean()
            w = n[:,1].x - n[:,1].x.mean()
            z = n[:,1].y - n[:,1].y.mean()
            dr = float(numpy.arctan2((w*y-z*x).sum(), (w*x+z*y).sum()))

    print("%s \t dx:%4.1f \t dy=%4.1f \t dt=%5.3f \t dr=%5.3f"%(fn, dx, dy, dt, dr))
    pos["dx"].append(dx)
    pos["dy"].append(dy)
    pos["dt"].append(dt)
    pos["dr"].append(dr)
    last = kp
h5.close()
import json
open("position.json","w").write(json.dumps(pos, indent=2))


