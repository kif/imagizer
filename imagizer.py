#!/usr/bin/python
# -*- coding: Latin1 -*-
# Programmé par Jérome Kieffer : kieffer@terre-adelie.org
# Conception : Jérôme KIEFFER et  Mickael Profeta
# Avec la participation de Isabelle Letard
# Licence GPL v2
# Bibliotheque contenant tout le prolog de selector basée sur le design Pattern MVC.

import os,sys,string,shutil,time,re,gc

try:
	import Image,ImageFile
except:
	raise "Selector needs PIL: Python Imagin Library\n PIL is available from http://www.pythonware.com/products/pil/"

try:
	import pygtk ; pygtk.require('2.0')
	import gtk,gtk.glade
except:
	raise "Selector needs pygtk and glade-2 available from http://www.pygtk.org/"


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
from signals import Signal
import EXIF

#Variables globales qui sont des CONSTANTES !
unifiedglade=os.path.join(installdir,"selector.glade")
gtkInterpolation=[gtk.gdk.INTERP_NEAREST,gtk.gdk.INTERP_TILES,gtk.gdk.INTERP_BILINEAR,gtk.gdk.INTERP_HYPER]	
#gtk.gdk.INTERP_NEAREST	Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
#gtk.gdk.INTERP_TILES	This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
#gtk.gdk.INTERP_BILINEAR	Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
#gtk.gdk.INTERP_HYPER	This is the slowest and highest quality reconstruction function. It is derived from the hyperbolic filters in Wolberg's "Digital Image Warping", and is formally defined as the hyperbolic-filter sampling the ideal hyperbolic-filter interpolated image (the filter is designed to be idempotent for 1:1 pixel mapping).



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
		
	def start(self,List):
		""" Lance les calculs
		"""
		self.startSignal.emit(self.__label, len(List))
#reste a implementer.
#		avcmt.setbar(0,"copie des fichiers existants")
		config=Config()
		self.refreshSignal.emit(-1,"copie des fichiers existants")
		if not os.path.isdir(config.SelectedDirectory): 	mkdir(config.SelectedDirectory)
#####first of all : copy the subfolders into the day folder to help mixing the files
		for day in os.listdir(config.SelectedDirectory):
			for File in os.listdir(os.path.join(config.SelectedDirectory,day)):
				if File.find(config.PagePrefix)==0:
					if os.path.isdir(os.path.join(config.SelectedDirectory,day,File)):
						for ImageFile in os.listdir(os.path.join(config.SelectedDirectory,day,File)):
							src=os.path.join(config.SelectedDirectory,day,File,ImageFile)
							dst=os.path.join(config.SelectedDirectory,day,ImageFile)
							if os.path.isfile(src) and not os.path.exists(dst):
								shutil.move(src,dst)
							if (os.path.isdir(src)) and (os.path.split(src)[1] in [scaled,thumb]):
								shutil.rmtree(src)
							
#######then copy the selected files to their folders###########################		
		for File in List:
			#avcmt.setbar(float(List.index(File))/len(List),"1 -> %s"%File)
			#print float(List.index(File))/len(List)
			dest=os.path.join(config.SelectedDirectory,File)
			src=os.path.join(config.DefaultRepository,File)
			destdir=os.path.dirname(dest)
			if not os.path.isdir(destdir): makedir(destdir)
			if not os.path.exists(dest):
				print "copie de %s "%(File)
				shutil.copy(src,dest)
				os.chmod(dest,config.DefaultFileMode)
			else :
				print "%s existe déja"%(dest)
########finaly recreate the structure with pages########################
		dirs=os.listdir(config.SelectedDirectory)
		dirs.sort()
		GlobalCount=0
		for day in dirs:
			#avcmt.setbar(float(dirs.index(day))/len(dirs),day)
			pathday=os.path.join(config.SelectedDirectory,day)
			files=[]
			for  i in os.listdir(pathday):
				if i[-4:]==".jpg":files.append(i)
			files.sort()
			if  len(files)>config.NbrPerPage:
				pages=1+(len(files)-1)/config.NbrPerPage
				for i in range(1, pages+1):
					folder=os.path.join(pathday,config.PagePrefix+str(i))
					if not os.path.isdir(folder): mkdir(folder)
				for j in range(len(files)):
					i=1+(j)/config.NbrPerPage
					filename=os.path.join(pathday,PagePrefix+str(i),files[j])
					self.refreshSignal.emit(GlobalCount,files[j])
					GlobalCount+=1
#					avcmt.setbar(float(j)/len(files),PagePrefix+str(i)+"/"+files[j])
					shutil.move(os.path.join(pathday,files[j]),filename)
					ScaleImage(filename)
			else:
				for j in files:
					self.refreshSignal.emit(GlobalCount,j)
					GlobalCount+=1
					ScaleImage(os.path.join(pathday,j))
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
	

	def start(self,RootDir):
		""" Lance les calculs
		"""
		config=Config()
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
	def __startCallback(self, label, nbVal):
		""" Callback pour le signal de début de progressbar."""
		self.__view.creatProgressBar(label, nbVal)
	def __refreshCallback(self, i,filename):
		""" Mise à jour de la progressbar."""
		self.__view.updateProgressBar(i,filename)
	def __stopCallback(self):
		""" Callback pour le signal de fin de splashscreen."""
		self.__view.finish()	



class ControlerX:
	""" Implémentation du contrôleur. C'est lui qui lie les modèle et la(les) vue(s)."""
	def __init__(self, model, viewx):
#		self.__model = model # Ne sert pas ici, car on ne fait que des actions modèle -> vue
		self.__viewx = viewx
		# Connection des signaux
		model.startSignal.connect(self.__startCallback)
		model.refreshSignal.connect(self.__refreshCallback)
		model.finishSignal.connect(self.__stopCallback)
	def __startCallback(self, label, nbVal):
		""" Callback pour le signal de début de progressbar."""
		self.__viewx.creatProgressBar(label, nbVal)
	def __refreshCallback(self, i,filename):
		""" Mise à jour de la progressbar.	"""
		self.__viewx.updateProgressBar(i,filename)
	def __stopCallback(self):
		""" ferme la fenetre. Callback pour le signal de fin de splashscreen."""
		self.__viewx.finish()



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
		self.pb.set_fraction(float(h+1)/self.__nbVal)
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
		self.Interpolation=1
		self.DefaultFileMode=int(self.DefaultMode,8)
		self.DefaultDirMode=self.DefaultFileMode+3145 #73 = +111 en octal ... 3145 +s mode octal
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
			elif j=="DefaultFileMode".lower():
				self.DefaultFileMode=int(i[1],8)
				self.DefaultDirMode=self.DefaultFileMode+3145 #73 = +111 en octal ... 3145 +s mode octal	
			elif j=="Extensions".lower(): self.Extensions=i[1].split()
			elif j=="DefaultRepository".lower():self.DefaultRepository=i[1]
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
		print "Size on the images on the Screen:%s"%self.ScreenSize
		print "Downsampling quality [0..3]:\t %s"%self.Interpolation
		print "Page prefix:\t\t\t %s"%self.PagePrefix
		print "Number of images per page:\t %s"%self.NbrPerPage
		print "Trash directory:\t\t %s"%self.TrashDirectory
		print "Selected directory:\t\t %s"%self.SelectedDirectory
		print "Selected images file:\t\t %s"%self.Selected_save
		print "Use Exif for Auto-Rotate:\t %s"%self.AutoRotate
		print "Default mode for files (octal):\t %o"%self.DefaultFileMode
		print "JPEG extensions:\t\t %s"%self.Extensions
		print "Default photo repository:\t %s"%self.DefaultRepository
		print "**** Scaled images configuration ****"
		print "Size:\t\t\t\t %s"%self.ScaledImages["Size"]
		print "Suffix:\t\t\t\t %s"%self.ScaledImages["Suffix"]
		print "Interpolation Quality:\t\t %s"%self.ScaledImages["Interpolation"]
		print "Progressive JPEG:\t\t %s"%self.ScaledImages["Progressive"]
		print "Optimized JPEG:\t\t\t %s"%self.ScaledImages["Optimize"]
		print "JPEG Quality:\t\t\t %s %%"%self.ScaledImages["Quality"]
		print "Allow Exif extraction:\t\t %s"%self.ScaledImages["ExifExtraction"]
		print "**** Thumbnail images configuration ****"
		print "Size:\t\t\t\t %s"%self.Thumbnails["Size"]
		print "Suffix:\t\t\t\t %s"%self.Thumbnails["Suffix"]
		print "Interpolation Quality:\t\t %s"%self.Thumbnails["Interpolation"]
		print "Progressive JPEG:\t\t %s"%self.Thumbnails["Progressive"]
		print "Optimized JPEG:\t\t\t %s"%self.Thumbnails["Optimize"]
		print "JPEG Quality:\t\t\t %s %%"%self.Thumbnails["Quality"]
		print "Allow Exif extraction:\t\t %s"%self.Thumbnails["ExifExtraction"]

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
		for i in ["ScaledImages","Thumbnails"]:
			txt+="[%s]\n"%i
			j=eval("self.%s"%i)
			txt+="#%s size\nSize: %s \n\n"%(i,j["Size"])
			txt+="#%s suffix\nSuffix: %s \n\n"%(i,j["Suffix"])
			txt+="#%s downsampling quality [0=nearest, 1=bilinear, 2=bicubic, 3=antialias] )\nInterpolation: %s \n\n"%(i,j["Interpolation"])
			txt+="#%s progressive JPEG files\nProgressive: %s \n\n"%(i,j["Progressive"])
			txt+="#%s optimized JPEG (2 pass encoding)\nOptimize: %s \n\n"%(i,j["Optimize"])
			txt+="#%s quality (in percent)\nQuality: %s \n\n"%(i,j["Quality"])
			txt+="#%s image can be obtained by Exif extraction ?\nExifExtraction: %s \n\n"%(i,j["ExifExtraction"])
		w=open(filename,"w")
		w.write(txt)
		w.close()


# # # # # # Début de la classe photo # # # # # # # # # # #

class photo:
	"""class photo that does all the operations available on photos"""
	def __init__(self,filename):
		self.config=Config()
		self.filename=filename
		self.fn=os.path.join(self.config.DefaultRepository,self.filename)
		if not os.path.isfile(self.fn): print "Erreur, le fichier %s n'existe pas"%self.fn 

	def LoadPIL(self):
		"""Load the image"""
		self.f=Image.open(self.fn)
	
	def larg(self):
		"""width-height of a jpeg file"""
		x,y=self.taille()
		return x-y

	def taille(self):
		"""width and height of a jpeg file"""
		self.LoadPIL()
		self.x,self.y=self.f.size
		return self.x,self.y	

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
				self.f.thumbnail((Size,Size),Interpolation)
				self.f.save(Thumbname,quality=Quality,progressive=Progressive,optimize=Optimize)
			os.chmod(Thumbname,self.config.DefaultFileMode)

	
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
		config=Config()	
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
		data["Taille"]="%s ko"%(os.path.getsize(self.fn)/1024)
		
		RawExif,comment=EXIF.process_file(open(self.fn,'rb'),0)
		if comment:
			data["Titre"]=comment
		else:
			data["Titre"]=""
		x,y=self.taille()
		data["Resolution"]="%s x %s "%(x,y)
		for i in clef:
			try:
				data[clef[i]]=str(RawExif[i].printable).strip()
			except:
				data[clef[i]]=""
		return data
		
	def show(self,Xsize=600,Ysize=600):
		"""return a pixbuf to shows the image in a Gtk window"""
		self.x,self.y=self.taille()			
		pixbuf = gtk.gdk.pixbuf_new_from_file(self.fn)
		if self.x>Xsize:
			RX=1.0*Xsize/self.x
		else :
			RX=1
		if self.y>Ysize:
			RY=1.0*Ysize/self.y
		else :
			RY=1	
		R=min(RY,RX)
		if R<1:
			nx=int(R*self.x)
			ny=int(R*self.y)
			scaled_buf=pixbuf.scale_simple(nx,ny,gtkInterpolation[self.config.Interpolation])
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
		import ImageChops
		try:
			import numarray
		except:
			raise "This filter needs the numarray library available on http://www.stsci.edu/resources/software_hardware/numarray"
		config=Config()	
		self.LoadPIL()
		x,y=self.f.size
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

		
# # # # # # fin de la classe photo # # # # # # # # # # #





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
	config=Config()
	os.mkdir(filename)
	os.chmod(filename,config.DefaultDirMode)


def FindFile(RootDir):
	"""returns a list of the files with the given suffix in the given dir
	files=os.system('find "%s"  -iname "*.%s"'%(RootDir,suffix)).readlines()
	"""
	files=[]
	config=Config()
	for i in config.Extensions:
		files+=parser().FindExts(RootDir,i)
	good=[]
	l=len(RootDir)+1
	for i in files: good.append(i.strip()[l:])
	return good


#######################################################################################
def ScaleImage(filename):
	"""common processing for one image : create a subfolder "scaled" and "thumb" : """
	print "Génération des vignettes pour %s "%filename
	config=Config()
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
	config=Config()
	config.load(ConfFile)
	config.DefaultRepository=os.path.abspath(sys.argv[1])
	print config.DefaultRepository
	RangeTout(sys.argv[1])
