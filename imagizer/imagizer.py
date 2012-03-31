#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2011,  Jérôme Kieffer <kieffer@terre-adelie.org>
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
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20111016"
__license__ = "GPL"
import os, sys, shutil, time, re, gc, logging
logger = logging.getLogger("imagizer.imagizer")


try:
    import Image #IGNORE:F0401
except:
    raise ImportError("Selector needs PIL: Python Imaging Library\n PIL is available from http://www.pythonware.com/products/pil/")
try:
    import pygtk ; pygtk.require('2.0') #IGNORE:F0401
    import gtk, gtk.gdk                 #IGNORE:E0601
    import gtk.glade as GTKglade        #IGNORE:E0611
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

unifiedglade = os.path.join(installdir, "selector.glade")
from signals import Signal
from encoding import unicode2ascii
from config import Config
config = Config()
import fileutils
from photo import Photo, Signature

def gtkFlush():
    """
    Flush all graphics stuff (outside main loop)
    """
    while gtk.events_pending(): #IGNORE:E1101
        gtk.main_iteration()    #IGNORE:E1101



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
    """
    Implemantation MVC de la procedure processSelected
    """
    def __init__(self):
        """
        """
        self.__label = "Un moment..."
        self.startSignal = Signal()
        self.refreshSignal = Signal()
        self.finishSignal = Signal()
        self.NbrJobsSignal = Signal()


    def start(self, lstFiles):
        """ 
        Lance les calculs pour "processSelected"
        i.e. 
        
        @param lstFiles: list of files to process
        """

        def splitIntoPages(pathday, globalCount):
            """Split a directory (pathday) into pages of 20 images (see config.NbrPerPage)
            
            @param pathday:
            @param globalCount:
            @return: the number of images for current page   
            """
            logger.debug("In splitIntoPages %s %s", pathday, globalCount)
            files = []
            for  i in os.listdir(pathday):
                if os.path.splitext(i)[1] in config.Extensions:files.append(i)
            files.sort()
            if  len(files) > config.NbrPerPage:
                pages = 1 + (len(files) - 1) / config.NbrPerPage
                for i in range(1, pages + 1):
                    folder = os.path.join(pathday, config.PagePrefix + str(i))
                    fileutils.mkdir(folder)
                for j in range(len(files)):
                    i = 1 + (j) / config.NbrPerPage
                    filename = os.path.join(pathday, config.PagePrefix + str(i), files[j])
                    self.refreshSignal.emit(globalCount, files[j])
                    globalCount += 1
                    shutil.move(os.path.join(pathday, files[j]), filename)
                    scaleImage(filename, filigrane)
            else:
                for j in files:
                    self.refreshSignal.emit(globalCount, j)
                    globalCount += 1
                    scaleImage(os.path.join(pathday, j), filigrane)
            return globalCount

        def arrangeOneFile(dirname, filename):
            """
            @param dirname:
            @param filename:
            """
            try:
                timetuple = time.strptime(filename[:19], "%Y-%m-%d_%Hh%Mm%S")
                suffix = filename[19:]
            except ValueError:
                try:
                    timetuple = time.strptime(filename[:11], "%Y-%m-%d_")
                    suffix = filename[11:]
                except ValueError:
                    logger.warning("Unable to handle such file: %s" % filename)
                    return
            daydir = os.path.join(SelectedDir, time.strftime("%Y-%m-%d", timetuple))
            os.mkdir(daydir)
            shutil.move(os.path.join(dirname, filename), os.path.join(daydir, time.strftime("%Hh%Mm%S", timetuple) + suffix))

        logger.debug("In Process Selected" + " ".join(lstFiles))
        self.startSignal.emit(self.__label, max(1, len(lstFiles)))
        if config.Filigrane:
            filigrane = Signature(config.FiligraneSource)
        else:
            filigrane = None

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        self.refreshSignal.emit(-1, "copie des fichiers existants")
        if not os.path.isdir(SelectedDir):
            fileutils.mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
        AlsoProcess = 0
        for day in os.listdir(SelectedDir):
#if SingleDir : revert to a foldered structure
            DayOrFile = os.path.join(SelectedDir, day)
            if os.path.isfile(DayOrFile):
                arrangeOneFile(SelectedDir, day)
                AlsoProcess += 1
#end SingleDir normalization
            elif os.path.isdir(DayOrFile):
                if day in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]:
                    fileutils.recursive_delete(DayOrFile)
                elif day.find(config.PagePrefix) == 0: #subpages in SIngleDir mode that need to be flatten
                    for File in os.listdir(DayOrFile):
                        if     os.path.isfile(os.path.join(DayOrFile, File)):
                            arrangeOneFile(DayOrFile, File)
                            AlsoProcess += 1
#                        elif os.path.isdir(os.path.join(DayOrFile,File)) and File in [config.ScaledImages["Suffix"],config.Thumbnails["Suffix"]]:
#                            recursive_delete(os.path.join(DayOrFile,File))
                    fileutils.recursive_delete(DayOrFile)
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
        for File in lstFiles:
            dest = os.path.join(SelectedDir, File)
            src = os.path.join(config.DefaultRepository, File)
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                fileutils.makedir(destdir)
            if not os.path.exists(dest):
                logger.info("copie de %s " % File)
                shutil.copy(src, dest)
                try:
                    os.chmod(dest, config.DefaultFileMode)
                except OSError:
                    logger.warning("Unable to chmod %s" % dest)
                AlsoProcess += 1
            else :
                logger.warning("%s existe déja" % dest)
        if AlsoProcess > 0:self.NbrJobsSignal.emit(AlsoProcess)
######copy the comments of the directory to the Selected directory 
        AlreadyDone = []
        for File in lstFiles:
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
        logger.debug("in ModelProcessSelected, SelectedDir= %s", SelectedDir)
        dirs = [ i for i in os.listdir(SelectedDir) if os.path.isdir(os.path.join(SelectedDir, i))]
        dirs.sort()
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
                            logger.info("Unable to handle dir: %s\t file: %s" , day, filename)
                            continue
                    src = os.path.join(daydir, filename)
                    dst = os.path.join(SelectedDir, time.strftime("%Y-%m-%d_%Hh%Mm%S", timetuple) + suffix)
                    shutil.move(src, dst)
                fileutils.recursive_delete(daydir)
            splitIntoPages(SelectedDir, 0)
        else: #Multidir
            logger.debug("in Multidir, dirs= " + " ".join(dirs))
            globalCount = 0
            for day in dirs:
                globalCount = splitIntoPages(os.path.join(SelectedDir, day), globalCount)

        self.finishSignal.emit()


class ModelCopySelected:
    """
    Implemantation MVC de la procedure copySelected
    """
    def __init__(self):
        """
        """
        self.__label = "Un moment..."
        self.startSignal = Signal()
        self.refreshSignal = Signal()
        self.finishSignal = Signal()
        self.NbrJobsSignal = Signal()

    def start(self, lstFiles):
        """ 
        Lance les calculs
        
        @param lstFiles: list of files to process
        """
        self.startSignal.emit(self.__label, max(1, len(lstFiles)))
        if config.Filigrane:
            filigrane = Signature(config.FiligraneSource)
        else:
            filigrane = None

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        self.refreshSignal.emit(-1, "copie des fichiers existants")
        if not os.path.isdir(SelectedDir):     fileutils.mkdir(SelectedDir)
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
        globalCount = 0
        for File in lstFiles:
            dest = os.path.join(SelectedDir, File)
            src = os.path.join(config.DefaultRepository, File)
            destdir = os.path.dirname(dest)
            self.refreshSignal.emit(globalCount, File)
            globalCount += 1
            if not os.path.isdir(destdir):
                fileutils.makedir(destdir)
            if not os.path.exists(dest):
                if filigrane:
                    image = Image.open(src)
                    filigrane.substract(image).save(dest, quality=config.FiligraneQuality, optimize=config.FiligraneOptimize, progressive=config.FiligraneOptimize)
                else:
                    shutil.copy(src, dest)
                try:
                    os.chmod(dest, config.DefaultFileMode)
                except OSError:
                    logger.warning("In ModelCopySelected: unable to chmod %s", dest)
            else :
                logger.info("In ModelCopySelected: %s already exists", dest)
######copy the comments of the directory to the Selected directory 
        AlreadyDone = []
        for File in lstFiles:
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
    """Implemantation MVC de la procedure rangeTout
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


    def start(self, rootDir):
        """ Lance les calculs
        
        @param rootDir: top level directory to start processing
        """
        config.DefaultRepository = rootDir
        AllJpegs = fileutils.findFiles(rootDir)
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
            myPhoto = Photo(i, dontCache=True)
            data = myPhoto.readExif()
            try:
                datei, heurei = data["Heure"].split()
                date = re.sub(":", "-", datei)
                heurej = re.sub(":", "h", heurei, 1)
                model = data["Modele"].split(",")[-1]
                heure = unicode2ascii("%s-%s.jpg" % (re.sub(":", "m", heurej, 1), re.sub("/", "", re.sub(" ", "_", model))))
            except ValueError:
                date = time.strftime("%Y-%m-%d", time.gmtime(os.path.getctime(os.path.join(rootDir, i))))
                heure = unicode2ascii("%s-%s.jpg" % (time.strftime("%Hh%Mm%S", time.gmtime(os.path.getctime(os.path.join(rootDir, i)))), re.sub("/", "-", re.sub(" ", "_", os.path.splitext(i)[0]))))
            if not (os.path.isdir(os.path.join(rootDir, date))) :
                fileutils.mkdir(os.path.join(rootDir, date))
#            strImageFile = os.path.join(rootDir, date, heure)
            ToProcess = os.path.join(date, heure)
            bSkipFile = False
            for strImageFile in fileutils.list_files_in_named_dir(rootDir, date, heure):
                logger.warning("%s -x-> %s", i, strImageFile)
                existing = Photo(strImageFile, dontCache=True)
                try:
                    existing.readExif()
                    originalName = existing.exif["Exif.Photo.UserComment"]
                except:
                    logger.error("in ModelRangeTout: reading Exif for %s", i)
                else:
                    if "human_value" in dir(originalName):
                        originalName = originalName.human_value
                    if os.path.basename(originalName) == os.path.basename(i):
                        logger.info("File already in repository, leaving as it is")
                        bSkipFile = True
                        continue #to next file, i.e. leave the existing one
            if bSkipFile:
                continue
            else:
                strImageFile = os.path.join(rootDir, date, heure)
            if os.path.isfile(strImageFile):
                s = 0
                for j in os.listdir(os.path.join(rootDir, date)):
                    if j.find(heure[:-4]) == 0:s += 1
                ToProcess = os.path.join(date, heure[:-4] + "-%s.jpg" % s)
                strImageFile = os.path.join(rootDir, ToProcess)
            shutil.move(os.path.join(rootDir, i), strImageFile)
            try:
                os.chown(strImageFile, uid, gid)
                os.chmod(strImageFile, config.DefaultFileMode)
            except OSError:
                logger.warning("in ModelRangeTout: unable to chown ot chmod  %s" , strImageFile)
            myPhoto = Photo(strImageFile, dontCache=True)
#            Save the old image name in exif tag
            myPhoto.storeOriginalName(i)

            if config.AutoRotate:
                myPhoto.autorotate()
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
    """ 
    Implementation of controleur via X11. 
    C'est lui qui lie les modèle et la(les) vue(s).
    """
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
        logger.info(label)

    def ProgressBarMax(self, nbVal):
        """re-definit le nombre maximum de la progress-bar"""
        self.__nbVal = nbVal

    def updateProgressBar(self, h, filename):
        """ Mise à jour de la progressbar
        """
        logger.info("%5.1f %% processing  ... %s" , 100.0 * (h + 1) / self.__nbVal, filename)

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
        gtkFlush()
        self.__nbVal = nbVal

    def ProgressBarMax(self, nbVal):
        """re-definit le nombre maximum de la progress-bar"""
        self.__nbVal = nbVal

    def updateProgressBar(self, h, filename):
        """ 
        Update the progress-bar to the given value with the given filename writen on it

        fr: Mise à jour de la progressbar
        fr: Dans le cas d'un toolkit, c'est ici qu'il faudra appeler le traitement
        fr:des évènements.
        
        @param h: current number of the file
        @type h: integer or float
        @param filename: name of the current element
        @type filename: string 
        @return: None
        """
        if h < self.__nbVal:
            self.pb.set_fraction(float(h + 1) / self.__nbVal)
        else:
            self.pb.set_fraction(1.0)
        self.pb.set_text(filename)
        gtkFlush()

    def finish(self):
        """destroys the interface of the splash screen"""
        self.xml.get_widget("splash").destroy()
        gtkFlush()
        del self.xml
        gc.collect()


def rangeTout(repository, bUseX=True):
    """moves all the JPEG files to a directory named from their day and with the 
    name according to the time
    This is a MVC implementation
    
    @param repository: the name of the starting repository
    @type repository: string
    @param bUseX: set to False to disable the use of the graphical splash screen
    @type bUseX: boolean
    """
    model = ModelRangeTout()
    view = View()
    Controler(model, view)
    if bUseX:
        viewx = ViewX()
        ControlerX(model, viewx)
    return model.start(repository)


def processSelected(lstSelectedFiles):
    """
    This procedure uses the MVC implementation of processSelected
    It makes a copy of all selected photos and scales them
    copy all the selected files to "selected" subdirectory, 20 per page

    @param  lstSelectedFiles: list of selected files to process
    @return: None 
    """
    logger.info("Process selected of " + " ".join(lstSelectedFiles))
    model = ModelProcessSelected()
    view = View()
    Controler(model, view)
    viewx = ViewX()
    ControlerX(model, viewx)
    model.start(lstSelectedFiles)


def copySelected(lstSelectedFiles):
    """
    This procedure makes a copy of all selected photos and scales them
    copy all the selected files to "selected" subdirectory

    @param  lstSelectedFiles: list of selected files to process
    @return: None 
    """
    logger.info("Copy Selected of " + " ".join(lstSelectedFiles))
    model = ModelCopySelected()
    view = View()
    Controler(model, view)
    viewx = ViewX()
    ControlerX(model, viewx)
    model.start(lstSelectedFiles)



#######################################################################################
def scaleImage(filename, filigrane=None):
    """Common processing for one image : 
    - create a subfolder "scaled" and "thumb"
    - populate it
    
    @param filename: path to the file
    @param filigrane: None or a Signature instance (see imagizer.photo.Signature) 
     """
    rootdir = os.path.dirname(filename)
    scaledir = os.path.join(rootdir, config.ScaledImages["Suffix"])
    thumbdir = os.path.join(rootdir, config.Thumbnails["Suffix"])
    fileutils.mkdir(scaledir)
    fileutils.mkdir(thumbdir)
    photo = Photo(filename, dontCache=True)
    param = config.ScaledImages.copy()
    param.pop("Suffix")
    param["strThumbFile"] = os.path.join(scaledir, os.path.basename(filename))[:-4] + "--%s.jpg" % config.ScaledImages["Suffix"]
    photo.saveThumb(**param)
    param = config.Thumbnails.copy()
    param.pop("Suffix")
    param["strThumbFile"] = os.path.join(thumbdir, os.path.basename(filename))[:-4] + "--%s.jpg" % config.Thumbnails["Suffix"]
    photo.saveThumb(**param)
    if filigrane is not None:
        filigrane.substract(photo.pil).save(filename, quality=config.FiligraneQuality, optimize=config.FiligraneOptimize, progressive=config.FiligraneOptimize)
        try:
            os.chmod(filename, config.DefaultFileMode)
        except OSError:
            logger.warning("in scaleImage: Unable to chmod %s" % filename)


def timer_pass():
    """
    Dummy function that releases the gil for 1ms
    """
    time.sleep(1e-3)
    return True



############################################################################################################



if __name__ == "__main__":
    ####################################################################################    
    #Definition de la classe des variables de configuration globales : Borg"""
    config.DefaultRepository = os.path.abspath(sys.argv[1])
    logger.info("%s", config.DefaultRepository)
    rangeTout(sys.argv[1])
