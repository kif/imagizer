#!/usr/bin/python
# -*- coding: Latin1 -*-

import os,sys,time

ATdir="TimeAdjusted"


def gettime(filename):
	"""gives the second count starting from Epoch"""
	if len(filename)>7:
		try:
			timetuple=time.strptime("2006-10-02_"+filename[:8],"%Y-%m-%d_%Hh%Mm%S")
		except:
			print("the file does not have look like a time")
			return
	else:
		print("the filename is far too short")
		return
#	print(timetuple)
	return time.mktime(timetuple)


if len(sys.argv)==1:
	raise RuntimeError("Enter the type of camera and the time-shift in seconds, for example \n $ Adjust-Time P92 -300\n to MOVE all files containg the «P92» string  of 5 minuts backwards \n The files are in the %s directory"%ATdir)

if not os.path.isdir(ATdir): os.mkdir(ATdir)

if len(sys.argv)==3:
	camera=sys.argv[1]
	try:
		shift=int(sys.argv[2])
	except:
		raise "the shift is not an interger"



fn=os.listdir(".")
for f in fn:
	if f.find(camera)>0:
		oldtime=gettime(f)
		if oldtime:
			suffix=f[8:]
			newtime=time.strftime("%Hh%Mm%S",time.localtime(oldtime+shift))
			dest=os.path.join(ATdir,newtime+suffix)
#			print(f[:8],oldtime,newtime
			print("%s\t==>\t%s"%(f,dest))
			os.rename(f,dest)
