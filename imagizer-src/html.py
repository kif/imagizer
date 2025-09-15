#!/usr/bin/env python
# coding: utf-8
# ******************************************************************************\
# *
# * Copyright (C) 2006 - 2010,  Jérôme Kieffer <kieffer@terre-adelie.org>
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
# *****************************************************************************/
__author__ = "Jérôme Kieffer"
__date__ = "15/09/2025"
__copyright__ = "Jerome Kieffer"
__license__ = "GPL"
__contact__ = "imagizer@terre-adelie.org"

import os
from .encoding import unicode2html


class Html(object):
    """
    simple class to construct HTML pages
    """

    def __init__(self, title="Test", enc="utf8", favicon=None):
        self.lsttxt = []
        self.enc = enc
        self.header(title, enc, favicon)

    def header(self, title, enc, favicon):
        self.lsttxt = [
            '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">',
            "<html>",
            "<head>",
        ]
        if favicon:
            self.lsttxt.append(
                f'<link rel="icon" type="image/{os.path.splitext(favicon)[1][1:]}" href="{favicon}" />'
            )
        if enc:
            self.lsttxt.append(f'<content="text/html; charset={enc}">')
        self.lsttxt.append(f"<title>{title}</title>")
        self.lsttxt.append("</head>")
        self.lsttxt.append("<body>")

    def footer(self):
        self.lsttxt.append("</body>")
        self.lsttxt.append("</html>")

    def write(self, filename):
        self.footer()
        f = open(filename, "w", encoding=self.enc)
        f.write(os.linesep.join(self.lsttxt))
        f.close()

    def start(self, tag, dico=None):
        txt = f"<{tag}"
        if isinstance(dico, dict):
            for i in dico:
                txt += f' {i}="{dico[i]}" '
        self.lsttxt.append(txt + " >")

    def stop(self, tag):
        self.lsttxt.append(f"</{tag}>")

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
