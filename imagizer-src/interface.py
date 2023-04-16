#!/usr/bin/env python
# coding: utf8
#
#******************************************************************************\
# * Copyright (C) 2006 - 2014,  Jérôme Kieffer <kieffer@terre-adelie.org>
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

__doc__ = """Graphical interface for selector."""
__author__ = "Jérôme Kieffer"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "16/04/2023"
__license__ = "GPL"

import gc
import os
import shutil
import logging
import random
import subprocess
import threading
import sys
if sys.version_info[0] > 2:
    unicode = str
logger = logging.getLogger("imagizer.interface")
from .imagizer import copy_selected, process_selected, to_jpeg
from . import qt
from .qt import buildUI, flush, icon_on, ExtendedQLabel, Signal
from .selection import Selected
from .photo import Photo
from .utils import get_pixmap_file
from .config import config, listConfigurationFiles
from .imagecache import image_cache, title_cache
from . import tree, __version__
from .dialogs import rename_day, quit_dialog, ask_media_size, synchronize_dialog, message_box, slideshow_dialog
from .search import SearchTitle
from .fileutils import smartSize, recursive_delete


class Interface(qt.QObject):
    """
    class interface that manages the GUI using Qt4
    """
    signal_status = Signal(str, int, int)
    signal_newfiles = Signal(list, int)
    signal_processed = Signal(list)

    def __init__(self, AllJpegs=None, first=0, selected=None, mode="Default", callback=None):
        qt.QObject.__init__(self)
        self.callback = callback
        self.left_tab_width = 350
        self.image = None
        self.processes = []
        self.job_sem = threading.Semaphore()
        self.fn_current = None
        self.is_zoomed = None
        self.min_mark = 0
        self.default_filter = None
        self.menubar_isvisible = True
        self.is_fullscreen = False
        self.in_slideshow = False
        self.treeview = None
        self.searchview = None
        self.rnd_lst = []
        logger.info("Initialization of the windowed graphical interface ...")
        self.gui = buildUI("principale")
        # Icons on buttons
        self.gui.logo.setPixmap(qt.QPixmap(get_pixmap_file("logo")))
        self._set_icons({"system": self.gui.filter,
                         "left":self.gui.left,
                         "right":self.gui.right,
                         "reload": self.gui.reload,
                         "next": self.gui.next,
                         "previous": self.gui.previous,
                         "gimp": self.gui.edit,
                         "trash": self.gui.trash
                         })
        icon_on("left", self.gui.previous)
        icon_on("left", self.gui.left)
        icon_on("right", self.gui.next)
        icon_on("right", self.gui.right)

        self.timer = None
        self.progress_bar = None
        self.status_bar = None
        self.create_statusbar()
        self._populate_action_data()
        self.gui.actionAutorotate.setChecked(bool(config.AutoRotate))
        self.gui.actionSignature_filigrane_web.setChecked(bool(config.Filigrane))

        self.set_images_per_page(value=config.NbrPerPage)
        self.set_interpolation(value=config.Interpolation)
#         self.show_image()
        flush()
        self._menu_filtrer()
        self._menu_editer()
        flush()
        self.navigation_dict = {
         # #Image
            self.gui.actionNav_img_first: ("image", "first"),
            self.gui.actionNav_img_previous10: ("image", "previous10"),
            self.gui.actionNav_img_previous: ("image", "previous"),
            self.gui.actionNav_img_next: ("image", "next"),
            self.gui.actionNav_img_next10: ("image", "next10"),
            self.gui.actionNav_img_last: ("image", "last"),
            # #Day
            self.gui.actionNav_day_first: ("day", "first"),
            self.gui.actionNav_day_previous: ("day", "previous"),
            self.gui.actionNav_day_next: ("day", "next"),
            self.gui.actionNav_day_last: ("day", "last"),
            # #Selected:
            self.gui.actionNav_sel_first: ("sel", "first"),
            self.gui.actionNav_sel_previous:("sel", "previous"),
            self.gui.actionNav_sel_next: ("sel", "next"),
            self.gui.actionNav_sel_last: ("sel", "last"),
            # #Non-selected:
            self.gui.actionNav_unsel_first: ("unsel", "first"),
            self.gui.actionNav_unsel_previous: ("unsel", "previous"),
            self.gui.actionNav_unsel_next: ("unsel", "next"),
            self.gui.actionNav_unsel_last: ("unsel", "last"),
            # #Entitled
            self.gui.actionNav_title_first: ("title", "first"),
            self.gui.actionNav_title_previous: ("title", "previous"),
            self.gui.actionNav_title_next: ("title", "next"),
            self.gui.actionNav_title_last: ("title", "last"),
            # #Non entitled
            self.gui.actionNav_untitle_first: ("untitle", "first"),
            self.gui.actionNav_untitle_previous: ("untitle", "previous"),
            self.gui.actionNav_untitle_next: ("untitle", "next"),
            self.gui.actionNav_untitle_last: ("untitle", "last"),
            }
        handlers = {self.gui.next.clicked:self.next1,
                    self.gui.previous.clicked: self.previous1,
                    self.gui.right.clicked:self.turn_right,
                    self.gui.left.clicked: self.turn_left,
                    self.gui.selection.stateChanged: self.select,
                    self.gui.trash.clicked: self.trash,
                    self.gui.edit.clicked:self.edit_im,
                    self.gui.reload.clicked:self.reload_img,
                    self.gui.filter.clicked:self.filter_im,

                    self.gui.menubar.triggered: self._action_handler,
                    self.gui.photo.zoom: self.image_zoom,
                    self.gui.photo.pan: self.image_pan,
                    self.signal_status: self.update_status,
                    self.signal_newfiles: self.set_data
        }
        for signal, callback in handlers.items():
            logger.debug(callback.__name__)
            signal.connect(callback)

        self.gui.show()
        flush()
        width = sum(self.gui.splitter.sizes())
        self.gui.splitter.setSizes([self.left_tab_width, width - self.left_tab_width])
        self.set_data(AllJpegs, first, selected)

    def set_data(self, AllJpegs=None, first=0, selected=None):
        self.AllJpegs = AllJpegs or []
        if selected is None:
            selected = Selected.load()
        self.selected = Selected(i for i in selected  if i in self.AllJpegs)
        self.idx_current = first
        if self.AllJpegs:
            self.show_image(first)

    def _set_icons(self, kwarg):
        """
        @param kwarg: dict with key: name of the image, value: widget
        """
        for name, widget in kwarg.items():
            icon = qt.QIcon()
            fullname = get_pixmap_file(name)
            pixmap = qt.QPixmap(fullname)
            icon.addPixmap(pixmap, qt.QIcon.Normal, qt.QIcon.Off)
            widget.setIcon(icon)

    def _menu_filtrer(self):
        # Drop-down filter menu
        self.filter_menu = qt.QMenu("Filtrer")

        icon_contrast = qt.QIcon()
        icon_contrast.addPixmap(qt.QPixmap(get_pixmap_file("contrast")), qt.QIcon.Normal, qt.QIcon.Off)
        action_contrast = qt.QAction(icon_contrast, "Masque de contrast", self.gui.filter)
        self.filter_menu.addAction(action_contrast)
        icon_colors = qt.QIcon()
        icon_colors.addPixmap(qt.QPixmap(get_pixmap_file("colors")), qt.QIcon.Normal, qt.QIcon.Off)
        action_color = qt.QAction(icon_colors, "Balance des blancs auto", self.gui.filter)
        self.filter_menu.addAction(action_color)
        self.gui.filter.setMenu(self.filter_menu)
        action_color.triggered.connect(self.filter_AutoWB)
        action_contrast.triggered.connect(self.filter_ContrastMask)

    def _menu_editer(self):
        # Drop-down filter menu
        self.edit_menu = qt.QMenu("Editer")

        icon_gimp = qt.QIcon()
        icon_gimp.addPixmap(qt.QPixmap(get_pixmap_file("image-editor")), qt.QIcon.Normal, qt.QIcon.Off)
        action_gimp = qt.QAction(icon_gimp, "Gimp", self.gui.edit)
        self.edit_menu.addAction(action_gimp)
        icon_rt = qt.QIcon()
        icon_rt.addPixmap(qt.QPixmap(get_pixmap_file("rt-logo")), qt.QIcon.Normal, qt.QIcon.Off)
        action_rt = qt.QAction(icon_rt, "RawTherapee", self.gui.edit)
        self.edit_menu.addAction(action_rt)
        self.gui.edit.setMenu(self.edit_menu)
        action_rt.triggered.connect(self.rawtherapee)
        action_gimp.triggered.connect(self.gimp)

    def _action_handler(self, act):
        """
        Generic action handler
        @param act: QAction
        """
        meth_name = str(act.data())
        logger.debug("Action %s => %s" % (act.text(), meth_name))

        try:
            callback = self.__getattribute__(meth_name)
        except AttributeError:
              logger.warning("Unhandeled menubar event on %s: no method %s" % (act.text(), meth_name))
        else:
            callback(act)

    def _populate_action_data(self):
        """
        Set the data in every action containing the name of the callback method
        """
        action_dict = {
            # Menu Fichier
            self.gui.actionName_day: "rename_day",
            #    <string>Ctrl+N</string>
            self.gui.actionDiaporama: "toggle_slideshow",
            #    <string>Ctrl+D</string>
            self.gui.actionPlein_cran: "toggle_fullscreen",
            #    <string>Ctrl+F</string>
            self.gui.actionTrash_Ctrl_Del: "trash",
            self.gui.actionImporter_Image: "importImages",
            self.gui.actionSynchroniser: "synchronize",
            self.gui.actionEmpty_selected: "empty_selected",
            self.gui.actionCopier_seulement: "copy",
            self.gui.actionVers_Jpeg: "to_jpeg",
            self.gui.actionCopier_et_graver: "burn",
            self.gui.actionCopier_et_redimensionner: "copy_resize",
            self.gui.actionVers_page_web: "to_web",
            self.gui.actionSortir: "destroy",
            #    <string>Ctrl+E</string>
            self.gui.actionQuitter: "die",
            #    <string>Ctrl+Q</string>

            # Menu Affichage
#                    self.gui.actionNote_minimale: self.start_image_mark_window,
            self.gui.actionReload: "reload_img",
            #    <string>Ctrl+R</string>
            self.gui.actionRotation_left: "turn_left",
            #    <string>Ctrl+Left</string>
            self.gui.actionRotation_right: "turn_right",
            #    <string>Ctrl+Right</string>
            self.gui.actionHide_toolbar: "toggle_toolbar",
            #    <string>Ctrl+T</string>

            # Menu Preference
            self.gui.actionMedia_size: "defineMediaSize",
            self.gui.actionAutorotate: "setAutoRotate",
            self.gui.actionSignature_filigrane_web:"setFiligrane",
            self.gui.actionSave_pref: "save_pref",
            self.gui.actionConfigurer_le_diaporama:"config_slideshow",

            # Menu Selection
            self.gui.selectionner: "select_shortcut",
            #    <string>Ctrl+S</string>
            self.gui.actionCharger: "load_selection",
            self.gui.actionSauver: "save_selection",
            self.gui.actionInverser: "invert_selection",
            self.gui.actionAucune: "select_none",
            self.gui.actionToutes: "select_all",
            self.gui.actionTaille_de_toute_la_selection: "display_selected_size",
            self.gui.actionCD_DVD_suivant: "selectMedia",
            self.gui.actionCD_DVD_precedent:"selectMedia",

#        self.gui.indexJ_activate': self.indexJ,
#        self.gui.searchJ_activate': self.searchJ,

            # Menu Filtres
            self.gui.actionAuto_whitebalance: "filter_AutoWB",
            self.gui.actionContrast_mask: "filter_ContrastMask",
            self.gui.actionGimp: "gimp",
            self.gui.actionRawTherapee: "rawtherapee",

            # Menu Aide
            self.gui.actionA_propos: "about",

            # Menu Preference
            self.gui.actionNearest:"set_interpolation",
            self.gui.actionLinear: "set_interpolation",
            self.gui.actionLanczos:"set_interpolation",
            self.gui.action9: "set_images_per_page",
            self.gui.action12: "set_images_per_page",
            self.gui.action16: "set_images_per_page",
            self.gui.action20: "set_images_per_page",
            self.gui.action25: "set_images_per_page",
            self.gui.action30: "set_images_per_page",
            self.gui.action0: "set_min_rate",
            self.gui.action1: "set_min_rate",
            self.gui.action2: "set_min_rate",
            self.gui.action3: "set_min_rate",
            self.gui.action4: "set_min_rate",
            self.gui.action5: "set_min_rate",
            # Menu navigation
            # #Image
            self.gui.actionNav_img_first: "navigate",
            self.gui.actionNav_img_previous10: "navigate",
            self.gui.actionNav_img_previous: "navigate",
            self.gui.actionNav_img_next: "navigate",
            self.gui.actionNav_img_next10: "navigate",
            self.gui.actionNav_img_last: "navigate",
            # #Day
            self.gui.actionNav_day_first: "navigate",
            self.gui.actionNav_day_previous: "navigate",
            self.gui.actionNav_day_next: "navigate",
            self.gui.actionNav_day_last: "navigate",
            # #Selected:
            self.gui.actionNav_sel_first: "navigate",
            self.gui.actionNav_sel_previous: "navigate",
            self.gui.actionNav_sel_next: "navigate",
            self.gui.actionNav_sel_last: "navigate",
            # #Non-selected:
            self.gui.actionNav_unsel_first: "navigate",
            self.gui.actionNav_unsel_previous: "navigate",
            self.gui.actionNav_unsel_next: "navigate",
            self.gui.actionNav_unsel_last: "navigate",
            # #Entitled
            self.gui.actionNav_title_first: "navigate",
            self.gui.actionNav_title_previous: "navigate",
            self.gui.actionNav_title_next: "navigate",
            self.gui.actionNav_title_last: "navigate",
            # #Non entitled
            self.gui.actionNav_untitle_first: "navigate",
            self.gui.actionNav_untitle_previous: "navigate",
            self.gui.actionNav_untitle_next: "navigate",
            self.gui.actionNav_untitle_last: "navigate",

            self.gui.actionNav_tree: "show_treeview",
            self.gui.actionRechercher: "show_searchview",

            }
        # assign as data the name of the method to be called as callback
        for k, v in action_dict.items():
            k.setData(v)
            self.gui.addAction(k)

    def update_title(self):
        """Set the new title of the image"""
        logger.debug("Interface.update_title")
        new_title = unicode(self.gui.title.text())
        new_rate = int(self.gui.rate.value())
        try:
            metadata = self.image.metadata
        except:
            metadata = {}
        else:
            metadata = metadata or {}
        if (new_title != metadata.get("title", "")) or (new_rate != metadata.get("rate", 0)):
            self.image.set_title(new_title, new_rate)

    def create_statusbar(self):
        self.status_bar = self.gui.statusBar()
        self.progress_bar = qt.QProgressBar(self.status_bar)
        self.status_bar.insertPermanentWidget(0, self.progress_bar, 0)
        self.status_bar.hide()

    def update_status(self, message="", current=0, maxi=0):
        """Update the status bar

        @param meassage: string to be displayed
        @param
        """
        if (message or current or maxi):
            self.status_bar.showMessage(message, 1000)
            if maxi:
                self.progress_bar.setMaximum(maxi)
                self.progress_bar.setValue(current)
            else:
                self.progress_bar.reset()
                # self.progress_bar.hide()
            self.status_bar.show()
        else:
            self.status_bar.clearMessage()
            self.status_bar.hide()

    def show_image(self, new_idx=None):
        """Show the image in the given widget and set up the exif tags in the GUI

        @param new_idx: index of the new image
        """
        logger.debug("Interface.showImage")
        if new_idx is not None:
            self.idx_current = new_idx
        else:
            new_idx = self.idx_current
        self.fn_current = self.AllJpegs[new_idx]
        self.image = Photo(self.fn_current)
        width, height = self.gui.photo.width(), self.gui.photo.height()
        logger.debug("Size of the image on screen: %sx%s" % (width, height))
        pixbuf = self.image.get_pixbuf(width, height)
        self.gui.photo.setPixmap(pixbuf)
        del pixbuf
        gc.collect()
        metadata = self.image.read_exif()
        if "rate" in metadata:
            self.gui.rate.setValue(int(float(metadata["rate"])))
            metadata.pop("rate")
        else:
            self.gui.rate.setValue(0)

        for key, value in metadata.items():
            try:
                self.gui.__getattribute__(key).setText(value)
            except Exception:  # unexcpected error
                logger.error("unexpected metadata %s: %s" % (key, value))

        self.gui.setWindowTitle("Selector : %s" % self.fn_current)
        self.gui.selection.setChecked(self.fn_current in self.selected)

    def calc_index(self, what="next", menu="image"):
        """
        @param what: can be "next, "next10","last", "previous10", "last" ...
        @param menu: can be "image", "day", "sel", "unsel", "title", "untitle", random
        @return: image index
        """
        logger.debug("calc_index %s %s %s" % (self.idx_current, what, menu))
        new_idx = current_idx = self.idx_current
        size = len(self.AllJpegs)
        if menu == "image":
            if what == "next":
                if self.min_mark == 0:
                    new_idx = current_idx + 1
                else:
                    for fn in self.AllJpegs[current_idx + 1:]:
                        image = Photo(fn)
                        data = image.read_exif()
                        if "rate" in data:
                            rate = int(float(data["rate"]))
                            if rate >= self.min_mark:
                                new_idx = self.AllJpegs.index(fn)
                                break
                    else:
                        new_idx = 0
                        logger.warning("No image found with rating > %s" % self.min_mark)

            elif what == "previous":
                if self.min_mark == 0:
                    new_idx = current_idx - 1
                else:
                    for fn in self.AllJpegs[current_idx - 1::-1]:
                        image = Photo(fn)
                        data = image.read_exif()
                        if "rate" in data:
                            rate = int(float(data["rate"]))
                            if rate >= self.min_mark:
                                new_idx = self.AllJpegs.index(fn)
                                break
                    else:
                        new_idx = 0
                        logger.warning("No image found with rating > %s" % self.min_mark)
            elif what == "next10":
                new_idx = current_idx + 10
            elif what == "previous10":
                new_idx = current_idx - 10
            elif what == "last":
                new_idx = len(self.AllJpegs) - 1
            elif what == "first":
                new_idx = 0

        elif menu == "day":
            day = os.path.dirname(self.AllJpegs[current_idx])
            if what == "next":
                for img in self.AllJpegs[current_idx:]:
                    if os.path.dirname(img) > day:
                        return  self.AllJpegs.index(img)
                else:
                    new_idx = len(self.AllJpegs) - 1
            elif what == "previous":
                if current_idx == 0:
                    return 0
                last = os.path.dirname(self.AllJpegs[current_idx - 1])
                for img in self.AllJpegs[current_idx - 1::-1]:
                    jc = os.path.dirname(img)
                    if (jc < day) and (jc < last):
                        return self.AllJpegs.index(img) + 1
                    last = jc
                new_idx = 0
            elif what == "first":
                return 0
            elif what == "last":
                lastday = os.path.dirname(self.AllJpegs[-1])
                last = lastday
                for img in self.AllJpegs[-1::-1]:
                    jc = os.path.dirname(img)
                    if (last == lastday) and (jc < last):
                        return self.AllJpegs.index(img) + 1
                    last = jc
                else:
                    return len(self.AllJpegs) - 1
        elif menu == "sel":
            if len(self.selected) == 0:
                logger.warning("No selected file")
                return current_idx
            if what == "first":
                new_idx = self.AllJpegs.index(self.selected[0])
            elif what == "previous":
                for i in self.AllJpegs[self.idx_current - 1::-1]:
                    if i in self.selected:
                        return self.AllJpegs.index(i)
            elif what == "next":
                for i in self.AllJpegs[self.idx_current + 1:]:
                    if i in self.selected:
                        return self.AllJpegs.index(i)
            elif what == "last":
                new_idx = self.AllJpegs.index(self.selected[-1])
        elif menu == "unsel":
            if what == "first":
                for i in self.AllJpegs:
                    if i not in self.selected:
                        return self.AllJpegs.index(i)
            elif what == "last":
                if current_idx == 0:
                    return 0
                for i in self.AllJpegs[current_idx - 1::-1]:
                    if i not in self.selected:
                        return self.AllJpegs.index(i)
            elif what == "next":
                for i in self.AllJpegs[current_idx + 1:]:
                    if i not in self.selected:
                        return self.AllJpegs.index(i)
            elif what == "first":
                for i in self.AllJpegs[-1::-1]:
                    if i not in self.selected:
                        return self.AllJpegs.index(i)
        elif menu == "title":
            if what == "first":
                for i in self.AllJpegs:
                    myPhoto = Photo(i)
                    if myPhoto.is_entitled():
                        return  self.AllJpegs.index(i)
            elif what == "previous":
                for i in self.AllJpegs[current_idx - 1::-1]:
                    myPhoto = Photo(i)
                    if myPhoto.is_entitled():
                        return self.AllJpegs.index(i)
            elif what == "next":
                for i in self.AllJpegs[current_idx + 1:]:
                    myPhoto = Photo(i)
                    if myPhoto.is_entitled():
                        return self.AllJpegs.index(i)
            elif what == "last":
                for i in self.AllJpegs[-1::-1]:
                    myPhoto = Photo(i)
                    if myPhoto.is_entitled():
                        return self.AllJpegs.index(i)
        elif menu == "untitle":
            if what == "first":
                for i in self.AllJpegs:
                    myPhoto = Photo(i)
                    if not myPhoto.is_entitled():
                        return  self.AllJpegs.index(i)
            elif what == "previous":
                for i in self.AllJpegs[current_idx - 1::-1]:
                    myPhoto = Photo(i)
                    if not myPhoto.is_entitled():
                        return self.AllJpegs.index(i)
            elif what == "next":
                for i in self.AllJpegs[current_idx + 1:]:
                    myPhoto = Photo(i)
                    if not myPhoto.is_entitled():
                        return self.AllJpegs.index(i)
            elif what == "last":
                for i in self.AllJpegs[-1::-1]:
                    myPhoto = Photo(i)
                    if not myPhoto.is_entitled():
                        return self.AllJpegs.index(i)
        elif menu == "random":
            if what == "last":
                new_idx = len(self.AllJpegs) - 1
            elif what == "first":
                new_idx = 0
            else:
                while True:
                    if not self.rnd_lst:
                        self.rnd_lst = list(range(len(self.AllJpegs)))
                        random.shuffle(self.rnd_lst)
                    new_idx = self.rnd_lst.pop()
                    image = Photo(self.AllJpegs[new_idx])
                    data = image.read_exif()
                    if "rate" in data:
                        rate = int(float(data["rate"]))
                        if rate >= self.min_mark:
                            break
        else:
            logger.warning("Unrecognized menu in navigate %s %s" % (menu, what))
        # final sanitization
        return new_idx % size

    def navigate(self, act):
        """
        Generic navigation
        """
        self.update_title()
        if act in self.navigation_dict:
            menu, what = self.navigation_dict[act]
            new_idx = self.calc_index(what, menu)
            logger.debug("Image %i -> %i" % (self.idx_current, new_idx))
            self.show_image(new_idx)
        else:
            logger.warning(u"Interface.navigate unknown action %s %s: %s " % (act.text(), act.data(), act))

    def next1(self):
        self.navigate(self.gui.actionNav_img_next)

    def previous1(self):
        self.navigate(self.gui.actionNav_img_previous)

    def turn_right(self, *args):
        """rotate the current image clockwise"""
        logger.debug("Interface.turn_right")
        self.update_title()
        self.image.rotate(90)
        self.show_image()

    def turn_left(self, *args):
        """rotate the current image counterclockwise"""
        logger.debug("Interface.turn_left")
        self.update_title()
        self.image.rotate(270)
        self.show_image()

    def trash(self, *args):
        """Send the current file to the trash"""
        logger.debug("Interface.trash")
        self.update_title()
        if self.fn_current in  self.selected:
            self.selected.remove(self.fn_current)
        if self.treeview is not None:
            self.treeview.remove_file(self.fn_current)
        self.AllJpegs.remove(self.fn_current)
        self.image.trash()
        self.show_image(min(self.idx_current, len(self.AllJpegs) - 1))

    def gimp(self, *args):
        """Edit the current file with the Gimp"""
        logger.debug("Interface.gimp")
        self.update_title()
        self.clean_processes()
        filename = self.fn_current
        base, ext = os.path.splitext(filename)
        newname = base + "-Gimp.jpg"
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort(key=lambda x:x[:-4])
        self.idx_current = self.AllJpegs.index(newname)
        self.fn_current = newname
        newnamefull = os.path.join(config.DefaultRepository, newname)
        self.image.as_jpeg(newnamefull)
        os.chmod(newnamefull, config.DefaultFileMode)
        p = subprocess.Popen([config.Gimp, newnamefull])
        with self.job_sem:
            self.processes.append(p)
        self.show_image()
        self.image.removeFromCache()

    def rawtherapee(self, *args):
        """Edit the current file with the RawTherapee"""
        logger.debug("Interface.rawtherapee")
        self.update_title()
        self.clean_processes()
        filename = self.fn_current
        base, ext = os.path.splitext(filename)
        filenamefull = os.path.join(config.DefaultRepository, filename)
        newname = base + "-RT.jpg"
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort(key=lambda x:x[:-4])
        self.idx_current = self.AllJpegs.index(newname)
        self.fn_current = newname
        newnamefull = os.path.join(config.DefaultRepository, newname)
        self.image.as_jpeg(newnamefull)
        os.chmod(newnamefull, config.DefaultFileMode)
        p = subprocess.Popen([config.Rawtherapee, filenamefull])
        with self.job_sem:
            self.processes.append(p)
        self.show_image()
        self.image.removeFromCache()

    def edit_im(self, *args):
        """Edit an image Gimp/RT"""
        logger.debug("Interface.edit_image")
        logger.debug("do_filter, default=%s" % self.default_filter)
        if self.default_filter == "ContrastMask":
            self.filter_ContrastMask()
        elif self.default_filter == "AutoWB":
            self.filter_AutoWB()
        else:
            logger.error("Unknown filter: %s", config.SelectedFilter)

    def reload_img(self, *args):
        """Remove image from cache and reloads it"""
        logger.debug("Interface.reload")
        self.update_title()
        filename = self.fn_current
        if (image_cache is not None) and (filename in image_cache):
            image_cache.pop(filename)
        self.image = Photo(filename)
        self.show_image()

    def filter_im(self, *args):
        """ Apply the selected filter to the current image"""
        logger.debug("Interface.filter_image")
        logger.debug("do_filter, default=%s" % self.default_filter)
        if self.default_filter == "ContrastMask":
            self.filter_ContrastMask()
        elif self.default_filter == "AutoWB":
            self.filter_AutoWB()
        else:
            logger.error("Unknown filter: %s", config.SelectedFilter)

    def filter_ContrastMask(self, *args):
        """Filter the current image with a contrast mask"""
        logger.debug("Interface.filter_ContrastMask")
        self.update_title()
        filename = self.fn_current
        base, ext = os.path.splitext(filename)
        newname = base + "-ContrastMask.jpg"
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort(key=lambda x:x[:-4])
        self.image = self.image.contrastMask(newname)
        self.show_image(self.AllJpegs.index(newname))

    def filter_AutoWB(self, *args):
        """Filter the current image with Auto White Balance"""
        logger.debug("Interface.filter_AutoWB")
        self.update_title()
        filename = self.fn_current
        base, ext = os.path.splitext(filename)
        newname = base + "-AutoWB.jpg"
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort(key=lambda x:x[:-4])
        self.image = self.image.autoWB(newname)
        self.show_image(self.AllJpegs.index(newname))

    def select_shortcut(self, *args):
        """Select or unselect the image (not directly clicked on the toggle button)"""
        logger.debug("Interface.select_shortcut")
        etat = not(self.gui.selection.isChecked())
        self.gui.selection.setChecked(etat)

    def select(self, *args):
        """Select or unselect the image (directly clicked on the toggle button)"""
        logger.debug("Interface.select")
        etat = bool(self.gui.selection.isChecked())
        if etat and (self.fn_current not in self.selected):
            self.selected.append(self.fn_current)
        if not(etat) and (self.fn_current in self.selected):
            self.selected.remove(self.fn_current)
        self.selected.sort()
        if (self.image.metadata["rate"] == 0) and  etat:
            self.gui.rate.setValue(config.DefaultRatingSelectedImage)
        self.update_title()

    def destroy(self, *args):
        """destroy clicked by user"""
        logger.debug("Interface.destroy")
        self.update_title()
        self.gui.close()
        if callable(self.callback):
            self.callback("quit")

    def die(self, *args):
        """you want to leave the program ??"""
        logger.debug("Interface.die")
        self.update_title()
        if quit_dialog(self.gui):
            self.selected.save()
            self.destroy()

    def copy_resize(self, *args):
        """lauch the copy of all selected files then scale them to generate web pages"""
        logger.debug("Interface.copy_resize")
        self.update_title()
        # TODO: go through MVC
        process_selected(self.selected[:], self.signal_status, self.signal_processed)
        self.selected = Selected()
        self.gui.selection.setChecked(self.fn_current in self.selected)
        logger.info("Interface.copy_resize: Done")

    def to_web(self, *args):
        """lauch the copy of all selected files then scale and finaly copy them to the generator-repository and generate web pages"""
        logger.debug("Interface.to_web")
        self.update_title()
        process_selected(self.selected[:], self.signal_status)
        self.selected = Selected()
        self.gui.selection.setChecked((self.fn_current in self.selected))
        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        out = os.system(config.WebServer.replace("$WebRepository", config.WebRepository).replace("$Selected", SelectedDir))
        if out != 0:
            logger.error("Error n° : %i", out)
        logger.info("Interface.to_web: Done")

    def empty_selected(self, *args):
        """remove all the files in the "Selected" folder"""

        sel_dirname = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        if not os.path.isdir(sel_dirname):
            os.mkdir(sel_dirname)
            return
        errors = []
        for dirs in os.listdir(sel_dirname):
            curfile = os.path.join(sel_dirname, dirs)
            if os.path.isdir(curfile):
                errors += recursive_delete(curfile)
            else:
                try:
                    os.remove(curfile)
                except:
                    errors.append(curfile)
        if errors:
            if len(errors) > 10:
                errors = errors[:10]
                errors.append("...")
            errors.insert(0, 'Unable to delete those files/folders:')
            msg = os.linesep.join(errors)
            emsg = qt.QErrorMessage(self.gui)
            emsg.setWindowModality(qt.Qt.WindowModal)
            emsg.showMessage(msg)
            logger.error(msg)
        else:
            logger.info("Done")

    def copy(self, *args):
        """lauch the copy of all selected files"""
        self.update_title()
        copy_selected(self.selected[:], self.signal_status, self.signal_processed)
        self.selected = Selected()
        self.gui.selection.setChecked((self.fn_current in self.selected))
        logger.info("Done")

    def to_jpeg(self, *args):
        """Export all selected files as JPEG"""
        self.update_title()
        to_jpeg(self.selected[:], self.signal_status, self.signal_processed)
        self.selected = Selected()
        self.gui.selection.setChecked((self.fn_current in self.selected))
        logger.info("Done")

    def burn(self, *args):
        """lauch the copy of all selected files then burn a CD according to the configuration file"""
        logger.debug("Interface.burn")
        self.update_title()
        copy_selected(self.selected[:], self.signal_status)
        self.selected = Selected()
        self.gui.selection.setChecked((self.fn_current in self.selected))
        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        out = os.system(config.Burn.replace("$Selected", SelectedDir))
        if out != 0:
            logger.error("Error n° : %i" % out)
        logger.info("Interface.burn: Done")

    def save_selection(self, *args):
        """Saves all the selection of photos """
        logger.debug("Interface.save_selection")
        self.update_title()
        self.selected.save()

    def load_selection(self, *args):
        """Load a previously saved  selection of photos """
        logger.debug("Interface.load_selection")
        self.update_title()
        self.selected = Selected.load()
        for i in self.selected:
            if not(i in self.AllJpegs):
                self.selected.remove(i)
        self.gui.selection.setChecked(self.fn_current in  self.selected)

    def select_all(self, *args):
        """Select all photos for processing"""
        logger.debug("Interface.select_all")
        self.update_title()
        self.selected = Selected(self.AllJpegs)
        self.gui.selection.setChecked(True)

    def select_none(self, *args):
        """Select NO photos and empty selection"""
        logger.debug("Interface.select_none")
        self.update_title()
        self.selected = Selected()
        self.gui.selection.setChecked(False)

    def invert_selection(self, *args):
        """Invert the selection of photos """
        logger.debug("Interface.invert_selection")
        self.update_title()
        temp = self.AllJpegs[:]
        for i in self.selected:
            temp.remove(i)
        self.selected = Selected(i for i in self.AllJpegs if i not in self.selected)
        self.gui.selection.setChecked(not self.gui.selection.isChecked())

    def about(self, *args):
        """display a copyright message"""
        logger.debug("Interface.about clicked")
        self.update_title()
        msg = "Selector vous permet de mélanger, de sélectionner et de tourner \ndes photos provenant de plusieurs sources.\nÉcrit par %s <%s>\nVersion %s (%s)" % (__author__, __contact__, __version__, __date__)
        message_box(self.gui, "À Propos", msg)

    def searchJ(self, *args):
        """start the searching widget"""
        logger.debug("Interface.searchJ clicked")
        SearchDay(self.AllJpegs, self.setDay)

    def setDay(self, path):
        try:
            self.idx_current = self.AllJpegs.index(path)
        except ValueError:
            logger.error("%s not in AllJpegs" % path)
        else:
            self.show_image()

    def save_pref(self, *args):
        """Preferences,save clicked. now we save the preferences in the file"""
        logger.debug("Interface.save_pref clicked")
        config.save(listConfigurationFiles[-1])

    def setAutoRotate(self, *args):
        """Set the autorotate flag"""
        logger.debug("Interface.setAutoRotate clicked")
#        config.AutoRotate = self.gui.Autorotate").get_active()

    def setFiligrane(self, *args):
        """Set the Signature/Filigrane flag"""
        logger.debug("Interface.setFiligrane clicked")

    def set_interpolation(self, act=None, value=None):
        """
        @param act: Qaction
        """
        logger.debug("Interface.set_interpolation")
        options = (self.gui.actionNearest,
                   self.gui.actionLinear,
                   self.gui.actionLanczos)
        if act:
            config.Interpolation = options.index(act)
        elif value is not None:
            config.Interpolation = value
            act = options[value]
        else:
            return

        for name in options:
            name.setChecked(name == act)

    def set_images_per_page(self, act=None, value=None):
        """
        @param act: Qaction
        @param value: numerical value
        """
        logger.debug("Interface.set_images_per_page")
        options = {9: self.gui.action9,
                   12: self.gui.action12,
                   16: self.gui.action16,
                   20: self.gui.action20,
                   25: self.gui.action25,
                   30: self.gui.action30,
                   }
        if value is not None:
            config.NbrPerPage = value
            act = options.get(value)
        elif act is not None:
            config.NbrPerPage = int(str(act.text()))
        else:
            return

        for name in options.values():
            name.setChecked(act == name)

    def set_min_rate(self, act=None, value=None):
        """
        @param act: Qaction
        @param value: numerical value
        """
        logger.debug("Interface.set_min_rate")
        options = (self.gui.action0,
                   self.gui.action1,
                   self.gui.action2,
                   self.gui.action3,
                   self.gui.action4,
                   self.gui.action5)

        if value is not None:
            act = options[value]
        elif act is not None:
            value = int(str(act.text())[-1])
        else:
            return
        self.min_mark = value
        for name in options:
            name.setChecked(act == name)

    def rename_day(self, *args):
        """Launch a new window and ask for anew name for the current directory"""
        logger.debug("Interface.rename_day clicked")
        self.update_title()
        res = rename_day(self.fn_current, self.AllJpegs, self.selected)
        if res is not None:
            if self.treeview is not None:
                self.treeview.close()
            self.image.filename = res
            self.image.fn = os.path.join(config.DefaultRepository, res)
            self.image._exif = None
            self.image._pil = None
            self.idx_current = self.AllJpegs.index(res)
            self.show_image()

    def importImages(self, *args):
        """Launch a filer window to select a directory from witch import all JPEG/RAW images"""
        logger.debug("Interface.importImages called")
        self.update_title()
        # TODO
        self.guiFiler = buildUI("filer")
#        self.guiFiler.filer").set_current_folder(config.DefaultRepository)
#        self.guiFiler.connect_signals({self.gui.Open, 'clicked()', self.filerSelect,
#                                       self.gui.Cancel, 'clicked()', self.filerDestroy})

    def filerSelect(self, *args):
        """Close the filer GUI and update the data"""
        logger.debug("dirchooser.filerSelect called")
#        self.importImageCallBack(self.guiFiler.filer").get_current_folder())
        self.guiFiler.filer.close()

    def filerDestroy(self, *args):
        """Close the filer GUI"""
        logger.debug("dirchooser.filerDestroy called")
        self.guiFiler.filer.close()

    def importImageCallBack(self, path):
        """This is the call back method for launching the import of new images"""
        logger.debug("Interface.importImageCallBack with dirname= %s" % path)
        self.update_title()
        listNew = []
        allJpegsFullPath = []
        for afile in self.AllJpegs[:]:
            if os.path.exists(os.path.join(config.DefaultRepository, afile)):
                allJpegsFullPath.append(os.path.join(config.DefaultRepository, afile))
            else:
                logger.info("Removing non existing image file: %s" % afile)
                self.AllJpegs.remove(afile)

        # TODO Use MVC here ...
        for oneRaw in findFiles(path, lstExtentions=config.RawExtensions + config.Extensions, bFromRoot=True):
            if oneRaw in allJpegsFullPath:
                logger.info("file already in repository: %s" % oneRaw)
            else:
                logger.debug("Importing: %s" % oneRaw)
                raw = RawImage(oneRaw)
                raw.extractJPEG()
                listNew.append(raw.getJpegPath())
        if len(listNew) > 0:
            listNew.sort(key=lambda x:x[:-4])
            first = listNew[0]
            self.AllJpegs += listNew
            self.AllJpegs.sort(key=lambda x:x[:-4])
            self.idx_current = self.AllJpegs.index(first)
            self.show_image()

    def defineMediaSize(self, *args):
        """lauch a new window and ask for the size of the backup media"""
        logger.debug("Interface.defineMediaSize clicked")
        self.update_title()
        ask_media_size()

    def toggle_slideshow(self, *args):
        if self.in_slideshow:
            self.stop_slideshow()
        else:
            self.start_slideshow()

    def config_slideshow(self, *args):
        """lauch a new window for seting up the slideshow"""
        logger.debug("Interface.config_slideshow clicked")
        self.update_title()
        self.in_slideshow = slideshow_dialog()
        if self.in_slideshow:
            self.start_slideshow()

    def start_slideshow(self, *args):
        """Switch to fullscreen mode and starts the SlideShow"""
        logger.debug("Interface.start_slideshow")

        self.update_title()
        self.in_slideshow = True
        self.set_min_rate(value=config.SlideShowMinRating)
        # goto full screen mode
        self.gui.setWindowState(qt.Qt.WindowFullScreen | qt.Qt.WindowActive)
        self.gui.menubar.setVisible(False)
        self.menubar_isvisible = False
        self.is_fullscreen = True
        flush()
        width = sum(self.gui.splitter.sizes())
        self.gui.splitter.setSizes([0, width])
        flush()
        self.show_image()
        # start timer
        self.timer = qt.QTimer(self.gui)
        self.timer.setInterval(1000.0 * config.SlideShowDelay)
        self.timer.timeout.connect(self.new_slide)
        self.timer.start(1000.0 * config.SlideShowDelay)

    def stop_slideshow(self, *args):
        """quit slideshow mode"""
        logger.debug("Interface.stop_slideshow")
        self.in_slideshow = False
        self.set_min_rate(value=config.SlideShowMinRating)
        if self.timer:
            self.timer.stop()
            self.timer = None

    def new_slide(self):
        """
        Slideshow slot to display next image
        """
        if not self.in_slideshow:
            self.stop_slideshow()
            return
        next_img = self.idx_current
        if config.SlideShowType == "chronological":
            next_img = self.calc_index("next", "image")
        elif config.SlideShowType == "antichronological":
            next_img = self.calc_index("previous", "image")
        elif config.SlideShowType == "random":
            next_img = self.calc_index("next", "random")
        self.show_image(next_img)

    def indexJ(self, *args):
        """lauch a new window for selecting the day of interest"""
        logger.debug("Interface.indexJ clicked")
        self.update_title()
        SelectDay(self)

    def synchronize(self, *args):
        """lauch the synchronization window"""
        logger.debug("Interface.synchronize clicked")
        self.update_title()
        synchronize_dialog(self.idx_current, self.AllJpegs, self.selected)

    def selectMedia(self, *args):
        """Calculate the size of the selected images then add newer images to complete the media (CD or DVD).
        Finally the last selected image is shown and the total size is printed"""
        logger.debug("Interface.selectMedia clicked with " + str(args))
        self.update_title()
        size = self.selected.get_nbytes()
        initsize = size
        maxsize = config.MediaSize * 1024 * 1024
        init = len(self.selected)

        if args[0] == self.gui.actionCD_DVD_suivant:
            tmplist = self.AllJpegs[self.idx_current:]
        elif args[0] == self.gui.actionCD_DVD_precedent:
            tmplist = self.AllJpegs[:self.idx_current + 1]
            tmplist.reverse()
        else:
            logger.warning("unknown action: " + str(args))
            return
        for i in tmplist:
            if i in self.selected:
                continue
            size += os.path.getsize(os.path.join(config.DefaultRepository, i))
            if size >= maxsize:
                size -= os.path.getsize(os.path.join(config.DefaultRepository, i))
                break
            else:
                self.selected.append(i)
        self.selected.sort()
        if len(self.selected) == 0:
            return
        if args[0] == self.gui.actionCD_DVD_suivant:
            idx = self.AllJpegs.index(self.selected[-1])
        elif args[0] == self.gui.actionCD_DVD_precedent:
            idx = self.AllJpegs.index(self.selected[0])
        else:
            logger.warning("unknown action: " + str(args))
            return
        self.show_image(idx)
        t = smartSize(size) + (len(self.selected),) + smartSize(initsize) + (init,)
        txt = u"%.2f %s de données dans %i images sélectionnées dont\n%.2f %s de données dans %i images précédement sélectionnées " % t
        message_box(self.gui, "taille selectionnée", txt)

    def display_selected_size(self, *args):
        """Calculate the size of the selection and print it"""
        logger.debug("Interface.display_selected_size clicked")
        self.update_title()
        size = self.selected.get_nbytes()
        t = smartSize(size) + (len(self.selected),)
        txt = u"%.2f %s de données dans %i images sélectionnées" % t
        message_box(self.gui, "taille selectionnée", txt)

    def filterAutoWB(self, *args):
        """
        Set the default filter to AutoWB
        """
        logger.debug("Interface.AutoWB clicked")
        config.selectedFilter = "AutoWB"

    def filterContrastMask(self, *args):
        """
        Set the default filter to Contrast Mask
        """
        logger.debug("Interface.ContrastMask clicked")
        config.SelectedFilter = "ContrastMask"

    def image_zoom(self, ev):
        """
        mouse scroll on the image to zoom

        @param ev: QWheelEvent. See qt.ExtendedLabel
        """
        logger.debug("Interface.image_zoom ")
        try:
            zoom = ev.angleDelta().y()
        except AttributeError:  # Qt4
            zoom = ev.delta()
        w_width = self.gui.photo.width()
        w_height = self.gui.photo.height()
        p_width = self.gui.photo.pixmap().width()
        p_height = self.gui.photo.pixmap().height()
        x = ev.x()
        y = ev.y()
        if zoom > 0 and not self.is_zoomed:
            nx = (x - (w_width - p_width) / 2.0) / p_width
            ny = (y - (w_height - p_height) / 2.0) / p_height
            pixbuf = self.image.get_pixbuf(w_width, w_height, nx, ny)
            self.gui.photo.setPixmap(pixbuf)
            del pixbuf
            self.is_zoomed = (nx, ny)
        elif zoom < 0 and self.is_zoomed:
            pixbuf = self.image.get_pixbuf(w_width, w_height)
            self.gui.photo.setPixmap(pixbuf)
            del pixbuf
            self.is_zoomed = None
        gc.collect()

    def image_pan(self, ev):
        """
        mouse pan on the image when zoomed in

        @param ev: moveEvent
        """
        logger.debug("Interface.image_pan %s", ev)
        if not self.is_zoomed:
            return
        w_width = self.gui.photo.width()
        w_height = self.gui.photo.height()
        p_width = self.image.pixelsX
        p_height = self.image.pixelsY
        x, y = self.is_zoomed
        dx = ev.pos().x() - ev.oldPos().x()
        dy = ev.pos().y() - ev.oldPos().y()
        nx = x - dx / p_width
        ny = y - dy / p_height
#         logger.info("dx %s, dy %s, oldxy %s %s new xy %s %s", dx, dy, x, y, nx, ny)
        pixbuf = self.image.get_pixbuf(w_width, w_height, nx, ny)
        self.is_zoomed = (nx, ny)
        self.gui.photo.setPixmap(pixbuf)
        del pixbuf
        gc.collect()

    def show_treeview(self, *arg):
        """
        """
        if self.treeview is None:
            tree_rep = tree.build_tree(self.AllJpegs)
            self.treeview = tree.TreeWidget(tree_rep)
            self.treeview.callback = self.goto_image
        self.treeview.show()

    def show_searchview(self, *arg):
        if self.searchview is None:
            self.searchview = SearchTitle(self.goto_image)
        self.searchview.show()

    def goto_image(self, name=None):
        """
        Callback for show_treeview
        """
        try:
            idx = self.AllJpegs.index(name)
        except:
            logger.warning("Unknown image in base %s" % name)
        else:
            self.show_image(idx)

    def toggle_toolbar(self, *arg):
        """
        Set toolbar visible/not
        """
        self.menubar_isvisible = not(self.menubar_isvisible)
        self.gui.menubar.setVisible(self.menubar_isvisible)

    def toggle_fullscreen(self, *arg):
        if self.is_fullscreen:
            self.gui.setWindowState(qt.Qt.WindowNoState | qt.Qt.WindowActive)
            self.gui.menubar.setVisible(True)
            self.menubar_isvisible = True
            self.is_fullscreen = False
            flush()
            width = sum(self.gui.splitter.sizes())
            self.gui.splitter.setSizes([self.left_tab_width, width - self.left_tab_width])
        else:
            self.gui.setWindowState(qt.Qt.WindowFullScreen | qt.Qt.WindowActive)
            self.gui.menubar.setVisible(False)
            self.menubar_isvisible = False
            self.is_fullscreen = True
            flush()
            width = sum(self.gui.splitter.sizes())
            self.gui.splitter.setSizes([0, width])
        flush()
        self.show_image()

    def clean_processes(self):
        """remove ended sub-processes
        """
        with self.job_sem:
            still = []
            for job in self.processes:
                job.poll()
                if job.returncode is None:
                    still.append(job)
            self.processes = still

################################################################################
# # # # # # # fin de la classe interface graphique # # # # # #
################################################################################


class SelectDay(object):

    def __init__(self, upperIface):
        self.upperIface = upperIface
        self.gui = buildUI("ChangeDir")
#        signals = {self.gui.ChangeDir_destroy': self.destroy,
#                   self.gui.annuler, 'clicked()', self.destroy,
#                   self.gui.Ouvrir, 'clicked()', self.continu}
#        self.gui.connect_signals(signals)
        self.combobox = self.gui.entry
        self.days = [os.path.split(self.upperIface.AllJpegs[0])[0]]
        self.combobox.append_text(self.days[0])
        for image in self.upperIface.AllJpegs[1:]:
            day = os.path.split(image)[0]
            if day != self.days[-1]:
                self.days.append(day)
                self.combobox.append_text(day)
        self.curday = self.days.index(os.path.split(self.upperIface.AllJpegs[self.upperIface.iCurrentImg])[0])
        self.combobox.set_active(self.curday)

    def continu(self, *args):
        """just distroy the window and goes on ...."""
        day = self.days[self.combobox.get_active()]
        for i in range(len(self.upperIface.AllJpegs)):
            if os.path.split(self.upperIface.AllJpegs[i])[0] == day:
                break
        self.upperIface.iCurrentImg = i
        self.upperIface.show_image()
        self.gui.ChangeDir.close()

    def destroy(self, *args):
        """destroy clicked by user -> quit the program"""
        try:
            self.gui.ChangeDir.close()
        except:
            pass
        flush()
