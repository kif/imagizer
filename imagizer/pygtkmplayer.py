# coding: utf8
__author__ = "Jérôme Kieffer"
__contact = "imagizer@terre-adelie.org"
__date__ = "20111016"
__license__ = "GPL"
import pygtk
pygtk.require('2.0')
import gtk
import os
import tempfile
import subprocess
import logging
import imagizer
logger = logging.getLogger("imagizer")
config = imagizer.Config()

class PyGtkMplayer(gtk.Socket):
    """
    Interface with mplayer
    
    List of available commands: mplayer -input cmdlist
    http://www.mplayerhq.hu/DOCS/tech/slave.txt
    """

    def __init__(self):
        gtk.Socket.__init__(self)
        logger.debug("PyGtkMplayer: without fifo")
        self.mplayerSubP = None
        self.currentFile = None
        self.videoFilter = None
        self.listMplayerCmd = None

    def startmplayer(self):
        self.mplayerSubP = subprocess.Popen(self.listMplayerCmd,
                 stdin=subprocess.PIPE
#                ,stdout=subprocess.PIPE
                )


    def execmplayer(self, cmd):
        "Write in the pipe in slave mode"
        if self.mplayerSubP.poll() is not None:
            self.startmplayer()
        self.mplayerSubP.stdin.write(cmd + os.linesep)

    def setwid(self, wid=None):
        "Run mplayer in the given window ID"
        logger.info("PyGtkMplayer: mplayer on wid=%s" % wid)
        self.listMplayerCmd = [config.MPlayer, "-nojoystick", "-nolirc", "-slave", "-vo", "x11", "-wid", str(wid), "-idle"]
        if self.videoFilter is not None:
            self.listMplayerCmd.append("-vf")
            self.listMplayerCmd += self.videoFilter.split()
        self.startmplayer()

    def loadfile(self, filename):
        self.currentFile = filename
        self.execmplayer("loadfile %s" % (filename))
#        self.execmplayer("change_rectangle 400 400")

    def play(self, *args):
        logger.debug("PyGtkMplayer: Play %s" % self.currentFile)
        self.execmplayer("loadfile %s" % self.currentFile)

    def pause(self, *args):
        logger.debug("PyGtkMplayer.pause")
        self.execmplayer("pause")

    def forward(self, *args):
        logger.debug("PyGtkMplayer.forward")
        self.execmplayer("seek +10")

    def backward(self, *args):
        logger.debug("PyGtkMplayer.backward")
        self.execmplayer("seek -10")

    def stop(self, *args):
        logger.debug("PyGtkMplayer.stop")
        self.execmplayer("stop")

    def quit(self, *args):
        logger.debug("PyGtkMplayer.quit")
        self.execmplayer("quit")

