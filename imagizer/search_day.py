#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2011,  Jérôme Kieffer <imagizer@terre-adelie.org>
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
Module containing most a class for searching a day in all
"""

__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20120415"
__license__ = "GPL"

import os, logging, time
import os.path as op
installdir = op.dirname(__file__)
logger = logging.getLogger("imagizer.search")

try:
    import pygtk ; pygtk.require('2.0')
    import gtk
    import gtk.glade as GTKglade
except ImportError:
    raise ImportError("Selector needs pygtk and glade-2 available from http://www.pygtk.org/")

from config import Config
from parser import AttrFile
config = Config()
from imagizer import unifiedglade, gtkFlush, timer_pass
from encoding import unicode2ascii

try:
    from rfoo.utils import rconsole
    rconsole.spawn_server()
except ImportError:
    logger.debug("No socket opened for debugging -> please install rfoo")

class Day(object):
    """class containing metadata for a directory"""
    cache = {}
    def __init__(self, filename):
        dirname, self.filename = os.path.split(filename)
        self.dirname = os.path.split(dirname)[-1]
        if self.dirname in self.__class__.cache:
            self.__dict__ = self.__class__.cache[self.dirname]
        else:
#            if not "year" in self.__dict__:
            self.year = self.month = self.day = self.comment = self.title = self.comment = self.picture = None
            self.analyse_name(self.dirname)
            self.analyse_comments()
            self.__class__.cache[self.dirname] = self.__dict__

    def __repr__(self):
        return "Day object: %s -> %s [%s/%s]" % (self.dirname, self.picture, self.title, self.comment)

    def analyse_name(self, dirname):
        if len(dirname) >= 10:
            try:
                timetuple = time.strptime(dirname[:10], "%Y-%m-%d")
            except ValueError:
                logger.error("Unable to handle such file: %s" % dirname)
            else:
                self.year, self.month, self.day = timetuple[:3]
            if len(dirname) > 11:
                self.title = dirname[11:]
            return

    def analyse_comments(self, idxname="index.desc"):
        indexfile = os.path.join(config.DefaultRepository, self.dirname, idxname)
        if os.path.isfile(indexfile):
            attr = AttrFile(indexfile)
            attr.read()
            if "comment" in attr:
                self.comment = attr["comment"]
            elif self.comment is None:
                self.comment = ""
            if "title" in attr:
                self.title = attr["title"]
            elif self.title is None:
                    self.title = ""
            if "image" in attr:
                self.picture = attr.get("image", self.filename)
            else:
                self.picture = self.filename

        else:
            self.picture = self.filename
            self.title = ""
            self.comment = ""

    def getdate(self):
        return [self.year, self.month, self.day]
    date = property(getdate)

    def getpicturepath(self):
        return os.path.join(config.DefaultRepository, self.dirname, self.picture)
    picture_path = property(getpicturepath)

    @classmethod
    def get(cls, key):
        """
        retrieve an instance from the cache   
        """
        instance = object.__new__(cls)
        instance.__dict__ = cls.cache[key]
        return instance

class SearchDay(object):
    """
    A class for searching a day from comments or title or dates
    """
    def __init__(self, lst_photo, callback=None):
        """
        @param lst_photo: list of input images...
        @param callback: callback function wich is called with the selected day/image on quit 
        """
        logger.info("Initialization of the search GUI")
        if callable(callback):
            self.callback = callback
        else:
            self.callback = logger.critical
        self.xml = GTKglade.XML(unifiedglade.replace("/imagizer/imagizer/", "/imagizer/"), root="SearchWindow")
        self.xml.get_widget("SearchWindow").show()
        self.timeout_handler_id = gtk.timeout_add(1000, timer_pass)
        dictSignals = {'on_SearchWindow_destroy': self.destroy,
                       "on_SearchButton_clicked": self.search,
                       "on_CalendarStart_day_selected_double_click":self.calendar,
                       "on_CalendarStop_day_selected_double_click":self.calendar,
                       "on_EntryStart_activate": self.date_changed,
                       "on_EntryStop_activate": self.date_changed,
                       "on_OK_clicked":self.validate,
                       "on_Cancel_clicked": self.destroy,
                       "on_InComment_activate":self.search,
                       "on_InTitle_activate":self.search,
                       }

        self.xml.signal_autoconnect(dictSignals)
        for img in lst_photo:
            a = Day(img)
        self.days = list(a.__class__.cache.keys())
        self.days.sort()
        first = Day.get(self.days[0])
        self.dateB = self.xml.get_widget("EntryStart")
        self.dateB.set_text("%02i/%02i/%04i" % (first.day, first.month, first.year))
        self.calB = self.xml.get_widget("CalendarStart")
        self.calB.select_month(first.month - 1, first.year)
        self.calB.select_day(first.day)

        last = Day.get(self.days[-1])
        self.dateE = self.xml.get_widget("EntryStop")
        self.dateE.set_text("%02i/%02i/%04i" % (last.day, last.month, last.year))
        self.calE = self.xml.get_widget("CalendarStop")
        self.calE.select_month(last.month - 1, last.year)
        self.calE.select_day(last.day)
        self.results = self.xml.get_widget("Results")
        self.store = gtk.ListStore(str, str, str, str)
        self.results.append_column(gtk.TreeViewColumn("Date", gtk.CellRendererText(), text=1))
        self.results.append_column(gtk.TreeViewColumn("Title", gtk.CellRendererText(), text=2))
        self.results.append_column(gtk.TreeViewColumn("Comment", gtk.CellRendererText(), text=3))
        self.results.set_model(self.store)

    def destroy(self, *args):
        """destroy clicked by user"""
        if self.xml.get_widget("SearchWindow"):
            self.xml.get_widget("SearchWindow").destroy()
        gtk.main_quit()

    def search(self, *args):
        logger.debug("search button pressed")
        t = self.calB.get_date()
        begin = "%04d-%02d-%02d" % (t[0], t[1] + 1, t[2])
        t = self.calE.get_date()
        end = "%04d-%02d-%02d" % (t[0], t[1] + 1, t[2])
        if end < begin:
            logger.warning("End date more recent than start time !!!")
            return
        inTitle = unicode2ascii(self.xml.get_widget("InTitle").get_text().lower()).split()
        inComment = unicode2ascii(self.xml.get_widget("InComment").get_text().lower()).split()
        print inTitle, inComment
        t0 = time.time()
        match = []
        for d in self.days:
            date = d[:10]
            if (end >= date >= begin):
                if len(inTitle) + len(inComment) == 0:
                    match.append(d)
                else:
                    day = Day.get(d)
                    good = False
                    for k in inTitle:
                        if k and (k in unicode2ascii(day.title.lower())):
                            good = True
                    if not good:
                        for k in inComment:
                            if k and (k in unicode2ascii(day.comment.lower())):
                                good = True
                    if good:
                        match.append(d)
        print("search took %.3f" % (time.time() - t0))
        self.store = gtk.ListStore(str, str, str, str)
        for i in match:
            d = Day.get(i)
            print(d)
            comment = d.comment.replace("<BR>", " ")
            if len(comment) > 60:
                comment = comment[:60] + "..."
            self.store.append([i, "%02i/%02i/%04i" % (d.day, d.month, d.year), d.title, comment])
        self.results.set_model(self.store)
        return match

    def calendar(self, *arg):
        logger.debug("Calendar day double clicked")
        start = self.calB.get_date()
        stop = self.calE.get_date()
        self.dateB.set_text("%02i/%02i/%04i" % (start[2], start[1] + 1, start[0]))
        self.dateE.set_text("%02i/%02i/%04i" % (stop[2], stop[1] + 1, stop[0]))

    def date_changed(self, *arg):
        logger.debug("date changed")
        try:
            timetuple = time.strptime(self.dateB.get_text(), "%d/%m/%Y")
        except:
            logger.warning("startDate: Unable to parse string to date")
        else:
            self.calB.select_month(timetuple[1] - 1, timetuple[0])
            self.calB.select_day(timetuple[2])
        try:
            timetuple = time.strptime(self.dateE.get_text(), "%d/%m/%Y")
        except:
            logger.warning("endDate: Unable to parse string to date")
        else:
            self.calE.select_month(timetuple[1] - 1, timetuple[0])
            self.calE.select_day(timetuple[2])

    def validate(self, *arg):
        logger.debug("validate")
        selection = self.results.get_selection()
        store, iter = selection.get_selected()
        path = store.get_value(iter, 0)
        path = os.path.join(path, Day.get(path).picture)
        self.callback(path)
        self.destroy()
        return path

if __name__ == "__main__":
    "test it"
    from imagizer import rangeTout
    listConfigurationFiles = ["/etc/imagizer.conf", os.path.join(os.getenv("HOME"), ".imagizer")]
    config.load(listConfigurationFiles)
    print config.DefaultRepository
    t0 = time.time()
    files, idx = rangeTout(config.DefaultRepository)
    print("startup took: %.3f;\tlen of files %s, %s" % (time.time() - t0, len(files), files[0]))
    t0 = time.time()
    for i in files:
        a = Day(i)
#        print a
    print("Analysis took: %.3f" % (time.time() - t0))
    print a
    print a.__dict__
    print len(a.cache)
    gui = SearchDay(files)
    gtk.main()
