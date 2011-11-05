#!/usr/bin/env python 
# -*- coding: UTF8 -*-
#******************************************************************************\
#* $Source$
#* $Id$
#*
#* Copyright (C) 2006 - 2010,  Jérôme Kieffer <kieffer@terre-adelie.org>
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
__author__ = "Jérôme Kieffer"
__date__ = "23 Feb 2011"
__copyright__ = "Jerome Kieffer"
__license__ = "GPL"
__contact__ = "imagizer@terre-adelie.org"

import os
from encoding import unicode2html


class Html(object):
    """
    simple class to construct HTML pages
    """

    def __init__(self, title="Test", enc="utf8", favicon=None):
        self.lsttxt = []
        self.enc = enc
        self.header(title, enc, favicon)



    def header(self, title, enc, favicon):
        self.lsttxt = ['<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">', '<html>', '<head>']
        if favicon:
             self.lsttxt.append(u'<link rel="icon" type="image/%s" href="%s" />' % (OP.splitext(favicon)[1][1:], favicon))
        if enc:
             self.lsttxt.append(u'<content="text/html; charset=%s">' % enc)
        self.lsttxt.append(u"<title>%s</title>" % title)
        self.lsttxt.append(u"</head>")
        self.lsttxt.append(u"<body>")

    def footer(self):
        self.lsttxt.append(u"</body>")
        self.lsttxt.append(u"</html>")


    def write(self, filename):
        self.footer()
        f = open(filename, "w")
        f.write(os.linesep.join(self.lsttxt).encode(self.enc))
        f.close()


    def start(self, tag, dico=None):
        txt = u"<%s" % tag
        if isinstance(dico, dict):
            for i in dico:
                 txt += u' %s="%s" ' % (i, dico[i])
        self.lsttxt.append(txt + u" >")


    def stop(self, tag):
         self.lsttxt.append(u"</%s>" % tag)


    def data(self, donnee, encoding=None):
        if encoding and isinstance(donnee, str):
            d = donnee.decode(encoding)
        else:
            d = donnee
        self.lsttxt.append(unicode2html(d))


    def element(self, tag, data="", encoding=""):
        self.start(tag)
        self.data(data, encoding)
        self.stop(tag)

