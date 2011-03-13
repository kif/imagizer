# coding: utf8
import pygtk
pygtk.require('2.0')
import gtk
import os
import tempfile
import subprocess
import logging
import imagizer
logger = logging.getLogger("imagizer")

class PyGtkMplayer(gtk.Socket):
    """Interface with mplayer"""

    def __init__(self):
        gtk.Socket.__init__(self)
        self.fifo = tempfile.mktemp(".fifo", "mplayer")
        logger.debug("PyGtkMplayer: fifo name=" + self.fifo)
        self.mplayerSubP = None
        os.mkfifo(self.fifo)
        os.chmod(self.fifo, 0666)
        self.currentFile = None

    def execmplayer(self, cmd):
        "Write in the pipe in slave mode"
        open(self.fifo, 'w').write(cmd + os.linesep)

    def setwid(self, wid):
        "Run mplayer in the given window ID"
        logger.debug("PyGtkMplayer: mplayer on wid=%s" % wid)
        self.mplayerSubP = subprocess.Popen(
                ["mplayer", "-nojoystick", "-nolirc", "-slave", "-vo", "x11", "-wid", str(wid), "-idle", "-input", "file=%s" % self.fifo],
                stdout=subprocess.PIPE)
#        os.system(" &" % (wid, self.fifo))

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

    def quit(self, *args):
        logger.debug("PyGtkMplayer.quit")
        self.execmplayer("quit")
