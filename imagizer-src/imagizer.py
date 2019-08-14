#!/usr/bin/env python
# coding: utf-8
#******************************************************************************\
# *
# * Copyright (C) 2006 - 2011,  Jérôme Kieffer <kieffer@terre-adelie.org>
# * Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
# * Licence GPL v2
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# *
#*****************************************************************************/
from __future__ import with_statement, division, print_function, absolute_import
__doc__ = """General library used by selector and generator.
It handles images, progress bars and configuration file.
"""
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "21/07/2019"
__license__ = "GPL"
import os
import shutil
import time
import re
import logging
import glob
import threading
logger = logging.getLogger("imagizer.imagizer")

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        logger.error("""Selector needs PIL: Python Imaging Library or pillow""")
        raise error


from .encoding import unicode2ascii
from .config import config
from . import fileutils
from .photo import Photo, Signature


class DummySignal(object):
    def emit(self, *arg, **kwarg):
        pass


class ThreadedProcessing(threading.Thread):
    """Abstract Thread class with lock and

    moves all the JPEG files to a directory named from
    their day and with the name according to the time"""
    sem = threading.Semaphore()
    def __init__(self, updated_signal=None, finished_signal=None):
        """
        Constructor
        """
        threading.Thread.__init__(self)
        self.updated_signal = updated_signal or DummySignal()
        self.finished_signal = finished_signal or DummySignal()
        self.dummy = finished_signal is None
        self.result = None

    def run(self):
        raise NotImplementedError("Abstract method to be overwritten")


class RangeTout(ThreadedProcessing):
    """Implemantation de range_tout

    moves all the JPEG files to a directory named from
    their day and with the name according to the time"""

    def __init__(self, rootdir=None, updated_signal=None, finished_signal=None):
        """Constructor"""
        ThreadedProcessing.__init__(self, updated_signal, finished_signal)
        self.rootdir = rootdir

    def run(self):
        """ Lance les calculs (utilisable dans un thread a part...

        @return: 2tuple containing the list of all images and the start-index
        @rtype: (list,integer)
        """
        self.updated_signal.emit("range tout", 0, 1)
        config.DefaultRepository = self.rootdir
        trashDir = os.path.join(self.rootdir, config.TrashDirectory)
        all_files = fileutils.findFiles(self.rootdir, config.Extensions +
                                        config.RawExtensions)
        files_to_process = []
        processed_files = []
        new_files = []
        uid = os.getuid()
        gid = os.getgid()
        for i in all_files:
            if i.find(config.TrashDirectory) == 0: continue
            if i.find(config.SelectedDirectory) == 0: continue
            try:
                a = int(i[:4])
                m = int(i[5:7])
                j = int(i[8:10])
                if (a >= 0000) and (m <= 12) and \
                    (j <= 31) and (i[4] in ["-", "_", "."]) and \
                        (i[7] in ["-", "_"]):
                    processed_files.append(i)
                else:
                    files_to_process.append(i)
            except ValueError:
                files_to_process.append(i)
        files_to_process.sort()
        number_of_files = len(files_to_process)
        self.updated_signal.emit("range tout", 0, number_of_files)
        for idx, fname in enumerate(files_to_process):
            self.updated_signal.emit(fname, idx, number_of_files)
            photo = Photo(fname, dontCache=True)
            data = photo.readExif()
            try:
                datei, heurei = data["time"].split()
                date = re.sub(":", "-", unicode2ascii(datei))
                heurej = re.sub(":", "h", heurei, 1)
                model = data["model"].split(",")[-1]
                heure = unicode2ascii("%s-%s" % (re.sub(":", "m", heurej, 1),
                                                 re.sub("/", "", re.sub(" ", "_", model))))
            except ValueError:
                date = time.strftime("%Y-%m-%d", time.gmtime(os.path.getctime(os.path.join(self.rootdir, fname))))
                heure = unicode2ascii("%s-%s" % (time.strftime("%Hh%Mm%S",
                                                                time.gmtime(os.path.getctime(os.path.join(self.rootdir, fname)))),
                                                 re.sub("/", "-", re.sub(" ", "_", os.path.splitext(fname)[0]))))
            if not (os.path.isdir(os.path.join(self.rootdir, date))):
                fileutils.mkdir(os.path.join(self.rootdir, date))
            heure_we = heure + photo.ext  # Hours with extension

            bSkipFile = False
            for existingfn in fileutils.list_files_in_named_dir(self.rootdir, date, heure_we) + \
                              fileutils.list_files_in_named_dir(trashDir, date, heure_we):
                logger.debug("%s <-?-> %s", fname, existingfn)
                existing = Photo(existingfn, dontCache=True)
                original_name = existing.retrieve_original_name()
                if original_name and (os.path.basename(original_name) == os.path.basename(fname)):
                    logger.debug("File already in repository, leaving as it is")
                    bSkipFile = existingfn
                    break
            if bSkipFile:
                logger.warning("%s -x-> %s", fname, bSkipFile)
                continue
            full_path = os.path.join(self.rootdir, date, heure_we)
            if os.path.isfile(full_path):
                s = 0
                for j in os.listdir(os.path.join(self.rootdir, date)):
                    if j.find(heure) == 0:
                        s += 1
                heure += "-%s" % s
                heure_we = heure + photo.ext  # Hours with extension
            new_fname = os.path.join(date, heure_we)
            full_path = os.path.join(self.rootdir, new_fname)
            shutil.move(os.path.join(self.rootdir, fname), full_path)
            try:
                os.chown(full_path, uid, gid)
                os.chmod(full_path, config.DefaultFileMode)
            except OSError:
                logger.warning("in ModelRangeTout: unable to chown or chmod  %s", full_path)
            photo = Photo(full_path)
#            Save the old image name in exif tag
            photo.storeOriginalName(fname)

            if config.AutoRotate:
                photo.autorotate()
            processed_files.append(new_fname)
            new_files.append(new_fname)
        processed_files.sort(key=lambda x: x[:-4])
        self.updated_signal.emit("", 0, 0)

        if len(new_files) > 0:
            first = processed_files.index(min(new_files))
        else:
            first = 0
        self.finished_signal.emit(processed_files, first)
        self.result = processed_files, first
        return self.result


    @classmethod
    def range_tout(cls, repository=None, bUseX=True, fast=False, updated=None, finished=None):
        """Moves all the JPEG/RAW files to a directory named from their day and with the
        name according to the time

        Threadeded implementation

        @param repository: the name of the starting repository
        @type repository: string
        @param bUseX: set to False to disable the use of the graphical splash screen
        @type bUseX: boolean
        @param fast: just retrieve the list of files.
        @param updated: signal for update
        @param finished: signal for finished
        @return: 2tuple containing the list of all images and the start-index (None when working in threaded mode)
        @rtype: (list,integer)
        """
        logger.debug("in range_tout bUseX=%s fast=%s" % (bUseX, fast))
        if not repository:
            repository = config.DefaultRepository
        else:
            config.DefaultRepository = repository
        if fast:
            l = len(repository)
            if not repository.endswith(os.sep):
                l += 1
            all_files = []
            for ext in config.Extensions + config.RawExtensions:
                all_files += [i[l:] for i in glob.iglob(os.path.join(repository, "????-??-??*/*" + ext))]
            all_files.sort()
            first = len(all_files) - 1
            return (all_files, first)
        else:
            rt = cls(repository, updated, finished)
            with cls.sem:
                if finished is None:
                    return rt.run()
                else:
                    rt.start()


range_tout = RangeTout.range_tout


class ToJpeg(ThreadedProcessing):
    """Copies of all selected photos "selected" subdirectory in JPEG format"""
    def __init__(self, lst=None, updated=None, finished=None):
        """Constructor"""
        ThreadedProcessing.__init__(self, updated, finished)
        self.input = lst or []

    def run(self):
        """Implement the processing"""
        nb_files = len(self.input)
        self.updated_signal.emit("to_jpeg", 0, nb_files)
        res = []
        for idx, src in enumerate(self.input):
            self.updated_signal.emit(src, idx, nb_files)
            dst = os.path.join(config.DefaultRepository, config.SelectedDirectory,
                               os.path.splitext(src)[0] + ".jpg")
            Photo(src).as_jpeg(dst)
            res.append(dst)
        self.updated_signal.emit("", 0, 0)
        self.result = res
        self.finished_signal.emit(res)
        return self.result

    @classmethod
    def to_jpeg(cls, lst=None, updated=None, finished=None):
        """Copies of all selected photos "selected" subdirectory in JPEG format

        @param  lst: list of selected files to process
        @param updated: signal for update
        @param finished: signal for finished
        @return: list of jpeg files in selected (None when working in threaded mode)
        """
        rt = cls(lst, updated, finished)
        with cls.sem:
            if finished is None:
                return rt.run()
            else:
                rt.start()

to_jpeg = ToJpeg.to_jpeg

class CopySelected(ThreadedProcessing):
    """
    CopySelected threaded implementation
    """
    def __init__(self, lst=None, updated=None, finished=None):
        """Constructor"""
        ThreadedProcessing.__init__(self, updated, finished)
        self.input = lst or []

    def run(self):
        """
        Lance les calculs

        @param self.input: list of files to process
        """
        res = []
        nbfiles = len(self.input)
        self.updated_signal.emit("Copy selected", 0, nbfiles)
        if config.Filigrane:
            filigrane = Signature(config.FiligraneSource)
        else:
            filigrane = None

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        self.updated_signal.emit("copy existing files", 0, nbfiles)
        if not os.path.isdir(SelectedDir):
            fileutils.mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
        for day in os.listdir(SelectedDir):
            for afile in os.listdir(os.path.join(SelectedDir, day)):
                if afile.find(config.PagePrefix) == 0:
                    if os.path.isdir(os.path.join(SelectedDir, day, afile)):
                        for strImageFile in os.listdir(os.path.join(SelectedDir, day, afile)):
                            src = os.path.join(SelectedDir, day, afile, strImageFile)
                            dst = os.path.join(SelectedDir, day, strImageFile)
                            if os.path.isfile(src) and not os.path.exists(dst):
                                shutil.move(src, dst)
                                res.append(dst)
                            if (os.path.isdir(src)) and (os.path.split(src)[1] in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]):
                                shutil.rmtree(src)

#######then copy the selected files to their folders###########################
        globalCount = 0
        for afile in self.input:
            dest = os.path.join(SelectedDir, afile)
            src = os.path.join(config.DefaultRepository, afile)
            destdir = os.path.dirname(dest)
            self.updated_signal.emit(afile, globalCount, max(nbfiles, globalCount))
            globalCount += 1
            if not os.path.isdir(destdir):
                fileutils.makedir(destdir)
            if not os.path.exists(dest):
                if filigrane:
                    image = Image.open(src)
                    filigrane.substract(image).save(dest, quality=config.FiligraneQuality, optimize=config.FiligraneOptimize, progressive=config.FiligraneOptimize)
                else:
                    shutil.copy(src, dest)
                res.append(dest)
                try:
                    os.chmod(dest, config.DefaultFileMode)
                except OSError:
                    logger.warning("In ModelCopySelected: unable to chmod %s", dest)
            else:
                logger.info("In ModelCopySelected: %s already exists", dest)
######copy the comments of the directory to the Selected directory
        already_done = []
        for afile in self.input:
            directory = os.path.split(afile)[0]
            if directory not in already_done:
                already_done.append(directory)
                dst = os.path.join(SelectedDir, directory, config.CommentFile)
                src = os.path.join(config.DefaultRepository, directory, config.CommentFile)
                if os.path.isfile(src):
                    shutil.copy(src, dst)
        self.result = res
        self.updated_signal.emit("", 0, 0)
        self.finished_signal.emit(res)
        return self.result

    @classmethod
    def copy_selected(cls, lst, updated=None, finished=None):

        """
        This procedure makes a copy of all selected photos and scales them
        copy all the selected files to "selected" subdirectory

        @param  lstSelectedFiles: list of selected files to process
        @param updated: signal for update
        @param finished: signal for finished
        @return: None (threaded) or list of processed files
        """
        logger.info("Copy Selected of " + " ".join(lst))
        rt = cls(lst, updated, finished)
        with cls.sem:
            if finished is None:
                return rt.run()
            else:
                rt.start()

copy_selected = CopySelected.copy_selected

class ProcessSelected(ThreadedProcessing):
    """
    """
    def __init__(self, lst, updated=None, finished=None):
        """Constructor

        @param lst: list of files to process.
        @param updated: update signal or None
        """
        ThreadedProcessing.__init__(self, updated, finished)
        self.input = lst or []

    def run(self):
        """Actually run processing for "processSelected"""
        res = []
        logger.debug("In Process Selected" + " ".join(self.input))
        nbfiles = len(self.input)
        self.updated_signal.emit("Process selected", 0, nbfiles)

        def splitIntoPages(pathday, globalCount):
            """Split a directory (pathday) into pages of 20 images (see config.NbrPerPage)

            @param pathday:
            @param globalCount:
            @return: the number of images for current page
            """
            logger.debug("In splitIntoPages %s %s", pathday, globalCount)
            files = [i for  i in os.listdir(pathday) \
                     if os.path.splitext(i)[1] in config.Extensions]
            files.sort()
            if  len(files) > config.NbrPerPage:
                pages = 1 + (len(files) - 1) // config.NbrPerPage
                for i in range(1, pages + 1):
                    folder = os.path.join(pathday, config.PagePrefix + str(i))
                    fileutils.mkdir(folder)
                for j in range(len(files)):
                    i = 1 + (j) // config.NbrPerPage
                    filename = os.path.join(pathday, config.PagePrefix + str(i), files[j])
                    self.updated_signal.emit(files[j], globalCount, max(nbfiles, globalCount))
                    globalCount += 1
                    shutil.move(os.path.join(pathday, files[j]), filename)
                    scaleImage(filename, filigrane)
            else:
                for j in files:
                    self.updated_signal.emit(j, globalCount, max(nbfiles, globalCount))
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

        if config.Filigrane:
            filigrane = Signature(config.FiligraneSource)
        else:
            filigrane = None

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        self.updated_signal.emit("Copy files", 0, nbfiles)
        if not os.path.isdir(SelectedDir):
            fileutils.mkdir(SelectedDir)
#####first of all : copy the subfolders into the day folder to help mixing the files
        for day in os.listdir(SelectedDir):
# if SingleDir : revert to a foldered structure
            DayOrFile = os.path.join(SelectedDir, day)
            if os.path.isfile(DayOrFile):
                arrangeOneFile(SelectedDir, day)
                nbfiles += 1
# end SingleDir normalization
            elif os.path.isdir(DayOrFile):
                if day in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]:
                    fileutils.recursive_delete(DayOrFile)
                elif day.find(config.PagePrefix) == 0:  # subpages in SIngleDir mode that need to be flatten
                    for afile in os.listdir(DayOrFile):
                        if     os.path.isfile(os.path.join(DayOrFile, afile)):
                            arrangeOneFile(DayOrFile, afile)
                            nbfiles += 1
#                        elif os.path.isdir(os.path.join(DayOrFile,afile)) and afile in [config.ScaledImages["Suffix"],config.Thumbnails["Suffix"]]:
#                            recursive_delete(os.path.join(DayOrFile,afile))
                    fileutils.recursive_delete(DayOrFile)
                else:
                    for afile in os.listdir(DayOrFile):
                        if afile.find(config.PagePrefix) == 0:
                            if os.path.isdir(os.path.join(SelectedDir, day, afile)):
                                for strImageFile in os.listdir(os.path.join(SelectedDir, day, afile)):
                                    src = os.path.join(SelectedDir, day, afile, strImageFile)
                                    dst = os.path.join(SelectedDir, day, strImageFile)
                                    if os.path.isfile(src) and not os.path.exists(dst):
                                        shutil.move(src, dst)
                                        nbfiles += 1
                                    if (os.path.isdir(src)) and (os.path.split(src)[1] in [config.ScaledImages["Suffix"], config.Thumbnails["Suffix"]]):
                                        shutil.rmtree(src)
                        else:
                            if os.path.splitext(afile)[1] in config.Extensions:
                                nbfiles += 1

#######then copy the selected files to their folders###########################
        for afile in self.input:
            ph = Photo(afile)
            if ph.is_raw:
                dest = os.path.join(SelectedDir, os.path.splitext(afile)[0] + ".jpg")
            else:
                dest = os.path.join(SelectedDir, afile)
            src = os.path.join(config.DefaultRepository, afile)
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                fileutils.makedir(destdir)
            if not os.path.exists(dest):
                logger.info("copie de %s " % afile)
                if ph.is_raw:
                    ph.as_jpeg(dest)
                else:
                    shutil.copy(src, dest)
                try:
                    os.chmod(dest, config.DefaultFileMode)
                except OSError:
                    logger.warning("Unable to chmod %s" % dest)
                nbfiles += 1
            else:
                logger.warning("%s existe déja" % dest)
######copy the comments of the directory to the Selected directory
        already_done = []
        for afile in self.input:
            directory = os.path.split(afile)[0]
            if directory not in already_done:
                already_done.append(directory)
                dst = os.path.join(SelectedDir,
                                   directory, config.CommentFile)
                src = os.path.join(config.DefaultRepository,
                                   directory, config.CommentFile)
                if os.path.isfile(src):
                    shutil.copy(src, dst)

########finally recreate the structure with pages or make a single page ######
        logger.debug("in ModelProcessSelected, SelectedDir= %s", SelectedDir)
        dirs = [i for i in os.listdir(SelectedDir) \
                if os.path.isdir(os.path.join(SelectedDir, i))]
        dirs.sort()
        if config.ExportSingleDir:  # SingleDir
            # first move all files to the root
            for day in dirs:
                daydir = os.path.join(SelectedDir, day)
                for filename in os.listdir(daydir):
                    try:
                        timetuple = time.strptime(day[:10] + "_" + filename[:8],
                                                  "%Y-%m-%d_%Hh%Mm%S")
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
        else:  # Multidir
            logger.debug("in Multidir, dirs= " + " ".join(dirs))
            globalCount = 0
            for day in dirs:
                globalCount = splitIntoPages(os.path.join(SelectedDir, day), globalCount)

        self.updated_signal.emit("", 0, 0)
        self.result = res
        self.finished_signal.emit(res)
        return self.result

    @classmethod
    def process_selected(cls, lst, updated=None, finished=None):
        """
        This procedure uses the threaded implementation of processSelected
        It makes a copy of all selected photos and scales them
        copy all the selected files to "selected" subdirectory, 20 per page

        @param  lst: list of selected files to process
        @return: None or the list of files generated
        """
        logger.info("Process Selected of " + " ".join(lst))
        rt = cls(lst, updated, finished)
        with cls.sem:
            if finished is None:
                return rt.run()
            else:
                rt.start()

process_selected = ProcessSelected.process_selected



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
    new_photo = photo.saveThumb(**param)
    if new_photo is None:
        new_photo = photo
    param = config.Thumbnails.copy()
    param.pop("Suffix")
    param["strThumbFile"] = os.path.join(thumbdir, os.path.basename(filename))[:-4] + "--%s.jpg" % config.Thumbnails["Suffix"]
    new_photo.saveThumb(**param)
    if filigrane is not None:
        filigrane.substract(photo.pil).save(filename, quality=config.FiligraneQuality, optimize=config.FiligraneOptimize, progressive=config.FiligraneOptimize)
        try:
            os.chmod(filename, config.DefaultFileMode)
        except OSError:
            logger.warning("in scaleImage: Unable to chmod %s", filename)

