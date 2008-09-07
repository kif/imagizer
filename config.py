#!/usr/bin/env python 
# -*- coding: Latin1 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006,  Jérome Kieffer <kieffer@terre-adelie.org>
#* Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
#* Licence GPL v2
#*
#* This program is free software; you can redistribute it and/or modify
#* it under the terms of the GNU General Public License as published by
#* the Free Software Foundation; either version 2 of the License, or
#* (at your option) any later version.
#*
#* This program is distributed in the hope that it will be useful,
#* but WITHOUT ANY WARRANTY; without even the implied warranty of
#* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#* GNU General Public License for more details.
#*
#* You should have received a copy of the GNU General Public License
#* along with this program; if not, write to the Free Software
#* Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#*
#*****************************************************************************/

"""
Config is a class containing all the configuration of the imagizer suite.
Technically it is a Borg (design Pattern) so every instance of Config has exactly the same contents.
"""

import os,sys,distutils.sysconfig,locale

installdir=os.path.join(distutils.sysconfig.get_python_lib(),"imagizer")
#here we detect the OS runnng the program so that we can call exftran in the right way
if os.name == 'nt': #sys.platform == 'win32':
	ConfFile=[os.path.join(os.getenv("ALLUSERSPROFILE"),"imagizer.conf"),os.path.join(os.getenv("USERPROFILE"),"imagizer.conf")]
elif os.name == 'posix':
	ConfFile=["/etc/imagizer.conf",os.path.join(os.getenv("HOME"),".imagizer")]
else:
	raise "Your platform does not seem to be an Unix nor a M$ Windows.\nI am sorry but the exiftran binary is necessary to run selector, and exiftran is probably not available for you plateform. If you have exiftran installed, please contact the developper to correct that bug, kieffer at terre-adelie dot org"
	sys.exit(1)

################################################################################################
class Config:
	"""this class is a Borg : always returns the same values regardless to the instance of the object"""
	__shared_state = {}
	def __init__(self):
		self.__dict__ = self.__shared_state
	def default(self):
		self.ScreenSize=600
		self.NbrPerPage=20
		self.PagePrefix="page"
		self.TrashDirectory="Trash"
		self.SelectedDirectory="Selected"
		self.Selected_save=".selected-photos"
		self.Extensions=[".jpg", ".jpeg",".jpe",".jfif"]
		self.AutoRotate=False
		self.DefaultMode="664"
		self.DefaultRepository=os.getcwd()
		self.CommentFile="Comment.txt"
		self.Interpolation=1
		self.DefaultFileMode=int(self.DefaultMode,8)
		self.DefaultDirMode=self.DefaultFileMode+3145 #73 = +111 en octal ... 3145 +s mode octal
		self.Filigrane=False
		self.FiligraneSource=os.path.join(installdir,"signature.png")
		self.FiligranePosition=5
		self.FiligraneQuality=75
		self.FiligraneOptimize=False		
		self.FiligraneProgressive=False	
		self.WebDirIndexStyle="list"	
		self.MediaSize=680
		self.Burn="grave-rep $Selected"
		self.WebServer="cp -r $Selected/* $WebRepository && generator" 
		self.WebRepository="/var/www/imagizer"
		self.Locale,self.Coding = locale.getdefaultlocale()
#		self.Locale="fr_FR"
#		self.Coding="Latin-1"
		self.ExportSingleDir=False
		self.GraphicMode="Normal"
		self.WebPageAnchor="end"
		self.SlideShowDelay=5.0
		self.SlideShowType="chronological"
		self.SynchronizeRep="user@host:/mnt/photo"
		self.SynchronizeType="Newer"
		self.Thumbnails={
			"Size":160,
			"Suffix": "thumb",
			"Interpolation":1,
			"Progressive":False,
			"Optimize":False,
			"ExifExtraction":True,
			"Quality": 75
			}
		self.ScaledImages={
			"Size":800,
			"Suffix": "scaled",
			"Interpolation":2,
			"Progressive":False,
			"Optimize":False,
			"ExifExtraction":False,
			"Quality": 75
			}
			
	def load(self,filenames):
		"""retrieves the the default options, if the filenames does not exist, uses the default instead
		type filenames: list of filename
		"""
		import ConfigParser
		config = ConfigParser.ConfigParser()
		self.default()
		files=[]
		for i in filenames:
			if os.path.isfile(i):files.append(i)
		if len(files)==0:
			print "No configuration file found. Falling back on defaults"
			return

		config.read(files)
		for i in config.items("Selector"):
			j=i[0]
			if j=="ScreenSize".lower():self.ScreenSize=int(i[1])
			elif j=="Interpolation".lower():self.Interpolation=int(i[1])
			elif j=="PagePrefix".lower():self.PagePrefix=i[1]
			elif j=="NbrPerPage".lower():self.NbrPerPage=int(i[1])
			elif j=="TrashDirectory".lower():self.TrashDirectory=i[1]
			elif j=="SelectedDirectory".lower():self.SelectedDirectory=i[1]
			elif j=="Selected_save".lower():self.Selected_save=i[1]
			elif j=="AutoRotate".lower():self.AutoRotate=config.getboolean("Selector","AutoRotate")
			elif j=="Filigrane".lower():self.Filigrane=config.getboolean("Selector","Filigrane")
			elif j=="FiligraneSource".lower():self.FiligraneSource=i[1]
			elif j=="FiligranePosition".lower():self.FiligranePosition=int(i[1])
			elif j=="FiligraneQuality".lower():self.FiligraneQuality=int(i[1])
			elif j=="FiligraneOptimize".lower():self.FiligraneOptimize=config.getboolean("Selector","FiligraneOptimize")
			elif j=="FiligraneProgressive".lower():self.FiligraneProgressive=config.getboolean("Selector","FiligraneProgressive")
			elif j=="CommentFile".lower():self.CommentFile=i[1]
			elif j=="WebDirIndexStyle".lower():self.WebDirIndexStyle=i[1]

			elif j=="DefaultFileMode".lower():
				self.DefaultFileMode=int(i[1],8)
				self.DefaultDirMode=self.DefaultFileMode+3145 #73 = +111 en octal ... 3145 +s mode octal	
			elif j=="Extensions".lower(): self.Extensions=i[1].split()
			elif j=="DefaultRepository".lower():self.DefaultRepository=i[1]
			elif j=="MediaSize".lower():self.MediaSize=float(i[1])
			elif j=="Burn".lower(): self.Burn=i[1]
			elif j=="WebServer".lower():self.WebServer=i[1]
			elif j=="WebRepository".lower():self.WebRepository=i[1]
			elif j=="Locale".lower():self.Locale=i[1]
			elif j=="Coding".lower():self.Coding=i[1]
			elif j=="ExportSingleDir".lower():self.ExportSingleDir=config.getboolean("Selector","ExportSingleDir")
			elif j=="WebPageAnchor".lower():self.WebPageAnchor=i[1]
			elif j=="SlideShowDelay".lower():self.SlideShowDelay=float(i[1])
			elif j=="SlideShowType".lower():self.SlideShowType=i[1]
			elif j=="SynchronizeRep".lower():self.SynchronizeRep=i[1]
			elif j=="SynchronizeType".lower(): self.SynchronizeType=i[1]

			else: print "unknown key "+j
		

		for k in ["ScaledImages","Thumbnails"]:
			try:
				dico=eval(k)
			except:
				dico={}
			for i in config.items(k):
				j=i[0]
				if j=="Size".lower():dico["Size"]=int(i[1])
				elif j=="Suffix".lower():dico["Suffix"]=i[1]
				elif j=="Interpolation".lower():dico["Interpolation"]=int(i[1])
				elif j=="Progressive".lower():dico["Progressive"]=config.getboolean(k,"Progressive")
				elif j=="Optimize".lower():dico["Optimize"]=config.getboolean(k,"Optimize")
				elif j=="ExifExtraction".lower():dico["ExifExtraction"]=config.getboolean(k,"ExifExtraction")
				elif j=="Quality".lower():dico["Quality"]=int(i[1])
			exec("self.%s=dico"%k)
	
	def PrintConfig(self):
		print "#"*80
		print "Size on the images on the Screen: %s"%self.ScreenSize
		print "Page prefix:\t\t\t  %s"%self.PagePrefix
		print "Number of images per page:\t  %s"%self.NbrPerPage
		print "Use Exif for Auto-Rotate:\t  %s"%self.AutoRotate
		print "Default mode for files (octal):\t  %o"%self.DefaultFileMode
		print "JPEG extensions:\t\t %s"%self.Extensions
		print "Default photo repository:\t  %s"%self.DefaultRepository
		print "Add signature for exported images:%s"%self.Filigrane
		print "Backup media size (CD,DVD) in Mb :%s"%self.MediaSize
		print "Scaled imagesSize:\t\t  %s"%self.ScaledImages["Size"]
		print "Thumbnail Size:\t\t\t  %s"%self.Thumbnails["Size"]

	def SaveConfig(self,filename):
		"""saves the default options"""
		txt="[Selector]\n"
		txt+="#Size of the image on the Screen, by default\nScreenSize: %s \n\n"%self.ScreenSize
		txt+="#Downsampling quality [0=nearest, 1=tiles, 2=bilinear, 3=hyperbolic]\nInterpolation: %s \n\n"%self.Interpolation
		txt+="#Page prefix (used when there are too many images per day to fit on one web page)\nPagePrefix: %s \n\n"%self.PagePrefix
		txt+="#Maximum number of images per web page\nNbrPerPage: %s\n\n"%self.NbrPerPage
		txt+="#Trash sub-directory\nTrashDirectory: %s \n\n"%self.TrashDirectory
		txt+="#Selected/processed images sub-directory\nSelectedDirectory: %s \n\n"%self.SelectedDirectory
		txt+="#File containing the list of selected but unprocessed images\nSelected_save: %s \n\n"%self.Selected_save
		txt+="#Use Exif data for auto-rotation of the images (canon cameras mainly)\nAutoRotate: %s\n\n"%self.AutoRotate
		txt+="#Default mode for files (in octal)\nDefaultFileMode: %o\n\n"%self.DefaultFileMode
		txt+="#Default JPEG extensions\nExtensions: "
		for i in self.Extensions: txt+=i+" "
		txt+="\n\n"
		txt+="#Default photo repository\nDefaultRepository: %s \n\n"%self.DefaultRepository
		txt+="#Size of the backup media (in MegaByte)\nMediaSize:	%s \n\n"%self.MediaSize
		txt+="#Add signature to web published images\nFiligrane: %s \n\n"%self.Filigrane
		txt+="#File containing the image of the signature for the filigrane\nFiligraneSource: %s\n\n"%self.FiligraneSource
		txt+="#Position of the filigrane : 0=center 12=top center 1=upper-right 3=center-right...\nFiligranePosition: %s\n\n"%self.FiligranePosition
		txt+="#Quality of the saved image in filigrane mode (JPEG quality)\nFiligraneQuality: %s\n\n"%self.FiligraneQuality
		txt+="#Optimize the filigraned image (2 pass JPEG encoding)\nFiligraneOptimize: %s\n\n"%self.FiligraneOptimize
		txt+="#Progressive JPEG for saving filigraned images\nFiligraneProgressive: %s\n\n"%self.FiligraneProgressive
		txt+="#File containing the description of the day in each directory\nCommentFile: %s\n\n"%self.CommentFile
		txt+="#Style of the dirindex web pages, either <<list>> or <<table>>, the latest includes thumbnail photos\nWebDirIndexStyle: %s\n\n"%self.WebDirIndexStyle
		txt+="#System command to use to burn a CD or a DVD\n# $Selected will be replaced by the directory where the files are\nBurn: %s\n\n"%self.Burn
		txt+="#System command to copy the selection to the server\n# $Selected will be replaced by the directory where the files are\n# $WebRepository will be replaced by the directory of the root of generator\nWebServer: %s\n\n"%self.WebServer
		txt+="#The location of the root of generator\nWebRepository: %s\n\n"%self.WebRepository
		txt+="#The localization code, fr_FR is suggested for unix or FR for win32\nLocale: %s\n\n"%self.Locale
		txt+="#Default encoding for text files, latin-1 is suggested,UTF-8 should be possible\nCoding: %s\n\n"%self.Coding
		txt+="#All selected photos should be exported in a single directory\nExportSingleDir: %s\n\n"%self.ExportSingleDir
		txt+="#Where should the dirindex page start-up ? [begin/end] \nWebPageAnchor: %s\n\n"%self.WebPageAnchor
		txt+="#Delay between imges in the slideshow? \nSlideShowDelay: %s\n\n"%self.SlideShowDelay
		txt+="#Type of slideshow : chronological, anti-chronological or random ?\nSlideShowType: %s\n\n"%self.SlideShowType
		txt+="#Remote repository to synchronize with (rsync like)\nSynchronizeRep: %s\n\n"%self.SynchronizeRep
		txt+="#Synchronization type, acceptable values are Newer, Older, Selected and All\nSynchronizeType: %s\n\n"%self.SynchronizeType


		for i in ["ScaledImages","Thumbnails"]:
			txt+="[%s]\n"%i
			j=eval("self.%s"%i)
			txt+="#%s size\nSize: %s \n\n"%(i,j["Size"])
			txt+="#%s suffix\nSuffix: %s \n\n"%(i,j["Suffix"])
			txt+="#%s downsampling quality [0=nearest, 1=bilinear, 2=bicubic, 3=antialias]\nInterpolation: %s \n\n"%(i,j["Interpolation"])
			txt+="#%s progressive JPEG files\nProgressive: %s \n\n"%(i,j["Progressive"])
			txt+="#%s optimized JPEG (2 pass encoding)\nOptimize: %s \n\n"%(i,j["Optimize"])
			txt+="#%s quality (in percent)\nQuality: %s \n\n"%(i,j["Quality"])
			txt+="#%s image can be obtained by Exif extraction ?\nExifExtraction: %s \n\n"%(i,j["ExifExtraction"])
		w=open(filename,"w")
		w.write(txt)
		w.close()
