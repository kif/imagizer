import sys
import subprocess
import os
import functools
import struct
bchr = functools.partial(struct.pack, 'B')
import pyexiv2
import glob

def parse_exif(filename):
    "Search for comment badly encoded UserComment"
    if not os.path.exists(filename):
        return
    s = subprocess.run(["exiv2", "-ph", "-g", "UserComment", filename], capture_output=True)
    res = b""
    for idx, line in enumerate(s.stdout.split(b"\n")):
  #      print(idx, line)
        if idx == 0: continue
        w = line.split()
        if len(w) < 2: continue
        for k in w[1:-1]:
            if len(k) == 2:
                try:
                    v = int(k, base=16)
                except:
                    break
                else:
                    res += bchr(v)
            else:
                break
    try:
        if len(res)>8:
            if res.startswith(b"Ascii") or res.startswith(b"ASCII"):
                res = res[8:].strip(b"\x00").decode("UTF-8").strip()
            elif res.startswith(b"Unicode") or res.startswith(b"UNICODE"):
                res = res[8:].decode("UTF-16").strip("\x00").strip()
            else:
                res = res.decode("UTF-8").strip()
        else:
            res = res.decode("UTF-8").strip()
    except Exception as err:
        print(type(err), err, res, fn)
        raise
    return res

if __name__ == "__main__":
    lst = []
    for fn in sys.argv[1:]:
        if "*" in fn or "?" in fn:
            lst+=glob.glob(fn)
        else:
            lst.append(fn)
    for fn in lst:
        m = pyexiv2.ImageMetadata(fn)
        m.read()
        e = m["Exif.Photo.UserComment"]
        if e.value=="binary comment":
            try:
                old = parse_exif(fn)
            except Exception as err:
                print("Error %s parsing file %s: %s "%(type(err), fn, err))
                continue
            print("Updated", fn, old)
            m["Exif.Photo.UserComment"] = "charset=Unicode " + old
            try:
                m.write(True)
            except Exception as err:
                print("Error Writing: ", fn, type(err), err)
        else:
            print("Correct", fn, e.value)
