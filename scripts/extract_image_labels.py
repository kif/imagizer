#!/usr/bin/python

from collections import OrderedDict
from imagizer.config import config
from imagizer.imagizer import range_tout
from imagizer.photo import Photo
from imagizer.sqlitedict import SqliteDict
import json
import sys
import os

data = OrderedDict()
save_every = 10000
filename = "images.json"
sqlitefile = "title.sqlite"
saved_dict = SqliteDict(sqlitefile, encode=json.dumps, decode=json.loads)

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
        saved_dict[onefile] = data[onefile] = read_dict[onefile]
    else:
        p = Photo(onefile)
        m = p.read_exif()
        title = m.get("title")
        saved_dict[onefile] = data[onefile] = title
        if title:
            print("%s: %s" % (onefile, title))
        if i % save_every == save_every - 1:
            saved_dict.sync()
            print("Saving %s (%i)" % (filename, i))
            with open("images.json", "w") as f:
                f.write(json.dumps(data, indent=2))

print("Done ! Saving %s (%i)" % (filename, i))
saved_dict.close()
with open("images.json", "w") as f:
    f.write(json.dumps(data, indent=2))
