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

"""
Graphical interface for selector.
"""
__author__ = "Jérôme Kieffer"
__version__ = "2.0.0"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "06/12/2014"
__license__ = "GPL"

import gc
import os
import logging
logger = logging.getLogger("imagizer.interface")
from .imagizer import copySelected, processSelected, timer_pass
from .qt import QtCore, QtGui, buildUI, flush, SIGNAL, icon_on
from .selection import Selected
from .photo import Photo
from .utils import get_pixmap_file
from .config import config
from .imagecache import imageCache
from . import tree
from .dialogs import rename_day, quit_dialog, ask_media_size, synchronize_dialog

################################################################################
#  ##### FullScreen Interface #####
################################################################################

class FullScreenInterface(object):
    def __init__(self, AllJpegs=[], first=0, selected=[], mode="FullScreen", callback=None):
        self.callback = callback
        self.AllJpegs = AllJpegs
        self.selected = Selected(i for i in selected if i in self.AllJpegs)
        self.image = None
        self.RandomList = []
        self.idx_current = first
        self.timestamp = time.time()

        logger.info("Initialization of the fullscreen GUI")
        self.gui = buildUI("FullScreen")
        self.timeout_handler_id = gobject.timeout_add(1000, timer_pass)
        self.show_image()
        flush()
        self.gui.FullScreen.maximize()
        flush()
        self.show_image()
        flush()
#        self.gui.connect_signals({self.gui.FullScreen_destroy': self.destroy,
#                                  "on_FullScreen_key_press_event":self.keypressed})
        if mode == "slideshow":
            self.SlideShow()
        self.QuitSlideShow = True
        self.gui.show()

    def show_image(self):
        """Show the image in the given GtkImage widget and set up the exif tags in the GUI"""
        self.image = Photo(self.AllJpegs[self.idx_current])
        X, Y = self.gui.FullScreen.get_size()
        logger.debug("Size of image on screen: %sx%s" % (X, Y))
        pixbuf = self.image.get_pixbuf(X, Y)
        self.gui.image793.set_from_pixbuf(pixbuf)
        del pixbuf
        gc.collect()
        if self.AllJpegs[self.idx_current] in self.selected:
            sel = "[Selected]"
        else:
            sel = ""
        self.gui.FullScreen.set_title("Selector : %s %s" % (self.AllJpegs[self.idx_current], sel))

    def keypressed(self, widget, event, *args):
        """keylogger"""
        key = gdk.keyval_name (event.keyval)
        if key == "Page_Up":
            self.previousJ()
        elif key == "Page_Down":
            self.nextJ()
        elif key == "d":
            self.SlideShow()
        elif key == "e":
            self.QuitSlideShow = True
            self.destroy()

        elif key == "Right":
            self.turn_right()
        elif key == "Left":
            self.turn_left()
        elif key == "f":
            self.NormalScreen()
        elif key == "Down":
            self.next1()
        elif key == "Up":
            self.previous1()
        elif key == "s":
            self.select_Shortcut()
        elif key in ["Escape", "Q"]:
            self.QuitSlideShow = True
        elif key in ["KP_Add", "plus"]:
            config.SlideShowDelay += 1
        elif key in ["KP_Subtract", "minus"]:
            config.SlideShowDelay -= 1
            if config.SlideShowDelay < 0:config.SlideShowDelay = 0

    def turn_right(self, *args):
        """rotate the current image clockwise"""
        self.image.rotate(90)
        self.show_image()
    def turn_left(self, *args):
        """rotate the current image clockwise"""
        self.image.rotate(270)
        self.show_image()

    def destroy(self, *args):
        """destroy clicked by user"""
        self.close("quit")

    def NormalScreen(self, *args):
        """Switch to Normal mode"""
        self.close("normal")

    def next1(self, *args):
        """Switch to the next image"""
        self.idx_current = (self.idx_current + 1) % len(self.AllJpegs)
        self.show_image()
    def previous1(self, *args):
        """Switch to the previous image"""
        self.idx_current = (self.idx_current - 1) % len(self.AllJpegs)
        self.show_image()
    def nextJ(self, *args):
        """Switch to the first image of the next day"""
        jour = os.path.dirname(self.AllJpegs[self.idx_current])
        for i in range(self.idx_current, len(self.AllJpegs)):
            jc = os.path.dirname(self.AllJpegs[i])
            if jc > jour: break
        self.idx_current = i
        self.show_image()
    def previousJ(self, *args):
        """Switch to the first image of the previous day"""
        if self.idx_current == 0: return
        jour = os.path.dirname(self.AllJpegs[self.idx_current])
        for i in range(self.idx_current - 1, -1, -1):
            jc = os.path.dirname(self.AllJpegs[i])
            jd = os.path.dirname(self.AllJpegs[i - 1])
            if (jc < jour) and (jd < jc): break
        self.idx_current = i
        self.show_image()

    def select_Shortcut(self, *args):
        """Select or unselect the image"""
        if self.AllJpegs[self.idx_current] not in self.selected:
            self.selected.append(self.AllJpegs[self.idx_current])
            sel = "[Selected]"
        else:
            self.selected.remove(self.AllJpegs[self.idx_current])
            sel = ""
        self.selected.sort()
        self.gui.setWindowTitle("Selector : %s %s" % (self.AllJpegs[self.idx_current], sel))

    def SlideShow(self):
        """Starts the slide show"""
        self.QuitSlideShow = False
        self.RandomList = []
        while not self.QuitSlideShow:
            if config.SlideShowType == "chronological":
                self.idx_current = (self.idx_current + 1) % len(self.AllJpegs)
            elif config.SlideShowType == "antichronological":
                self.idx_current = (self.idx_current - 1) % len(self.AllJpegs)
            elif config.SlideShowType == "random":
                if len(self.RandomList) == 0:
                    self.RandomList = range(len(self.AllJpegs))
                    random.shuffle(self.RandomList)
                self.idx_current = self.RandomList.pop()
            self.image = Photo(self.AllJpegs[self.idx_current])
            self.image.readExif()
            if self.image.metadata["rate"] < config.SlideShowMinRating:
                flush()
                continue
            now = time.time()
            if now - self.timestamp < config.SlideShowDelay:
                time.sleep(config.SlideShowDelay - now + self.timestamp)
            self.show_image()
            flush()
            self.timestamp = time.time()

    def close(self, what=None):
        """close the gui and call the call-back"""
        self.selected.save()
        self.gui.close()
        if self.callback:
            self.callback(what)

################################################################################
# ##### Normal Interface #####
################################################################################

class Interface(object):
    """
    class interface that manages the GUI using Glade-2
    """
    def __init__(self, AllJpegs=[], first=0, selected=[], mode="Default", callback=None):
        self.callback = callback
        self.AllJpegs = AllJpegs
        self.selected = Selected(i for i in selected if i in self.AllJpegs)
        self.idx_current = first
        self.left_tab_width = 350
        self.image = None
        self.current_title = ""
        self.current_rate = 0
        self.fn_current = None
        self.is_zoomed = False
        self.min_mark = 0
        self.default_filter = None
        self.menubar_isvisible = True
        self.treeview = None
        print("Initialization of the windowed graphical interface ...")
        logger.info("Initialization of the windowed graphical interface ...")
        self.gui = buildUI("principale")

        # Icons on buttons
        self.gui.logo.setPixmap(QtGui.QPixmap(get_pixmap_file("logo")))
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

#        self.timeout_handler_id = gobject.timeout_add(1000, timer_pass)
        self._populate_action_data()
        self.gui.actionAutorotate.setChecked(bool(config.AutoRotate))
        self.gui.actionSignature_filigrane_web.setChecked(bool(config.Filigrane))

        self.set_images_per_page(value=config.NbrPerPage)
        self.set_interpolation(value=config.Interpolation)
        self.show_image()
        flush()
        self._menu_filtrer()
        flush()
        self.navigation_dict= {
         ##Image
            self.gui.actionNav_img_first: ("image", "first"),
            self.gui.actionNav_img_previous10: ("image","previous10"),
            self.gui.actionNav_img_previous: ("image","previous"),
            self.gui.actionNav_img_next: ("image","next"),
            self.gui.actionNav_img_next10: ("image","next10"),
            self.gui.actionNav_img_last: ("image","last"),
            ##Day
            self.gui.actionNav_day_first: ("day","first"),
            self.gui.actionNav_day_previous: ("day","previous"),
            self.gui.actionNav_day_next: ("day","next"),
            self.gui.actionNav_day_last: ("day","last"),
            ##Selected:
            self.gui.actionNav_sel_first: ("sel","first"),
            self.gui.actionNav_sel_previous:("sel","previous"),
            self.gui.actionNav_sel_next: ("sel","next"),
            self.gui.actionNav_sel_last: ("sel","last"),
            ##Non-selected:
            self.gui.actionNav_unsel_first: ("unsel","first"),
            self.gui.actionNav_unsel_previous: ("unsel","previous"),
            self.gui.actionNav_unsel_next: ("unsel","next"),
            self.gui.actionNav_unsel_last: ("unsel","last"),
            ##Entitled
            self.gui.actionNav_title_first: ("title","first"),
            self.gui.actionNav_title_previous: ("title","previous"),
            self.gui.actionNav_title_next: ("title","next"),
            self.gui.actionNav_title_last: ("title","last"),
            ##Non entitled
            self.gui.actionNav_untitle_first: ("untitle","first"),
            self.gui.actionNav_untitle_previous: ("untitle","previous"),
            self.gui.actionNav_untitle_next: ("untitle","next"),
            self.gui.actionNav_untitle_last: ("untitle","last"),
            }
        handlers = {self.gui.next.clicked:self.next1,
                    self.gui.previous.clicked: self.previous1,
                    self.gui.right.clicked:self.turn_right,
                    self.gui.left.clicked: self.turn_left,
                    self.gui.selection.stateChanged: self.select,
                    self.gui.trash.clicked: self.trash,
                    self.gui.edit.clicked:self.gimp,
                    self.gui.reload.clicked:self.reload_img,
                    self.gui.filter.clicked:self.filter_im,

                    self.gui.menubar.triggered: self._action_handler,
#
#        self.gui.enregistrerS_activate': self.save_selection,
#        self.gui.chargerS_activate': self.load_selection,
#        self.gui.inverserS_activate': self.invert_selection,
#        self.gui.aucun1_activate': self.select_none,
#        self.gui.TouS_activate': self.select_all,
#        self.gui.taille_selection_activate': self.calculateSize,
#        self.gui.media_apres_activate': self.selectNewerMedia,
#        self.gui.media_avant_activate': self.SelectOlderMedia,
#
#
#
#

#
#        self.gui.fullscreen_activate': self.FullScreen,
#        self.gui.lance_diaporama_activate': self.SlideShow,

#        "on_AutoWB_activate": self.filterAutoWB,
#        "on_ContrastMask_activate": self.filterContrastMask,
#
#        "on_photo_button_press_event": self.image_pressed,

        }
        for signal, callback in handlers.items():
            print(callback.__name__)
            signal.connect(callback)

        self.gui.show()
        flush()
        width = sum(self.gui.splitter.sizes())
        self.gui.splitter.setSizes([self.left_tab_width,width-self.left_tab_width])
        self.show_image(first)

    def _set_icons(self, kwarg):
        """
        @param kwarg: dict with key: name of the image, value: widget
        """
        for name, widget in kwarg.items():
            icon = QtGui.QIcon()
            fullname = get_pixmap_file(name)
            pixmap = QtGui.QPixmap(fullname)
            icon.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            widget.setIcon(icon)

    def _menu_filtrer(self):
        #Drop-down filter menu
        self.filter_menu = QtGui.QMenu("Filtrer")

        icon_contrast = QtGui.QIcon()
        icon_contrast.addPixmap(QtGui.QPixmap(get_pixmap_file("contrast")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        action_contrast = QtGui.QAction(icon_contrast, "Masque de contrast", self.gui.filter)
        self.filter_menu.addAction(action_contrast)
        icon_colors = QtGui.QIcon()
        icon_colors.addPixmap(QtGui.QPixmap(get_pixmap_file("colors")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        action_color = QtGui.QAction(icon_colors, "Balance des blancs auto", self.gui.filter)
        self.filter_menu.addAction(action_color)
        self.gui.filter.setMenu(self.filter_menu)
        action_color.triggered.connect(self.filter_AutoWB)
        action_contrast.triggered.connect(self.filter_ContrastMask)


    def _action_handler(self, act):
        """
        Generic action handler
        @param act: QAction
        """
        meth_name = str(act.data().toString())
        print("Action %s => %s" % (act.text(), meth_name))

        try:
            callback = self.__getattribute__(meth_name)
        except AttributeError:
              logger.warning("Unhandeled menubar event on %s: no method %s" % (act.text(),meth_name))
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
            self.gui.actionDiaporama: "SlideShow",
            #    <string>Ctrl+D</string>
            self.gui.actionPlein_cran: "FullScreen",
            #    <string>Ctrl+F</string>
            self.gui.actionTrash_Ctrl_Del: "trash",
            self.gui.actionImporter_Image: "importImages",
            self.gui.actionSynchroniser: "synchronize",
            self.gui.actionEmpty_selected: "empty_selected",
            self.gui.actionCopier_seulement: "copy",
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
            self.gui.actionSave_pref: "savePref",
            self.gui.actionConfigurer_le_diaporama:"slideShowSetup",

            #Menu Selection
            self.gui.selectionner: "select_shortcut",
            #    <string>Ctrl+S</string>


#        self.gui.indexJ_activate': self.indexJ,
#        self.gui.searchJ_activate': self.searchJ,

            #Menu Filtres
            self.gui.actionAuto_whitebalance: "filter_AutoWB",
            self.gui.actionContrast_mask: "filter_ContrastMask",
            #Menu Aide
            self.gui.actionA_propos: "about",

            # Menu Preference
            self.gui.actionNearest:"set_interpolation",
            self.gui.actionLinear: "set_interpolation",
            self.gui.actionLanczos:"set_interpolation",
            self.gui.action9:  "set_images_per_page",
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
            #Menu navigation
            ##Image
            self.gui.actionNav_img_first: "navigate",
            self.gui.actionNav_img_previous10: "navigate",
            self.gui.actionNav_img_previous: "navigate",
            self.gui.actionNav_img_next: "navigate",
            self.gui.actionNav_img_next10: "navigate",
            self.gui.actionNav_img_last: "navigate",
            ##Day
            self.gui.actionNav_day_first: "navigate",
            self.gui.actionNav_day_previous: "navigate",
            self.gui.actionNav_day_next: "navigate",
            self.gui.actionNav_day_last: "navigate",
            ##Selected:
            self.gui.actionNav_sel_first: "navigate",
            self.gui.actionNav_sel_previous: "navigate",
            self.gui.actionNav_sel_next: "navigate",
            self.gui.actionNav_sel_last: "navigate",
            ##Non-selected:
            self.gui.actionNav_unsel_first: "navigate",
            self.gui.actionNav_unsel_previous: "navigate",
            self.gui.actionNav_unsel_next: "navigate",
            self.gui.actionNav_unsel_last: "navigate",
            ##Entitled
            self.gui.actionNav_title_first: "navigate",
            self.gui.actionNav_title_previous: "navigate",
            self.gui.actionNav_title_next: "navigate",
            self.gui.actionNav_title_last: "navigate",
            ##Non entitled
            self.gui.actionNav_untitle_first: "navigate",
            self.gui.actionNav_untitle_previous: "navigate",
            self.gui.actionNav_untitle_next: "navigate",
            self.gui.actionNav_untitle_last: "navigate",

            self.gui.actionNav_tree: "show_treeview",

            }
        #assign as data the name of the method to be called as callback
        for k, v in action_dict.items():
            k.setData(v)

    def update_title(self):
        """Set the new title of the image"""
        logger.debug("Interface.update_title")
        newtitle = unicode(self.gui.title.text())
        newRate = float(self.gui.rate.value())
        if (newtitle != self.current_title) or (newRate != self.current_rate):
            self.image.name(newtitle, newRate)


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
        X, Y = self.gui.photo.width(), self.gui.photo.height()
        logger.debug("Size of the image on screen: %sx%s" % (X, Y))
        pixbuf = self.image.get_pixbuf(X, Y)
#        if X <= self.left_tab_width :
#            X = self.left_tab_width + config.ScreenSize
#        pixbuf = self.image.get_pixbuf(X - self.left_tab_width, Y)
        self.gui.photo.setPixmap(pixbuf)
        del pixbuf
        gc.collect()
        metadata = self.image.readExif()
        if "rate" in metadata:
            self.current_rate = int(float(metadata["rate"]))
            self.gui.rate.setValue(self.current_rate)
            metadata.pop("rate")
        else:
            self.current_rate = 0

        for key, value in metadata.items():
            try:
                self.gui.__getattribute__(key).setText(value)
            except Exception:  # unexcpected error
                logger.error("unexpected metadata %s: %s" % (key, value))

        self.gui.setWindowTitle("Selector : %s" % self.fn_current)
        self.gui.selection.setCheckState(self.fn_current in self.selected)
        self.current_title = metadata["title"]


    def calc_index(self, what="next", menu="image"):
        """
        @param what: can be "next, "next10","last", "previous10", "last" ...
        @param menu: can be "image", "day", "sel", "unsel", "title", "untitle"
        @return: image index
        """
        print("calc_index %s %s %s" % (self.idx_current, what, menu))
        new_idx = current_idx = self.idx_current
        size = len(self.AllJpegs)
        if menu == "image":
            if what == "next":
                if self.min_mark == 0:
                    new_idx = current_idx + 1
                else:
                    for fn in self.AllJpegs[current_idx + 1:]:
                        image = Photo(fn)
                        data = image.readExif()
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
                        data = image.readExif()
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
                for img in self.AllJpegs[-1 ::-1]:
                    jc = os.path.dirname(img)
                    if (jc == lastday) and (jc < last):
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
                for i in self.AllJpegs[self.idx_current + 1]:
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
                    if myPhoto.has_title():
                        return  self.AllJpegs.index(i)
            elif what == "previous":
                for i in self.AllJpegs[current_idx - 1::-1]:
                    myPhoto = Photo(i)
                    if myPhoto.has_title():
                        return self.AllJpegs.index(i)
            elif what == "next":
                for i in self.AllJpegs[current_idx + 1:]:
                    myPhoto = Photo(i)
                    if myPhoto.has_title():
                        return self.AllJpegs.index(i)
            elif what == "last":
                for i in self.AllJpegs[-1::-1]:
                    myPhoto = Photo(i)
                    if myPhoto.has_title():
                        return self.AllJpegs.index(i)
        elif menu == "untitle":
            if what == "first":
                for i in self.AllJpegs:
                    myPhoto = Photo(i)
                    if not myPhoto.has_title():
                        return  self.AllJpegs.index(i)
            elif what == "previous":
                for i in self.AllJpegs[current_idx - 1::-1]:
                    myPhoto = Photo(i)
                    if not myPhoto.has_title():
                        return self.AllJpegs.index(i)
            elif what == "next":
                for i in self.AllJpegs[current_idx + 1:]:
                    myPhoto = Photo(i)
                    if not myPhoto.has_title():
                        return self.AllJpegs.index(i)
            elif what == "last":
                for i in self.AllJpegs[-1::-1]:
                    myPhoto = Photo(i)
                    if not myPhoto.has_title():
                        return self.AllJpegs.index(i)
        else:
            logger.warning("Unrecognized menu in navigate %s %s" % (menu, what))
        # final sanitization
        return new_idx % size

    def navigate(self, act):
        """
        Generic navigation
        """
        if act in self.navigation_dict:
            menu, what = self.navigation_dict[act]
            self.update_title()
            new_idx = self.calc_index(what, menu)
            logger.warning("Image %i -> %i" % (self.idx_current, new_idx))
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
        self.AllJpegs.remove(self.fn_current)
        self.image.trash()
        self.idx_current = self.idx_current % len(self.AllJpegs)
        self.fn_current = self.AllJpegs[self.idx_current]
        self.show_image()

    def gimp(self, *args):
        """Edit the current file with the Gimp"""
        logger.debug("Interface.gimp")
        self.update_title()
        filename = self.fn_current
        base, ext = os.path.splitext(filename)
        newname = base + "-Gimp" + ext
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort()
        self.idx_current = self.AllJpegs.index(newname)
        self.fn_current = newname
        newnamefull = os.path.join(config.DefaultRepository, newname)
        shutil.copy(os.path.join(config.DefaultRepository, filename), newnamefull)
        os.chmod(newnamefull, config.DefaultFileMode)
        os.system("%s %s &" % (config.Gimp, newnamefull))
        self.show_image()
        self.image.removeFromCache()

    def reload_img(self, *args):
        """Remove image from cache and reloads it"""
        logger.debug("Interface.reload")
        self.update_title()
        filename = self.AllJpegs[self.idx_current]
        if (imageCache is not None) and (filename in imageCache):
            imageCache.pop(filename)
        self.image = Photo(filename)
        self.show_image()

    def filter_im(self, *args):
        """ Apply the selected filter to the current image"""
        logger.debug("Interface.filter_image")
        print("do_filter, default=%s" % self.default_filter)
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
        filename = self.AllJpegs[self.idx_current]
        base, ext = os.path.splitext(filename)
        newname = base + "-ContrastMask" + ext
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort()
        self.idx_current = self.AllJpegs.index(newname)
        self.image = self.image.contrastMask(newname)
        self.show_image()

    def filter_AutoWB(self, *args):
        """Filter the current image with Auto White Balance"""
        logger.debug("Interface.filter_AutoWB")
        self.update_title()
        filename = self.AllJpegs[self.idx_current]
        base, ext = os.path.splitext(filename)
        newname = base + "-AutoWB" + ext
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort()
        self.idx_current = self.AllJpegs.index(newname)
        self.image = self.image.autoWB(newname)
        self.show_image()

    def select_shortcut(self, *args):
        """Select or unselect the image (not directly clicked on the toggle button)"""
        logger.debug("Interface.select_shortcut")
        etat = not(self.gui.Selection.active())
        self.gui.Selection.set_active(etat)

    def select(self, *args):
        """Select or unselect the image (directly clicked on the toggle button)"""
        logger.debug("Interface.select")
        self.fn_current = self.AllJpegs[self.idx_current]
        etat = bool(self.gui.selection.checkState())
        if etat and (self.fn_current not in self.selected):
            self.selected.append(self.fn_current)
        if not(etat) and (self.fn_current in self.selected):
            self.selected.remove(self.fn_current)
        self.selected.sort()
#        self.gui.selection.set_active(etat)
        if (self.image.metadata["rate"] == 0) and  etat:
            self.image.metadata["rate"] = config.DefaultRatingSelectedImage
            self.gui.rate.setValue(config.DefaultRatingSelectedImage)
        self.update_title()

    def destroy(self, *args):
        """destroy clicked by user"""
        logger.debug("Interface.destroy")
        self.update_title()
        self.gui.close()
#        config.GraphicMode = "quit"
        self.callback("quit")

    def die(self, *args):
        """you want to leave the program ??"""
        logger.debug("Interface.die")
        self.update_title()
        if quit_dialog(self.gui):
            self.selected.save()
            self.destroy()

    def FullScreen(self, *args):
        """Switch to fullscreen mode"""
        logger.debug("Interface.fullscreen")
        self.update_title()
        self.gui.close()
#        config.GraphicMode = "FullScreen"
#        gtk.main_quit()
        self.callback("fullscreen")

    def SlideShow(self, *args):
        """Switch to fullscreen mode and starts the SlideShow"""
        logger.debug("Interface.slideshow")
        self.update_title()
        self.gui.close
#        config.GraphicMode = "SlideShow"
#        gtk.main_quit()
        self.callback("slideshow")

    def copy_resize(self, *args):
        """lauch the copy of all selected files then scale them to generate web pages"""
        logger.debug("Interface.copy_resize")
        self.update_title()
        # TODO: go through MVC
        processSelected(self.selected)
        self.selected = Selected()
        self.gui.selection.set_active((self.AllJpegs[self.idx_current] in self.selected))
        logger.info("Interface.copy_resize: Done")

    def to_web(self, *args):
        """lauch the copy of all selected files then scale and finaly copy them to the generator-repository and generate web pages"""
        logger.debug("Interface.to_web")
        self.update_title()
        processSelected(self.selected)
        self.selected = Selected()
        self.gui.selection.set_active((self.AllJpegs[self.idx_current] in self.selected))
        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        out = os.system(config.WebServer.replace("$WebRepository", config.WebRepository).replace("$Selected", SelectedDir))
        if out != 0:
            print("Error n° : %i" % out)
        logger.info("Interface.to_web: Done")

    def empty_selected(self, *args):
        """remove all the files in the "Selected" folder"""

        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        for dirs in os.listdir(SelectedDir):
            curfile = os.path.join(SelectedDir, dirs)
            if os.path.isdir(curfile):
                recursive_delete(curfile)
            else:
                os.remove(curfile)
        print("Done")

    def copy(self, *args):
        """lauch the copy of all selected files"""
        self.update_title()
        copySelected(self.selected)
        self.selected = Selected()
        self.gui.selection.set_active((self.AllJpegs[self.idx_current] in self.selected))
        print("Done")

    def burn(self, *args):
        """lauch the copy of all selected files then burn a CD according to the configuration file"""
        logger.debug("Interface.burn")
        self.update_title()
        copySelected(self.selected)
        self.selected = Selected()
        # TODO : MVC
        self.gui.selection.set_active((self.AllJpegs[self.idx_current] in self.selected))
        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        out = os.system(config.Burn.replace("$Selected", SelectedDir))
        if out != 0:
            print("Error n° : %i" % out)
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
        self.gui.selection.set_active(self.AllJpegs[self.idx_current] in  self.selected)

    def select_all(self, *args):
        """Select all photos for processing"""
        logger.debug("Interface.select_all")
        self.update_title()
        self.selected = self.AllJpegs
        self.gui.selection.set_active(True)

    def select_none(self, *args):
        """Select NO photos and empty selection"""
        logger.debug("Interface.select_none")
        self.update_title()
        self.selected = Selected()
        self.gui.selection.set_active(False)

    def invert_selection(self, *args):
        """Invert the selection of photos """
        logger.debug("Interface.invert_selection")
        self.update_title()
        temp = self.AllJpegs[:]
        for i in self.selected:
            temp.remove(i)
        self.selected = temp
        self.gui.selection.set_active(self.AllJpegs[self.idx_current] in  self.selected)

    def about(self, *args):
        """display a copyright message"""
        logger.debug("Interface.about clicked")
        self.update_title()
        msg = "Selector vous permet de mélanger, de sélectionner et de tourner \ndes photos provenant de plusieurs sources.\nÉcrit par %s <%s>\nVersion %s" % (__author__, __contact__, __version__)
        QMessageBox.about(self.gui, "À Propos", msg)

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

    def savePref(self, *args):
        """Preferences,save clicked. now we save the preferences in the file"""
        logger.debug("Interface.savePref clicked")
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
        options = {9:  self.gui.action9,
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

    def renameDayCallback(self, renamdayinstance):
        logger.debug("Interface.renameDayCallback")
        self.AllJpegs = renamdayinstance.AllPhotos
        self.selected = renamdayinstance.selected
        newFilename = renamdayinstance.newFilename

    def start_image_mark_window(self, *args):
        """display widget to select minimum mark"""
        self.mark_window = MinimumRatingWindow(self)
        self.mark_window.show_all()

    def importImages(self, *args):
        """Launch a filer window to select a directory from witch import all JPEG/RAW images"""
        logger.debug("Interface.importImages called")
        self.update_title()
        self.guiFiler = buildUI("filer")
#        self.guiFiler.filer").set_current_folder(config.DefaultRepository)
#        self.guiFiler.connect_signals({self.gui.Open, 'clicked()', self.filerSelect,
#                                       self.gui.Cancel, 'clicked()', self.filerDestroy})

    def filerSelect(self, *args):
        """Close the filer GUI and update the data"""
        logger.debug("dirchooser.filerSelect called")
#        self.importImageCallBack(self.guiFiler.filer").get_current_folder())
        self.guiFiler.filer.close

    def filerDestroy(self, *args):
        """Close the filer GUI"""
        logger.debug("dirchooser.filerDestroy called")
        self.guiFiler.filer.close

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
            listNew.sort()
            first = listNew[0]
            self.AllJpegs += listNew
            self.AllJpegs.sort()
            self.idx_current = self.AllJpegs.index(first)
            self.show_image()


    def defineMediaSize(self, *args):
        """lauch a new window and ask for the size of the backup media"""
        logger.debug("Interface.defineMediaSize clicked")
        self.update_title()
        ask_media_size()

    def slideShowSetup(self, *args):
        """lauch a new window for seting up the slideshow"""
        logger.debug("Interface.slideShowSetup clicked")
        self.update_title()
        AskSlideShowSetup(self)
        if config.GraphicMode == "SlideShow":
            self.gui.close()
            gtk.main_quit()

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

    def selectNewerMedia(self, *args):
        """Calculate the size of the selected images then add newer images to complete the media (CD or DVD).
        Finally the last selected image is shown and the total size is printed"""
        logger.debug("Interface.selectNewerMedia clicked")
        self.update_title()
        size = self.selected.get_nbytes()
        initsize = size
        maxsize = config.MediaSize * 1024 * 1024
        init = len(self.selected)
        for i in self.AllJpegs[self.idx_current:]:
            if i in self.selected:
                continue
            size += os.path.getsize(os.path.join(config.DefaultRepository, i))
            if size >= maxsize:
                size -= os.path.getsize(os.path.join(config.DefaultRepository, i))
                break
            else:
                self.selected.append(i)
        self.selected.sort()
        if len(self.selected) == 0:return
        self.idx_current = self.AllJpegs.index(self.selected[-1])
        self.show_image()
        t = smartSize(size) + (len(self.selected),) + smartSize(initsize) + (init,)
        txt = "%.2f %s de données dans %i images sélectionnées dont\n%.2f %s de données dans %i images précédement sélectionnées " % t
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, txt.decode("UTF8"))
        dialog.run()
        dialog.destroy()
#        result = dialog.run()
#        dialog.destroy()


    def SelectOlderMedia(self, *args):
        """Calculate the size of the selected images then add older images to complete the media (CD or DVD).
        Finally the first selected image is shown and the total size is printed"""
        logger.debug("Interface.SelectOlderMedia clicked")
        self.update_title()
        size = self.selected.get_nbytes()
        initsize = size
        maxsize = config.MediaSize * 1024 * 1024
        init = len(self.selected)
        tmplist = self.AllJpegs[:self.idx_current]
        tmplist.reverse()
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
        if len(self.selected) == 0:return
        self.idx_current = self.AllJpegs.index(self.selected[0])
        self.show_image()
        t = smartSize(size) + (len(self.selected),) + smartSize(initsize) + (init,)
        txt = "%.2f %s de données dans %i images sélectionnées dont\n%.2f %s de données dans %i images précédement sélectionnées " % t
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, txt.decode("UTF8"))
        dialog.run()
        dialog.destroy()


    def calculateSize(self, *args):
        """Calculate the size of the selection and print it"""
        logger.debug("Interface.calculateSize clicked")
        self.update_title()
        size = self.selected.get_nbytes()
        t = smartSize(size) + (len(self.selected),)
        txt = "%.2f %s de données dans %i images sélectionnées" % t
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, txt.decode("UTF8"))
        dialog.run()
        dialog.destroy()

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

    def image_pressed(self, *args):
        """
        mouse button pressed on image
        """
        logger.info("Interface.image_pressed")
        ev_box, event = args
        width = ev_box.allocation.width
        height = ev_box.allocation.height
        if event.button == 1:
            if self.is_zoomed:
                pixbuf = self.image.get_pixbuf(width, height)
                self.gui.photo.set_from_pixbuf(pixbuf) #todo
                del pixbuf
                gc.collect()
                self.is_zoomed = False
            else:
                return
        elif event.button == 3:
            if self.is_zoomed:
                return
            else:
                pixbuf = self.image.get_pixbuf(width, height,
                                         float(event.x) / width,
                                         float(event.y) / height)
                self.gui.photo.set_from_pixbuf(pixbuf)
                del pixbuf
                gc.collect()
                self.is_zoomed = True


    def show_treeview(self, *arg):
        """
        """
        if self.treeview is None:
            tree_rep = tree.build_tree(self.AllJpegs)
            self.treeview = tree.TreeWidget(tree_rep)
            self.treeview.callback = self.goto_image
        self.treeview.show()

    def goto_image(self, name=None):
        """
        Callback for show_treeview
        """
        try:
            idx = self.AllJpegs.index(name)
        except:
            logger.warning("Unknown image in base %s"%name)
        else:
            self.show_image(idx)


    def toggle_toolbar(self, *arg):
        """
        Set toolbar visible/not
        """
        if  self.menubar_isvisible:
            self.menubar_height = self.gui.menubar.height()
        self.menubar_isvisible = not(self.menubar_isvisible)
        if self.menubar_isvisible:
            print("Set size to %s" % self.menubar_height)
            self.gui.menubar.setGeometry(0, 0, self.gui.width(), self.menubar_height)
        else:
            print("Set size to 0")
            self.gui.menubar.setGeometry(0, 0, self.gui.width(), 0)

        #self.gui.menubar.setVisible(self.toolbar_isvisible)
        #TODO:
        # create a toolbar and copy all sensible action to it

################################################################################
# # # # # # # fin de la classe interface graphique # # # # # #
################################################################################


class AskSlideShowSetup(object):
    """pop up a windows and asks for the setup of the SlideShow"""
    def __init__(self, upperIface):
        self.upperIface = upperIface
        self.gui = buildUI("Diaporama")
#        signals = {self.gui.Diaporama_destroy': self.destroy,
#                    self.gui.cancel, 'clicked()', self.kill_window,
#                    self.gui.apply, 'clicked()', self.continu,
#                    self.gui.Lauch, 'clicked()', self.LauchSlideShow,
#                    }
#        self.gui.connect_signals(signals)
        self.adj_Rate = gtk.Adjustment(0, 0, 5, 1)
        self.gui.Rating.set_adjustment(self.adj_Rate)
        self.adj_delai = gtk.Adjustment(10, 1, 60, 1)
        self.gui.delai.set_adjustment(self.adj_delai)
        self.gui.delai.set_value(config.SlideShowDelay)
        self.gui.Rating.set_value(config.SlideShowMinRating)
        if   config.SlideShowType.find("chrono") == 0:
            self.gui.radio-chrono.set_active(1)
        elif config.SlideShowType.find("anti") == 0:
            self.gui.radio-antichrono.set_active(1)
        else:
            self.gui.radio-random.set_active(1)

    def LauchSlideShow(self, *args):
        """retrieves the data, destroy the window and lauch the slideshow"""
        config.SlideShowDelay = self.gui.delai.value()
        config.SlideShowMinRating = self.gui.Rating.value()
        if self.gui.radio-antichrono.get_active():
            config.SlideShowType = "antichronological"
        elif self.gui.radio-chrono.get_active():
            config.SlideShowType = "chronological"
        else:
            config.SlideShowType = "random"
        config.GraphicMode = "SlideShow"
        self.gui.Diaporama.close
        self.upperIface.xml.lance_diaporama.activate()
#        self.gui.signal_connect(self.gui.lance_diaporama_activate'

    def continu(self, *args):
        """retrieves the data, destroy the window and goes on ...."""
        config.SlideShowDelay = self.gui.delai.value()
        config.SlideShowMinRating = self.gui.Rating.value()
        if self.gui.radio-antichrono.get_active():
            config.SlideShowType = "antichronological"
        elif self.gui.radio-chrono.get_active():
            config.SlideShowType = "chronological"
        else:
            config.SlideShowType = "random"
        self.gui.Diaporama.close

    def destroy(self, *args):
        """destroy clicked by user -> close the window"""
        flush()

    def kill_window(self, *args):
        """
        send the signal to close the window
        """
        try:
            self.gui.Diaporama.close
        except:
            pass







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
