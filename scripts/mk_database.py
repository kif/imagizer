#!/usr/bin/python
import Image
import imagizer, imagizer.config, imagizer.imagizer
import hashlib
import time
import os
import json
import sys

def save(db):
    with open("db_" + time.strftime("%Y-%m-%d-%Hh%Mm%S") + ".json", "w") as f:
        json.dump(db, f, indent=4)
    print("Dumped database with %s entries" % len(db))

def img_cmp(a, b):
    da, ba = os.path.split(a)
    db, bb = os.path.split(b)
    if len(da) > len(db):
        return -1
    elif len(da) < len(db):
        return 1
    else:
        if len(ba) < len(bb):
            return -1
        elif len(ba) > len(bb):
            return 1
        else:
            print(a, b)
            if a[:-4] < b[:-4]:
                return -1
            else:
                return 1


root = imagizer.config.config.DefaultRepository
lst = imagizer.imagizer.rangeTout(fast=True)[0]

if len(sys.argv)==2 and os.path.exists(sys.argv[1]):
    database = json.load(open(sys.argv[1]))
    processed = set()
    for v in database.values():
        processed.update(v)
else:
    database = {}
    processed = set()
for idx,fn in  enumerate(lst):
    if fn in processed:
        continue
    img = Image.open(os.path.join(root, fn))
    try:
        data = img.tostring()
    except IOError:
        print("Error while reading %s" % fn)
    hsh = hashlib.sha1(data).hexdigest()
    if hsh in database:
        database[hsh].append(fn)
    else:
        database[hsh] = [fn]
    if idx % 1000 == 0:
        save(database)
save(database)
