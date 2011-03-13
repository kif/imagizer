#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2011,  Jérôme Kieffer <kieffer@terre-adelie.org>
#* Licence GPL v3+
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
__author__ = "Jérôme Kieffer"
__date__ = "15 march 2011"
__copyright__ = "Jérôme Kieffer"
__license__ = "GPLv3+"
__contact__ = "Jerome.Kieffer@terre-adelie.org"

import sys, os
from imagizer.pygtkmplayer import PyGtkMplayer
from imagizer.video import Video
from imagizer.imagizer import unifiedglade, smartSize
import logging
import imagizer
logger = logging.getLogger("imagizer")
logger.setLevel(logging.INFO)
try:
    import pygtk ; pygtk.require('2.0')
    import gtk
    import gtk.glade as GTKglade
except ImportError:
    raise ImportError("Selector needs pygtk and glade-2 available from http://www.pygtk.org/")


DEBUG = False

def intro(ob):
    import collections
    print "Introspection of %s" % ob
    for i in dir(ob):
        if isinstance(eval("ob.%s" % (i)), collections.Callable):
            logger.debug("%s\t\tMethod" % i)
        else:
            logger.debug("%s\t\tAttribute" % i)

class VideoInterface(object):
    """
    class interface that manages the GUI using Glade-2
    """
    def __init__(self, inFile):
        self.filename = inFile
        logger.info("Initialization of the windowed graphical interface ...")
        self.xml = GTKglade.XML(unifiedglade, root="videoWindow")
        self.xml.get_widget("videoWindow").resize(800, 400)
#        self.xml.get_widget("videoWindow").set_default_size(550, 400)
        self.xml.get_widget("videoWindow").show_now()
        hbox1 = self.xml.get_widget("hbox1")
        self.mplayer = PyGtkMplayer()
        hbox1.pack_end(self.mplayer)
        hbox1.show_all()
        self.mplayer.setwid(long(self.mplayer.get_id()))
        self.mplayer.loadfile(self.filename)
        self.flush_event_queue()
#        if config.ScreenSize == 300:
#            self.xml.get_widget("t300").set_active(1)
#            self.xml.get_widget("t600").set_active(0)
#            self.xml.get_widget("t900").set_active(0)
#            self.xml.get_widget("tauto").set_active(0)
        dictHandlers = {
        'on_videoWindow_destroy': self.destroy,
        'on_play_clicked': self.mplayer.play,
        "on_pause_clicked":self.mplayer.pause,
        "on_rewind_clicked":self.mplayer.backward,
        "on_forward_clicked":self.mplayer.forward,
        }

        self.xml.signal_autoconnect(dictHandlers)
#        self.flush_event_queue()
        self.video = None


    def flush_event_queue(self):
        """Updates the GTK GUI before coming back to the gtk.main()"""
#        self.xml.show_all()
        while gtk.events_pending():
            gtk.main_iteration()


    def destroy(self, *args):
        """destroy clicked by user"""
        self.mplayer.quit()
        gtk.main_quit()


    def loadVideo(self):
        """Load the video information and setup the GUI"""
        logger.debug("VideoInterface.loadVideo")
        self.video = Video(self.filename)
        self.xml.get_widget("mark").set_text(self.video.videoFile)
        self.xml.get_widget("model").set_text(self.video.camera.encode("UTF-8"))
        self.xml.get_widget("resolution").set_text("%ix%i" % (self.video.width, self.video.height))
        self.xml.get_widget("size").set_text("%.2f %s" % smartSize(os.path.getsize(self.filename)))
        self.xml.get_widget("dateTime").set_text(self.video.timeStamp.strftime("%Y:%m:%d %Hh%Mm%Ss"))
        self.xml.get_widget("duration").set_text("%s s" % self.video.duration)
        self.xml.get_widget("video").set_text("%.1f fps\t%s\t%s" % (self.video.frameRate, self.video.videoCodec, self.video.videoBitRate))
        self.xml.get_widget("audio").set_text("%i ch\t%.1fHz\t%s\t%s" % (self.video.audioChannel, self.video.audioSampleRate, self.video.audioCodec, self.video.audioBitRate))

if __name__ == "__main__":
    inFile = None
    for key in sys.argv[1:]:
        if key.lower().find("-d") in [0, 1]:
            DEBUG = True
        elif os.path.isfile(key):
            inFile = key
    if DEBUG:
        loggerImagizer = logging.getLogger("imagizer")
        loggerImagizer.setLevel(logging.DEBUG)
        logger.debug("We are in debug mode ...First Debug message")

    if inFile:
        logger.debug("%s" % inFile)
        gui = VideoInterface(inFile)
        gui.loadVideo()
        gtk.main()
