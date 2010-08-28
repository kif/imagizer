#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2010,  Jérôme Kieffer <kieffer@terre-adelie.org>
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
General library used by selector and generator.
It handles images, progress bars and configuration file.
"""

import os, sys, shutil, time, re, gc

from Exiftran import Exiftran

try:
    import Image, ImageStat, ImageChops, ImageFile
except:
    raise ImportError("Selector needs PIL: Python Imaging Library\n PIL is available from http://www.pythonware.com/products/pil/")
try:
    import pygtk ; pygtk.require('2.0')
    import gtk
    import gtk.glade as GTKglade
except ImportError:
    raise ImportError("Selector needs pygtk and glade-2 available from http://www.pygtk.org/")
#Variables globales qui sont des CONSTANTES !
gtkInterpolation = [gtk.gdk.INTERP_NEAREST, gtk.gdk.INTERP_TILES, gtk.gdk.INTERP_BILINEAR, gtk.gdk.INTERP_HYPER]
#gtk.gdk.INTERP_NEAREST    Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
#gtk.gdk.INTERP_TILES    This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
#gtk.gdk.INTERP_BILINEAR    Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
#gtk.gdk.INTERP_HYPER    This is the slowest and highest quality reconstruction function. It is derived from the hyperbolic filters in Wolberg's "Digital Image Warping", and is formally defined as the hyperbolic-filter sampling the ideal hyperbolic-filter interpolated image (the filter is designed to be idempotent for 1:1 pixel mapping).


#here we detect the OS runnng the program so that we can call exftran in the right way
installdir = os.path.dirname(__file__)
if os.name == 'nt': #sys.platform == 'win32':
#    exiftran = os.path.join(installdir, "exiftran.exe ")
    ConfFile = [os.path.join(os.getenv("ALLUSERSPROFILE"), "imagizer.conf"), os.path.join(os.getenv("USERPROFILE"), "imagizer.conf"), "imagizer.conf"]
elif os.name == 'posix':
#    MaxJPEGMem = 100000 # OK up to 10 Mpix
#    exiftran = "JPEGMEM=%i %s " % (MaxJPEGMem, os.path.join(installdir, "exiftran "))
    ConfFile = ["/etc/imagizer.conf", os.path.join(os.getenv("HOME"), ".imagizer"), ".imagizer"]
#else:
#    raise OSError("Your platform does not seem to be an Unix nor a M$ Windows.\nI am sorry but the exiftran binary is necessary to run selector, and exiftran is probably not available for you plateform. If you have exiftran installed, please contact the developper to correct that bug, kieffer at terre-adelie dot org")

#sys.path.append(installdir)    
unifiedglade = os.path.join(installdir, "selector.glade")
from signals import Signal
from config import Config
config = Config()
config.load(ConfFile)
if config.ImageCache > 1:
    import imagecache
    imageCache = imagecache.ImageCache(maxSize=config.ImageCache)
else:
    imageCache = None
import pyexiv2



#class Model:
#    """ Implémentation de l'applicatif
#    """
#    def __init__(self, label):
#        """
#        """
#        self.__label = label
#        self.startSignal = Signal()
#        self.refreshSignal = Signal()
#        
#    def start(self):
#        """ Lance les calculs
#        """
#        self.startSignal.emit(self.__label, NBVALUES)
#        for i in xrange(NBVALUES):
#            time.sleep(0.5)
#            
#            # On lève le signal de rafraichissement des vues éventuelles
#            # Note qu'ici on ne sait absolument pas si quelque chose s'affiche ou non
#            # ni de quelle façon c'est affiché.
#            self.refreshSignal.emit(i)



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
    def start(self, List):
        """ Lance les calculs
        """

        def SplitIntoPages(pathday, GlobalCount):
            """Split a directory (pathday) into pages of 20 images"""
            files = []
            for  i in os.listdir(pathday):
                if os.path.splitext(i)[1] in config.Extensions:files.append(i)
            files.sort()
            if  len(files) > config.NbrPerPage:
                pages = 1 + (len(files) - 1) / config.NbrPerPage
                for i in range(1, pages + 1):
                    folder = os.path.join(pathday, config.PagePrefix + str(i))
                    if not os.path.isdir(folder): mkdir(folder)
                for j in range(len(files)):
                    i = 1 + (j) / config.NbrPerPage
                    filename = os.path.join(pathday, config.PagePrefix + str(i), files[j])
                    self.refreshSignal.emit(GlobalCount, files[j])
                    GlobalCount += 1
                    shutil.move(os.path.join(pathday, files[j]), filename)
                    ScaleImage(filename, filigrane)
            else:
                for j in files:
                    self.refreshSignal.emit(GlobalCount, j)
                    GlobalCount += 1
                    ScaleImage(os.path.join(pathday, j), filigrane)
            return GlobalCount
        def ArrangeOneFile(dirname, filename):
            try:
                timetuple = time.strptime(filename[:19], "%Y-%m-%d_%Hh%Mm%S")
                suffix = filename[19:]
            except ValueError:
                try:
                    timetuple = time.strptime(filename[:11], "%Y-%m-%d_")
                    suffix = filename[11:]
                except ValueError:
                    print("Unable to handle such file: %s" % filename)
                    return
            daydir = os.path.join(SelectedDir, time.strftime("%Y-%m-%d", timetuple))
            if not os.path.isdir(daydir):
                os.mkdir(daydir)
            shutil.move(os.path.join(dirname, filename), os.path.join(daydir, time.strftime("%Hh%Mm%S", timetuple) + suffix))

        self.startSignal.emit(self.__label, max(1, len(List)))
        if config.Filigrane:
            filigrane = signature(config.FiligraneSource)
        else:
            filigrane = None

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        self.refreshSignal.emit(-1, "copie des fichiers existants")
        if not os.path.isdir(SelectedDir):     mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
        AlsoProcess = 0
        for day in os.listdir(SelectedDir):
#if SingleDir : revert to a foldered structure
            DayOrFile = os.path.join(SelectedDir, day)
            if os.path.isfile(DayOrFile):
                ArrangeOneFile(SelectedDir, day)
                AlsoProcess += 1
#end SingleDir normalization
            elif os.path.isdir(DayOrFile):
                if day in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]:
                    recursive_delete(DayOrFile)
                elif day.find(config.PagePrefix) == 0: #subpages in SIngleDir mode that need to be flatten
                    for File in os.listdir(DayOrFile):
                        if     os.path.isfile(os.path.join(DayOrFile, File)):
                            ArrangeOneFile(DayOrFile, File)
                            AlsoProcess += 1
#                        elif os.path.isdir(os.path.join(DayOrFile,File)) and File in [config.ScaledImages["Suffix"],config.Thumbnails["Suffix"]]:
#                            recursive_delete(os.path.join(DayOrFile,File))
                    recursive_delete(DayOrFile)
                else:
                    for File in os.listdir(DayOrFile):
                        if File.find(config.PagePrefix) == 0:
                            if os.path.isdir(os.path.join(SelectedDir, day, File)):
                                for strImageFile in os.listdir(os.path.join(SelectedDir, day, File)):
                                    src = os.path.join(SelectedDir, day, File, strImageFile)
                                    dst = os.path.join(SelectedDir, day, strImageFile)
                                    if os.path.isfile(src) and not os.path.exists(dst):
                                        shutil.move(src, dst)
                                        AlsoProcess += 1
                                    if (os.path.isdir(src)) and (os.path.split(src)[1] in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]):
                                        shutil.rmtree(src)
                        else:
                            if os.path.splitext(File)[1] in config.Extensions:
                                AlsoProcess += 1

#######then copy the selected files to their folders###########################        
        for File in List:
            dest = os.path.join(SelectedDir, File)
            src = os.path.join(config.DefaultRepository, File)
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir): makedir(destdir)
            if not os.path.exists(dest):
                print "copie de %s " % (File)
                shutil.copy(src, dest)
                try:
                    os.chmod(dest, config.DefaultFileMode)
                except OSError:
                    print("Warning: unable to chmod %s" % dest)
                AlsoProcess += 1
            else :
                print "%s existe déja" % (dest)
        if AlsoProcess > 0:self.NbrJobsSignal.emit(AlsoProcess)
######copy the comments of the directory to the Selected directory 
        AlreadyDone = []
        for File in List:
            directory = os.path.split(File)[0]
            if directory in AlreadyDone:
                continue
            else:
                AlreadyDone.append(directory)
                dst = os.path.join(SelectedDir, directory, config.CommentFile)
                src = os.path.join(config.DefaultRepository, directory, config.CommentFile)
                if os.path.isfile(src):
                    shutil.copy(src, dst)

########finaly recreate the structure with pages or make a single page ########################
        dirs = os.listdir(SelectedDir)
        dirs.sort()
#        print "config.ExportSingleDir = "+str(config.ExportSingleDir)
        if config.ExportSingleDir: #SingleDir
            #first move all files to the root
            for day in dirs:
                daydir = os.path.join(SelectedDir, day)
                for filename in os.listdir(daydir):
                    try:
                        timetuple = time.strptime(day[:10] + "_" + filename[:8], "%Y-%m-%d_%Hh%Mm%S")
                        suffix = filename[8:]
                    except ValueError:
                        try:
                            timetuple = time.strptime(day[:10], "%Y-%m-%d")
                            suffix = filename
                        except ValueError:
                            print ("Unable to handle dir: %s\t file: %s" % (day, filename))
                            continue
                    src = os.path.join(daydir, filename)
                    dst = os.path.join(SelectedDir, time.strftime("%Y-%m-%d_%Hh%Mm%S", timetuple) + suffix)
                    shutil.move(src, dst)
                recursive_delete(daydir)
            SplitIntoPages(SelectedDir, 0)
        else: #Multidir
            GlobalCount = 0
            for day in dirs:
                GlobalCount = SplitIntoPages(os.path.join(SelectedDir, day), GlobalCount)

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
    def start(self, List):
        """ Lance les calculs
        """
        self.startSignal.emit(self.__label, max(1, len(List)))
        if config.Filigrane:
            filigrane = signature(config.FiligraneSource)
        else:
            filigrane = None

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        self.refreshSignal.emit(-1, "copie des fichiers existants")
        if not os.path.isdir(SelectedDir):     mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
        for day in os.listdir(SelectedDir):
            for File in os.listdir(os.path.join(SelectedDir, day)):
                if File.find(config.PagePrefix) == 0:
                    if os.path.isdir(os.path.join(SelectedDir, day, File)):
                        for strImageFile in os.listdir(os.path.join(SelectedDir, day, File)):
                            src = os.path.join(SelectedDir, day, File, strImageFile)
                            dst = os.path.join(SelectedDir, day, strImageFile)
                            if os.path.isfile(src) and not os.path.exists(dst):
                                shutil.move(src, dst)
                            if (os.path.isdir(src)) and (os.path.split(src)[1] in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]):
                                shutil.rmtree(src)

#######then copy the selected files to their folders###########################        
        GlobalCount = 0
        for File in List:
            dest = os.path.join(SelectedDir, File)
            src = os.path.join(config.DefaultRepository, File)
            destdir = os.path.dirname(dest)
            self.refreshSignal.emit(GlobalCount, File)
            GlobalCount += 1
            if not os.path.isdir(destdir): makedir(destdir)
            if not os.path.exists(dest):
                if filigrane:
                    Img = Image.open(src)
                    filigrane.substract(Img).save(dest, quality=config.FiligraneQuality, optimize=config.FiligraneOptimize, progressive=config.FiligraneOptimize)
                else:
                    shutil.copy(src, dest)
                try:
                    os.chmod(dest, config.DefaultFileMode)
                except OSError:
                    print("Warning: unable to chmod %s" % dest)
            else :
                print "%s existe déja" % (dest)
######copy the comments of the directory to the Selected directory 
        AlreadyDone = []
        for File in List:
            directory = os.path.split(File)[0]
            if directory in AlreadyDone:
                continue
            else:
                AlreadyDone.append(directory)
                dst = os.path.join(SelectedDir, directory, config.CommentFile)
                src = os.path.join(config.DefaultRepository, directory, config.CommentFile)
                if os.path.isfile(src):
                    shutil.copy(src, dst)
        self.finishSignal.emit()




class ModelRangeTout:
    """Implemantation MVC de la procedure RangeTout
    moves all the JPEG files to a directory named from 
    their day and with the name according to the time"""

    def __init__(self):
        """
        """
        self.__label = "Initial renaming of new images .... "
        self.startSignal = Signal()
        self.refreshSignal = Signal()
        self.finishSignal = Signal()
        self.NbrJobsSignal = Signal()


    def start(self, RootDir):
        """ Lance les calculs
        """
        config.DefaultRepository = RootDir
        AllJpegs = FindFile(RootDir)
        AllFilesToProcess = []
        AllreadyDone = []
        NewFiles = []
        uid = os.getuid()
        gid = os.getgid()
        for i in AllJpegs:
            if i.find(config.TrashDirectory) == 0: continue
            if i.find(config.SelectedDirectory) == 0: continue
            try:
                a = int(i[:4])
                m = int(i[5:7])
                j = int(i[8:10])
                if (a >= 0000) and (m <= 12) and (j <= 31) and (i[4] in ["-", "_", "."]) and (i[7] in ["-", "_"]):
                    AllreadyDone.append(i)
                else:
                    AllFilesToProcess.append(i)
            except ValueError:
                AllFilesToProcess.append(i)
        AllFilesToProcess.sort()
        NumFiles = len(AllFilesToProcess)
        self.startSignal.emit(self.__label, NumFiles)
        for h in range(NumFiles):
            i = AllFilesToProcess[h]
            self.refreshSignal.emit(h, i)
            myPhoto = photo(i)
            try:
                imageCache[i] = myPhoto
            except:
                pass
            data = myPhoto.readExif()
            try:
                datei, heurei = data["Heure"].split()
                date = re.sub(":", "-", datei)
                heurej = re.sub(":", "h", heurei, 1)
                model = data["Modele"].split(",")[-1]
                heure = unicode_to_ascii("%s-%s.jpg" % (re.sub(":", "m", heurej, 1), re.sub("/", "", re.sub(" ", "_", model))))
            except ValueError:
                date = time.strftime("%Y-%m-%d", time.gmtime(os.path.getctime(os.path.join(RootDir, i))))
                heure = unicode_to_ascii("%s-%s.jpg" % (time.strftime("%Hh%Mm%S", time.gmtime(os.path.getctime(os.path.join(RootDir, i)))), re.sub("/", "-", re.sub(" ", "_", os.path.splitext(i)[0]))))
            if not (os.path.isdir(os.path.join(RootDir, date))) : mkdir(os.path.join(RootDir, date))
            strImageFile = os.path.join(RootDir, date, heure)
            ToProcess = os.path.join(date, heure)
            if os.path.isfile(strImageFile):
                print "Problème ... %s existe déja " % i
                s = 0
                for j in os.listdir(os.path.join(RootDir, date)):
                    if j.find(heure[:-4]) == 0:s += 1
                ToProcess = os.path.join(date, heure[:-4] + "-%s.jpg" % s)
                strImageFile = os.path.join(RootDir, ToProcess)
            shutil.move(os.path.join(RootDir, i), strImageFile)
            try:
                os.chown(strImageFile, uid, gid)
                os.chmod(strImageFile, config.DefaultFileMode)
            except OSError:
                print "Warning: unable to chown ot chmod  %s" % strImageFile
            myPhoto = photo(strImageFile)
            if config.AutoRotate:
                myPhoto.autorotate()
#Set the new images in cache for further display 
            try:
                imageCache[ ToProcess ] = myPhoto
            except:
                pass
##################################################
            AllreadyDone.append(ToProcess)
            NewFiles.append(ToProcess)
        AllreadyDone.sort()
        self.finishSignal.emit()

        if len(NewFiles) > 0:
            FirstImage = min(NewFiles)
            return AllreadyDone, AllreadyDone.index(FirstImage)
        else:
            return AllreadyDone, 0

class Controler:
    """ Implémentation du contrôleur de la vue utilisant la console"""
    def __init__(self, model, view):
#        self.__model = model # Ne sert pas ici, car on ne fait que des actions modèle -> vue
        self.__view = view

        # Connection des signaux
        model.startSignal.connect(self.__startCallback)
        model.refreshSignal.connect(self.__refreshCallback)
        model.finishSignal.connect(self.__stopCallback)
        model.NbrJobsSignal.connect(self.__NBJCallback)
    def __startCallback(self, label, nbVal):
        """ Callback pour le signal de début de progressbar."""
        self.__view.creatProgressBar(label, nbVal)
    def __refreshCallback(self, i, filename):
        """ Mise à jour de la progressbar."""
        self.__view.updateProgressBar(i, filename)
    def __stopCallback(self):
        """ Callback pour le signal de fin de splashscreen."""
        self.__view.finish()
    def __NBJCallback(self, NbrJobs):
        """ Callback pour redefinir le nombre de job totaux."""
        self.__view.ProgressBarMax(NbrJobs)



class ControlerX:
    """ Implémentation du contrôleur. C'est lui qui lie les modèle et la(les) vue(s)."""
    def __init__(self, model, viewx):
#        self.__model = model # Ne sert pas ici, car on ne fait que des actions modèle -> vue
        self.__viewx = viewx
        # Connection des signaux
        model.startSignal.connect(self.__startCallback)
        model.refreshSignal.connect(self.__refreshCallback)
        model.finishSignal.connect(self.__stopCallback)
        model.NbrJobsSignal.connect(self.__NBJCallback)
    def __startCallback(self, label, nbVal):
        """ Callback pour le signal de début de progressbar."""
        self.__viewx.creatProgressBar(label, nbVal)
    def __refreshCallback(self, i, filename):
        """ Mise à jour de la progressbar.    """
        self.__viewx.updateProgressBar(i, filename)
    def __stopCallback(self):
        """ ferme la fenetre. Callback pour le signal de fin de splashscreen."""
        self.__viewx.finish()
    def __NBJCallback(self, NbrJobs):
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
        """ Création de la progressbar.        """
        self.__nbVal = nbVal
        print label

    def ProgressBarMax(self, nbVal):
        """re-definit le nombre maximum de la progress-bar"""
        self.__nbVal = nbVal
#        print "Modification du maximum : %i"%self.__nbVal    

    def updateProgressBar(self, h, filename):
        """ Mise à jour de la progressbar
        """
        print "%5.1f %% processing  ... %s" % (100.0 * (h + 1) / self.__nbVal, filename)
    def finish(self):
        """nothin in text mode"""
        pass

class ViewX:
    """ 
    Implementation of the view as a splashscren
    """
    def __init__(self):
        """ 
        Initialization of the view in the constructor 

        Ici, on ne fait rien, car la progressbar sera créée au moment
        où on en aura besoin. Dans un cas réel, on initialise les widgets
        de l'interface graphique
        """
        self.__nbVal = None
        self.xml = None
        self.pb = None

    def creatProgressBar(self, label, nbVal):
        """ 
        Creation of a progress bar.
        """
        self.xml = GTKglade.XML(unifiedglade, root="splash")
        self.xml.get_widget("image").set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(installdir, "Splash.png")))
        self.pb = self.xml.get_widget("progress")
        self.xml.get_widget("splash").set_title(label)
        self.xml.get_widget("splash").show()
        while gtk.events_pending():gtk.main_iteration()
        self.__nbVal = nbVal
    def ProgressBarMax(self, nbVal):
        """re-definit le nombre maximum de la progress-bar"""
        self.__nbVal = nbVal

    def updateProgressBar(self, h, filename):
        """ Mise à jour de la progressbar
        Dans le cas d'un toolkit, c'est ici qu'il faudra appeler le traitement
        des évènements.
        set the progress-bar to the given value with the given name
        @param h: current number of the file
        @type val: integer or float
        @param name: name of the current element
        @type name: string 
        @return: None"""
        if h < self.__nbVal:
            self.pb.set_fraction(float(h + 1) / self.__nbVal)
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
    Controler(model, view)
    viewx = ViewX()
    ControlerX(model, viewx)
    return model.start(repository)

def ProcessSelected(SelectedFiles):
    """This procedure uses the MVC implementation of processSelected
    It makes a copy of all selected photos and scales them
    copy all the selected files to "selected" subdirectory, 20 per page
    """
    print "execution %s" % SelectedFiles
    model = ModelProcessSelected()
    view = View()
    Controler(model, view)
    viewx = ViewX()
    ControlerX(model, viewx)
    model.start(SelectedFiles)

def CopySelected(SelectedFiles):
    """This procedure makes a copy of all selected photos and scales them
    copy all the selected files to "selected" subdirectory
    """
    print "Copy %s" % SelectedFiles
    model = ModelCopySelected()
    view = View()
    Controler(model, view)
    viewx = ViewX()
    ControlerX(model, viewx)
    model.start(SelectedFiles)




##########################################################
# # # # # # Début de la classe photo # # # # # # # # # # #
##########################################################
class photo:
    """class photo that does all the operations available on photos"""
    def __init__(self, filename):
        self.filename = filename
        self.fn = os.path.join(config.DefaultRepository, self.filename)
        self.metadata = None
        self.pixelsX = None
        self.pixelsY = None
        self.pil = None
        self.exif = None
        if not os.path.isfile(self.fn):
            print "Erreur, le fichier %s n'existe pas" % self.fn
        self.bImageCache = (imageCache is not None)
        self.scaledPixbuffer = None
        self.orientation = 1

    def LoadPIL(self):
        """Load the image"""
        self.pil = Image.open(self.fn)

    def larg(self):
        """width-height of a jpeg file"""
        self.taille()
        return self.pixelsX - self.pixelsY

    def taille(self):
        """width and height of a jpeg file"""
        if self.pixelsX == None and self.pixelsY == None:
            self.LoadPIL()
            self.pixelsX, self.pixelsY = self.pil.size

    def SaveThumb(self, Thumbname, Size=160, Interpolation=1, Quality=75, Progressive=False, Optimize=False, ExifExtraction=False):
        """save a thumbnail of the given name, with the given size and the interpolation methode (quality) 
        resampling filters :
        NONE = 0
        NEAREST = 0
        ANTIALIAS = 1 # 3-lobed lanczos
        LINEAR = BILINEAR = 2
        CUBIC = BICUBIC = 3
        """
        if  os.path.isfile(Thumbname):
            print "sorry, file %s exists" % Thumbname
        else:
            if self.exif is None:
                self.exif = pyexiv2.Image(self.fn)
                self.exif.readMetadata()
            extract = False
            print "process file %s exists" % Thumbname
            if ExifExtraction:
                try:
                    self.exif.dumpThumbnailToFile(Thumbname[:-4])
                    extract = True
                except (OSError, IOError):
                    extract = False
            if not extract:
#                print "on essaie avec PIL"
                if self.pil is None:
                    self.LoadPIL()
                copyOfImage = self.pil.copy()
                copyOfImage.thumbnail((Size, Size), Interpolation)
                copyOfImage.save(Thumbname, quality=Quality, progressive=Progressive, optimize=Optimize)
            try:
                os.chmod(Thumbname, config.DefaultFileMode)
            except OSError:
                print("Warning: unable to chmod %s" % Thumbname)


    def Rotate(self, angle=0):
        """does a looseless rotation of the given jpeg file"""
        if os.name == 'nt' and self.pil != None:
            del self.pil
        self.taille()
        x = self.pixelsX
        y = self.pixelsY
        if config.DEBUG:
            print("Before rotation %i, x=%i, y=%i, scaledX=%i, scaledY=%i" % (angle, x, y, self.scaledPixbuffer.get_width(), self.scaledPixbuffer.get_height()))

        if angle == 90:
            if imageCache is not None:
                Exiftran.rotate90(self.fn)
#                os.system('%s -ip -9 "%s" &' % (exiftran, self.fn))
                newPixbuffer = self.scaledPixbuffer.rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)
                self.pixelsX = y
                self.pixelsY = x
                self.metadata["Resolution"] = "%i x % i" % (y, x)
            else:
                Exiftran.rotate90(self.fn)
#                os.system('%s -ip -9 "%s" ' % (exiftran, self.fn))
                self.pixelsX = None
                self.pixelsY = None
        elif angle == 270:
            if imageCache is not None:
                Exiftran.rotate270(self.fn)
#                os.system('%s -ip -2 "%s" &' % (exiftran, self.fn))
                newPixbuffer = self.scaledPixbuffer.rotate_simple(gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE)
                self.pixelsX = y
                self.pixelsY = x
                self.metadata["Resolution"] = "%i x % i" % (y, x)
            else:
                Exiftran.rotate270(self.fn)
#                os.system('%s -ip -2 "%s" ' % (exiftran, self.fn))
                self.pixelsX = None
                self.pixelsY = None
        elif angle == 180:
            if imageCache is not None:
                Exiftran.rotate180(self.fn)
#                os.system('%s -ip -1 "%s" &' % (exiftran, self.fn))
                newPixbuffer = self.scaledPixbuffer.rotate_simple(gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN)
            else:
                Exiftran.rotate180(self.fn)
#                os.system('%s -ip -1 "%s" ' % (exiftran, self.fn))
                self.pixelsX = None
                self.pixelsY = None
        else:
            print "Erreur ! il n'est pas possible de faire une rotation de ce type sans perte de donnée."
        if imageCache is not None:
            self.scaledPixbuffer = newPixbuffer
        if config.DEBUG:
            print("After   rotation %i, x=%i, y=%i, scaledX=%i, scaledY=%i" % (angle, self.pixelsX, self.pixelsY, self.scaledPixbuffer.get_width(), self.scaledPixbuffer.get_height()))


    def RemoveFromCache(self):
        """remove the curent image from the Cache .... for various reasons"""
        if imageCache is not None:
            if self.filename in imageCache.ordered:
                imageCache.imageDict.pop(self.filename)
                index = imageCache.ordered.index(self.filename)
                imageCache.ordered.pop(index)
                imageCache.size -= 1


    def Trash(self):
        """Send the file to the trash folder"""
        self.RemoveFromCache()
        Trashdir = os.path.join(config.DefaultRepository, config.TrashDirectory)
        td = os.path.dirname(os.path.join(Trashdir, self.filename))
        if not os.path.isdir(td): makedir(td)
        shutil.move(self.fn, os.path.join(Trashdir, self.filename))


    def readExif(self):
        """return exif data + title from the photo"""
        clef = {'Exif.Image.Make':'Marque',
 'Exif.Image.Model':'Modele',
 'Exif.Photo.DateTimeOriginal':'Heure',
 'Exif.Photo.ExposureTime':'Vitesse',
 'Exif.Photo.FNumber':'Ouverture',
# 'Exif.Photo.DateTimeOriginal':'Heure2',
 'Exif.Photo.ExposureBiasValue':'Bias',
 'Exif.Photo.Flash':'Flash',
 'Exif.Photo.FocalLength':'Focale',
 'Exif.Photo.ISOSpeedRatings':'Iso' ,
# 'Exif.Image.Orientation':'Orientation'
}

        if self.metadata is None:
            self.metadata = {}
            self.metadata["Taille"] = "%.2f %s" % SmartSize(os.path.getsize(self.fn))
            self.exif = pyexiv2.Image(self.fn)
            self.exif.readMetadata()
            self.metadata["Titre"] = self.exif.getComment()
            if self.pixelsX and self.pixelsY:
                self.metadata["Resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            else:
                try:
                    self.pixelsX = self.exif["Exif.Photo.PixelXDimension"]
                    self.pixelsY = self.exif["Exif.Photo.PixelYDimension"]
                except IndexError:
                    self.taille()
                self.metadata["Resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            if "Exif.Image.Orientation" in self.exif.exifKeys():
                self.orientation = self.exif["Exif.Image.Orientation"]
            for key in clef:
                try:
                    self.metadata[clef[key]] = self.exif.interpretedExifValue(key).decode(config.Coding)
                except:
                    self.metadata[clef[key]] = u""
        return self.metadata.copy()


    def has_title(self):
        """return true if the image is entitled"""
        if self.metadata == None:
            self.readExif()
        if  self.metadata["Titre"]:
            return True
        else:
            return False


    def show(self, Xsize=600, Ysize=600):
        """return a pixbuf to shows the image in a Gtk window"""
        scaled_buf = None
        if Xsize > config.ImageWidth :
            config.ImageWidth = Xsize
        if Ysize > config.ImageHeight:
            config.ImageHeight = Ysize
        self.taille()

#        Prepare the big image to be put in cache
        Rbig = min(float(config.ImageWidth) / self.pixelsX, float(config.ImageHeight) / self.pixelsY)
        if Rbig < 1:
            nxBig = int(round(Rbig * self.pixelsX))
            nyBig = int(round(Rbig * self.pixelsY))
        else:
            nxBig = self.pixelsX
            nyBig = self.pixelsY

        R = min(float(Xsize) / self.pixelsX, float(Ysize) / self.pixelsY)
        if R < 1:
            nx = int(round(R * self.pixelsX))
            ny = int(round(R * self.pixelsY))
        else:
            nx = self.pixelsX
            ny = self.pixelsY

        if self.scaledPixbuffer is None:
            pixbuf = gtk.gdk.pixbuf_new_from_file(self.fn)
#            Put in Cache the "BIG" image
            if Rbig < 1:
                self.scaledPixbuffer = pixbuf.scale_simple(nxBig, nyBig, gtkInterpolation[config.Interpolation])
            else :
                self.scaledPixbuffer = pixbuf
            if config.DEBUG:
                    print("Sucessfully cached  %s, size (%i,%i)" % (self.filename, nxBig, nyBig))
        if (self.scaledPixbuffer.get_width() == nx) and (self.scaledPixbuffer.get_height() == ny):
            scaled_buf = self.scaledPixbuffer
            if config.DEBUG:
                print("Sucessfully fetched %s from cache, directly with the right size." % (self.filename))
        else:
            if config.DEBUG:
                print("%s pixmap in buffer but not with the right shape: nx=%i,\tny=%i,\tw=%i,h=%i" % (self.filename, nx, ny, self.scaledPixbuffer.get_width(), self.scaledPixbuffer.get_height()))
            scaled_buf = self.scaledPixbuffer.scale_simple(nx, ny, gtkInterpolation[config.Interpolation])
        return scaled_buf

    def name(self, titre):
        """write the title of the photo inside the description field, in the JPEG header"""
        if os.name == 'nt' and self.pil != None:
            self.pil = None
        self.metadata["Titre"] = titre
        self.exif.setComment(titre)
        self.exif.writeMetadata()


    def autorotate(self):
        """does autorotate the image according to the EXIF tag"""
        if os.name == 'nt' and self.pil is not None:
            del self.pil

        self.readExif()
        if self.orientation != 1:
            Exiftran.autorotate(self.fn)
#            os.system('%s -aip "%s" &' % (exiftran, self.fn))
            if self.orientation > 4:
                self.pixelsX = self.exif["Exif.Photo.PixelYDimension"]
                self.pixelsY = self.exif["Exif.Photo.PixelXDimension"]
                self.metadata["Resolution"] = "%s x %s " % (self.pixelsX, self.pixelsY)
            self.orientation = 1


    def ContrastMask(self, outfile):
        """Ceci est un filtre de debouchage de photographies, aussi appelé masque de contraste, il permet de rattrapper une photo trop contrasté, un contre jour, ...
        Écrit par Jérôme Kieffer, avec l'aide de la liste python@aful, en particulier A. Fayolles et F. Mantegazza
        avril 2006
        necessite numpy et PIL."""
        try:
            import numpy
        except:
            raise ImportError("This filter needs the numpy library available on https://sourceforge.net/projects/numpy/files/")
        self.LoadPIL()
        x, y = self.pil.size
        ImageFile.MAXBLOCK = x * y
        img_array = numpy.fromstring(self.pil.tostring(), dtype="UInt8").astype("UInt16")
        img_array.shape = (y, x, 3)
        red, green, blue = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        desat_array = (numpy.minimum(numpy.minimum(red, green), blue) + numpy.maximum(numpy.maximum(red, green), blue)) / 2
        inv_desat = 255 - desat_array
        k = Image.fromarray(inv_desat, "L").convert("RGB")
        S = ImageChops.screen(self.pil, k)
        M = ImageChops.multiply(self.pil, k)
        F = ImageChops.add(ImageChops.multiply(self.pil, S), ImageChops.multiply(ImageChops.invert(self.pil), M))
        F.save(os.path.join(config.DefaultRepository, outfile), quality=90, progressive=True, Optimize=True)
        try:
            os.chmod(os.path.join(config.DefaultRepository, outfile), config.DefaultFileMode)
        except:
            print("Warning: unable to chmod %s" % outfile)


########################################################        
# # # # # # fin de la classe photo # # # # # # # # # # #
########################################################

class signature:
    def __init__(self, filename):
        """
        this filter allows add a signature to an image
        """
        self.img = None
        self.sig = Image.open(filename)
        self.sig.convert("RGB")
        (self.xs, self.ys) = self.sig.size
        self.bigsig = self.sig
        #The signature file is entented to be white on a black background, this inverts the color if necessary
        if ImageStat.Stat(self.sig)._getmean() > 127:
            self.sig = ImageChops.invert(self.sig)

        self.orientation = -1 #this is an impossible value
        (self.x, self.y) = (self.xs, self.ys)

    def mask(self, orientation=5):
        """
        x and y are the size of the initial image
        the orientation correspond to the position on a clock :
        0 for the center
        1 or 2 upper right
        3 centered in heith right side ...."""
        if orientation == self.orientation and (self.x, self.y) == self.bigsig.size:
            #no need to change the mask
            return
        self.orientation = orientation
        self.bigsig = Image.new("RGB", (self.x, self.y), (0, 0, 0))
        if self.x < self.xs or self.y < self.ys :
            #the signature is larger than the image
            return
        if self.orientation == 0:
            self.bigsig.paste(self.sig, (self.x / 2 - self.xs / 2, self.y / 2 - self.ys / 2, self.x / 2 - self.xs / 2 + self.xs, self.y / 2 - self.ys / 2 + self.ys))
        elif self.orientation in [1, 2]:
            self.bigsig.paste(self.sig, (self.x - self.xs, 0, self.x, self.ys))
        elif self.orientation == 3:
            self.bigsig.paste(self.sig, (self.x - self.xs, self.y / 2 - self.ys / 2, self.x, self.y / 2 - self.ys / 2 + self.ys))
        elif self.orientation in [ 5, 4]:
            self.bigsig.paste(self.sig, (self.x - self.xs, self.y - self.ys, self.x, self.y))
        elif self.orientation == 6:
            self.bigsig.paste(self.sig, (self.x / 2 - self.xs / 2, self.y - self.ys, self.x / 2 - self.xs / 2 + self.xs, self.y))
        elif self.orientation in [7, 8]:
            self.bigsig.paste(self.sig, (0, self.y - self.ys, self.xs, self.y))
        elif self.orientation == 9:
            self.bigsig.paste(self.sig, (0, self.y / 2 - self.ys / 2, self.xs, self.y / 2 - self.ys / 2 + self.ys))
        elif self.orientation in [10, 11]:
            self.bigsig.paste(self.sig, (0, 0, self.xs, self.ys))
        elif self.orientation == 12:
            self.bigsig.paste(self.sig, (self.x / 2 - self.xs / 2, 0, self.x / 2 - self.xs / 2 + self.xs, self.ys))
        return

    def substract(self, inimage, orientation=5):
        """apply a substraction mask on the image"""
        self.img = inimage
        self.x, self.y = self.img.size
        ImageFile.MAXBLOCK = self.x * self.y
        self.mask(orientation)
        k = ImageChops.difference(self.img, self.bigsig)
        return k



############################################################################################################

def makedir(filen):
    """creates the tree structure for the file"""
    dire = os.path.dirname(filen)
    if os.path.isdir(dire):
        mkdir(filen)
    else:
        makedir(dire)
        mkdir(filen)

def mkdir(filename):
    """create an empty directory with the given rights"""
#    config=Config()
    os.mkdir(filename)
    try:
        os.chmod(filename, config.DefaultDirMode)
    except OSError:
        print("Warning: unable to chmod %s" % filename)

def FindFile(RootDir):
    """returns a list of the files with the given suffix in the given dir
    files=os.system('find "%s"  -iname "*.%s"'%(RootDir,suffix)).readlines()
    """
    files = []
#    config=Config()
    for i in config.Extensions:
        files += parser().FindExts(RootDir, i)
    good = []
    l = len(RootDir) + 1
    for i in files: good.append(i.strip()[l:])
    good.sort()
    return good


#######################################################################################
def ScaleImage(filename, filigrane=None):
    """common processing for one image : create a subfolder "scaled" and "thumb" : """
#    config=Config()
    rootdir = os.path.dirname(filename)
    scaledir = os.path.join(rootdir, config.ScaledImages["Suffix"])
    thumbdir = os.path.join(rootdir, config.Thumbnails["Suffix"])
    if not os.path.isdir(scaledir) : mkdir(scaledir)
    if not os.path.isdir(thumbdir) : mkdir(thumbdir)
    Img = photo(filename)
    Param = config.ScaledImages.copy()
    Param.pop("Suffix")
    Param["Thumbname"] = os.path.join(scaledir, os.path.basename(filename))[:-4] + "--%s.jpg" % config.ScaledImages["Suffix"]
    Img.SaveThumb(**Param)
    Param = config.Thumbnails.copy()
    Param.pop("Suffix")
    Param["Thumbname"] = os.path.join(thumbdir, os.path.basename(filename))[:-4] + "--%s.jpg" % config.Thumbnails["Suffix"]
    Img.SaveThumb(**Param)
    if filigrane:
        filigrane.substract(Img.f).save(filename, quality=config.FiligraneQuality, optimize=config.FiligraneOptimize, progressive=config.FiligraneOptimize)
        try:
            os.chmod(filename, config.DefaultFileMode)
        except OSError:
            print("Warning: unable to chmod %s" % filename)

def unicode_to_ascii(unicrap):
    """
    This takes a UNICODE string and replaces unicode characters with
    something equivalent in 7-bit ASCII. It returns a plain ASCII string. 
    This function makes a best effort to convert unicode characters into 
    ASCII equivalents. It does not just strip out the Latin-1 characters.
    All characters in the standard 7-bit ASCII range are preserved. 
    In the 8th bit range all the Latin-1 accented letters are converted 
    to unaccented equivalents. Most symbol characters are converted to 
    something meaningful. Anything not converted is deleted.
    """
    xlate = {0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
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

    r = []
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
    unit = "o"
    fsize = float(size)
    if len(str(size)) > 3:
        size /= 1024
        fsize /= 1024.0
        unit = "ko"
        if len(str(size)) > 3:
            size = size / 1024
            fsize /= 1024.0
            unit = "Mo"
            if len(str(size)) > 3:
                size = size / 1024
                fsize /= 1024.0
                unit = "Go"
    return fsize, unit


################################################################################
# We should refactorize this with os.walk !!!
################################################################################
class parser:
    """this class searches all the jpeg files"""
    def __init__(self):
        self.imagelist = []
        self.root = None
        self.suffix = None

    def OneDir(self, curent):
        """ append all the imagesfiles to the list, then goes recursively to the subdirectories"""
        ls = os.listdir(curent)
        for i in ls:
            a = os.path.join(curent, i)
            if    os.path.isdir(a):
                self.OneDir(a)
            if  os.path.isfile(a):
                if i[(-len(self.suffix)):].lower() == self.suffix:
                    self.imagelist.append(os.path.join(curent, i))
    def FindExts(self, root, suffix):
        self.root = root
        self.suffix = suffix
        self.OneDir(self.root)
        return self.imagelist


def recursive_delete(dirname):
    files = os.listdir(dirname)
    for filename in files:
        path = os.path.join (dirname, filename)
        if os.path.isdir(path):
            recursive_delete(path)
        else:
            print 'Removing file: "%s"' % path
            os.remove(path)

    print 'Removing directory:', dirname
    os.rmdir(dirname)




if __name__ == "__main__":
    ####################################################################################    
    #Definition de la classe des variables de configuration globales : Borg"""
    config.DefaultRepository = os.path.abspath(sys.argv[1])
    print config.DefaultRepository
    RangeTout(sys.argv[1])
