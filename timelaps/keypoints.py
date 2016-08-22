#!/usr/bin/python
import numpy
import glob
images = glob.glob("*.jpg")
print(len(images))
images.sort()
from scipy.misc import imread,imsave
fn = images[0]
img = imread(fn)
print(img.shape)
import h5py
import sift_pyocl as sift
plan = sift.SiftPlan(template=img, devicetype="gpu")
match = sift.MatchPlan(devicetype='GPU')
kp = plan.keypoints(img)
print(len(kp))
pos = {"dx":[], "dy":[]}
last = kp
h5 = h5py.File("keypoints.h5")
for fn in images:
    img = imread(fn)
    kp = plan.keypoints(img)
    h5[fn] = kp
    m = match.match(kp,last)
    if len(m) == 0:
        dx = dy = 0
    else:
        dx = float(numpy.median(m[:,0].x-m[:,1].x))
        dy = float(numpy.median(m[:,0].y-m[:,1].y))

    print("%s \t dx:%4.1f \t dy=%4.1f"%(fn, dx or 0, dy or 0))
    pos["dx"].append(dx)
    pos["dy"].append(dy)
    last = kp
h5.close()
import json
open("position.json","w").write(json.dumps(pos, indent=2))


