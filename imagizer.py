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
General library used by selector and (in a near futur) generator.
It handles images, progress bars and configuration file.
"""




import os,sys,string,shutil,time,re,gc

try:
	import Image,ImageStat,ImageChops,ImageFile
except:
	raise "Selector needs PIL: Python Imagin Library\n PIL is available from http://www.pythonware.com/products/pil/"
try:
	import pygtk ; pygtk.require('2.0')
	import gtk,gtk.glade
except:
		raise "Selector needs pygtk and glade-2 available from http://www.pygtk.org/"
#Variables globales qui sont des CONSTANTES !
gtkInterpolation=[gtk.gdk.INTERP_NEAREST,gtk.gdk.INTERP_TILES,gtk.gdk.INTERP_BILINEAR,gtk.gdk.INTERP_HYPER]	
#gtk.gdk.INTERP_NEAREST	Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
#gtk.gdk.INTERP_TILES	This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
#gtk.gdk.INTERP_BILINEAR	Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
#gtk.gdk.INTERP_HYPER	This is the slowest and highest quality reconstruction function. It is derived from the hyperbolic filters in Wolberg's "Digital Image Warping", and is formally defined as the hyperbolic-filter sampling the ideal hyperbolic-filter interpolated image (the filter is designed to be idempotent for 1:1 pixel mapping).


#here we detect the OS runnng the program so that we can call exftran in the right way
if os.name == 'nt': #sys.platform == 'win32':
	installdir="c:\\Imagizer"
	exiftran=os.path.join(installdir,"exiftran.exe ")
	gimpexe="gimp-remote "
	ConfFile=["c:\\imagizer.conf",os.path.join(installdir,".imagizer")]
elif os.name == 'posix':
	installdir='/usr/share/imagizer'
	exiftran=os.path.join(installdir,"exiftran ")
	gimpexe="gimp-remote "
	ConfFile=["/etc/imagizer.conf",os.path.join(os.getenv("HOME"),".imagizer")]
else:
	raise "Your platform does not seem to be an Unix nor a M$ Windows.\nI am sorry but the exiftran binary is necessary to run selector, and exiftran is probably not available for you plateform. If you have exiftran installed, please contact the developper to correct that bug, kieffer at terre-adelie dot org"
	sys.exit(1)

sys.path.append(installdir)	
unifiedglade=os.path.join(installdir,"selector.glade")
from signals import Signal
from config import Config
config=Config()
config.load(ConfFile)

import EXIF



#class Model:
#	""" Implémentation de l'applicatif
#	"""
#	def __init__(self, label):
#		"""
#		"""
#		self.__label = label
#		self.startSignal = Signal()
#		self.refreshSignal = Signal()
#		
#	def start(self):
#		""" Lance les calculs
#		"""
#		self.startSignal.emit(self.__label, NBVALUES)
#		for i in xrange(NBVALUES):
#			time.sleep(0.5)
#			
#			# On lève le signal de rafraichissement des vues éventuelles
#			# Note qu'ici on ne sait absolument pas si quelque chose s'affiche ou non
#			# ni de quelle façon c'est affiché.
#			self.refreshSignal.emit(i)



class ModelProcessSelected:
	"""Implemantation MVC de la procedure ProcessSelected"""
	def __init__(self):
		"""
		"""
		self.__label = "Un moment..."
		self.startSignal = Signal()
		self.refreshSignal = Signal()
		self.finishSignal = Signal()
		self.NbrJobsSignal = Signal()
	def start(self,List):
		""" Lance les calculs
		"""
		self.startSignal.emit(self.__label, max(1,len(List)))
#		config=Config()
		if config.Filigrane:
			filigrane=signature(config.FiligraneSource)
		else:
			filigrane=None

		SelectedDir=os.path.join(config.DefaultRepository,config.SelectedDirectory)
		self.refreshSignal.emit(-1,"copie des fichiers existants")
		if not os.path.isdir(SelectedDir): 	mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
		AlsoProcess=0
		for day in os.listdir(SelectedDir):
			for File in os.listdir(os.path.join(SelectedDir,day)):
				if File.find(config.PagePrefix)==0:
					if os.path.isdir(os.path.join(SelectedDir,day,File)):
						for ImageFile in os.listdir(os.path.join(SelectedDir,day,File)):
							src=os.path.join(SelectedDir,day,File,ImageFile)
							dst=os.path.join(SelectedDir,day,ImageFile)
							if os.path.isfile(src) and not os.path.exists(dst):
								shutil.move(src,dst)
								AlsoProcess+=1
							if (os.path.isdir(src)) and (os.path.split(src)[1] in [config.ScaledImages["Suffix"],config.Thumbnails["Suffix"]]):
								shutil.rmtree(src)
				else:
					if os.path.splitext(File)[1] in config.Extensions:
						AlsoProcess+=1
						
#######then copy the selected files to their folders###########################		
		for File in List:
			dest=os.path.join(SelectedDir,File)
			src=os.path.join(config.DefaultRepository,File)
			destdir=os.path.dirname(dest)
			if not os.path.isdir(destdir): makedir(destdir)
			if not os.path.exists(dest):
				print "copie de %s "%(File)
				shutil.copy(src,dest)
				os.chmod(dest,config.DefaultFileMode)
				AlsoProcess+=1
			else :
				print "%s existe déja"%(dest)
		if AlsoProcess>0:self.NbrJobsSignal.emit(AlsoProcess)					

########finaly recreate the structure with pages########################
		dirs=os.listdir(SelectedDir)
		dirs.sort()
		GlobalCount=0
		
		for day in dirs:
			pathday=os.path.join(SelectedDir,day)
			files=[]
			for  i in os.listdir(pathday):
				if os.path.splitext(i)[1] in config.Extensions:files.append(i)
			files.sort()

			if  len(files)>config.NbrPerPage:
				pages=1+(len(files)-1)/config.NbrPerPage
				for i in range(1, pages+1):
					folder=os.path.join(pathday,config.PagePrefix+str(i))
					if not os.path.isdir(folder): mkdir(folder)
				for j in range(len(files)):
					i=1+(j)/config.NbrPerPage
					filename=os.path.join(pathday,config.PagePrefix+str(i),files[j])
					self.refreshSignal.emit(GlobalCount,files[j])
					GlobalCount+=1
					shutil.move(os.path.join(pathday,files[j]),filename)
					ScaleImage(filename,filigrane)
			else:
				for j in files:
					self.refreshSignal.emit(GlobalCount,j)
					GlobalCount+=1
					ScaleImage(os.path.join(pathday,j),filigrane)
######copy the comments of the directory to the Selected directory 
		AlreadyDone=[]
		for File in List:
			directory=os.path.split(File)[0]
			if directory in AlreadyDone:
				continue
			else:
				AlreadyDone.append(directory)
				dst=os.path.join(SelectedDir,directory,config.CommentFile)
				src=os.path.join(config.DefaultRepository,directory,config.CommentFile)
				if os.path.isfile(src):
					shutil.copy(src,dst)

		self.finishSignal.emit()


class ModelCopySelected:
	"""Implemantation MVC de la procedure CopySelected"""
	def __init__(self):
		"""
		"""
		self.__label = "Un moment..."
		self.startSignal = Signal()
		self.refreshSignal = Signal()
		self.finishSignal = Signal()
		self.NbrJobsSignal = Signal()
	def start(self,List):
		""" Lance les calculs
		"""
		self.startSignal.emit(self.__label, max(1,len(List)))
#		config=Config()
		if config.Filigrane:
			filigrane=signature(config.FiligraneSource)
		else:
			filigrane=None

		SelectedDir=os.path.join(config.DefaultRepository,config.SelectedDirectory)
		self.refreshSignal.emit(-1,"copie des fichiers existants")
		if not os.path.isdir(SelectedDir): 	mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
		for day in os.listdir(SelectedDir):
			for File in os.listdir(os.path.join(SelectedDir,day)):
				if File.find(config.PagePrefix)==0:
					if os.path.isdir(os.path.join(SelectedDir,day,File)):
						for ImageFile in os.listdir(os.path.join(SelectedDir,day,File)):
							src=os.path.join(SelectedDir,day,File,ImageFile)
							dst=os.path.join(SelectedDir,day,ImageFile)
							if os.path.isfile(src) and not os.path.exists(dst):
								shutil.move(src,dst)
							if (os.path.isdir(src)) and (os.path.split(src)[1] in [config.ScaledImages["Suffix"],config.Thumbnails["Suffix"]]):
								shutil.rmtree(src)
						
#######then copy the selected files to their folders###########################		
		GlobalCount=0
		for File in List:
			dest=os.path.join(SelectedDir,File)
			src=os.path.join(config.DefaultRepository,File)
			destdir=os.path.dirname(dest)
			self.refreshSignal.emit(GlobalCount,File)
			GlobalCount+=1
			if not os.path.isdir(destdir): makedir(destdir)
			if not os.path.exists(dest):
				if filigrane: 
					Img=Image.open(src)
					filigrane.substract(Img).save(dest,quality=config.FiligraneQuality,optimize=config.FiligraneOptimize,progressive=config.FiligraneOptimize)
				else:
					shutil.copy(src,dest)
				os.chmod(dest,config.DefaultFileMode)
			else :
				print "%s existe déja"%(dest)
######copy the comments of the directory to the Selected directory 
		AlreadyDone=[]
		for File in List:
			directory=os.path.split(File)[0]
			if directory in AlreadyDone:
				continue
			else:
				AlreadyDone.append(directory)
				dst=os.path.join(SelectedDir,directory,config.CommentFile)
				src=os.path.join(config.DefaultRepository,directory,config.CommentFile)
				if os.path.isfile(src):
					shutil.copy(src,dst)
		self.finishSignal.emit()




class ModelRangeTout:
	"""Implemantation MVC de la procedure RangeTout
	moves all the JPEG files to a directory named from 
	their day and with the name according to the time"""

	def __init__(self):
		"""
		"""
		self.__label = "Rangement photo"
		self.startSignal = Signal()
		self.refreshSignal = Signal()
		self.finishSignal = Signal()
		self.NbrJobsSignal = Signal()


	def start(self,RootDir):
		""" Lance les calculs
		"""
#		config=Config()
		AllJpegs=FindFile(RootDir)
		AllFilesToProcess=[]
		AllreadyDone=[]
		NewFiles=[]
		for i in AllJpegs:
			if i.find(config.TrashDirectory)==0: continue
			if i.find(config.SelectedDirectory)==0: continue
			try:
				a=int(i[:4])
				m=int(i[5:7])
				j=int(i[8:10])
				if (a>=0000) and (m<=12) and (j<=31) and (i[4] in ["-","_","."]) and (i[7] in ["-","_"]): 
					AllreadyDone.append(i)
				else:
					AllFilesToProcess.append(i)
			except : 
				AllFilesToProcess.append(i)
		AllFilesToProcess.sort()
		NumFiles=len(AllFilesToProcess)
		self.startSignal.emit(self.__label,NumFiles)
		for h in range(NumFiles):
			i=AllFilesToProcess[h]
			self.refreshSignal.emit(h,i)
			data=photo(i).exif() 
			try:
				datei,heurei=data["Heure"].split()
				date=re.sub(":","-",datei)
				heurej=re.sub(":","h",heurei,1)
				model=data["Modele"].split(",")[-1]
				heure=latin1_to_ascii("%s-%s.jpg"%(re.sub(":","m",heurej,1),re.sub("/","",re.sub(" ","_",model))))
			except:
				date=time.strftime("%Y-%m-%d",time.gmtime(os.path.getctime(os.path.join(RootDir,i))))
				heure=latin1_to_ascii("%s-%s.jpg"%(time.strftime("%Hh%Mm%S",time.gmtime(os.path.getctime(os.path.join(RootDir,i)))),re.sub("/","-",re.sub(" ","_",os.path.splitext(i)[0]))))
			if not (os.path.isdir(os.path.join(RootDir,date))) : mkdir(os.path.join(RootDir,date))
			imagefile=os.path.join(RootDir,date,heure)
			ToProcess=os.path.join(date,heure)
			if os.path.isfile(imagefile):
				print "Problème ... %s existe déja "%i
				s=0
				for j in os.listdir(os.path.join(RootDir,date)):
					if j.find(heure[:-4])==0:s+=1
				ToProcess=os.path.join(date,heure[:-4]+"-%s.jpg"%s)
				imagefile=os.path.join(RootDir,ToProcess)
			shutil.move(os.path.join(RootDir,i),imagefile)
			if config.AutoRotate :
				photo(imagefile).autorotate()
			AllreadyDone.append(ToProcess)
			NewFiles.append(ToProcess)
		AllreadyDone.sort()
		self.finishSignal.emit()

		if len(NewFiles)>0:
			FirstImage=min(NewFiles)
			return AllreadyDone,AllreadyDone.index(FirstImage)
		else:
			return AllreadyDone,0

		
		
		

class Controler:
	""" Implémentation du contrôleur de la vue utilisant la console"""
	def __init__(self, model, view):
#		self.__model = model # Ne sert pas ici, car on ne fait que des actions modèle -> vue
		self.__view = view
		
		# Connection des signaux
		model.startSignal.connect(self.__startCallback)
		model.refreshSignal.connect(self.__refreshCallback)
		model.finishSignal.connect(self.__stopCallback)
		model.NbrJobsSignal.connect(self.__NBJCallback)
	def __startCallback(self, label, nbVal):
		""" Callback pour le signal de début de progressbar."""
		self.__view.creatProgressBar(label, nbVal)
	def __refreshCallback(self, i,filename):
		""" Mise à jour de la progressbar."""
		self.__view.updateProgressBar(i,filename)
	def __stopCallback(self):
		""" Callback pour le signal de fin de splashscreen."""
		self.__view.finish()	
	def __NBJCallback(self,NbrJobs):
		""" Callback pour redefinir le nombre de job totaux."""
		self.__view.ProgressBarMax(NbrJobs)



class ControlerX:
	""" Implémentation du contrôleur. C'est lui qui lie les modèle et la(les) vue(s)."""
	def __init__(self, model, viewx):
#		self.__model = model # Ne sert pas ici, car on ne fait que des actions modèle -> vue
		self.__viewx = viewx
		# Connection des signaux
		model.startSignal.connect(self.__startCallback)
		model.refreshSignal.connect(self.__refreshCallback)
		model.finishSignal.connect(self.__stopCallback)
		model.NbrJobsSignal.connect(self.__NBJCallback)
	def __startCallback(self, label, nbVal):
		""" Callback pour le signal de début de progressbar."""
		self.__viewx.creatProgressBar(label, nbVal)
	def __refreshCallback(self, i,filename):
		""" Mise à jour de la progressbar.	"""
		self.__viewx.updateProgressBar(i,filename)
	def __stopCallback(self):
		""" ferme la fenetre. Callback pour le signal de fin de splashscreen."""
		self.__viewx.finish()
	def __NBJCallback(self,NbrJobs):
		""" Callback pour redefinir le nombre de job totaux."""
		self.__viewx.ProgressBarMax(NbrJobs)



class View:
	""" Implémentation de la vue.
	Utilisation de la console.
	"""
	def __init__(self):
		""" On initialise la vue."""
		self.__nbVal = None
	def creatProgressBar(self, label, nbVal):
		""" Création de la progressbar.		"""
		self.__nbVal = nbVal
		print label

	def ProgressBarMax(self,nbVal):
		"""re-definit le nombre maximum de la progress-bar"""
		self.__nbVal = nbVal
#		print "Modification du maximum : %i"%self.__nbVal	
		
	def updateProgressBar(self,h,filename):
		""" Mise à jour de la progressbar
		"""
		print "%5.1f %% processing  ... %s"%(100.0*(h+1)/self.__nbVal,filename)
	def finish(self):
		"""nothin in text mode"""
		pass
		
class ViewX:
	""" Implémentation de la vue comme un splashscren
	"""
	def __init__(self):
		""" On initialise la vue.
		Ici, on ne fait rien, car la progressbar sera créée au moment
		où on en aura besoin. Dans un cas réel, on initialise les widgets
		de l'interface graphique
		"""
		self.__nbVal = None
	def creatProgressBar(self, label, nbVal):
		""" Création de la progressbar.
		"""
		self.xml=gtk.glade.XML(unifiedglade,root="splash")
		self.xml.get_widget("image").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(installdir,"Splash.png")))
		self.pb=self.xml.get_widget("progress")
		self.xml.get_widget("splash").set_title(label)
		self.xml.get_widget("splash").show()
		while gtk.events_pending():gtk.main_iteration()
		self.__nbVal = nbVal
	def ProgressBarMax(self,nbVal):
		"""re-definit le nombre maximum de la progress-bar"""
		self.__nbVal = nbVal
		 	
	def updateProgressBar(self,h,filename):
		""" Mise à jour de la progressbar
		Dans le cas d'un toolkit, c'est ici qu'il faudra appeler le traitement
		des évènements.
		set the progress-bar to the given value with the given name
		@param h: current number of the file
		@type val: integer or float
		@param name: name of the current element
		@type name: string 
		@return: None"""
		if h<self.__nbVal:
			self.pb.set_fraction(float(h+1)/self.__nbVal)
		else:
			self.pb.set_fraction(1.0)
		self.pb.set_text(filename)
		while gtk.events_pending():gtk.main_iteration()
	def finish(self):
		"""destroys the interface of the splash screen"""			
		self.xml.get_widget("splash").destroy()
		while gtk.events_pending():gtk.main_iteration()		
		del self.xml
		gc.collect()


def RangeTout(repository):
	"""moves all the JPEG files to a directory named from their day and with the 
	name according to the time
	This is a MVC implementation"""
	model = ModelRangeTout()
	view = View()
	ctrl = Controler(model, view)
	viewx = ViewX()
	ctrlx = ControlerX(model, viewx)
	return model.start(repository)

def ProcessSelected(SelectedFiles):
	"""This procedure uses the MVC implementation of processSelected
	It makes a copy of all selected photos and scales them
	copy all the selected files to "selected" subdirectory, 20 per page
	"""
	print "execution %s"%SelectedFiles
	model = ModelProcessSelected()
	view = View()
	ctrl = Controler(model, view)
	viewx = ViewX()
	ctrlx = ControlerX(model, viewx)
	model.start(SelectedFiles)

def CopySelected(SelectedFiles):
	"""This procedure makes a copy of all selected photos and scales them
	copy all the selected files to "selected" subdirectory
	"""
	print "Copy %s"%SelectedFiles
	model = ModelCopySelected()
	view = View()
	ctrl = Controler(model, view)
	viewx = ViewX()
	ctrlx = ControlerX(model, viewx)
	model.start(SelectedFiles)





# # # # # # Début de la classe photo # # # # # # # # # # #

class photo:
	"""class photo that does all the operations available on photos"""
	def __init__(self,filename):
		self.filename=filename
		self.fn=os.path.join(config.DefaultRepository,self.filename)
		if not os.path.isfile(self.fn): print "Erreur, le fichier %s n'existe pas"%self.fn 

	def LoadPIL(self):
		"""Load the image"""
		self.f=Image.open(self.fn)
	
	def larg(self):
		"""width-height of a jpeg file"""
		self.taille()
		return self.x-self.y

	def taille(self):
		"""width and height of a jpeg file"""
		self.LoadPIL()
		self.x,self.y=self.f.size

	def SaveThumb(self,Thumbname,Size=160,Interpolation=1,Quality=75,Progressive=False,Optimize=False,ExifExtraction=False):
		"""save a thumbnail of the given name, with the given size and the interpollation mathode (quality) 
		resampling filters :
		NONE = 0
		NEAREST = 0
		ANTIALIAS = 1 # 3-lobed lanczos
		LINEAR = BILINEAR = 2
		CUBIC = BICUBIC = 3
		"""
		if  os.path.isfile(Thumbname):
			print "sorry, file %s exists"%Thumbname
		else:
			RawExif,comment=EXIF.process_file(open(self.fn,'rb'),0)
			if RawExif.has_key("JPEGThumbnail") and ExifExtraction:
				w=open(Thumbname,"wb")
				w.write(RawExif["JPEGThumbnail"])
				w.close()			
			else:
				self.LoadPIL()
				self.g=self.f.copy()
				self.g.thumbnail((Size,Size),Interpolation)
				self.g.save(Thumbname,quality=Quality,progressive=Progressive,optimize=Optimize)
			os.chmod(Thumbname,config.DefaultFileMode)

	
	def Rotate(self,angle=0):
		"""does a looseless rotation of the given jpeg file"""
		if os.name == 'nt' and self.f!=None: del self.f
#		self.taille()
		if angle==90:
			os.system('JPEGMEM=%i %s -ip -9 "%s"'%(self.x*self.y/100,exiftran,self.fn))	
		elif angle==270:
			os.system('JPEGMEM=%i %s -ip -2 "%s"'%(self.x*self.y/100,exiftran,self.fn))
		elif angle==180:
			os.system('JPEGMEM=%i %s -ip -1 "%s"'%(self.x*self.y/100,exiftran,self.fn))	
		else:
			print "Erreur ! il n'est pas possible de faire une rotation de ce type sans perte de donnée."

	def Trash(self):
		"""Send the file to the trash folder"""
		Trashdir=os.path.join(config.DefaultRepository,config.TrashDirectory)
		td=os.path.dirname(os.path.join(Trashdir,self.filename))
		tf=os.path.join(Trashdir,self.filename)
		if not os.path.isdir(td): makedir(td)
		shutil.move(self.fn,os.path.join(Trashdir,self.filename))
			
	def exif(self):
		"""return exif data + title from the photo"""
		clef={
			'Image Make': 'Marque',
			'Image Model': 'Modele',
			'Image DateTime': 'Heure',
			'EXIF Flash':'Flash',
			'EXIF FocalLength': 'Focale',
			'EXIF FNumber': 'Ouverture',
			'EXIF ExposureTime' :'Vitesse',
			'EXIF ISOSpeedRatings': 'Iso',
			'EXIF ExposureBiasValue': 'Bias'}

		data={}
		data["Taille"]="%.2f %s"%SmartSize(os.path.getsize(self.fn))
		
		RawExif,comment=EXIF.process_file(open(self.fn,'rb'),0)
		if comment:
			data["Titre"]=comment
		else:
			data["Titre"]=""
		self.taille()
		data["Resolution"]="%s x %s "%(self.x,self.y)
		for i in clef:
			try:
				data[clef[i]]=str(RawExif[i].printable).strip()
			except:
				data[clef[i]]=""
		return data

	def has_title(self):
		"""return true if the image is entitled"""
		RawExif,comment=EXIF.process_file(open(self.fn,'rb'),0)
		if comment:
			return True	 
		else:
			return False
	
		
	def show(self,Xsize=600,Ysize=600):
		"""return a pixbuf to shows the image in a Gtk window"""
		self.taille()			
		pixbuf = gtk.gdk.pixbuf_new_from_file(self.fn)
#		print "Taille voulue %sx%s"%(Xsize,Ysize)
		R=min(float(Xsize)/self.x,float(Ysize)/self.y)
		if R<1:
			nx=int(R*self.x)
			ny=int(R*self.y)
#			print  "Taille Obtenue  %sx%s"%(nx,ny)
			scaled_buf=pixbuf.scale_simple(nx,ny,gtkInterpolation[config.Interpolation])
		else :
			scaled_buf=pixbuf
		return scaled_buf
				
	def name(self,titre):
		"""write the title of the photo inside the description field, in the JPEG header"""	
                if os.name == 'nt' and self.f!=None: del self.f
		os.system('%s -ipc "%s"  "%s"'%(exiftran,titre,self.fn))
		
	def autorotate(self):
		"""does autorotate the image according to the EXIF tag"""
		if os.name == 'nt' and self.f!=None: del self.f
		self.taille()
		os.system('JPEGMEM=%i %s -aip "%s"'%(self.x*self.y/100,exiftran,self.fn))

	def ContrastMask(self,outfile):
		"""Ceci est un filtre de debouchage de photographies, aussi appelé masque de contraste, il permet de rattrapper une photo trop contrasté, un contre jour, ...
		Écrit par Jérôme Kieffer, avec l'aide de la liste python@aful, en particulier A. Fayolles et F. Mantegazza
		avril 2006
		necessite numarray et PIL."""
		try:
			import numarray
		except:
			raise "This filter needs the numarray library available on http://www.stsci.edu/resources/software_hardware/numarray"
		self.LoadPIL()
		x,y=self.f.size
		ImageFile.MAXBLOCK=x*y
		img_array = numarray.fromstring(self.f.tostring(),type="UInt8").astype("UInt16") 
		img_array.shape = (x, y, 3) 
		red, green, blue = img_array[:,:,0], img_array[:,:,1],img_array[:,:,2]
		desat_array = (numarray.minimum(numarray.minimum(red, green), blue) + numarray.maximum( numarray.maximum(red, green), blue))/2
		inv_desat=255-desat_array
		k=Image.fromstring("L",(x,y),inv_desat.astype("UInt8").tostring()).convert("RGB")
		S=ImageChops.screen(self.f,k)
		M=ImageChops.multiply(self.f,k)
		F=ImageChops.add(ImageChops.multiply(self.f,S),ImageChops.multiply(ImageChops.invert(self.f),M))
		F.save(os.path.join(config.DefaultRepository,outfile),quality=90,progressive=True,Optimize=True)
		os.chmod(os.path.join(config.DefaultRepository,outfile),config.DefaultFileMode)

		
# # # # # # fin de la classe photo # # # # # # # # # # #
class signature:
	def __init__(self,filename):
		"""this filter allows add a signature to an image"""
		self.sig=Image.open(filename)
		self.sig.convert("RGB")
		(self.xs,self.ys)=self.sig.size
		self.bigsig=self.sig
		#The signature file is entented to be white on a black background, this inverts the color if necessary
		if ImageStat.Stat(self.sig)._getmean()>127:
			self.sig=ImageChops.invert(self.sig)

		self.orientation=-1 #this is an impossible value
		(self.x,self.y)=(self.xs,self.ys)
		
	def mask(self,orientation=5):
		"""
		x and y are the size of the initial image
		the orientation correspond to the position on a clock :
		0 for the center
		1 or 2 upper right
		3 centered in heith right side ...."""
		if orientation==self.orientation and (self.x,self.y)==self.bigsig.size:
			#no need to change the mask
			return 
		self.orientation=orientation
		self.bigsig=Image.new("RGB", (self.x,self.y), (0,0,0)) 
		if self.x<self.xs or self.y<self.ys : 
			#the signature is larger than the image
			return 
		if self.orientation == 0:
			self.bigsig.paste(self.sig,(self.x/2-self.xs/2,self.y/2-self.ys/2,self.x/2-self.xs/2+self.xs,self.y/2-self.ys/2+self.ys))
		elif self.orientation in [1,2]:
			self.bigsig.paste(self.sig,(self.x-self.xs,0,self.x,self.ys))
		elif self.orientation == 3:
			self.bigsig.paste(self.sig,(self.x-self.xs,self.y/2-self.ys/2,self.x,self.y/2-self.ys/2+self.ys))
		elif self.orientation in [ 5,4]: 
			self.bigsig.paste(self.sig,(self.x-self.xs,self.y-self.ys,self.x,self.y))
		elif self.orientation == 6:
			self.bigsig.paste(self.sig,(self.x/2-self.xs/2,self.y-self.ys,self.x/2-self.xs/2+self.xs,self.y))
		elif self.orientation in [7,8]: 
			self.bigsig.paste(self.sig,(0,self.y-self.ys,self.xs,self.y))
		elif self.orientation == 9:
			self.bigsig.paste(self.sig,(0,self.y/2-self.ys/2,self.xs,self.y/2-self.ys/2+self.ys))
		elif self.orientation in [10,11]:
			self.bigsig.paste(self.sig,(0,0,self.xs,self.ys))
		elif self.orientation == 12:
			self.bigsig.paste(self.sig,(self.x/2-self.xs/2,0,self.x/2-self.xs/2+self.xs,self.ys))
		return
	
	def substract(self,inimage,orientation=5):
		"""apply a substraction mask on the image"""
		self.img=inimage	 
		self.x,self.y=self.img.size
		ImageFile.MAXBLOCK=self.x*self.y
		self.mask(orientation)
		k=ImageChops.difference(self.img, self.bigsig)
		return k



############################################################################################################

def makedir(filen):
		"""creates the tree structure for the file"""
		dire=os.path.dirname(filen)
		if os.path.isdir(dire):
				mkdir(filen)
		else:
				makedir(dire)
				mkdir(filen)

def mkdir(filename):
	"""create an empty directory with the given rights"""
#	config=Config()
	os.mkdir(filename)
	os.chmod(filename,config.DefaultDirMode)


def FindFile(RootDir):
	"""returns a list of the files with the given suffix in the given dir
	files=os.system('find "%s"  -iname "*.%s"'%(RootDir,suffix)).readlines()
	"""
	files=[]
#	config=Config()
	for i in config.Extensions:
		files+=parser().FindExts(RootDir,i)
	good=[]
	l=len(RootDir)+1
	for i in files: good.append(i.strip()[l:])
	good.sort()
	return good


#######################################################################################
def ScaleImage(filename,filigrane=None):
	"""common processing for one image : create a subfolder "scaled" and "thumb" : """
#	config=Config()
	rootdir=os.path.dirname(filename)
	scaledir=os.path.join(rootdir,config.ScaledImages["Suffix"])
	thumbdir=os.path.join(rootdir,config.Thumbnails["Suffix"])
	if not os.path.isdir(scaledir) : mkdir(scaledir)
	if not os.path.isdir(thumbdir) : mkdir(thumbdir)
	Img=photo(filename)
	Param=config.ScaledImages.copy()
	Param.pop("Suffix")
	Param["Thumbname"]=os.path.join(scaledir,os.path.basename(filename))[:-4]+"--%s.jpg"%config.ScaledImages["Suffix"]
	Img.SaveThumb(**Param)
	Param=config.Thumbnails.copy()
	Param.pop("Suffix")
	Param["Thumbname"]=os.path.join(thumbdir,os.path.basename(filename))[:-4]+"--%s.jpg"%config.Thumbnails["Suffix"]
	Img.SaveThumb(**Param)
	if filigrane: 
		filigrane.substract(Img.f).save(filename,quality=config.FiligraneQuality,optimize=config.FiligraneOptimize,progressive=config.FiligraneOptimize)
		os.chmod(filename,config.DefaultFileMode)






def latin1_to_ascii (unicrap):
	"""This takes a UNICODE string and replaces Latin-1 characters with
		something equivalent in 7-bit ASCII. It returns a plain ASCII string. 
		This function makes a best effort to convert Latin-1 characters into 
		ASCII equivalents. It does not just strip out the Latin-1 characters.
		All characters in the standard 7-bit ASCII range are preserved. 
		In the 8th bit range all the Latin-1 accented letters are converted 
		to unaccented equivalents. Most symbol characters are converted to 
		something meaningful. Anything not converted is deleted.
	"""
	xlate={0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
		0xc6:'Ae', 0xc7:'C',
		0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E',
		0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
		0xd0:'Th', 0xd1:'N',
		0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
		0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
		0xdd:'Y', 0xde:'th', 0xdf:'ss',
		0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
		0xe6:'ae', 0xe7:'c',
		0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e',
		0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
		0xf0:'th', 0xf1:'n',
		0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
		0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
		0xfd:'y', 0xfe:'th', 0xff:'y',
		0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
		0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
		0xa9:'{C}', 0xaa:'{^a}', 0xab:'<<', 0xac:'{not}',
		0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
		0xb1:'{+/-}', 0xb2:'{^2}', 0xb3:'{^3}', 0xb4:"'",
		0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
		0xb9:'{^1}', 0xba:'{^o}', 0xbb:'>>', 
		0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'?',
		0xd7:'*', 0xf7:'/'
		}

	r=[]
	for i in unicrap:
		if xlate.has_key(ord(i)):
			r.append(xlate[ord(i)])
		elif ord(i) >= 0x80:
			pass
		else:
			r.append(str(i))
	return "".join(r)

def SmartSize(size):
	"""print the size of files in a pretty way"""
	unit="o"
	fsize=float(size)
	if len(str(size))>3:
		size/=1024
		fsize/=1024.0
		unit="ko"
		if len(str(size))>3:
			size=size/1024
			fsize/=1024.0
			unit="Mo"
			if len(str(size))>3:
				size=size/1024
				fsize/=1024.0
				unit="Go"
	return fsize,unit


	
#############################################################################
class parser:
	"""this class searches all the jpeg files""" 
	def __init__(self):
		self.imagelist=[]
				
	def OneDir(self,curent):
		""" append all the imagesfiles to the list, then goes recursively to the subdirectories"""
		ls=os.listdir(curent)
		subdirs=[]
		for i in ls:
			a=os.path.join(curent,i)
			if	os.path.isdir(a):
				self.OneDir(a)
			if  os.path.isfile(a):
				if i[(-len(self.suffix)):].lower()==self.suffix:
					self.imagelist.append(os.path.join(curent,i))
	def FindExts(self,root,suffix):
		self.root=root
		self.suffix=suffix
		self.OneDir(self.root)
		return self.imagelist




	
if __name__ == "__main__":
	####################################################################################	
	#Definition de la classe des variables de configuration globales : Borg"""
	config.DefaultRepository=os.path.abspath(sys.argv[1])
	print config.DefaultRepository
	RangeTout(sys.argv[1])
