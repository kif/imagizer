#!/usr/bin/python
#Small utility to find all index.desc files and convert them from latin1 to UTF8
#written by Jerome 23/03/2009
# $Id$ 
import  os, sys

def convertToUTF8(unknownStr):
    enc = None
    unicStr = u""
    for line in unknownStr.split("\n"):
        if line.find("coding:") == 0:
            enc = line.split(":", 1)[1].strip()
    if enc == None:
        enc = "Latin-1"
        unicStr = u"coding: UTF-8\n\n"
    for line in unknownStr.split("\n"):
        if line.find("coding:") == 0:
            unicStr += u"coding: UTF-8\n"
        else:
            unicStr += line.strip().decode(enc) + u"\n"
    return unicStr.encode("UTF-8")

for root, dirs, files in os.walk(os.path.abspath(sys.argv[1])):
    if "index.desc" in files >= 0:
        filein = os.path.join(os.path.abspath(sys.argv[1]), root, "index.desc")
        f = open(filein).read()
        g = convertToUTF8(f)
        if f != g[:-1]:
            open(filein, "w").write(g)
