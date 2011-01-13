#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Written by Jerome Kieffer 20100420 Licence GPLv3+
#Find all the videos and renames them, compress then .... and write an html file to set online

import logging

import os.path as OP
import os, sys, tempfile, shutil, datetime, time, locale
import subprocess
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
#from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
#from hachoir_core.i18n import getTerminalCharset

local = locale.getdefaultlocale()[1]
webEncoding = "latin1"
fileEncoding = "UTF8"

VIDEO_BIT_RATE = 600
AUDIO_BIT_RATE_PER_CHANNEL = 64
x264opts = "subq=7:nr=100:me=umh:partitions=all:direct_pred=auto:bframes=3:frameref=5 -ofps 25"

mplayer = "/usr/bin/mplayer"
mencoder = "/usr/bin/mencoder"
sox = "/usr/bin/sox"
convert = "/usr/bin/convert"
avimerge = "/usr/bin/avimerge"

VideoExts = [".avi", ".mpeg", ".mpg", ".mp4", ".divx", ".mov"]
ThumbExts = [".thm", ".jpg"]

RootDir = os.getcwd()
UpperDir = OP.split(RootDir)[0]


class Video:
    """main Video class"""
    def __init__(self, infile):
        """initialise the class"""
        self.fullPath = OP.abspath(infile)
        print "Processing %s" % self.fullPath
        [self.videoPath, self.videoFile] = OP.split(self.fullPath)
        self.title = u""
        self.width = 0
        self.height = 0
        self.rotation = None
        self.duration = 0
        self.camera = "Imagizer"
        self.root = None
        self.suffix = None
        self.metadata = None
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
        self.data = {}
        self.destinationFile = None
        self.thumbName = None
        self.thumb = None
        self.deinterleave = True

        self.timeStamp = datetime.datetime.fromtimestamp(OP.getmtime(self.fullPath))
        self.loadMetadata()
        if self.camera.lower().strip() in ["mencoder", "transcode", "imagizer"]:
            if self.videoFile.lower().startswith("dscf")  :
                self.camera = "Fuji"
            elif self.videoFile.lower().startswith("mvi_"):
                self.camera = "Canon"
            elif self.videoFile.lower().startswith("mov") :
                self.camera = "Sony"
            elif self.videoFile.lower().startswith("sdc") :
                self.camera = "Samsung"
            elif self.videoFile.lower().startswith("m2u") :
                self.camera = "Sony"
            elif self.videoFile.lower().startswith("p") :
                self.camera = "Panasonic"
            logging.debug(str("%s %s" % (self.videoFile.lower(), self.camera)))
        dirname = OP.split(self.videoPath)[1]
        dirdate = None
        if len(dirname) >= 10:
            if dirname[0] == "M": dirname = dirname[1:]
            try:
                dirdate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dirname[:10], "%Y-%m-%d")))
            except:
                pass
        if dirdate:
            if dirdate.date() < self.timeStamp.date():
                self.timeStamp = datetime.datetime.combine(dirdate.date(), self.timeStamp.time())
        self.data["ICRD"] = self.timeStamp.strftime("%Y-%m-%d")
        self.data["ISRF"] = self.camera
        self.data["IARL"] = self.videoFile.replace("-H264", "")
        self.CommentFile = OP.splitext(self.fullPath.replace(" ", "_"))[0] + ".txt"
        if OP.isfile(self.CommentFile):
            for l in open(OP.splitext(self.fullPath.replace(" ", "_"))[0] + ".txt").readlines():
                if len(l) > 2:
                    k, d = l.decode(fileEncoding).split(None, 1)
                    self.data[k] = d.strip()
        self.Date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(self.data["ICRD"], "%Y-%m-%d")))
        if self.Date.date < self.timeStamp.date:
            self.timeStamp = datetime.datetime.combine(self.Date.date(), self.timeStamp.time())
        self.camera = self.data["ISRF"]


    def __repr__(self):
        """Returns some information on the current video flux"""
        txt = "%s\n" % self.videoFile
        txt += "camera: %s\tWidth= %i\tHeigth= %i\n" % (self.camera, self.width, self.height)
        txt += "Type: %s,\t title:%s\n" % (type(self.title), self.title)
        for key in self.data:
            txt += "\t%s:\t%s\n" % (key, self.data[key])
        return txt


    def mkdir(self):
        if not OP.isdir("%s/%s" % (UpperDir, self.timeStamp.date().isoformat())):
            os.mkdir("%s/%s" % (UpperDir, self.timeStamp.date().isoformat()))
        self.destinationFile = os.path.join(UpperDir, self.timeStamp.date().isoformat(), "%s-%s.avi" % (self.timeStamp.strftime("%Hh%Mm%Ss"), self.camera))
        if OP.isfile(self.destinationFile):
            logging.warning(str("Destination file %s exists !" % self.destinationFile))


    def loadMetadata(self):
        """Load the metadata, either using Hachoir, ... either using mplayer"""
        if len(self.videoFile) != 0:
            filename = OP.join(self.videoPath, self.videoFile)
            filename, realname = unicodeFilename(filename), filename
            myParser = createParser(filename, realname)
            try:
                self.metadata = extractMetadata(myParser)
            except HachoirError, err:
                print "Metadata extraction error: %s" % unicode(err)
                self.metadata = None
        if self.metadata:
            bDoMplayer = False
            try:
                self.timeStamp = self.metadata.get("creation_date")
            except:
                pass
            if type(self.timeStamp) == type(datetime.date(2000, 10, 10)):
                try:
                    hour = datetime.time(*time.strptime(self.videoFile[:9], "%Hh%Mm%Ss")[3:6])
                except:
                    hour = datetime.time(0, 0, 0)
                self.timeStamp = datetime.datetime.combine(self.timeStamp, hour)
            self.duration = self.metadata.get("duration")
            self.width = self.metadata.get("width")
            try:
                self.title = self.metadata.get("title")
            except:
                self.title = ""
#            convertLatin1ToUTF8 = False
#            for i in self.title:
#                logging.debug("%s %s" % (i, ord(i)))
#                if ord(i) > 127: convertLatin1ToUTF8 = True
#            if convertLatin1ToUTF8:
#                self.title = self.title.encode("latin1").decode("UTF8")
#Work-around for latin1 related bug 
            self.height = self.metadata.get("height")
            try:
                self.frameRate = self.metadata.get("frame_rate")
            except:
                bDoMplayer = True
                #self.frameRate = 24 #default value for Canon G11

            try:
                self.bitRate = self.metadata.get("bit_rate")
            except:
                bDoMplayer = True
                #self.bitRate = None
            oldcamera = self.camera
            try:
                self.camera = self.metadata.get("producer").replace(" ", "_")
                self.deinterleave = False
            except:
                self.camera = oldcamera
            try:
                self.metadata.iterGroups()
            except:
                bDoMplayer = True
            if not bDoMplayer:
                for n in self.metadata.iterGroups():
                    if n.header.find("Video stream") == 0:
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
        mplayerProcess = subprocess.Popen([mplayer, self.fullPath, "-identify", "-vo", "null", "-ao", "null", "-frames", "0"],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if not mplayerProcess.wait() == 0:
            logging.warning("mplayer ended with error !")
        for i in  mplayerProcess.stdout.readlines():
            if i.find("ID_AUDIO_NCH") == 0:
                self.audioChannel = int(i.split("=")[1].strip())
            elif i.find("ID_AUDIO_CODEC") == 0:
                self.audioCodec = i.split("=")[1].strip()
            elif i.find("ID_AUDIO_RATE") == 0:
                self.audioSampleRate = int(i.split("=")[1].strip())
            elif i.find("ID_AUDIO_BITRATE") == 0:
                self.audioBitRate = int(i.split("=")[1].strip())
            elif i.find("ID_VIDEO_CODEC") == 0:
                self.videoCodec = i.split("=")[1].strip()
            elif i.find("ID_LENGTH") == 0:
                self.duration = float(i.split("=")[1].strip())
            elif i.find("ID_VIDEO_FPS") == 0:
                self.frameRate = float(i.split("=")[1].strip())
            elif i.find("ID_VIDEO_HEIGHT") == 0:
                self.height = int(i.split("=")[1].strip())
            elif i.find("ID_VIDEO_WIDTH") == 0:
                self.width = int(i.split("=")[1].strip())


    def FindThumb(self):
        """scan the current directory for the thumbnail image"""
        for i in os.listdir(self.videoPath):
            b, e = OP.splitext(i)
            if self.videoFile.find(b) == 0 and e.lower() in ThumbExts:
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
                os.system('mplayer -vf rotate=1 "%s"' % self.fullPath)
            elif self.rotation == u"Rotated 90 counter clock-wise":
                os.system('mplayer -vf rotate=2 "%s"' % self.fullPath)
            else:
                os.system('mplayer "%s"' % self.fullPath)
        else:
            os.system('mplayer "%s"' % self.fullPath)
            rotate = raw_input("What rotation should be applied to the file ? [0] ")
            rotate = rotate.strip().lower().decode(local)
            logging.debug(rotate)
            if rotate in ["90", "cw"]:
                self.rotation = u"Rotated 90 clock-wise"
            elif rotate in ["-90", "270", "ccw"]:
                self.rotation = u"Rotated 90 counter clock-wise"
            else:
                self.rotation = u"Horizontal (normal)"


    def setTitle(self):
        """asks for a Title and comments for the video"""
        print "Processing file %s" % self.fullPath
        print "camera : %s" % self.camera
        if self.data.has_key("INAM"):
            print "Former title: %s" % self.data["INAM"]
        title = raw_input("Title (INAM): ").decode(local)
        if len(title) > 0:
            self.data["INAM"] = title.strip()
        if self.data.has_key("IKEY"):
            print "Former keywords: " + "\t".join(self.data["IKEY"].split(";"))
        keywords = raw_input("Keywords (IKEY): ").decode(local).split()
        if len(keywords) > 0:
            self.data["IKEY"] = ";".join(keywords)
        f = open(self.CommentFile, "w")
        for i in self.data:
            f.write((u"%s %s\n" % (i, self.data[i])).encode(fileEncoding))
        f.close()


    def Rencode(self):
        """re-encode the video to the given quality"""
        if self.rotation:
            if self.rotation == u"Rotated 90 clock-wise":
                rotate = " -vf rotate=1 "
            elif self.rotation == u"Rotated 90 counter clock-wise":
                rotate = " -vf rotate=2 "
            else:
                rotate = " "
        bDoAudio = (self.audioCodec.lower().find("pcm") >= 0)
        #print "Audio spec= " + self.audioCodec
        bDoVideo = (not (self.videoCodec.lower().find("h264") >= 0 or self.videoCodec.lower().find("avc1") >= 0)) or self.videoFile.lower().endswith(".mov")
        logging.debug(str("DoAudio=%s\tDoVideo=%s" % (bDoAudio, bDoVideo)))
        if bDoAudio:
            __, rawaudio = tempfile.mkstemp(suffix=".raw")
            os.system(mplayer + " %s -dumpaudio   -dumpfile %s " % (self.fullPath, rawaudio))
            __, wavaudio = tempfile.mkstemp(suffix=".wav")
            print "AudioSampleRate= %s" % self.audioSampleRate
#            if self.audioSampleRate == 44100:
            os.system(sox + " -r %s -c %s -u -b 8 -t raw %s -r 44100 %s " % (self.audioSampleRate, self.audioChannel, rawaudio, wavaudio))
        __, tmpavi = tempfile.mkstemp(suffix=".avi")
        if False:
        #if bDoVideo:
            os.system(mencoder + rotate + " -nosound -ovc x264 -x264encopts bitrate=%s:pass=1:turbo=1:%s -o %s %s" % (VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
            os.remove(tmpavi)
            os.system(mencoder + rotate + " -nosound -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s %s" % (VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
            os.remove(tmpavi)
            if bDoAudio:
                os.system(mencoder + rotate + "-oac mp3lame -lameopts mode=3:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s %s " % (AUDIO_BIT_RATE_PER_CHANNEL, wavaudio, VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
#                os.remove(wavaudio)
            else:
                os.system(mencoder + rotate + "-oac copy -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s %s" % (VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
            if os.path.isfile("divx2pass.log"):os.remove("divx2pass.log")
            if os.path.isfile("divx2pass.log.temp"):os.remove("divx2pass.log.temp")
        else:
            shutil.copy(self.fullPath, tmpavi)
        print "%s -o %s -i %s -f %s" % (avimerge, self.destinationFile, tmpavi, self.CommentFile)
        os.system("%s -o %s -i %s -f %s" % (avimerge, self.destinationFile, tmpavi, self.CommentFile))
#        os.remove(tmpavi)


    def PBSRencode(self):
        """re-encode the video to the given quality, using the PBS queuing system"""
        pbsFilename = os.path.splitext(self.fullPath.replace(" ", "_"))[0] + ".pbs"
        pbsfile = open(pbsFilename, "w")
        pbsfile.write("#!/bin/bash\n#PBS -d/scratch\nif  [ -d /scratch/$PBS_JOBID ] ; then cd /scratch/$PBS_JOBID ;else cd /tmp; fi\n")

        bDoResize = (self.width > 640)

        videoFilters = " -vf"
        if self.deinterleave is True:
            videoFilters += " yadif=0"

        if bDoResize:
            if len(videoFilters) < 5:
                videoFilters += " "
            else:
                videoFilters += ","
            videoFilters += "scale=640:%i" % (self.height * 640 / self.width)

        if self.rotation:
            if len(videoFilters) < 5:
                videoFilters += " "
            else:
                videoFilters += ","
            if self.rotation == u"Rotated 90 clock-wise":
                videoFilters += "rotate=1 "
            elif self.rotation == u"Rotated 90 counter clock-wise":
                videoFilters = "rotate=2 "
        if len(videoFilters) < 6:
            videoFilters = " "
        else:
            videoFilters = videoFilters[:-1]
# last line of video filters
        videoFilters += " "

        bDoAudio = (self.audioCodec.lower().find("pcm") >= 0)
        bDoAudio = bDoAudio or bDoResize
        bDoVideo = bDoResize or not (self.videoFile.lower().endswith(".avi"))
        bDoVideo = bDoVideo or not (self.videoCodec.lower().find("h264") >= 0 or self.videoCodec.lower().find("avc1") >= 0)
        if bDoAudio:
            newSampleRate = 44100
            wavaudio = "audio-%s.wav" % newSampleRate
            if (self.audioSampleRate == 11024) and (self.audioChannel == 1): #specific Ixus 
                rawaudio = "audio-%s.raw" % self.audioSampleRate
                pbsfile.write(mplayer + ' "%s" -dumpaudio   -dumpfile %s \n' % (self.fullPath, rawaudio))
                pbsfile.write(sox + " -r %s -c %s -u -b 8 -t raw %s -r 44100 %s \n" % (self.audioSampleRate, self.audioChannel, rawaudio, wavaudio))
                pbsfile.write("rm %s \n" % rawaudio)
            elif self.audioSampleRate == 44100:
                wavaudio = "audio-44100.wav"
                pbsfile.write(mplayer + ' -ao pcm:fast:file=%s -vo null "%s"  \n' % (wavaudio, self.fullPath))
            else:
                rawaudio = "audio-%s.wav" % self.audioSampleRate
                pbsfile.write(mplayer + ' -ao pcm:fast:file=%s -vo null "%s"  \n' % (rawaudio, self.fullPath))
                pbsfile.write(sox + " %s -r %s  %s \n" % (rawaudio, newSampleRate, wavaudio))
                pbsfile.write("rm %s \n" % rawaudio)

        tmpavi = "temporary.avi"
        if bDoVideo:
            pbsfile.write(mencoder + videoFilters + ' -nosound -ovc x264 -x264encopts bitrate=%s:pass=1:%s -o %s "%s" \n' % (VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
            pbsfile.write("rm %s \n" % tmpavi)
            pbsfile.write(mencoder + videoFilters + ' -nosound -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
            pbsfile.write("rm %s \n" % tmpavi)
            if bDoAudio:
                if self.audioChannel < 2:
                    pbsfile.write(mencoder + videoFilters + ' -oac mp3lame -lameopts mode=3:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (AUDIO_BIT_RATE_PER_CHANNEL, wavaudio, VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
                else:
                    pbsfile.write(mencoder + videoFilters + ' -oac mp3lame -lameopts mode=0:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (2 * AUDIO_BIT_RATE_PER_CHANNEL, wavaudio, VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
                pbsfile.write("rm %s \n" % wavaudio)
            else:
                pbsfile.write(mencoder + videoFilters + '-oac copy -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (VIDEO_BIT_RATE, x264opts, tmpavi, self.fullPath))
            pbsfile.write("if [ -f divx2pass.log ]; then rm divx2pass.log ; fi\n")
            pbsfile.write("if [ -f divx2pass.log.temp ]; then rm divx2pass.log.temp ; fi\n")
        else:
            pbsfile.write("cp %s %s\n" % (self.fullPath, tmpavi))
#            shutil.copy(self.fullPath, tmpavi)
        pbsfile.write('%s -o %s -i %s -f "%s" \n' % (avimerge, self.destinationFile, tmpavi, self.CommentFile))
        pbsfile.write("rm %s \n" % tmpavi)
        pbsfile.close()
        os.system('qsub "%s"' % pbsFilename)


    def GenThumb(self, size=160):
        """Generate a thumbnail for the image"""
        Thumbdir = tempfile.mkdtemp()
        os.system("%s %s -vo jpeg:outdir=%s -ao null -frames 1 " % (mplayer, self.fullPath, Thumbdir))
        self.thumbName = OP.splitext(self.fullPath)[0] + "--Thumb.jpg"
        os.system("%s -geometry %ix%i %s/*.jpg %s" % (convert, size, size, Thumbdir, self.thumbName))
        for i in os.listdir(Thumbdir):os.remove(OP.join(Thumbdir, i))
        os.rmdir(Thumbdir)

################################################################################
# END of the class VIDEO
################################################################################

def FindFile(rootDir):
    """returns a list of the files with the given suffix in the given dir
    files=os.system('find "%s"  -iname "*.%s"'%(rootDir,suffix)).readlines()
    """
    files = []
    for i in VideoExts:
        files += parser().findExts(rootDir, i)
    good = []
    l = len(rootDir) + 1
    for i in files: good.append(i.strip()[l:])
    good.sort()
    return good



class parser:
    """this class searches all the jpeg files"""
    def __init__(self):
        self.imagelist = []
        self.root = None
        self.suffix = None


    def oneDir(self, curent):
        """ append all the imagesfiles to the list, then goes recursively to the subdirectories"""
        ls = os.listdir(curent)
        for i in ls:
            a = os.path.join(curent, i)
            if    os.path.isdir(a):
                self.oneDir(a)
            if  os.path.isfile(a):
                if i.lower().endswith(self.suffix):
                    self.imagelist.append(os.path.join(curent, i))


    def findExts(self, root, suffix):
        self.root = root
        self.suffix = suffix
        self.oneDir(self.root)
        return self.imagelist



class HTML(object):

    def __init__(self, title="Test", enc="latin1", favicon=None):
        self.txt = u""
        self.enc = enc
        self.header(title, enc, favicon)


    def header(self, title, enc, favicon):
        self.txt += '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n<html>\n<head>\n'
        if favicon:
            self.txt += '<link rel="icon" type="image/%s" href="%s" />\n' % (OP.splitext(favicon)[1][1:], favicon)
        if enc:self.txt += '<content="text/html; charset=%s">\n' % enc
        self.txt += "<title>%s</title>\n" % title
        self.txt += "</head>\n"


    def footer(self):
        self.txt += "</html>\n"


    def write(self, filename):
        self.footer()
        f = open(filename, "w")
        f.write(self.txt.encode(self.enc))
        f.close()


    def start(self, tag, dico=None):
        self.txt += "<%s" % tag
        if isinstance(dico, dict):
            for i in dico:
                self.txt += ' %s="%s" ' % (i, dico[i])
        self.txt += " >\n"


    def stop(self, tag):
        self.txt += "</%s>\n" % tag


    def data(self, donnee, cod=""):
        if cod:
            d = donnee.decode(cod)
        else:
            d = donnee
        self.txt += d.replace(u"&", u"&amp;").replace(u"<", u"&lt;").replace(u">", u"&gt;").replace(u'\xb0', u"&deg;").replace(u"\xb9", u"&sup1;").replace(u"\xb2", u"&sup2;").replace(u"\xb3", u"&sup3;").replace(u"\xb5", u"&micro;")
#    s = replace(s, "", "&Aring;")
#    s = replace(s, "", "&szlig;")

    def element(self, tag, data="", cod=""):
        self.start(tag)
        self.data(data, cod)
        self.stop(tag)



def RelativeName(Name):
    cur = []
    a = RootDir
    while len(a) > 1:
        a, b = os.path.split(a)
        cur.append(b)
    cur.reverse()
    fil = []
    a = Name
    while len(a) > 1:
        a, b = os.path.split(a)
        fil.append(b)
    fil.reverse()
    newfil = []
    for i in range(len(fil)):
#        print i,newfil
        if len(cur) < i + 1:newfil.append(fil[i])
        elif fil[i] == cur[i]:continue
    return OP.join(*tuple(newfil))





################################################################################################
############ Main program Start ################################################################
################################################################################################
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if OP.isdir(sys.argv[1]):
            RootDir = sys.argv[1]
    if sys.argv[0].lower().find("nommevideo") >= 0:
        Action = "Rename"
    elif sys.argv[0].lower().find("genhtml") >= 0:
        Action = "GenHTML"
    else: #sys.argv[0].lower().find("genhtml") >= 0:
        Action = "DEBUG"
    UpperDir = OP.split(RootDir)[0]
    if Action == "Rename":
        for onefile in FindFile(RootDir):
    #for onefile in os.listdir("."):
    #    if OP.splitext(onefile)[1].lower() in VideoExts:
            vi = Video(onefile)
            vi.FindThumb()
            vi.mkdir()
            if not OP.isfile(vi.destinationFile):
                vi.PlayVideo()
                logging.info(vi.__repr__())
                vi.setTitle()
                vi.PBSRencode()
    elif Action == "GenHTML":
        videos = {}
        for onefile in FindFile(RootDir):
            vi = Video(onefile)
            if not videos.has_key(vi.timeStamp.date().isoformat()):
                videos[vi.timeStamp.date().isoformat()] = [vi]
            else:
                videos[vi.timeStamp.date().isoformat()].append(vi)
        date = videos.keys()
        date.sort()
        print date
        html = HTML("Videos", enc=webEncoding)
        html.start("body")
        html.element("a name='begin'")

        for onedate in date:
            html.element("b", videos[onedate][0].timeStamp.date().strftime("%A, %d %B %Y").capitalize().decode(local))
            html.start("table", {"cellspacing":10})
            for onevideo in videos[onedate]:
                onevideo.GenThumb()
                html.start("tr")
                html.start("td", {"width":200})
                print RelativeName(onevideo.fullPath)
                html.start("a", {"href":RelativeName(onevideo.fullPath)})
                thumb = RelativeName(onevideo.thumbName)
                html.start("img", {"src":thumb, "alt":thumb})
                html.stop("img")
                html.stop("a")
                html.stop("td")
                html.start("td")
                html.data(onevideo.timeStamp.time().strftime("%Hh%Mm%Ss").decode(local))
                html.start("br")
                logging.debug(str("duration: %s" % onevideo.duration))
                html.data(u"Dur\xe9e %is" % onevideo.duration.seconds)
                html.stop("td")
                html.element("td", onevideo.title)
                html.stop("tr")
            html.stop("table")
            html.start("hr/")
        html.element("a name='end'")
        html.stop("body")
        html.write("index.html")
#        for onevideo in videos[onedate]:
#            logging.info(onevideo.timeStamp)

    else:
        videos = {}
        for onefile in FindFile(RootDir):
            vi = Video(onefile)
            if not videos.has_key(vi.timeStamp.date().isoformat()):
                videos[vi.timeStamp.date().isoformat()] = [vi]
            else:
                videos[vi.timeStamp.date().isoformat()].append(vi)
        date = videos.keys()
        date.sort()
        logging.info("List of all dates:" + os.linesep.join(date))
        for onedate in date:
            for onevideo in videos[onedate]:
                try:
                    logging.info(str(onevideo))
                except:
                    logging.error(str("in processing %s " % onevideo.fullPath))
                    logging.error(str(onevideo.__repr__()))
                print "#" * 50

