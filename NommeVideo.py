#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#Written by Jerome Kieffer 20100228 Licence GPLv3+
#Find all the videos and renames them, compress then .... and write an html file to set online

import os.path as OP
import os, sys, tempfile, shutil, datetime, time, locale
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import getTerminalCharset

local = locale.getdefaultlocale()[1]
webEncoding = "latin1"
fileEncoding = "UTF8"

VBitrate = 600
ABitRate = 64
x264opts = "subq=7:nr=100:me=umh:partitions=all:direct_pred=auto:b_pyramid:bframes=3:frameref=5 -ofps 24"
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
        self.FullPath = OP.abspath(infile)
        print "Processing %s" % self.FullPath
        [self.Path, self.Video] = OP.split(self.FullPath)
        self.Width = 0
        self.Height = 0
        self.Rotate = None
        self.Duration = 0
        self.Producer = "Imagizer"
        self.data = {}
        self.DateTime = datetime.datetime.fromtimestamp(OP.getmtime(self.FullPath))
        self.LoadMetadata()
        if self.Producer.lower().strip() in ["mencoder", "transcode", "imagizer"]:
           if self.Video.lower().startswith("dscf")  :self.Producer = "Fuji"
           elif self.Video.lower().startswith("mvi_"):self.Producer = "Canon"
           elif self.Video.lower().startswith("mov") :self.Producer = "Sony"
           elif self.Video.lower().startswith("sdc") :self.Producer = "Samsung"
           print "DEBUG", self.Video.lower(), self.Producer
        dirname = OP.split(self.Path)[1]
        dirdate = None
        if len(dirname) >= 10:
            if dirname[0] == "M": dirname = dirname[1:]
            try:
                dirdate = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dirname[:10], "%Y-%m-%d")))
            except:
                pass
        if dirdate:
            if dirdate.date() < self.DateTime.date():
                self.DateTime = datetime.datetime.combine(dirdate.date(), self.DateTime.time())
        self.data["ICRD"] = self.DateTime.strftime("%Y-%m-%d")
        self.data["ISRF"] = self.Producer
        self.data["IARL"] = self.Video.replace("-H264", "")
        self.CommentFile = OP.splitext(self.FullPath.replace(" ", "_"))[0] + ".txt"
        if OP.isfile(self.CommentFile):
            for l in open(OP.splitext(self.FullPath.replace(" ", "_"))[0] + ".txt").readlines():
                if len(l) > 2:
                    k, d = l.decode(fileEncoding).split(None, 1)
                    self.data[k] = d.strip()
        self.Date = datetime.datetime.fromtimestamp(time.mktime(time.strptime(self.data["ICRD"], "%Y-%m-%d")))
        if self.Date.date < self.DateTime.date:
            self.DateTime = datetime.datetime.combine(self.Date.date(), self.DateTime.time())
        self.Producer = self.data["ISRF"]

    def __repr__(self):
        """Returns some information on the current video flux"""
        txt = self.Video + "\n"
        txt += "Producer: %s\tWidth= %i\tHeigth= %i\n" % (self.Producer, self.Width, self.Height)
        for i in self.data:
            txt += "%s:\t%s\n" % (i, self.data[i])
        return txt

    def MkDir(self):
        if not OP.isdir("%s/%s" % (UpperDir, self.DateTime.date().isoformat())):
            os.mkdir("%s/%s" % (UpperDir, self.DateTime.date().isoformat()))
        self.DestFile = os.path.join(UpperDir, self.DateTime.date().isoformat(), "%s-%s.avi" % (self.DateTime.strftime("%Hh%Mm%Ss"), self.Producer))
        if OP.isfile(self.DestFile):
            print "*" * 80 + "\n**  Warning Destination file exists ! **\n" + "*" * 80

    def LoadMetadata(self):
        """Load the metadata, either using Hachoir, ... either using mplayer"""
        if len(self.Video) != 0:
            filename = OP.join(self.Path, self.Video)
            filename, realname = unicodeFilename(filename), filename
            parser = createParser(filename, realname)
            try:
                self.metadata = extractMetadata(parser)
            except HachoirError, err:
                print "Metadata extraction error: %s" % unicode(err)
                self.metadata = None
        if self.metadata:
            DoMplayer = False
            try:
                self.DateTime = self.metadata.get("creation_date")
            except:
                pass
            if type(self.DateTime) == type(datetime.date(2000, 10, 10)):
                try:
                    hour = datetime.time(*time.strptime(self.Video[:9], "%Hh%Mm%Ss")[3:6])
                except:
                    hour = datetime.time(0, 0, 0)
                self.DateTime = datetime.datetime.combine(self.DateTime, hour)
            self.Duration = self.metadata.get("duration")
            self.Width = self.metadata.get("width")
            try:
                self.title = self.metadata.get("title")#.decode(fileEncoding)
            except:
                self.title = ""
            self.Height = self.metadata.get("height")
            try:
                self.FrameRate = self.metadata.get("frame_rate")
            except:
                self.FrameRate = 24 #default value for Canon G11
            try:
                self.BitRate = self.metadata.get("bit_rate")
            except:
                self.BitRate = None
            try:
                self.Producer = self.metadata.get("producer").replace(" ", "_")
            except:
                self.Producer = "Imagizer"
            try:
                self.metadata.iterGroups()
            except:
                DoMplayer = True
            if DoMplayer:
                self.MplayerMetadata()
            else:
                for n in self.metadata.iterGroups():
                    if n.header.find("Video stream") == 0:
                        self.VideoCodec = n.get("compression")
                        selfVideoBpP = n.get("bits_per_pixel")
                    elif n.header.find("Audio stream") == 0:
                        self.AudioCodec = n.get("compression")
                        self.AudioBitRate = n.get("bit_rate")
                        self.VideoBitRate = self.BitRate - self.AudioBitRate
                        self.AudioChannel = n.get("nb_channel")
                        self.AudioSampleRate = n.get("sample_rate")
                        try:
                            self.AudioBits = n.get("bits_per_sample")
                        except:
                            self.AudioBits = None
        else:#Doing it in the not clean way, i.e. parse mplayer output !
            self.MplayerMetadata()

    def MplayerMetadata(self):
        """Extract metadata using Mplayer"""
        for i in os.popen('%s "%s" -identify -vo null -ao null -frames 0 ' % (mplayer, self.FullPath)).readlines():
                if i.find("ID_AUDIO_NCH") == 0:self.AudioChannel = int(i.split("=")[1].strip())
                elif i.find("ID_AUDIO_CODEC") == 0:self.AudioCodec = i.split("=")[1].strip()
                elif i.find("ID_AUDIO_RATE") == 0:self.AudioSampleRate = int(i.split("=")[1].strip())
                elif i.find("ID_AUDIO_BITRATE") == 0:self.AudioBitRate = int(i.split("=")[1].strip())
                elif i.find("ID_VIDEO_CODEC") == 0:self.VideoCodec = i.split("=")[1].strip()
                elif i.find("ID_LENGTH") == 0:self.Duration = float(i.split("=")[1].strip())
                elif i.find("ID_VIDEO_FPS") == 0:self.FrameRate = float(i.split("=")[1].strip())
                elif i.find("ID_VIDEO_HEIGHT") == 0:self.Height = int(i.split("=")[1].strip())
                elif i.find("ID_VIDEO_WIDTH") == 0:self.Width = int(i.split("=")[1].strip())

    def FindThumb(self):
        """scan the current directory for the thumbnail image"""
        for i in os.listdir(self.Path):
            b, e = OP.splitext(i)
            if self.Video.find(b) == 0 and e.lower() in ThumbExts:
                self.Thumb = i
                filename = OP.join(self.Path, self.Thumb)
                filename, realname = unicodeFilename(filename), filename
                parser = createParser(filename, realname)
                try:
                    exif = extractMetadata(parser)
                except:
                    return
                try:
                    self.Rotate = exif.get("image_orientation")
                except:
                    self.Rotate = None
                print self.Rotate
                ThmDate = exif.get("creation_date")
                if (self.DateTime - ThmDate).days > 0:self.DateTime = ThmDate
    def PlayVideo(self):
        """Plays the video using mplayer, tries to rotate the video of needed"""
        if self.Rotate:
            if self.Rotate == u"Rotated 90 clock-wise":
                os.system('mplayer -vf rotate=1 "%s"' % self.FullPath)
            elif self.Rotate == u"Rotated 90 counter clock-wise":
                os.system('mplayer -vf rotate=2 "%s"' % self.FullPath)
            else:
                os.system('mplayer "%s"' % self.FullPath)
        else:
            os.system('mplayer "%s"' % self.FullPath)
            rotate = raw_input("What rotation should be applied to the file ? [0] ")
            rotate = rotate.strip().lower().decode(local)
            print rotate
            if rotate in ["90", "cw"]:
                self.Rotate = u"Rotated 90 clock-wise"
            elif rotate in ["-90", "270", "ccw"]:
                self.Rotate = u"Rotated 90 counter clock-wise"
            else:
                self.Rotate = u"Horizontal (normal)"
    def SetTitle(self):
        """asks for a Title and comments for the video"""
        print "Processing file %s" % self.FullPath
        print "Producer : %s" % self.Producer
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
        if self.Rotate:
            if self.Rotate == u"Rotated 90 clock-wise":
                rotate = " -vf rotate=1 "
            elif self.Rotate == u"Rotated 90 counter clock-wise":
                rotate = " -vf rotate=2 "
            else:
                rotate = " "
        DoAudio = (self.AudioCodec.lower().find("pcm") >= 0)
        #print "Audio spec= " + self.AudioCodec
        DoVideo = (not (self.VideoCodec.lower().find("h264") >= 0 or self.VideoCodec.lower().find("avc1") >= 0)) or self.Video.lower().endswith(".mov")
        print "DoAudio=%s\tDoVideo=%s" % (DoAudio, DoVideo)
        if DoAudio:
            __, rawaudio = tempfile.mkstemp(suffix=".raw")
            os.system(mplayer + " %s -dumpaudio   -dumpfile %s " % (self.FullPath, rawaudio))
            __, wavaudio = tempfile.mkstemp(suffix=".wav")
            print "AudioSampleRate= %s" % self.AudioSampleRate
            if self.AudioSampleRate == 44100:
                os.system(sox + " -r %s -c %s -u -b -t raw %s -r 44100 %s " % (self.AudioSampleRate, self.AudioChannel, rawaudio, wavaudio))
            else:
                os.system(sox + " -r %s -c %s -u -b -t raw %s -r 44100 %s resample " % (self.AudioSampleRate, self.AudioChannel, rawaudio, wavaudio))
#            os.remove(rawaudio)
        __, tmpavi = tempfile.mkstemp(suffix=".avi")
        if False:
        #if DoVideo:
            os.system(mencoder + rotate + " -nosound -ovc x264 -x264encopts bitrate=%s:pass=1:turbo=1:%s -o %s %s" % (VBitrate, x264opts, tmpavi, self.FullPath))
            os.remove(tmpavi)
            os.system(mencoder + rotate + " -nosound -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s %s" % (VBitrate, x264opts, tmpavi, self.FullPath))
            os.remove(tmpavi)
            if DoAudio:
                os.system(mencoder + rotate + "-oac mp3lame -lameopts mode=3:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s %s " % (ABitRate, wavaudio, VBitrate, x264opts, tmpavi, self.FullPath))
#                os.remove(wavaudio)
            else:
                os.system(mencoder + rotate + "-oac copy -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s %s" % (VBitrate, x264opts, tmpavi, self.FullPath))
            if os.path.isfile("divx2pass.log"):os.remove("divx2pass.log")
            if os.path.isfile("divx2pass.log.temp"):os.remove("divx2pass.log.temp")
        else:
            shutil.copy(self.FullPath, tmpavi)
        print "%s -o %s -i %s -f %s" % (avimerge, self.DestFile, tmpavi, self.CommentFile)
        os.system("%s -o %s -i %s -f %s" % (avimerge, self.DestFile, tmpavi, self.CommentFile))
#        os.remove(tmpavi)

    def PBSRencode(self):
        """re-encode the video to the given quality, using the PBS queuing system"""
        pbsFilename = os.path.splitext(self.FullPath.replace(" ", "_"))[0] + ".pbs"
        pbsfile = open(pbsFilename, "w")
        pbsfile.write("#!/bin/bash\nif  [ -d /tmp/$PBS_JOBID ] ; then cd /tmp/$PBS_JOBID ;else cd /tmp; fi\n")
        if self.Rotate:
            if self.Rotate == u"Rotated 90 clock-wise":
                rotate = " -vf rotate=1 "
            elif self.Rotate == u"Rotated 90 counter clock-wise":
                rotate = " -vf rotate=2 "
            else:
                rotate = " "
        Resize = False
        DoAudio = (self.AudioCodec.lower().find("pcm") >= 0)
#        DoResize = (self.Width == 1280) and (self.Height == 720)
        DoResize = (self.Width > 640)
        DoAudio = DoAudio or DoResize
        DoVideo = DoResize or not (self.Video.lower().endswith(".avi"))
        DoVideo = DoVideo or not (self.VideoCodec.lower().find("h264") >= 0 or self.VideoCodec.lower().find("avc1") >= 0)
        if DoAudio:
            wavaudio = "audio.wav"
            if self.AudioSampleRate == 44100:
                 pbsfile.write(mplayer + ' -ao pcm:fast:file=%s -vo null "%s"  \n' % (wavaudio, self.FullPath))
            else:
                rawaudio = "audio.raw"
                pbsfile.write(mplayer + " %s -dumpaudio   -dumpfile %s \n" % (self.FullPath, rawaudio))
                pbsfile.write(sox + " -r %s -c %s -u -b -t raw %s -r 44100 %s resample \n" % (self.AudioSampleRate, self.AudioChannel, rawaudio, wavaudio))
                pbsfile.write("rm %s \n" % rawaudio)

        tmpavi = "temporary.avi"
        if DoResize:
            #Resize = " -vf scale=736:416 "
            Resize = " -vf scale=640:%i " % (self.Height * 640 / self.Width)
            #Resize = " "
        else:
            Resize = " "
        if DoVideo:
            pbsfile.write(mencoder + rotate + Resize + ' -nosound -ovc x264 -x264encopts bitrate=%s:pass=1:turbo=1:%s -o %s "%s" \n' % (VBitrate, x264opts, tmpavi, self.FullPath))
            pbsfile.write("rm %s \n" % tmpavi)
            pbsfile.write(mencoder + rotate + Resize + ' -nosound -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (VBitrate, x264opts, tmpavi, self.FullPath))
            pbsfile.write("rm %s \n" % tmpavi)
            if DoAudio:
                pbsfile.write(mencoder + rotate + Resize + ' -oac mp3lame -lameopts mode=3:vbr=3:br=%s -audiofile %s -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (ABitRate, wavaudio, VBitrate, x264opts, tmpavi, self.FullPath))
                pbsfile.write("rm %s \n" % wavaudio)
            else:
                pbsfile.write(mencoder + rotate + Resize + '-oac copy -ovc x264 -x264encopts bitrate=%s:pass=3:%s -o %s "%s" \n' % (VBitrate, x264opts, tmpavi, self.FullPath))
            pbsfile.write("if [ -f divx2pass.log ]; then rm divx2pass.log ; fi\n")
            pbsfile.write("if [ -f divx2pass.log.temp ]; then rm divx2pass.log.temp ; fi\n")
        else:
            pbsfile.write("cp %s %s\n" % (self.FullPath, tmpavi))
#            shutil.copy(self.FullPath, tmpavi)
        pbsfile.write('%s -o %s -i %s -f "%s" \n' % (avimerge, self.DestFile, tmpavi, self.CommentFile))
        pbsfile.write("rm %s \n" % tmpavi)
        pbsfile.close()
        os.system('qsub "%s"' % pbsFilename)

    def GenThumb(self, size=160):
        """Generate a thumbnail for the image"""
        Thumbdir = tempfile.mkdtemp()
        os.system("%s %s -vo jpeg:outdir=%s -ao null -frames 1 " % (mplayer, self.FullPath, Thumbdir))
        self.ThumbName = OP.splitext(self.FullPath)[0] + "--Thumb.jpg"
        os.system("%s -geometry %ix%i %s/*.jpg %s" % (convert, size, size, Thumbdir, self.ThumbName))
        for i in os.listdir(Thumbdir):os.remove(OP.join(Thumbdir, i))
        os.rmdir(Thumbdir)







def FindFile(RootDir):
    """returns a list of the files with the given suffix in the given dir
    files=os.system('find "%s"  -iname "*.%s"'%(RootDir,suffix)).readlines()
    """
    files = []
    for i in VideoExts:
        files += parser().FindExts(RootDir, i)
    good = []
    l = len(RootDir) + 1
    for i in files: good.append(i.strip()[l:])
    good.sort()
    return good

class parser:
    """this class searches all the jpeg files"""
    def __init__(self):
        self.imagelist = []

    def OneDir(self, curent):
        """ append all the imagesfiles to the list, then goes recursively to the subdirectories"""
        ls = os.listdir(curent)
        subdirs = []
        for i in ls:
            a = os.path.join(curent, i)
            if    os.path.isdir(a):
                self.OneDir(a)
            if  os.path.isfile(a):
                if i.lower().endswith(self.suffix):
                    self.imagelist.append(os.path.join(curent, i))
    def FindExts(self, root, suffix):
        self.root = root
        self.suffix = suffix
        self.OneDir(self.root)
        return self.imagelist

class HTML:
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
    def start(self, tag, dico={}):
        self.txt += "<%s" % tag
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
    else:
        Action = "GenHTML"
    UpperDir = OP.split(RootDir)[0]
    if Action == "Rename":
        for filename in FindFile(RootDir):
    #for filename in os.listdir("."):
    #    if OP.splitext(filename)[1].lower() in VideoExts:
            vi = Video(filename)
            vi.FindThumb()
            vi.MkDir()
            if not OP.isfile(vi.DestFile):
                vi.PlayVideo()
                print vi
                vi.SetTitle()
                vi.PBSRencode()
    else:
        videos = {}
        for filename in FindFile(RootDir):
            vi = Video(filename)
            if not videos.has_key(vi.DateTime.date().isoformat()):
                videos[vi.DateTime.date().isoformat()] = [vi]
            else:
                videos[vi.DateTime.date().isoformat()].append(vi)
        date = videos.keys()
        date.sort()
        print date
        html = HTML("Videos", enc=webEncoding)
        html.start("body")
        html.element("a name='begin'")

        for i in date:
            html.element("b", videos[i][0].DateTime.date().strftime("%A, %d %B %Y").capitalize().decode(local))
            html.start("table", {"cellspacing":10})
            for j in videos[i]:
                j.GenThumb()
                html.start("tr")
                html.start("td", {"width":200})
                print RelativeName(j.FullPath)
                html.start("a", {"href":RelativeName(j.FullPath)})
                thumb = RelativeName(j.ThumbName)
                html.start("img", {"src":thumb, "alt":thumb})
                html.stop("img")
                html.stop("a")
                html.stop("td")
                html.start("td")
                html.data(j.DateTime.time().strftime("%Hh%Mm%Ss").decode(local))
                html.start("br")
    #            print j.Duration
                html.data("Durée %is" % j.Duration.seconds, "UTF8")
                html.stop("td")
                html.element("td", j.title, fileEncoding)
                html.stop("tr")
            html.stop("table")
            html.start("hr/")
        html.element("a name='end'")
        html.stop("body")
        html.write("index.html")
        for j in videos[i]:
            print j.DateTime




