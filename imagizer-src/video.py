#!/usr/bin/env python
# -*- coding: utf8 -*-
#******************************************************************************\
#*
#* Copyright (C) 2006 - 2011,  Jérôme Kieffer <kieffer@terre-adelie.org>
#* Conception: Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
#* Licence GPL v2
#*
#* This program is free software; you can redistribute it and/or modify
#* it under the terms of the GNU General Public License as published by
#* the Free Software Foundation; either version 3 of the License, or
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
from __future__ import with_statement

__author__ = "Jérôme Kieffer"
__date__ = "09 Apr 2012"
__copyright__ = "Jérôme Kieffer"
__license__ = "GPLv3+"
__contact__ = "Jerome.Kieffer@terre-adelie.org"


import os, sys, hashlib, logging, tempfile, datetime, time, subprocess, threading, json, stat

logger = logging.getLogger("imagizer.video")
logger.setLevel(logging.INFO)

#Find all the videos and renames them, compress then .... and write an html file to set online

import Image
import os.path as OP
if sys.version >= (3, 0):
    from queue import Queue
else:
    from Queue import Queue
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata

from config  import Config
config = Config()


def writeStdOutErr(std, filename):
        open(filename, 'wb').write(std.read())

def calcFastMd5(filename):
    block = 2 ** 20
    size = os.path.getsize(filename)
    if size > 2 * block :
        with open(filename, "rb") as myFile:
            data = myFile.read(block)
            myFile.seek(size - 2 * block)
            data += myFile.read(block)
    else:
        data = open(filename, "rb").read()
    return hashlib.md5(data).hexdigest()

class Video(object):
    """main Video class"""
    root = None
    queue = Queue()
    sem = threading.Semaphore()
    semLauncher = threading.Semaphore()
    jobId = 0

    @classmethod
    def startProcessing(cls, script):
        """
        @param script:
        @return: jobID which is a sting: Plugin-000001
        """
        if script.strip() == "":
            return
        with cls.semLauncher:
            cls.jobId += 1
            idx = cls.jobId
        logger.warning("Starting processing job %i" % idx)
        cls.queue.put_nowait((idx, script))
        logger.warning("Size of the process queue: %s", cls.queue.qsize())
        if cls.sem._Semaphore__value > 0:
            logger.warning("No process Loop running: stating it")
            t = threading.Thread(target=cls.processingLoop)
            t.start()
        return idx

    @classmethod
    def processingLoop(cls):
        """
        Process all jobs in the queue.
        """
        with cls.sem:
            while not cls.queue.empty():
                idx, script = cls.queue.get_nowait()
                logger.warning("%s %s", idx, script)
                encodeProcess = subprocess.Popen(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.warning("Subprocess %i with pid=%s" % (idx, encodeProcess.pid))
#                out, err = encodeProcess.communicate()
                threadStdErr = threading.Thread(target=writeStdOutErr, name="BatchWriteStdErr", args=(encodeProcess.stderr, "%s.e%s" % (script, idx)))
                threadStdOut = threading.Thread(target=writeStdOutErr, name="BatchWriteStdOut", args=(encodeProcess.stdout, "%s.o%s" % (script, idx)))
                threadStdErr.start()
                threadStdOut.start()
#                open("%s.e%s" % (script, idx), 'wb').write(err)
#                open("%s.o%s" % (script, idx), 'wb').write(out)
                logging.warning(str("Subprocess %i with pid=%s finished with %s" % (idx, encodeProcess.pid, encodeProcess.wait())))



    def __init__(self, infile, root=None):
        """initialise the class"""
        self.fullPath = OP.abspath(infile)
        if (Video.root is None) and root is not None:
            Video.root = OP.abspath(root)
        self.videoPath = ""
        self.videoFile = ""
        self.origName = ""
        [self.videoPath, self.videoFile] = OP.split(self.fullPath)
        self.timeStamp = datetime.datetime.fromtimestamp(OP.getmtime(self.fullPath))
        self.title = u""
        self.width = 0
        self.height = 0
        self.rotation = None
        self.duration = 0
        self.root = None
        self.suffix = None
        self.bitRate = None
        self.audioCodec = None
        self.audioBitRate = None
        self.audioChannel = None
        self.audioSampleRate = None
        self.audioBits = None
        self.videoCodec = None
        self.videoBitRate = None
        self.videoBpP = None
        self.frameRate = None
        self.destinationFile = None
        self.thumbName = None
        self.thumb = None
        self.camera = None
        self.keywords = []
        self.deinterleave = None
        self.fastMd5 = calcFastMd5(self.fullPath)
        try:
            time.strptime(self.videoFile[:9], "%Hh%Mm%Ss")
        except:
            self.origMd5 = self.fastMd5
        else:
            self.origMd5 = None
        self.fromDisk()

    def analyse(self):
        """
        analyses a video
        """
        logger.info("Analyzing %s" % self.fullPath)
        if self.videoFile.lower().startswith("dscf"):
            self.camera = "Fuji"
            self.deinterleave = False
        elif self.videoFile.lower().startswith("mvi_"):
            self.camera = "Canon"
            self.deinterleave = False
        elif self.videoFile.lower().startswith("mov"):
            self.camera = "Sony"
            self.deinterleave = False
        elif self.videoFile.lower().startswith("sdc"):
            self.camera = "Samsung"
            self.deinterleave = False
        elif self.videoFile.lower().startswith("m2u"):
            self.camera = "Sony"
            self.deinterleave = True
        elif self.videoFile.lower().startswith("p"):
            self.camera = "Panasonic"
            self.deinterleave = False
        else:
            self.camera = "Imagizer"
            self.deinterleave = True
        self.loadMetadata()
        dirname = OP.split(self.videoPath)[1]
        dirdate = None
        if len(dirname) >= 10:
            if dirname[0] == "M":
                dirname = dirname[1:]
            try:
                dirdate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dirname[:10], "%Y-%m-%d")))
            except:
                logging.warning(str("Unable to read date from: %s" % dirname))
        if dirdate:
            if dirdate.date() < self.timeStamp.date():
                self.timeStamp = datetime.datetime.combine(dirdate.date(), self.timeStamp.time())
        CommentFile = OP.splitext(self.fullPath.replace(" ", "_"))[0] + ".meta"
        if OP.isfile(CommentFile):
            for l in open(CommentFile):
                if len(l) > 2:
                    k, d = l.decode(config.Coding).split(None, 1)
                    if k == "ISRF":
                        self.camera = d.strip()
                    elif k == "ICRD":
                        videoDate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(d.strip(), "%Y-%m-%d")))
                        if videoDate.date < self.timeStamp.date:
                            self.timeStamp = datetime.datetime.combine(videoDate.date(), self.timeStamp.time())
                    elif k == "INAM":
                        self.title = d.strip()
                    elif k == "IKEY":
                        self.keyword = d.strip().split(";")

    def __repr__(self):
        """Returns some information on the current video flux"""
        txt = "%s\n" % self.videoFile
        txt += "camera: %s\tWidth= %i\tHeigth= %i\n" % (self.camera, self.width, self.height)
        txt += "Type: %s,\t title:%s\n" % (type(self.title), self.title)
        txt += self.getComment()
        return txt


    def toDisk(self, filename=None):
        """
        Save the metadata to a file, by default .metadata/videoFile.avi.json
        """
        if filename is None:
            filename = os.path.join(OP.dirname(self.fullPath), ".metadata", OP.basename(self.fullPath) + ".json")
        if not OP.isdir(OP.dirname(filename)):
            os.makedirs(OP.dirname(filename))
        dictToSave = {}
        for key in self.__dict__:
            val = self.__dict__[key]
            if hasattr(val, "__call__"): #skip methods
                continue
            elif key == "timeStamp":
                dictToSave[key] = tuple(val.utctimetuple())
            else:
                dictToSave[key] = val
        with open(filename, "wb") as myFile:
            json.dump(dictToSave, myFile, sort_keys=True, indent=4)

    def fromDisk(self, filename=None):
        """
        Load the metadata from a file, by default .metadata/videoFile.avi.json
        """
        if filename is None:
            filename = os.path.join(OP.dirname(self.fullPath), ".metadata", OP.basename(self.fullPath) + ".json")
        if not os.path.isfile(filename):
            logger.warning("No metadata dump for %s", self.videoFile)
            self.analyse()
            self.toDisk()
            return
        logger.info("Loading metadata for %s" % self.fullPath)
        try:
            with open(filename, "rb") as myFile:
                red = json.load(myFile)
        except Exception as err:
            logger.warning("Json failed to load %s with error: %s", file,err)
            self.analyse()
            self.toDisk()
            return
        if ("fastMd5" in red) and (self.fastMd5 == red["fastMd5"]):
            self.__dict__.update(red)
            if "timeStamp" in red:
                self.timeStamp = datetime.datetime(*(red["timeStamp"][:-2]))
        else:
            logger.warning("Metadata are not consistent: the video has changed")
            self.analyse()
            self.toDisk()

    def isEncoded(self):
        """
        Return if a video is already encoded (H264, MP3, name according to convention
        @return: True if a video is already encoded
        @rtype: boolean
        """
        bIsEncoded = self.videoFile.endswith(".avi") and\
                      (self.audioCodec is not None and "mp" in self.audioCodec.lower()) and\
                      (self.videoCodec is not None and "h264" in self.videoCodec.lower())
        try:
            day = "-".join(os.path.split(self.videoPath)[-1].split("-", 3)[:3])
            time.strptime(day, "%Y-%m-%d")
        except:
            bIsEncoded = False
        try:
            time.strptime(self.videoFile.split("-")[0], "%Hh%Mm%Ss")
        except:
            bIsEncoded = False
        return bIsEncoded

    def mkdir(self):
        if not OP.isdir("%s/%s" % (Video.root, self.timeStamp.date().isoformat())):
            os.mkdir("%s/%s" % (Video.root, self.timeStamp.date().isoformat()))
        self.destinationFile = os.path.join(Video.root, self.timeStamp.date().isoformat(), "%s-%s.avi" % (self.timeStamp.strftime("%Hh%Mm%Ss"), self.camera))
        if OP.isfile(self.destinationFile):
            logging.warning(str("Destination file %s exists !" % self.destinationFile))


    def loadMetadata(self):
        """Load the metadata, either using Hachoir, ... either using mplayer"""
        if len(self.videoFile) != 0:
            filename = OP.join(self.videoPath, self.videoFile)
            filename, realname = unicodeFilename(filename), filename
            myParser = createParser(filename, realname)
            try:
                hachoirMetadata = extractMetadata(myParser)
            except HachoirError, err:
                print "Metadata extraction error: %s" % unicode(err)
                hachoirMetadata = None
        if hachoirMetadata:
            bDoMplayer = False
            try:
                self.timeStamp = hachoirMetadata.get("creation_date")
            except:
                pass
            if type(self.timeStamp) == type(datetime.date(2000, 10, 10)):
                try:
                    hour = datetime.time(*time.strptime(self.videoFile[:9], "%Hh%Mm%Ss")[3:6])
                except:
                    hour = datetime.time(0, 0, 0)
                self.timeStamp = datetime.datetime.combine(self.timeStamp, hour)
            try:
                self.duration = hachoirMetadata.get("duration").seconds
            except:
                bDoMplayer = True
            try:
                self.width = hachoirMetadata.get("width")
                self.height = hachoirMetadata.get("height")
            except:
                bDoMplayer = True
            try:
                self.title = hachoirMetadata.get("title").encode("latin1").decode("utf8")
            except:
                self.title = u""
            try:
                self.frameRate = hachoirMetadata.get("frame_rate")
            except:
                bDoMplayer = True
                #self.frameRate = 24 #default value for Canon G11

            try:
                self.bitRate = hachoirMetadata.get("bit_rate")
            except:
                bDoMplayer = True
                #self.bitRate = None
            oldcamera = self.camera
            try:
                self.camera = hachoirMetadata.get("producer").replace(" ", "_")
                self.deinterleave = False
            except:
                self.camera = oldcamera
            try:
                hachoirMetadata.iterGroups()
            except:
                bDoMplayer = True
            if not bDoMplayer:
                for n in hachoirMetadata.iterGroups():
                    if n.header.startswith("Video stream"):
                        self.videoCodec = n.get("compression")
                        self.videoBpP = n.get("bits_per_pixel")
                    elif n.header.find("Audio stream") == 0:
                        self.audioCodec = n.get("compression")
                        self.audioBitRate = n.get("bit_rate")
                        self.videoBitRate = self.bitRate - self.audioBitRate
                        self.audioSampleRate = n.get("sample_rate")
                        try:
                            self.audioBits = n.get("bits_per_sample")
                        except:
                            self.audioBits = None
            if bDoMplayer is True or \
                    (self.audioCodec is None) or \
                    (self.audioBitRate is None) or \
                    (self.audioSampleRate is None) or \
                    (self.videoBitRate is None) or \
                    (self.audioBits is None) or \
                    (self.videoCodec) is None or \
                    (self.videoBpP) is None:
                self.MplayerMetadata()
        else:#Doing it in the not clean way, i.e. parse mplayer output !
            self.MplayerMetadata()

    def MplayerMetadata(self):
        """Extract metadata using Mplayer"""
#        for i in os.popen('%s "%s" -identify -vo null -ao null -frames 0 ' % (mplayer, self.fullPath)).readlines():
        mplayerProcess = subprocess.Popen([config.MPlayer, self.fullPath, "-identify", "-vo", "null", "-ao", "null", "-frames", "0"],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not mplayerProcess.wait() == 0:
            logging.warning("mplayer ended with error !")
        for i in  mplayerProcess.stdout.readlines():
            if i.startswith("ID_AUDIO_NCH"):
                self.audioChannel = int(i.split("=")[1].strip())
            elif i.startswith("ID_AUDIO_CODEC"):
                self.audioCodec = i.split("=")[1].strip()
            elif i.startswith("ID_AUDIO_RATE"):
                self.audioSampleRate = int(i.split("=")[1].strip())
            elif i.startswith("ID_AUDIO_BITRATE"):
                self.audioBitRate = int(i.split("=")[1].strip())
            elif i.startswith("ID_VIDEO_CODEC"):
                self.videoCodec = i.split("=")[1].strip()
            elif i.startswith("ID_LENGTH"):
                self.duration = float(i.split("=")[1].strip())
            elif i.startswith("ID_VIDEO_FPS"):
                self.frameRate = float(i.split("=")[1].strip())
            elif i.startswith("ID_VIDEO_HEIGHT"):
                self.height = int(i.split("=")[1].strip())
            elif i.startswith("ID_VIDEO_WIDTH"):
                self.width = int(i.split("=")[1].strip())
            elif i.startswith(" Source Form:"):
                self.camera = i.split(":")[1].strip()
            elif i.startswith(" Archival Location:"):
                self.origName = i.split(":")[1].strip()
            elif i.startswith(" Creation Date:"):
                videoDate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(i.split(":")[1].strip(), "%Y-%m-%d")))
                if videoDate.date < self.timeStamp.date:
                    self.timeStamp = datetime.datetime.combine(videoDate.date(), self.timeStamp.time())
            elif i.startswith(" Source:"):
                self.fastMd5 = i.split(":")[1].strip()

    def FindThumb(self):
        """scan the current directory for the thumbnail image"""
        for i in os.listdir(self.videoPath):
            b, e = OP.splitext(i)
            if self.videoFile.find(b) == 0 and e.lower() in config.ThumbnailExtensions:
                self.thumb = i
                filename = OP.join(self.videoPath, self.thumb)
                filename, realname = unicodeFilename(filename), filename
                myParser = createParser(filename, realname)
                try:
                    exif = extractMetadata(myParser)
                except:
                    return
                try:
                    self.rotation = exif.get("image_orientation")
                except:
                    self.rotation = None
                logging.info(str(self.rotation))
                ThmDate = exif.get("creation_date")
                if (self.timeStamp - ThmDate).days > 0:self.timeStamp = ThmDate


    def PlayVideo(self):
        """Plays the video using mplayer, tries to rotate the video of needed"""
        if self.rotation:
            if self.rotation == u"Rotated 90 clock-wise":
                os.system('%s -vf rotate=1 "%s"' % (config.MPlayer, self.fullPath))
            elif self.rotation == u"Rotated 90 counter clock-wise":
                os.system('%s -vf rotate=2 "%s"' % (config.MPlayer, self.fullPath))
            else:
                os.system('%s "%s"' % (config.MPlayer, self.fullPath))
            logging.info(str("self.rotation was: %s" % self.rotation))
        else:
            os.system('%s "%s"' % (config.MPlayer, self.fullPath))
            rotate = raw_input("What rotation should be applied to the file ? [0] ")
            rotate = rotate.strip().lower().decode(config.Coding)
            logging.debug(rotate)
            if rotate in ["90", "cw"]:
                self.rotation = u"Rotated 90 clock-wise"
            elif rotate in ["-90", "270", "ccw"]:
                self.rotation = u"Rotated 90 counter clock-wise"
            else:
                self.rotation = u"Horizontal (normal)"


    def setTitle(self):
        """asks for a Title and comments for the video"""

        print("Analyzing file %s" % self.fullPath)
        print("camera : %s" % self.camera)
        if self.title:
            print("Former title: %s" % self.title)
        self.title = raw_input("Title (INAM): ").decode(config.Coding).strip()
        if self.keywords:
            print "Former keywords: " + "\t".join(self.keywords.split(";"))
        self.keywords = raw_input("Keywords (IKEY): ").decode(config.Coding).split()
        self.toDisk()

    def getComment(self):
        data = {"ICRD":self.timeStamp.strftime("%Y-%m-%d"),
                "ISRC":self.fastMd5,
                }
        if self.origName:
            data["IARL"] = self.origName
        else:
            data["IARL"] = self.videoFile.replace("-H264", "")
        if self.camera:
            data["ISRF"] = self.camera
        if self.title:
            data["INAM"] = self.title
        if self.keywords:
            data["IKEY"] = ";".join(self.keywords)
        return os.linesep.join([u"%s %s" % (i, j) for i, j in data.iteritems()]).encode(config.Coding)



    def reEncode(self):
        """re-encode the video to the given quality, using the PBS queuing system"""
        self.mkdir()
        pbsFilename = os.path.splitext(self.fullPath.replace(" ", "_"))[0] + ".sh"
        pbsfile = open(pbsFilename, "w")
        pbsfile.write("#!/bin/bash\nWorkDir=$(mktemp -d --tempdir=%s -t imagizer-XXXXXX)\necho going to $WorkDir\ncd $WorkDir\n" % (config.ScratchDir))
        bDoResize = (self.width > 640)

        listVideoFilters = []
        if self.deinterleave is True:
            listVideoFilters.append("yadif=0")

        if bDoResize:
            listVideoFilters.append("scale=640:%i" % (self.height * 640 / self.width))

        if self.rotation:
            if self.rotation == u"Rotated 90 clock-wise":
                listVideoFilters.append("rotate=1")
            elif self.rotation == u"Rotated 90 counter clock-wise":
                listVideoFilters.append("rotate=2")

        if len(listVideoFilters) > 0:
            videoFilters = " -vf " + ",".join(listVideoFilters) + " "
        else:
            videoFilters = " "

        bDoAudio = (self.audioCodec.lower().find("pcm") >= 0)
        bDoAudio = bDoAudio or bDoResize
        bDoVideo = bDoResize or not (self.videoFile.lower().endswith(".avi"))
        bDoVideo = bDoVideo or not (self.videoCodec.lower().find("h264") >= 0 or self.videoCodec.lower().find("avc1") >= 0)
        if bDoAudio:
            newSampleRate = 44100
            wavaudio = "audio-%s.wav" % newSampleRate
            if (self.audioSampleRate == 11024) and (self.audioChannel == 1): #specific Ixus
                rawaudio = "audio-%s.raw" % self.audioSampleRate
                pbsfile.write(config.MPlayer + ' -quiet "%s" -dumpaudio   -dumpfile %s \n' % (self.fullPath, rawaudio))
                pbsfile.write(config.Sox + " -r %s -c %s -u -b 8 -t raw %s -r 44100 %s \n" % (self.audioSampleRate, self.audioChannel, rawaudio, wavaudio))
                pbsfile.write("rm %s \n" % rawaudio)
            elif self.audioSampleRate == 44100:
                wavaudio = "audio-44100.wav"
                pbsfile.write(config.MPlayer + ' -quiet -ao pcm:fast:file=%s -vo null "%s"  \n' % (wavaudio, self.fullPath))
            else:
                rawaudio = "audio-%s.wav" % self.audioSampleRate
                pbsfile.write(config.MPlayer + ' -quiet -ao pcm:fast:file=%s -vo null "%s"  \n' % (rawaudio, self.fullPath))
                pbsfile.write(config.Sox + " %s -r %s  %s \n" % (rawaudio, newSampleRate, wavaudio))
                pbsfile.write("rm %s \n" % rawaudio)

        tmpavi = "temporary.avi"
        if bDoVideo:
            if config.FramesPerSecond:
                ofps = "-ofps %s"%config.FramesPerSecond
            else:
                ofps = ""
            pbsfile.write(config.MEncoder + videoFilters + ' -quiet -nosound -ovc x264 -x264encopts bitrate=%s:pass=1:%s %s -o %s "%s" \n' % (config.VideoBitRate, config.X264Options, ofps, tmpavi, self.fullPath))
            pbsfile.write("rm %s \n" % tmpavi)
            pbsfile.write(config.MEncoder + videoFilters + ' -quiet -nosound -ovc x264 -x264encopts bitrate=%s:pass=3:%s %s -o %s "%s" \n' % (config.VideoBitRate, config.X264Options, ofps, tmpavi, self.fullPath))
            pbsfile.write("rm %s \n" % tmpavi)
            if bDoAudio:
                if self.audioChannel < 2:
                    pbsfile.write(config.MEncoder + videoFilters + ' -quiet -oac mp3lame -lameopts mode=3:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s %s -o %s "%s" \n' % (config.AudioBitRatePerChannel, wavaudio, config.VideoBitRate, config.X264Options, ofps, tmpavi, self.fullPath))
                else:
                    pbsfile.write(config.MEncoder + videoFilters + ' -quiet -oac mp3lame -lameopts mode=0:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s %s -o %s "%s" \n' % (2 * config.AudioBitRatePerChannel, wavaudio, config.VideoBitRate, config.X264Options, ofps, tmpavi, self.fullPath))
                pbsfile.write("rm %s \n" % wavaudio)
            else:
                pbsfile.write(config.MEncoder + videoFilters + ' -quiet -oac copy -ovc x264 -x264encopts bitrate=%s:pass=3:%s %s -o %s "%s" \n' % (config.VideoBitRate, config.X264Options, ofps, tmpavi, self.fullPath))
            pbsfile.write("if [ -f divx2pass.log ]; then rm divx2pass.log ; fi\n")
            pbsfile.write("if [ -f divx2pass.log.temp ]; then rm divx2pass.log.temp ; fi\n")
        else:
            pbsfile.write("cp %s %s\n" % (self.fullPath, tmpavi))
        pbsfile.write('cat  > comment.txt << EndOfComment\n')
        pbsfile.write(self.getComment() + "\n"*2)
        pbsfile.write('EndOfComment\n')
        pbsfile.write('%s -o %s -i %s -f comment.txt \n' % (config.AviMerge, self.destinationFile, tmpavi))
        pbsfile.write("rm %s \n" % tmpavi)
        pbsfile.flush()
        pbsfile.close()
        os.chmod(pbsFilename, stat.S_IEXEC + stat.S_IWRITE + stat.S_IREAD)
        pid = self.__class__.startProcessing(pbsFilename)
        logging.debug(str("Subprocess with pid=%s" % pid))


    def GenThumb(self, size=160):
        """Generate a thumbnail for the image"""
        tempdir = tempfile.mkdtemp()
        sub = subprocess.Popen([config.MPlayer, self.fullPath, "-vo", "jpeg:outdir=%s" % tempdir, "-ao", "null", "-frames", "1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sub.wait()
        listThumb = [os.path.join(tempdir, i) for i in os.listdir(tempdir)]
        if len(listThumb) != 1:
            print ("Unexpected result ... have a look at %s ther should only be one jpeg image" % tempdir)
        self.thumbName = OP.splitext(self.fullPath)[0] + "--Thumb.jpg"
        img = Image.open(listThumb[0])
        img.thumbnail((size, size))
        img.save(self.thumbName)
        for i in listThumb:
            os.remove(i)
        os.rmdir(tempdir)

################################################################################
# END of the class VIDEO
################################################################################


class PairVideo(object):
    """
    This class represents a pair of video:
    -Raw Video of any type
    -Encoded video in H264+MP3
    -metatdata can either come from an extra file beside the Raw video or from the header of the encoded video
    """
    def __init__(self, rawFile=None, encFile=None, rawVideo=None, encVideo=None, datetime=None, md5sum=None):
        """
        Constructor...
        """
        self.__fTime = None
        self.__datetime = None
        self.comment = None
        self.__md5sum = None
        self.__rawFile = None
        self.__rawVideo = None
        self.__encFile = None
        self.__encVideo = None
        if rawFile is not None:
            self.setRawFile(rawFile)
        if encFile is not None:
            self.setEncFile(encFile)
        if rawVideo is not None:
            self.setRawVideo(rawVideo)
        if encVideo is not None:
            self.setEncVideo(encVideo)
        if datetime is not None:
            self.__datetime = datetime
        if md5sum is not None:
            self.__md5sum = md5sum

    def __repr__(self):
        return "PairVideo( %s , %s ) with md5= '%s'" % (self.__rawFile, self.__encFile, self.__md5sum)

    def __cmp__(self, other):
        """
        Comparator for two pairs of videos
        """
        if self.__datetime < other.__datetime:
            return -1
        elif self.__datetime > other.__datetime:
            return 1
        else:
            return 0

    def getRawFile(self):
        return self.__rawFile
    def setRawFile(self, rawFile):
        """
        setter for raw file name
        @param rawFile: name of the raw file
        @type rawFile: string
        """
        self.__rawFile = rawFile
        if self.__datetime is None:
            self.__rawVideo = Video(self.__rawFile)
            self.setDateTime(self.__rawVideo.timeStamp)
        if self.__md5sum is None:
            self.setMd5(self.__rawVideo.fastMd5)
    rawFile = property(getRawFile, setRawFile, "property for get/setRawFile")

    def getEncFile(self):
        return self.__encFile
    def setEncFile(self, encFile):
        """
        setter for enc file
        @param encFile: name of the raw file
        @type encFile: string
        """
        self.__encFile = encFile
        if self.__datetime is None:
            self.__encVideo = Video(encFile)
            self.setDateTime(self.__encVideo.timeStamp)
    encFile = property(getEncFile, setEncFile, "Property for get/setEncFile")

    def getRawVideo(self):
        if (self.__rawVideo is None) and (self.__rawFile is not None):
            self.__rawVideo = Video(self.__rawFile)
        return self.__rawVideo
    def setRawVideo(self, rawVideo):
        """
        setter for raw file name
        @param rawVideo: input raw video
        @type rawVideo: instance of Video
        """
        self.__rawVideo = rawVideo
        self.__rawFile = rawVideo.fullPath
        self.setDateTime(self.__rawVideo.timeStamp)
        self.setMd5(rawVideo.fastMd5)
    rawVideo = property(getRawVideo, setRawVideo, "property for get/setRawVideo")

    def getEncVideo(self):
        if (self.__encVideo is None) and (self.__encFile is not None):
            self.__encVideo = Video(self.__encFile)
        return self.__encVideo
    def setEncVideo(self, encVideo):
        """
        setter for enc file
        @param encVideo: name of the raw file
        @type encVideo: string
        """
        self.__encVideo = encVideo
        self.__encFile = encVideo.fullPath
        self.setDateTime(self.__encVideo.timeStamp)
        if encVideo.origMd5:
            self.setMd5(encVideo.origMd5)
    encVideo = property(getEncVideo, setEncVideo, "Property for get/setEncVideo")

    def getMd5(self):
        return self.__md5sum
    def setMd5(self, md5):
        if self.__md5sum is None:
            self.__md5sum = md5
        else:
            if self.__md5sum != md5:
                logger.warning("Un-consistency between md5 was: %s is now %s." % (self.__md5sum, md5))
            self.__md5sum = md5
    md5sum = property(getMd5, setMd5, "Property for get/setMd5")

    def getDateTime(self):
        return self.__datetime
    def setDateTime(self, _dateTime):
        if self.__datetime is None:
            self.__datetime = _dateTime
        else:
            if self.__datetime > _dateTime:
                self.__datetime = _dateTime
    datetime = property(getDateTime, setDateTime, "Property for get/setDateTime")

    def toDisk(self):
        if self.__rawVideo is not None:
            self.__rawVideo.toDisk()
        if self.__encVideo is not None:
            self.__encVideo.toDisk()

    def reEncode(self):
        if self.__rawVideo is not None:
            self.__rawVideo.reEncode()
        else:
            logger.error("No raw video to encode !! \n%s"%self.__repr__())

    #TODO:
    #use python properties to set/read the underlying videos attributes.

################################################################################
# END of the class PairVideo
################################################################################

    def saveMetadata(self):
        if self.__rawVideo:
            self.__rawVideo.toDisk()
        if self.__encVideo:
            self.__encVideo.toDisk()

class AllVideos(object):
    """
    Class containing all videos in a given path.
    """
    def __init__(self, root):
        """
        Constructor
        @param root: path to the top of the tree to analyse
        @type root: string or unicode
        """
        self.__root = os.path.abspath(root)
        self.__listVideoFiles = []
        self.__dictVideoPairs = {} #key=md5sum
        self.__listVideoPairs = []
        self.current = 0
        self.load()
        self.rescan()

    def __len__(self):
        return len(self.__listVideoPairs)

    def __getitem__(self, key):
        res = None
        if isinstance(key, int):
            res = self.__listVideoPairs[key % len(self.__listVideoPairs)]
        elif isinstance(key, (str, unicode)):
            if key in self.__dictVideoPairs:
                res = self.__listVideoPairs[key]
            else:
                raise KeyError("No such key")
        else:
            raise KeyError("No such key")
        return res

    def __iter__(self):
        return self.__listVideoPairs.__iter__()

    def save(self, filename=None):
        """
        Save the list of video pairs to file.
        @param filename: filename of the file to be written.
        @type filename: string
        """
        if filename is None:
            filename = os.path.join(self.__root, ".video.lst")
        logger.debug("AllVideos.save to file %s" % filename)
        f = open(filename, "w")
        for vp in self.__listVideoPairs:
            f.write("%s\t%s\t%s\t%s%s" % (vp.datetime.isoformat(), vp.md5sum, vp.encFile, vp.rawFile, os.linesep))
        f.close()

    def load(self, filename=None):
        """
        Load the list of video pairs to file.
        @param filename: filename of the file to be written.
        @type filename: string
        """
        if filename is None:
            filename = os.path.join(self.__root, ".video.lst")
        if not os.path.isfile(filename):
            logger.warning("AllVideos.load: No such file %s" % filename)
            return
        else:
            logger.debug("AllVideos.load from file %s" % filename)
        for oneLine in  open(filename, "rb"):
            try:
                dt, md5, ef, rf = oneLine.split(None, 3)
            except:
                logger.warning("AllVideos.load: error in parsing %s" % oneLine)
            else:
                if md5 == "None":
                    continue
                if ef == "None" or not os.path.isfile(ef):
                    ef = None
                if rf == "None" or not os.path.isfile(rf):
                    rf = None
                if rf is None and ef is None:
                    continue
                try:
                    timestamp = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                except:
                    logger.warning("AllVideos.load: error in parsing datetime %s" % dt)
                    continue
                vp = PairVideo(rawFile=rf, encFile=ef, datetime=timestamp, md5sum=md5)
                if md5 in self.__dictVideoPairs:
                    logger.warning("AllVideos.load: Pair Video already loaded %s" % vp)
                else:
                    self.__listVideoPairs.append(vp)
                    self.__dictVideoPairs[md5] = vp
                    if ef is not None:
                        self.__listVideoFiles.append(ef)
                    if rf is not None:
                        self.__listVideoFiles.append(rf)

    def rescan(self):
        """
        Rescan all files, looking for new videos
        """
        logger.debug("Scanning folder %s" % self.__root)
        try:
            currentPair = self.__listVideoPairs[self.current]
        except:
            currentPair = None
        for root, dirs, files in os.walk(self.__root):
            for oneFile in files:
                if os.path.splitext(oneFile)[1].lower() in config.VideoExtensions:
                    videoFile = os.path.join(os.path.join(self.__root, root, oneFile))
                    if videoFile in self.__listVideoFiles:
                        continue #process only new files
                    video = Video(videoFile, root=self.__root)
                    md5 = video.fastMd5
                    if md5 in self.__dictVideoPairs:
                        pv = self.__dictVideoPairs[md5]
                        if video.isEncoded():
                            pv.setEncVideo(video)
                        else:
                            pv.setRawVideo(video)
                    else:
                        if video.isEncoded():
                            pv = PairVideo(encVideo=video)
                        else:
                            pv = PairVideo(rawVideo=video)
                        self.__listVideoPairs.append(pv)
                        self.__dictVideoPairs[pv.md5sum] = pv
        self.__listVideoPairs.sort()
        if currentPair is not None:
            self.current = self.__listVideoPairs.index(currentPair)

    def next(self):
        """
        @return: next pair of videos
        @rtype: instance of PairVideo
        """
        self.current = (self.current + 1) % len(self.__listVideoPairs)
        return self.__listVideoPairs[self.current]

    def previous(self):
        """
        @return: previous pair of videos
        @rtype: instance of PairVideo
        """
        self.current = (self.current - 1) % len(self.__listVideoPairs)
        return self.__listVideoPairs[self.current]

    def first(self):
        """
        @return: next pair of videos
        @rtype: instance of PairVideo
        """
        self.current = 0
        return self.__listVideoPairs[self.current]

    def last(self):
        """
        @return: last pair of videos
        @rtype: instance of PairVideo
        """
        self.current = len(self.__listVideoPairs) - 1
        return self.__listVideoPairs[self.current]

def test(inFile):
    allV = AllVideos(inFile)
    print "test 1"
    for i in range(len(allV)):
        print allV.next()

    print "test 2"
    for i in range(len(allV)):
        print allV[i]

    print "test 3"
    for i in allV:
        print i

    print "test 4"

if __name__ == "__main__":
    DEBUG = False
    inFile = False
    for key in sys.argv[1:]:
        if key.lower().find("-d") in [0, 1]:
            DEBUG = True
        elif os.path.exists(key):
            inFile = key
    if DEBUG:
        loggerImagizer = logging.getLogger("imagizer")
        loggerImagizer.setLevel(logging.DEBUG)
        logger.debug("We are in debug mode ...First Debug message")
    if inFile is None:
        print("To test those video classes, give apath containing videos in it.")
    else:
        test(inFile)
