#!/usr/bin/python

from collections import OrderedDict
from imagizer.config import config
from imagizer.imagizer import range_tout
from imagizer.photo import Photo
from imagizer.imagecache import title_cache
import json
import sys
import os

data = OrderedDict()
save_every = 10000
filename = os.path.join(config.DefaultRepository, "images.json")
title_cache.autocommit = False
print("SQLite database contained %s entries" % len(title_cache))
title_cache.clear()

if os.path.exists(filename):
    print("Loading %s" % filename)
    with open(filename) as f:
        read_dict = json.load(f)
else:
    read_dict = {}
print("Exploring the tree ...")
all_jpg = range_tout(repository=config.DefaultRepository, bUseX=False, fast=True, updated=None, finished=None)[0]
for i, onefile in enumerate(all_jpg):
    if onefile in read_dict:
        title_cache[onefile] = data[onefile] = read_dict[onefile]
    else:
        p = Photo(onefile)
        m = p.read_exif()
        title = m.get("title")
        title_cache[onefile] = data[onefile] = title
        if title:
            print("%s: %s" % (onefile, title))
        if i % save_every == save_every - 1:
            title_cache.sync()
            print("Saving %s (%i)" % (filename, i))
            with open("images.json", "w") as f:
                f.write(json.dumps(data, indent=2))

print("Done ! Saving %s (%i)" % (filename, i))
title_cache.sync()
with open(filename, "w") as f:
    f.write(json.dumps(data, indent=2))
