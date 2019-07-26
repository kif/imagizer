#!/usr/bin/python

from collections import OrderedDict
from imagizer.config import config
from imagizer.imagizer import range_tout
from imagizer.photo import Photo
import json
import sys
import os

data = OrderedDict()
save_every = 10000
filename = "images.json"

if os.path.exists(filename):
    print("Loading %s" % filename)
    with open(filename) as f:
        read_dict = json.load(f)
    keys = list(read_dict.keys())
    keys.sort()
    for i in keys:
        data[i] = read_dict[i]

all_jpg = range_tout(repository=config.DefaultRepository, bUseX=False, fast=True, updated=None, finished=None)[0]
for i, onefile in enumerate(all_jpg):
    if onefile in data:
        continue
    p = Photo(onefile)
    m = p.read_exif()
    title = m.get("title")
    data[onefile] = title
    if title:
        print("%s: %s" % (onefile, title))
    if i % save_every == save_every - 1:
        print("Saving %s (%i)" % (filename, i))
        with open("images.json", "w") as f:
            f.write(json.dumps(data, indent=2))
print("Saving %s (%i)" % (filename, i))
with open("images.json", "w") as f:
    f.write(json.dumps(data, indent=2))

