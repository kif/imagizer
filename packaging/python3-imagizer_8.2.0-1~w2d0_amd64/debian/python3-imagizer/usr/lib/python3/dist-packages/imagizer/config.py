#!/usr/bin/env python
# coding: utf-8
#
#******************************************************************************\
# *
# * Copyright (C) 2006 - 2014,  Jérôme Kieffer <imagizer@terre-adelie.org>
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
"""
Config is a class containing all the configuration of the imagizer suite.
Technically it is a Borg (design Pattern) so every instance of Config has exactly the same contents.
"""
__author__ = "Jérôme Kieffer"
__contact = "imagizer@terre-adelie.org"
__date__ = "20191222"
__license__ = "GPL"

import os, locale, logging

try: 
    from configparser import  ConfigParser, NoSectionError
except ImportError:
    #Python2 version ... 
    from ConfigParser import ConfigParser, NoSectionError
installdir = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger("imagizer.config")
try:
    import resource
except ImportError:
    resource = None

if os.name == 'nt':  # sys.platform == 'win32':
    listConfigurationFiles = [os.path.join(os.getenv("ALLUSERSPROFILE"), "imagizer.conf"), os.path.join(os.getenv("USERPROFILE"), "imagizer.conf")]
elif os.name == 'posix':
    listConfigurationFiles = ["/etc/imagizer.conf", os.path.join(os.getenv("HOME"), ".imagizer")]




def float_or_None(inp):
    try:
        out = float(inp)
    except:
        out = None
    return out


################################################################################################
###############  Class Config for storing the configuratio in a Borg ############################
################################################################################################
class Config(object):
    """this class is a Borg : always returns the same values regardless to the instance of the object"""
    __shared_state = {}
    def __init__(self, configuration_files=None):
        """
        This is  a Borg, so the constructor is more or less empty
        """
        self.__dict__ = self.__shared_state
        if len(self.__dict__) < 5:
            logging.debug("Config: initialization of the class")
            self.ScreenSize = 600
            self.NbrPerPage = 20
            self.PagePrefix = "page"
            self.TrashDirectory = "Trash"
            self.SelectedDirectory = "Selected"
            self.Selected_save = ".selected-photos"
            self.Database_file = ".imagizer.sqlite"
            self.Extensions = [".jpg", ".jpeg", ".jpe", ".jfif"]
            self.RawExtensions = [".cr2", ".arw", ".mrw", ".dng", ".pef", ".nef", ".raf"]
            self.AutoRotate = False
            self.DefaultMode = "664"
            try:
                self.DefaultRepository = os.getcwd()
            except OSError:
                self.DefaultRepository = ""
            self.CommentFile = "index.desc"
            self.Interpolation = 1
            self.DefaultFileMode = int(self.DefaultMode, 8)
            self.DefaultDirMode = self.DefaultFileMode + 3145  # 73 = +111 en octal ... 3145 +s mode octal
            self.Filigrane = False
            self.FiligraneSource = os.path.join(installdir, "signature.png")
            self.FiligranePosition = 5
            self.FiligraneQuality = 75
            self.FiligraneOptimize = False
            self.FiligraneProgressive = False
            self.ContrastMaskGaussianSize = 11.77
            self.WebDirIndexStyle = "list"
            self.MediaSize = 680
            self.Burn = "grave-rep $Selected"
            self.WebServer = "cp -r $Selected/* $WebRepository && generator"
            self.WebRepository = "/var/www/imagizer"
            self.Locale, self.Coding = locale.getdefaultlocale()
            self.ExportSingleDir = False
            self.GraphicMode = "Normal"
            self.WebPageAnchor = "end"
            self.SlideShowDelay = 5.0
            self.SlideShowType = "chronological"
            self.SlideShowMinRating = 3
            self.SynchronizeRep = "user@host:/mnt/photo"
            self.SynchronizeType = "Newer"
            self.ImageCache = 100
            self.ImageWidth = None
            self.ImageHeight = None
            self.DEBUG = None
            self.Gimp = "gimp"
            self.Rawtherapee = "rawtherapee"
            self.Dcraw = "dcraw -w -c"
            self.DefaultRatingSelectedImage = 3
            self.SelectedFilter = "ContrastMask"
            self.Thumbnails = {
                "Size":160,
                "Suffix": "thumb",
                "Interpolation":1,
                "Progressive":False,
                "Optimize":False,
                "ExifExtraction":True,
                "Quality": 75
                }
            self.ScaledImages = {
                "Size":800,
                "Suffix": "scaled",
                "Interpolation":1,
                "Progressive":False,
                "Optimize":False,
                "ExifExtraction":False,
                "Quality": 75
                }
            # Video default options
            self.ScratchDir = "/tmp"
            self.VideoBitRate = 600
            self.AudioBitRatePerChannel = 64
            self.X264Options = "subq=7:nr=100:me=umh:partitions=all:direct_pred=auto:bframes=3:frameref=5"
            self.FramesPerSecond = None
            self.MPlayer = "/usr/bin/mplayer"
            self.MEncoder = "/usr/bin/mencoder"
            self.Sox = "/usr/bin/sox"
            self.Convert = "/usr/bin/convert"
            self.AviMerge = "/usr/bin/avimerge"
            self.VideoExtensions = [".avi", ".mpeg", ".mpg", ".mp4", ".divx", ".mov", ".webm", ".mkv", ".m2ts"]
            self.ThumbnailExtensions = [".thm", ".jpg"]
            self.BatchScriptExecutor = "/usr/bin/batch"
            self.BatchUsesPipe = True
            if configuration_files is not None:
                self.load(configuration_files)

    def load(self, filenames):
        """retrieves the the default options, if the filenames does not exist, uses the default instead
        @param filenames: list of filename
        @type filenames: list of strings or unicode
        """
        logging.debug("Config.load")
        configparser = ConfigParser()
        files = []
        for i in filenames:
            if os.path.isfile(i):files.append(i)
        if len(files) == 0:
            logging.warning("No configuration file found. Falling back on defaults")
            return

        configparser.read(files)
        for (key, value) in configparser.items("Selector"):
            if key == "ScreenSize".lower():         self.ScreenSize = int(value)
            elif key == "Interpolation".lower():    self.Interpolation = int(value)
            elif key == "PagePrefix".lower():       self.PagePrefix = value
            elif key == "NbrPerPage".lower():       self.NbrPerPage = int(value)
            elif key == "TrashDirectory".lower():   self.TrashDirectory = value
            elif key == "SelectedDirectory".lower():self.SelectedDirectory = value
            elif key == "Selected_save".lower():    self.Selected_save = value
            elif key == "Database_file".lower():    self.Database_file = value
            elif key == "AutoRotate".lower():       self.AutoRotate = configparser.getboolean("Selector", "AutoRotate")
            elif key == "Filigrane".lower():        self.Filigrane = configparser.getboolean("Selector", "Filigrane")
            elif key == "FiligraneSource".lower():  self.FiligraneSource = value
            elif key == "FiligranePosition".lower():self.FiligranePosition = int(value)
            elif key == "FiligraneQuality".lower(): self.FiligraneQuality = int(value)
            elif key == "FiligraneOptimize".lower():self.FiligraneOptimize = configparser.getboolean("Selector", "FiligraneOptimize")
            elif key == "FiligraneProgressive".lower():self.FiligraneProgressive = configparser.getboolean("Selector", "FiligraneProgressive")
            elif key == "CommentFile".lower():      self.CommentFile = value
            elif key == "WebDirIndexStyle".lower(): self.WebDirIndexStyle = value
            elif key == "DefaultFileMode".lower():
                self.DefaultFileMode = int(value, 8)
                self.DefaultDirMode = self.DefaultFileMode + 3145  # 73 = +111 en octal ... 3145 +s mode octal
            elif key == "RawExtensions".lower():      self.RawExtensions = value.split()
            elif key == "Extensions".lower():         self.Extensions = value.split()
            elif key == "DefaultRepository".lower():  self.DefaultRepository = value
            elif key == "MediaSize".lower():          self.MediaSize = float(value)
            elif key == "Burn".lower():               self.Burn = value
            elif key == "WebServer".lower():          self.WebServer = value
            elif key == "WebRepository".lower():      self.WebRepository = value
            elif key == "Locale".lower():
                self.Locale = value
                try:
                    locale.setlocale(locale.LC_ALL, self.Locale)
                except locale.Error:
                    self.Locale, _ = locale.getdefaultlocale()
                    logger.warning("Unsupported locale %s, reverting to %s" % (value, self.Locale))
            elif key == "Coding".lower():             self.Coding = value
            elif key == "ExportSingleDir".lower():    self.ExportSingleDir = configparser.getboolean("Selector", "ExportSingleDir")
            elif key == "WebPageAnchor".lower():      self.WebPageAnchor = value
            elif key == "SlideShowDelay".lower():     self.SlideShowDelay = float(value)
            elif key == "SlideShowMinRating".lower(): self.SlideShowMinRating = min(5, max(0, int(value)))
            elif key == "SlideShowType".lower():      self.SlideShowType = value
            elif key == "SynchronizeRep".lower():     self.SynchronizeRep = value
            elif key == "SynchronizeType".lower():    self.SynchronizeType = value
            elif key == "ImageCache".lower():         self.ImageCache = int(value)
            elif key == "ImageWidth".lower():         self.ImageWidth = int(value)
            elif key == "ImageHeight".lower():        self.ImageHeight = int(value)
            elif key == "gimp".lower():               self.Gimp = value
            elif key == "dcraw".lower():              self.Dcraw = value
            elif key == "SelectedFilter".lower():      self.SelectedFilter = value
            else: logging.warning(str("Config.load: unknown key %s" % key))

        for k in ["ScaledImages", "Thumbnails"]:
            try:
                dico = eval(k)
            except:
                dico = {}
            for (key, value) in configparser.items(k):
                if key == "Size".lower():dico["Size"] = int(value)
                elif key == "Suffix".lower():dico["Suffix"] = value
                elif key == "Interpolation".lower():dico["Interpolation"] = int(value)
                elif key == "Progressive".lower():dico["Progressive"] = configparser.getboolean(k, "Progressive")
                elif key == "Optimize".lower():dico["Optimize"] = configparser.getboolean(k, "Optimize")
                elif key == "ExifExtraction".lower():dico["ExifExtraction"] = configparser.getboolean(k, "ExifExtraction")
                elif key == "Quality".lower():dico["Quality"] = int(value)
            self.__setattr__(k, dico)
#            exec("self.%s=dico" % k)

        # Read Video options
        try:
            for (key, value) in configparser.items("Video"):
                if key == "ScratchDir".lower():           self.ScratchDir = os.path.abspath(value)
                elif key == "VideoBitRate".lower():       self.VideoBitRate = int(value)
                elif key == "AudioBitRatePerChannel".lower(): self.AudioBitRatePerChannel = int(value)
                elif key == "X264Options".lower():        self.X264Options = value
                elif key == "FramesPerSecond".lower():    self.FramesPerSecond = float_or_None(value)
                elif key == "MPlayer".lower():            self.MPlayer = os.path.abspath(value)
                elif key == "MEncoder".lower():           self.MEncoder = os.path.abspath(value)
                elif key == "Sox".lower():                self.Sox = os.path.abspath(value)
                elif key == "Convert".lower():            self.Convert = os.path.abspath(value)
                elif key == "AviMerge".lower():           self.AviMerge = os.path.abspath(value)
                elif key == "VideoExtensions".lower():    self.VideoExtensions = value.split()
                elif key == "ThumbnailExtensions".lower():    self.ThumbnailExtensions = value.split()
                elif key == "BatchScriptExecutor".lower():    self.BatchScriptExecutor = os.path.abspath(value)
                elif key == "BatchUsesPipe".lower():            self.BatchUsesPipe = configparser.getboolean("Video", "BatchUsesPipe")

                else: logging.warning(str("Config.load: unknown key %s" % key))
        except NoSectionError:
            logging.warning("No Video section in configuration file !")
        if resource:
            max_files = resource.getrlimit(resource.RLIMIT_NOFILE)[0] - 15
            if max_files < self.ImageCache:
                self.ImageCache = max_files

        if self.Interpolation > 1:
            self.Interpolation = 1
        if self.Interpolation < 0:
            self.Interpolation = 0


    def __repr__(self):
        logging.debug("Config.__repr__")
        listtxt = ["",
        "Size on the images on the Screen: %s pixels in the largest dimension" % self.ScreenSize,
        "Page prefix:\t\t\t  %s" % self.PagePrefix,
        "Number of images per page:\t  %s" % self.NbrPerPage,
        "Use Exif for Auto-Rotate:\t  %s" % self.AutoRotate,
        "Default mode for files (octal):\t  %o" % self.DefaultFileMode,
        "JPEG extensions:\t\t %s" % self.Extensions,
        "Default photo repository:\t  %s" % self.DefaultRepository,
        "Add signature for exported images:%s" % self.Filigrane,
        "Backup media size (CD,DVD):\t  %s MByte" % self.MediaSize,
        "Scaled imagesSize:\t\t  %s pixels in the largest dimension" % self.ScaledImages["Size"],
        "Thumbnail Size:\t\t\t  %s pixels in the largest dimension" % self.Thumbnails["Size"],
        "Caching of %s images " % self.ImageCache
        ]
        return  os.linesep.join(listtxt)

    def printConfig(self):
        """
        Print out the configuration
        """
        logging.debug("Config.printConfig")
        logging.info(self.__repr__())

    def saveConfig(self, filename):
        """Wrapper for self.config"""
        self.save(filename)

    def save(self, filename):
        """
        Saves the default options to file

        @param filename: name of the file to save the configuration to
        @type filename: string or unicode
        """
        logging.debug("Config.save")
        lsttxt = ["[Selector]",
        "#Size of the image on the Screen, by default", "ScreenSize: %s" % self.ScreenSize, "",
        "#Downsampling quality [0=nearest, 1=bilinear]", "Interpolation: %s" % self.Interpolation, "",
        "#Page prefix (used when there are too many images per day to fit on one web page)", "PagePrefix: %s" % self.PagePrefix, "",
        "#Maximum number of images per web page", "NbrPerPage: %s" % self.NbrPerPage, "",
        "#Trash sub-directory", "TrashDirectory: %s" % self.TrashDirectory, "",
        "#Selected/processed images sub-directory", "SelectedDirectory: %s" % self.SelectedDirectory, "",
        "#File containing the list of selected but unprocessed images", "Selected_save: %s" % self.Selected_save, "",
        "#File containing the database with all title of images", "Database_file: %s" % self.Database_file, "",
        "#Use Exif data for auto-rotation of the images (canon cameras mainly)", "AutoRotate: %s" % self.AutoRotate, "",
        "#Default mode for files (in octal)", "DefaultFileMode: %o" % self.DefaultFileMode, "",
        "#Default JPEG extensions", "Extensions: " + " ".join(self.Extensions), "",
        "#Default Raw images extensions", "RawExtensions: " + " ".join(self.RawExtensions), "",
        "#Default photo repository", "DefaultRepository: %s" % self.DefaultRepository, "",
        "#Size of the backup media (in MegaByte)", "MediaSize:    %s" % self.MediaSize, "",
        "#Add signature to web published images", "Filigrane: %s" % self.Filigrane, "",
        "#File containing the image of the signature for the filigrane", "FiligraneSource: %s" % self.FiligraneSource, "",
        "#Position of the filigrane : 0=center 12=top center 1=upper-right 3=center-right...", "FiligranePosition: %s" % self.FiligranePosition, "",
        "#Quality of the saved image in filigrane mode (JPEG quality)", "FiligraneQuality: %s" % self.FiligraneQuality, "",
        "#Optimize the filigraned image (2 pass JPEG encoding)", "FiligraneOptimize: %s" % self.FiligraneOptimize, "",
        "#Progressive JPEG for saving filigraned images", "FiligraneProgressive: %s" % self.FiligraneProgressive, "",
        "#File containing the description of the day in each directory", "CommentFile: %s" % self.CommentFile, "",
        "#Style of the dirindex web pages, either <<list>> or <<table>>, the latest includes thumbnail photos", "WebDirIndexStyle: %s" % self.WebDirIndexStyle, "",
        "#System command to use to burn a CD or a DVD", "# $Selected will be replaced by the directory where the files are", "Burn: %s" % self.Burn, "",
        "#System command to copy the selection to the server", "# $Selected will be replaced by the directory where the files are", "# $WebRepository will be replaced by the directory of the root of generator", "WebServer: %s" % self.WebServer, "",
        "#The location of the root of generator", "WebRepository: %s" % self.WebRepository, "",
        "#The localization code, fr_FR is suggested for unix or FR for win32", "Locale: %s" % self.Locale, "",
        "#Default encoding for text files, latin-1 is suggested,UTF-8 should be possible", "Coding: %s" % self.Coding, "",
        "#All selected photos should be exported in a single directory", "ExportSingleDir: %s" % self.ExportSingleDir, "",
        "#Where should the dirindex page start-up ? [begin/end] ", "WebPageAnchor: %s" % self.WebPageAnchor, "",
        "#Delay between imges in the slideshow? ", "SlideShowDelay: %s" % self.SlideShowDelay, "",
        "#Type of slideshow : chronological, anti-chronological or random ?", "SlideShowType: %s" % self.SlideShowType, "",
        "#Minimum rating of an image to appear in the slidesho [0-5]", "SlideShowMinRating: %i" % self.SlideShowMinRating, "",
        "#Remote repository to synchronize with (rsync like)", "SynchronizeRep: %s" % self.SynchronizeRep, "",
        "#Synchronization type, acceptable values are Newer, Older, Selected and All", "SynchronizeType: %s" % self.SynchronizeType, "",
        "#Allow the creation of a Cache of images with the given size in number of images", "ImageCache: %s" % self.ImageCache, "",
        "#Gnu Image Manipulation Program (GIMP) path to executable", "Gimp: %s" % self.Gimp, "",
        "#Digital Camera Raw (dcraw) extraction program and option (-w -c is  suggested)", "Dcraw: %s" % self.Dcraw, "",
        "#Filter selected by default for image processing: ContrastMask, AutoWB, ...", "SelectedFilter: %s" % self.SelectedFilter, ""]
        if self.ImageWidth is not None:
            lsttxt += ["#Width of the last image displayed ... should not be modified", "ImageWidth:%s" % self.ImageWidth, ""]
        if self.ImageHeight is not None:
            lsttxt += ["#Height of the last image displayed ... should not be modified", "ImageHeight:%s" % self.ImageHeight, ""]

        for i in ["ScaledImages", "Thumbnails"]:
            lsttxt += ["[%s]" % i, ""]
            j = eval("self.%s" % i)
            lsttxt += ["#%s size" % i, "Size: %s" % j["Size"], ""]
            lsttxt += ["#%s suffix" % i, "Suffix: %s" % j["Suffix"], ""]
            lsttxt += ["#%s downsampling quality [0=nearest, 1=antialias 2=bilinear, 3=bicubic]" % i, "Interpolation: %s" % j["Interpolation"], ""]
            lsttxt += ["#%s progressive JPEG files" % i, "Progressive: %s" % j["Progressive"], ""]
            lsttxt += ["#%s optimized JPEG (2 pass encoding)" % i, "Optimize: %s" % j["Optimize"], ""]
            lsttxt += ["#%s quality (in percent)" % i, "Quality: %s" % j["Quality"], ""]
            lsttxt += ["#%s image can be obtained by Exif extraction ?" % i, "ExifExtraction: %s" % j["ExifExtraction"], ""]

        lsttxt += ["[Video]",
            "#Directory where you want PBS to work? (/tmp)", "ScratchDir: %s" % self.ScratchDir, "",
            "#Video bit rate Higher is better but bigger (600)", "VideoBitRate: %s" % self.VideoBitRate, "",
            "#audio bit rate per ausio channel (x2 for stereo), default=64", "AudioBitRatePerChannel: %s" % self.AudioBitRatePerChannel, "",
            "#Options to be used for the X264 encoder (man mencoder)", "X264Options: %s" % self.X264Options, "",
            "#Number of Frames per secondes in the video (25):", "FramesPerSecond: %s" % self.FramesPerSecond, "",
            "#Path to the mplayer (mplayer package) executable", "MPlayer: %s" % self.MPlayer, "",
            "#Path to the mencoder (mplayer package) executable", "MEncoder: %s" % self.MEncoder, "",
            "#Path to the sox (Sound processing) executable", "Sox: %s" % self.Sox, "",
            "#Path to the convert (imagemagick package) executable", "Convert: %s" % self.Convert, "",
            "#Path to the avimerge (transcode package) executable", "AviMerge: %s" % self.AviMerge, "",
            "#List of video extensions", "VideoExtensions: %s" % " ".join(self.VideoExtensions), "",
            "#list of thumbnail extension related to videos", "ThumbnailExtensions: %s" % " ".join(self.ThumbnailExtensions), "",
            "#Batch queueing system launcher (/bin/sh if none present)", "BatchScriptExecutor: %s" % self.BatchScriptExecutor, "",
            "#Batch queuing needs a pipe (like batch) or not (like PBS)", "BatchUsesPipe: %s" % self.BatchUsesPipe, "",
            ]
        w = open(filename, "w")
        w.write(os.linesep.join(lsttxt))
        w.close()
        if self.DEBUG:
            logging.info(str("Configuration saved to file %s" % filename))


config = Config(listConfigurationFiles)
