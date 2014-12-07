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

logger.debug("from core")

from .imagizer import copySelected, processSelected, timer_pass
from .qt import QtCore, QtGui, buildUI, flush, SIGNAL, icon_on
from .selection import Selected
from .photo import Photo
from .utils import get_pixmap_file
from .config import config
from .imagecache import imageCache

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
        self.iCurrentImg = first
        self.timestamp = time.time()
        logger.info("Initialization of the fullscreen GUI")
        self.gui = buildUI("FullScreen")
        self.timeout_handler_id = gobject.timeout_add(1000, timer_pass)
        self.showImage()
        flush()
        self.gui.FullScreen.maximize()
        flush()
        self.showImage()
        flush()
#        self.gui.connect_signals({self.gui.FullScreen_destroy': self.destroy,
#                                  "on_FullScreen_key_press_event":self.keypressed})
        if mode == "slideshow":
            self.SlideShow()
        self.QuitSlideShow = True
        self.gui.show()

    def showImage(self):
        """Show the image in the given GtkImage widget and set up the exif tags in the GUI"""
        self.image = Photo(self.AllJpegs[self.iCurrentImg])
        X, Y = self.gui.FullScreen.get_size()
        logger.debug("Size of image on screen: %sx%s" % (X, Y))
        pixbuf = self.image.get_pixbuf(X, Y)
        self.gui.image793.set_from_pixbuf(pixbuf)
        del pixbuf
        gc.collect()
        if self.AllJpegs[self.iCurrentImg] in self.selected:
            sel = "[Selected]"
        else:
            sel = ""
        self.gui.FullScreen.set_title("Selector : %s %s" % (self.AllJpegs[self.iCurrentImg], sel))

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
        self.showImage()
    def turn_left(self, *args):
        """rotate the current image clockwise"""
        self.image.rotate(270)
        self.showImage()

    def destroy(self, *args):
        """destroy clicked by user"""
        self.close("quit")

    def NormalScreen(self, *args):
        """Switch to Normal mode"""
        self.close("normal")

    def next1(self, *args):
        """Switch to the next image"""
        self.iCurrentImg = (self.iCurrentImg + 1) % len(self.AllJpegs)
        self.showImage()
    def previous1(self, *args):
        """Switch to the previous image"""
        self.iCurrentImg = (self.iCurrentImg - 1) % len(self.AllJpegs)
        self.showImage()
    def nextJ(self, *args):
        """Switch to the first image of the next day"""
        jour = os.path.dirname(self.AllJpegs[self.iCurrentImg])
        for i in range(self.iCurrentImg, len(self.AllJpegs)):
            jc = os.path.dirname(self.AllJpegs[i])
            if jc > jour: break
        self.iCurrentImg = i
        self.showImage()
    def previousJ(self, *args):
        """Switch to the first image of the previous day"""
        if self.iCurrentImg == 0: return
        jour = os.path.dirname(self.AllJpegs[self.iCurrentImg])
        for i in range(self.iCurrentImg - 1, -1, -1):
            jc = os.path.dirname(self.AllJpegs[i])
            jd = os.path.dirname(self.AllJpegs[i - 1])
            if (jc < jour) and (jd < jc): break
        self.iCurrentImg = i
        self.showImage()

    def select_Shortcut(self, *args):
        """Select or unselect the image"""
        if self.AllJpegs[self.iCurrentImg] not in self.selected:
            self.selected.append(self.AllJpegs[self.iCurrentImg])
            sel = "[Selected]"
        else:
            self.selected.remove(self.AllJpegs[self.iCurrentImg])
            sel = ""
        self.selected.sort()
        self.gui.setWindowTitle("Selector : %s %s" % (self.AllJpegs[self.iCurrentImg], sel))

    def SlideShow(self):
        """Starts the slide show"""
        self.QuitSlideShow = False
        self.RandomList = []
        while not self.QuitSlideShow:
            if config.SlideShowType == "chronological":
                self.iCurrentImg = (self.iCurrentImg + 1) % len(self.AllJpegs)
            elif config.SlideShowType == "antichronological":
                self.iCurrentImg = (self.iCurrentImg - 1) % len(self.AllJpegs)
            elif config.SlideShowType == "random":
                if len(self.RandomList) == 0:
                    self.RandomList = range(len(self.AllJpegs))
                    random.shuffle(self.RandomList)
                self.iCurrentImg = self.RandomList.pop()
            self.image = Photo(self.AllJpegs[self.iCurrentImg])
            self.image.readExif()
            if self.image.metadata["rate"] < config.SlideShowMinRating:
                flush()
                continue
            now = time.time()
            if now - self.timestamp < config.SlideShowDelay:
                time.sleep(config.SlideShowDelay - now + self.timestamp)
            self.showImage()
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
        self.iCurrentImg = first
        self.Xmin = 350
        self.image = None
        self.current_title = ""
        self.current_rate = 0
        self.current_image = AllJpegs[first]
        self.is_zoomed = False
        self.min_mark = 0
        self.default_filter = None
        print("Initialization of the windowed graphical interface ...")
        logger.info("Initialization of the windowed graphical interface ...")
        self.gui = buildUI("principale")

        # Icons on buttons
        self.gui.logo.setPixmap(QtGui.QPixmap(get_pixmap_file("logo")))
        self._set_icons({"contrast": self.gui.filter,
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
        self.gui.actionAutorotate.setChecked(bool(config.AutoRotate))
        self.gui.actionSignature_filigrane_web.setChecked(bool(config.Filigrane))
        self.set_images_per_page(config.NbrPerPage)
        self.set_interpolation(config.Interpolation)
        self.showImage()
        flush()
        self._menu_filtrer()
        flush()

        handlers = {self.gui.next.clicked:self.next1,
                    self.gui.previous.clicked: self.previous1,
                    self.gui.right.clicked:self.turn_right,
                    self.gui.left.clicked: self.turn_left,
                    self.gui.selection.stateChanged: self.select,
                    self.gui.trash.clicked: self.trash,
                    self.gui.edit.clicked:self.gimp,
                    self.gui.reload.clicked:self.reload_img,
                    self.gui.filter.clicked:self.filter_im,

                    # Menu Fichier
                    self.gui.actionName_day.triggered: self.renameDay,
                    #    <string>Ctrl+N</string>
                    self.gui.actionDiaporama.triggered: self.SlideShow,
                    #    <string>Ctrl+D</string>
                    self.gui.actionPlein_cran.triggered: self.FullScreen,
                    #    <string>Ctrl+F</string>
                    self.gui.actionTrash_Ctrl_Del.triggered: self.trash,
                    self.gui.actionImporter_Image.triggered: self.importImages,
                    self.gui.actionSynchroniser.triggered: self.synchronize,
                    self.gui.actionEmpty_selected.triggered: self.emptySelected,
                    self.gui.actionCopier_seulement.triggered: self.copy,
                    self.gui.actionCopier_et_graver.triggered: self.burn,
                    self.gui.actionCopier_et_redimensionner.triggered: self.copyAndResize,
                    self.gui.actionVers_page_web.triggered: self.toWeb,
                    self.gui.actionSortir.triggered: self.destroy,
                    #    <string>Ctrl+E</string>
                    self.gui.actionQuitter.triggered: self.die,
                    #    <string>Ctrl+Q</string>

                    # Menu Affichage
                    self.gui.actionNote_minimale.triggered: self.start_image_mark_window,
                    self.gui.actionReload.triggered: self.reload_img,
                    self.gui.actionRotation_left.triggered: self.turn_left,
                    #    <string>Ctrl+Left</string>
                    self.gui.actionRotation_right.triggered: self.turn_right,
                    #    <string>Ctrl+Right</string>


                    # Menu Preference
                    self.gui.actionMedia_size.triggered:self.defineMediaSize,
                    self.gui.actionAutorotate.triggered:self.setAutoRotate,
                    self.gui.actionSignature_filigrane_web.triggered:self.setFiligrane,
                    self.gui.actionSave_pref.triggered: self.savePref,
                    self.gui.actionNearest.triggered:self.setInterpolNearest,
                    self.gui.actionLinear.triggered: self.setInterpolBilin,
                    self.gui.actionLanczos.triggered:self.setInterpolLanczos,
                    self.gui.action9.triggered:  self.set9PerPage,
                    self.gui.action12.triggered: self.set12PerPage,
                    self.gui.action16.triggered: self.set16PerPage,
                    self.gui.action20.triggered: self.set20PerPage,
                    self.gui.action25.triggered: self.set25PerPage,
                    self.gui.action30.triggered: self.set30PerPage,
                    self.gui.actionConfigurer_le_diaporama.triggered:self.slideShowSetup,

                    #Menu Selection
                    self.gui.selectionner.triggered:self.select_shortcut,
                    #    <string>Ctrl+S</string>


                    #Menu navigation
                    ##Image
                    self.gui.actionNav_img_first.triggered: self.first,
                    self.gui.actionNav_img_previous10.triggered: self.previous10,
                    self.gui.actionNav_img_previous.triggered: self.previous1,
                    self.gui.actionNav_img_next.triggered: self.next1,
                    self.gui.actionNav_img_next10.triggered: self.next10,
                    self.gui.actionNav_img_last.triggered: self.last,
                    ##Day
                    self.gui.actionNav_day_first.triggered: self.firstJ,
                    self.gui.actionNav_day_previous.triggered: self.previousJ,
                    self.gui.actionNav_day_next.triggered: self.nextJ,
                    self.gui.actionNav_day_last.triggered: self.lastJ,
#        self.gui.indexJ_activate': self.indexJ,
#        self.gui.searchJ_activate': self.searchJ,
                    ##Selected:
                    self.gui.actionNav_sel_first.triggered: self.firstS,
                    self.gui.actionNav_sel_previous.triggered: self.previousS,
                    self.gui.actionNav_sel_next.triggered: self.nextS,
                    self.gui.actionNav_sel_last.triggered: self.lastS,
                    ##Non-selected:
                    self.gui.actionNav_non_sel_first.triggered: self.firstNS,
                    self.gui.actionNav_non_sel_previous.triggered: self.previousNS,
                    self.gui.actionNav_non_sel_next.triggered: self.nextNS,
                    self.gui.actionNav_non_sel_last.triggered: self.lastNS,
                    ##Entitled
                    self.gui.actionNav_title_first.triggered: self.firstT,
                    self.gui.actionNav_title_previous.triggered: self.previousT,
                    self.gui.actionNav_title_next.triggered: self.nextT,
                    self.gui.actionNav_title_last.triggered: self.lastT,
                    ##Non entitled
                    self.gui.actionNav_non_title_first.triggered: self.firstNT,
                    self.gui.actionNav_non_title_previous.triggered: self.previousNT,
                    self.gui.actionNav_non_title_next.triggered: self.nextNT,
                    self.gui.actionNav_non_title_last.triggered: self.lastNT,

                    #Menu Filtres
                    self.gui.actionAuto_whitebalance.triggered: self.filter_AutoWB,
                    self.gui.actionContrast_mask.triggered: self.filter_ContrastMask,
                    #Menu Aide
                    self.gui.actionA_propos.triggered: self.about,

#
#        self.gui.enregistrerS_activate': self.saveSelection,
#        self.gui.chargerS_activate': self.loadSelection,
#        self.gui.inverserS_activate': self.invertSelection,
#        self.gui.aucun1_activate': self.selectNone,
#        self.gui.TouS_activate': self.selectAll,
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

###################################################################

#        self.gui.actionCharger.triggered
#        self.gui.actionSauver.triggered
#        self.gui.actionInverser.triggered
#        self.gui.actionAucune.triggered
#        self.gui.actionToutes.triggered
#        self.gui.actionTaille_de_toute_la_s_lection.triggered
#        self.gui.actionCD_DVD_suivant.triggered
#        self.gui.actionCD_DVD_pr_c_dent.triggered
#        self.gui.actionD_but.triggered
#        #    <string>Home</string>
#        self.gui.actionMoins_10.triggered
#        #    <string>Ctrl+PgUp</string>
#        self.gui.actionPr_c_dent_Ctrl_Haut.triggered
#        #    <string>Ctrl+Up</string>
#        self.gui.actionSuivant_Ctrl_Bas.triggered
#        #    <string>Ctrl+Down</string>
#        self.gui.actionPlus_10_Ctrl_PgDn.triggered
#        #    <string>Ctrl+PgDown</string>
#        self.gui.actionFin.triggered
#        #    <string>End</string>
#        self.gui.actionD_but_2.triggered
#        self.gui.actionPr_c_dent_PgUp.triggered
#        #    <string>PgUp</string>
#        self.gui.actionSuivant_PgDn.triggered
#        #    <string>PgDown</string>
#        self.gui.actionFin_2.triggered
#        self.gui.actionD_but_3.triggered
#        self.gui.actionPr_c_dent_Alt_Haut.triggered
#        #    <string>Meta+Alt+Up</string>
#        self.gui.actionSuivant_Alt_Bas.triggered
#        #    <string>Meta+Alt+Down</string>
#        self.gui.actionFin_3.triggered
#        self.gui.actionD_but_4.triggered
#        self.gui.actionPr_c_dent.triggered
#        self.gui.actionSuivant.triggered
#        self.gui.actionFin_4.triggered
#        self.gui.actionD_but_5.triggered
#        self.gui.actionPr_c_dent_2.triggered
#        self.gui.actionSuivant_2.triggered
#        self.gui.actionFin_5.triggered
#        self.gui.actionD_but_6.triggered
#        self.gui.actionPr_c_dent_3.triggered
#        self.gui.actionSuivant_3.triggered
#        self.gui.actionFin_6.triggered
#        self.gui.actionBalance_des_blancs_auto.triggered
#        self.gui.actionMasque_de_contraste.triggered



        }
        for signal, callback in handlers.items():
            print(callback.__name__)
            signal.connect(callback)
        self.showImage()
        self.gui.show()

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



    def update_title(self):
        """Set the new title of the image"""
        logger.debug("Interface.update_title")
        newtitle = unicode(self.gui.title.text())
        newRate = float(self.gui.rate.value())
        if (newtitle != self.current_title) or (newRate != self.current_rate):
            self.image.name(newtitle, newRate)


    def showImage(self):
        """Show the image in the given GtkImage widget and set up the exif tags in the GUI"""
        logger.debug("Interface.showImage")
        self.current_image = self.AllJpegs[self.iCurrentImg]
        self.image = Photo(self.current_image)
        X, Y = self.gui.width(), self.gui.photo.height()
        logger.debug("Size of the image on screen: %sx%s" % (X, Y))
        if X <= self.Xmin : X = self.Xmin + config.ScreenSize
        pixbuf = self.image.get_pixbuf(X - self.Xmin, Y)
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

        self.gui.setWindowTitle("Selector : %s" % self.current_image)
        self.gui.selection.setCheckState(self.current_image in self.selected)
        self.current_title = metadata["title"]



    def next1(self, *args):
        """Switch to the next image"""
        logger.debug("Interface.next1")
        self.update_title()
        if self.min_mark < 1:
            self.iCurrentImg = (self.iCurrentImg + 1) % len(self.AllJpegs)
        else:
            for i in range(self.iCurrentImg + 1, len(self.AllJpegs)):
                image = Photo(self.AllJpegs[i])
                data = image.readExif()
                if "rate" in data:
                    rate = int(float(data["rate"]))
                    if rate >= self.min_mark:
                        break
            else:
                print("No image found with rating > %s" % self.min_mark)
            self.iCurrentImg = i
        self.showImage()

    def next10(self, *args):
        """Switch forward of 10 images """
        logger.debug("Interface.next10")
        self.update_title()
        self.iCurrentImg = self.iCurrentImg + 10
        if self.iCurrentImg > len(self.AllJpegs):self.iCurrentImg = len(self.AllJpegs) - 1
        self.showImage()

    def previous1(self, *args):
        """Switch to the previous image"""
        logger.debug("Interface.previous")
        self.update_title()
        if self.min_mark < 1:
            self.iCurrentImg = (self.iCurrentImg - 1) % len(self.AllJpegs)
        else:
            for i in range(self.iCurrentImg - 1, -1, -1):
                image = Photo(self.AllJpegs[i])
                data = image.readExif()
                if "rate" in data:
                    rate = int(float(data["rate"]))
                    if rate >= self.min_mark:
                        break
            else:
                i = 0
                print("No image found with rating > %s" % self.min_mark)
            self.iCurrentImg = i

        self.showImage()

    def previous10(self, *args):
        """Switch 10 images backward"""
        logger.debug("Interface.previous10")
        self.update_title()
        self.iCurrentImg = self.iCurrentImg - 10
        if self.iCurrentImg < 0: self.iCurrentImg = 0
        self.showImage()

    def first(self, *args):
        """switch to the first image"""
        logger.debug("Interface.first")
        self.update_title()
        self.iCurrentImg = 0
        self.showImage()

    def last(self, *args):
        """switch to the last image"""
        logger.debug("Interface.last")
        self.update_title()
        self.iCurrentImg = len(self.AllJpegs) - 1
        self.showImage()

    def turn_right(self, *args):
        """rotate the current image clockwise"""
        logger.debug("Interface.turn_right")
        self.update_title()
        self.image.rotate(90)
        self.showImage()

    def turn_left(self, *args):
        """rotate the current image counterclockwise"""
        logger.debug("Interface.turn_left")
        self.update_title()
        self.image.rotate(270)
        self.showImage()

    def trash(self, *args):
        """Send the current file to the trash"""
        logger.debug("Interface.trash")
        self.update_title()
        if self.current_image in  self.selected:
            self.selected.remove(self.current_image)
        self.AllJpegs.remove(self.current_image)
        self.image.trash()
        self.iCurrentImg = self.iCurrentImg % len(self.AllJpegs)
        self.current_image = self.AllJpegs[self.iCurrentImg]
        self.showImage()

    def gimp(self, *args):
        """Edit the current file with the Gimp"""
        logger.debug("Interface.gimp")
        self.update_title()
        filename = self.current_image
        base, ext = os.path.splitext(filename)
        newname = base + "-Gimp" + ext
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort()
        self.iCurrentImg = self.AllJpegs.index(newname)
        self.current_image = newname
        newnamefull = os.path.join(config.DefaultRepository, newname)
        shutil.copy(os.path.join(config.DefaultRepository, filename), newnamefull)
        os.chmod(newnamefull, config.DefaultFileMode)
        os.system("%s %s &" % (config.Gimp, newnamefull))
        self.showImage()
        self.image.removeFromCache()

    def reload_img(self, *args):
        """Remove image from cache and reloads it"""
        logger.debug("Interface.reload")
        self.update_title()
        filename = self.AllJpegs[self.iCurrentImg]
        if (imageCache is not None) and (filename in imageCache):
            imageCache.pop(filename)
        self.image = Photo(filename)
        self.showImage()

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
        filename = self.AllJpegs[self.iCurrentImg]
        base, ext = os.path.splitext(filename)
        newname = base + "-ContrastMask" + ext
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort()
        self.iCurrentImg = self.AllJpegs.index(newname)
        self.image = self.image.contrastMask(newname)
        self.showImage()

    def filter_AutoWB(self, *args):
        """Filter the current image with Auto White Balance"""
        logger.debug("Interface.filter_AutoWB")
        self.update_title()
        filename = self.AllJpegs[self.iCurrentImg]
        base, ext = os.path.splitext(filename)
        newname = base + "-AutoWB" + ext
        if not newname in self.AllJpegs:
            self.AllJpegs.append(newname)
            self.AllJpegs.sort()
        self.iCurrentImg = self.AllJpegs.index(newname)
        self.image = self.image.autoWB(newname)
        self.showImage()

    def select_shortcut(self, *args):
        """Select or unselect the image (not directly clicked on the toggle button)"""
        logger.debug("Interface.select_shortcut")
        etat = not(self.gui.Selection.active())
        self.gui.Selection.set_active(etat)

    def select(self, *args):
        """Select or unselect the image (directly clicked on the toggle button)"""
        logger.debug("Interface.select")
        self.current_image = self.AllJpegs[self.iCurrentImg]
        etat = bool(self.gui.selection.checkState())
        if etat and (self.current_image not in self.selected):
            self.selected.append(self.current_image)
        if not(etat) and (self.current_image in self.selected):
            self.selected.remove(self.current_image)
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

    def copyAndResize(self, *args):
        """lauch the copy of all selected files then scale them to generate web pages"""
        logger.debug("Interface.copyAndResize")
        self.update_title()
        # TODO: go through MVC
        processSelected(self.selected)
        self.selected = Selected()
        self.gui.selection.set_active((self.AllJpegs[self.iCurrentImg] in self.selected))
        logger.info("Interface.copyAndResize: Done")

    def toWeb(self, *args):
        """lauch the copy of all selected files then scale and finaly copy them to the generator-repository and generate web pages"""
        logger.debug("Interface.toWeb")
        self.update_title()
        processSelected(self.selected)
        self.selected = Selected()
        self.gui.selection.set_active((self.AllJpegs[self.iCurrentImg] in self.selected))
        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        out = os.system(config.WebServer.replace("$WebRepository", config.WebRepository).replace("$Selected", SelectedDir))
        if out != 0:
            print("Error n° : %i" % out)
        logger.info("Interface.toWeb: Done")

    def emptySelected(self, *args):
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
        self.gui.selection.set_active((self.AllJpegs[self.iCurrentImg] in self.selected))
        print("Done")

    def burn(self, *args):
        """lauch the copy of all selected files then burn a CD according to the configuration file"""
        logger.debug("Interface.burn")
        self.update_title()
        copySelected(self.selected)
        self.selected = Selected()
        # TODO : MVC
        self.gui.selection.set_active((self.AllJpegs[self.iCurrentImg] in self.selected))
        SelectedDir = os.path.join(config.DefaultRepository, config.SelectedDirectory)
        out = os.system(config.Burn.replace("$Selected", SelectedDir))
        if out != 0:
            print("Error n° : %i" % out)
        logger.info("Interface.burn: Done")

    def die(self, *args):
        """you wanna leave the program ??"""
        logger.debug("Interface.die")
        self.update_title()
        print("TODO: die")
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, "Voulez vous vraiment quitter ce programme ?")
        result = dialog.run()
        dialog.destroy()
        if result == gtk.RESPONSE_OK:
            self.selected.save()
            config.GraphicMode = "Quit"
            gtk.main_quit()
            config.GraphicMode = "Quit"


    def saveSelection(self, *args):
        """Saves all the selection of photos """
        logger.debug("Interface.saveSelection")
        self.update_title()
        self.selected.save()


    def loadSelection(self, *args):
        """Load a previously saved  selection of photos """
        logger.debug("Interface.loadSelection")
        self.update_title()
        self.selected = Selected.load()
        for i in self.selected:
            if not(i in self.AllJpegs):
                self.selected.remove(i)
        self.gui.selection.set_active(self.AllJpegs[self.iCurrentImg] in  self.selected)


    def selectAll(self, *args):
        """Select all photos for processing"""
        logger.debug("Interface.selectAll")
        self.update_title()
        self.selected = self.AllJpegs
        self.gui.selection.set_active(True)

    def selectNone(self, *args):
        """Select NO photos and empty selection"""
        logger.debug("Interface.selectNone")
        self.update_title()
        self.selected = Selected()
        self.gui.selection.set_active(False)

    def invertSelection(self, *args):
        """Invert the selection of photos """
        logger.debug("Interface.invertSelection")
        self.update_title()
        temp = self.AllJpegs[:]
        for i in self.selected:
            temp.remove(i)
        self.selected = temp
        self.gui.selection.set_active(self.AllJpegs[self.iCurrentImg] in  self.selected)

    def about(self, *args):
        """display a copyright message"""
        logger.debug("Interface.about clicked")
        self.update_title()
        msg = "Selector vous permet de mélanger, de sélectionner et de tourner \ndes photos provenant de plusieurs sources.\nÉcrit par %s <%s>\nVersion %s" % (__author__, __contact__, __version__)
#        MessageError(msg.decode("UTF8"), Message=gtk.MESSAGE_INFO)
        print(msg)
        QMessageBox.about(self.gui, "À Propos", msg)


    def nextJ(self, *args):
        """Switch to the first image of the next day"""
        logger.debug("Interface.nextJ clicked")
        self.update_title()
        jour = os.path.dirname(self.AllJpegs[self.iCurrentImg])
        for i in range(self.iCurrentImg, len(self.AllJpegs)):
            jc = os.path.dirname(self.AllJpegs[i])
            if jc > jour: break
        self.iCurrentImg = i
        self.showImage()

    def previousJ(self, *args):
        """Switch to the first image of the previous day"""
        logger.debug("Interface.previousJ clicked")
        self.update_title()
        if self.iCurrentImg == 0: return
        jour = os.path.dirname(self.AllJpegs[self.iCurrentImg])
        for i in range(self.iCurrentImg - 1, -1, -1):
            jc = os.path.dirname(self.AllJpegs[i])
            jd = os.path.dirname(self.AllJpegs[i - 1])
            if (jc < jour) and (jd < jc): break
        self.iCurrentImg = i
        self.showImage()

    def firstJ(self, *args):
        """switch to the first image of the first day"""
        logger.debug("Interface.firstJ clicked")
        self.update_title()
        self.iCurrentImg = 0
        self.showImage()

    def lastJ(self, *args):
        """switch to the first image of the last day"""
        logger.debug("Interface.lastJ clicked")
        self.update_title()
        lastday = os.path.dirname(self.AllJpegs[-1])
        for i in range(len(self.AllJpegs) - 1, -1, -1):
            jc = os.path.dirname(self.AllJpegs[i])
            jd = os.path.dirname(self.AllJpegs[i - 1])
            if (jc == lastday) and (jd < jc): break
        self.iCurrentImg = i
        self.showImage()

    def searchJ(self, *args):
        """start the searching widget"""
        logger.debug("Interface.searchJ clicked")
        SearchDay(self.AllJpegs, self.setDay)

    def setDay(self, path):
        try:
            self.iCurrentImg = self.AllJpegs.index(path)
        except ValueError:
            logger.error("%s not in AllJpegs" % path)
        else:
            self.showImage()
    def firstS(self, *args):
        """switch to the first image selected"""
        logger.debug("Interface.firstS clicked")
        self.update_title()
        if len(self.selected) == 0:
            return
        self.iCurrentImg = self.AllJpegs.index(self.selected[0])
        self.showImage()

    def lastS(self, *args):
        """switch to the last image selected"""
        logger.debug("Interface.lastS clicked")
        self.update_title()
        if len(self.selected) == 0:
            return
        self.iCurrentImg = self.AllJpegs.index(self.selected[-1])
        self.showImage()

    def nextS(self, *args):
        """switch to the next image selected"""
        logger.debug("Interface.nextS clicked")
        self.update_title()
        if len(self.selected) == 0:return
        for i in self.AllJpegs[self.iCurrentImg + 1:]:
            if i in self.selected:
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def previousS(self, *args):
        """switch to the previous image selected"""
        logger.debug("Interface.previousS clicked")
        self.update_title()
        if len(self.selected) == 0:return
        temp = self.AllJpegs[:self.iCurrentImg]
        temp.reverse()
        for i in temp:
            if i in self.selected:
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def firstNS(self, *args):
        """switch to the first image NOT selected"""
        logger.debug("Interface.firstNS clicked")
        self.update_title()
        for i in self.AllJpegs:
            if i not in self.selected:
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def lastNS(self, *args):
        """switch to the last image NOT selected"""
        logger.debug("Interface.lastNS clicked")
        self.update_title()
        temp = self.AllJpegs[:]
        temp.reverse()
        for i in temp:
            if i not in self.selected:
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def nextNS(self, *args):
        """switch to the next image NOT selected"""
        logger.debug("Interface.nextNS clicked")
        self.update_title()
        for i in self.AllJpegs[self.iCurrentImg + 1:]:
            if i not in self.selected:
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def previousNS(self, *args):
        """switch to the previous image NOT selected"""
        logger.debug("Interface.previousNS clicked")
        self.update_title()
        temp = self.AllJpegs[:self.iCurrentImg]
        temp.reverse()
        for i in temp:
            if i not in self.selected:
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def firstT(self, *args):
        """switch to the first entiteled image"""
        logger.debug("Interface.firstT clicked")
        self.update_title()
        for i in self.AllJpegs:
            myPhoto = Photo(i)
            if myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def    previousT(self, *args):
        """switch to the previous titeled image"""
        logger.debug("Interface.previousT clicked")
        self.update_title()
        temp = self.AllJpegs[:self.iCurrentImg]
        temp.reverse()
        for i in temp:
            myPhoto = Photo(i)
            if myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def nextT(self, *args):
        """switch to the next titeled image"""
        logger.debug("Interface.nextT")
        self.update_title()
        for i in self.AllJpegs[self.iCurrentImg + 1:]:
            myPhoto = Photo(i)
            if myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def lastT(self, *args):
        """switch to the last titeled image"""
        logger.debug("Interface.lastT clicked")
        self.update_title()
        temp = self.AllJpegs[:]
        temp.reverse()
        for i in temp:
            myPhoto = Photo(i)
            if myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def firstNT(self, *args):
        """switch to the first non-titeled image"""
        logger.debug("Interface.firstNT clicked")
        self.update_title()
        for i in self.AllJpegs:
            myPhoto = Photo(i)
            if not myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def previousNT(self, *args):
        """switch to the previous non-titeled image"""
        logger.debug("Interface.previousNT clicked")
        self.update_title()
        temp = self.AllJpegs[:self.iCurrentImg]
        temp.reverse()
        for i in temp:
            myPhoto = Photo(i)
            if not myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def nextNT(self, *args):
        """switch to the next non-titeled image"""
        logger.debug("Interface.nextNT clicked")
        self.update_title()
        for i in self.AllJpegs[self.iCurrentImg + 1:]:
            myPhoto = Photo(i)
            if not myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return

    def lastNT(self, *args):
        """switch to the last non-titeled image"""
        logger.debug("Interface.lastNT clicked")
        self.update_title()
        temp = self.AllJpegs[:]
        temp.reverse()
        for i in temp:
            myPhoto = Photo(i)
            if not myPhoto.has_title():
                self.iCurrentImg = self.AllJpegs.index(i)
                self.showImage()
                return



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
#        config.Filigrane = self.gui.Filigrane").get_active()

    def sizeCurrent(self, *args):
        """reads the current size of the image and defines it as default for next-time"""
        logger.debug("Interface.sizeCurrent clicked")
        X, Y = self.gui.width(), self.gui.heigth()
        config.ScreenSize = max(X - self.Xmin, Y)

    def setSize300(self, *args):
        """reads the current size of the image and defines it as default for next-time"""
        logger.debug("Interface.setSize300 clicked")
        config.ScreenSize = 300

    def setSize600(self, *args):
        """reads the current size of the image and defines it as default for next-time"""
        logger.debug("Interface.setSize600 clicked")
        config.ScreenSize = 600

    def setSize900(self, *args):
        """reads the current size of the image and defines it as default for next-time"""
        logger.debug("Interface.setSize900 clicked")
        config.ScreenSize = 900

    def set_interpolation(self, value):
        logger.debug("Interface.set_interpolation")
        options = (self.gui.actionNearest,
                    self.gui.actionLinear,
                    self.gui.actionLanczos)

        value = int(value)
        config.Interpolation = value
        for i, name in enumerate(options):
            name.setChecked(i == value)

    def setInterpolNearest(self, *args):
        """set interpolation level to nearest"""
        print("Interface.setInterpolNearest")
        self.set_interpolation(0)

    def setInterpolBilin(self, *args):
        """set interpolation level to bilinear"""
        logger.debug("Interface.setInterpolBilin clicked (bilinear)")
        self.set_interpolation(1)

    def setInterpolLanczos(self, *args):
        """set interpolation level to Lanczos"""
        logger.debug("Interface.setInterpolLanczos clicked ")
        self.set_interpolation(2)

    def set_images_per_page(self, value):
        logger.debug("Interface.set_interpolation")
        options = {9:self.gui.action9,
                   12:self.gui.action12,
                   16:self.gui.action16,
                   20:self.gui.action20,
                   25:self.gui.action25,
                   30:self.gui.action30,
        }

        value = int(value)
        config.NbrPerPage = value
        for i, name in options.items():
            name.setChecked(i == value)


    def set30PerPage(self, *args):
        """set 30 images per web-page"""
        logger.debug("Interface.set30PerPage clicked")
        self.set_images_per_page(30)

    def set25PerPage(self, *args):
        """set 25 images per web-page"""
        logger.debug("Interface.set25PerPage clicked")
        self.set_images_per_page(25)

    def set20PerPage(self, *args):
        """set 20 images per web-page"""
        logger.debug("Interface.set20PerPage clicked")
        self.set_images_per_page(20)

    def set16PerPage(self, *args):
        """set 16 images per web-page"""
        logger.debug("Interface.set16PerPage clicked")
        self.set_images_per_page(16)

    def set12PerPage(self, *args):
        """set 12 images per web-page"""
        logger.debug("Interface.set12PerPage clicked")
        self.set_images_per_page(12)

    def set9PerPage(self, *args):
        """set  9 images per web-page"""
        logger.debug("Interface.set9PerPage clicked")
        self.set_images_per_page(9)

    def renameDay(self, *args):
        """Launch a new window and ask for anew name for the current directory"""
        logger.debug("Interface.renameDay clicked")
        self.update_title()
        RenameDay(self.AllJpegs[self.iCurrentImg], self.AllJpegs, self.selected, self.renameDayCallback)

    def renameDayCallback(self, renamdayinstance):
        logger.debug("Interface.renameDayCallback")
        self.AllJpegs = renamdayinstance.AllPhotos
        self.selected = renamdayinstance.selected
        newFilename = renamdayinstance.newFilename
        self.image.filename = newFilename
        self.image.fn = os.path.join(config.DefaultRepository, newFilename)
        self.image._exif = None
        self.image._pil = None
        self.iCurrentImg = self.AllJpegs.index(newFilename)
        self.showImage()

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
            self.iCurrentImg = self.AllJpegs.index(first)
            self.showImage()


    def defineMediaSize(self, *args):
        """lauch a new window and ask for the size of the backup media"""
        logger.debug("Interface.defineMediaSize clicked")
        self.update_title()
        AskMediaSize()

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
        Synchronize(self.iCurrentImg, self.AllJpegs, self.selected)


    def selectNewerMedia(self, *args):
        """Calculate the size of the selected images then add newer images to complete the media (CD or DVD).
        Finally the last selected image is shown and the total size is printed"""
        logger.debug("Interface.selectNewerMedia clicked")
        self.update_title()
        size = self.selected.get_nbytes()
        initsize = size
        maxsize = config.MediaSize * 1024 * 1024
        init = len(self.selected)
        for i in self.AllJpegs[self.iCurrentImg:]:
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
        self.iCurrentImg = self.AllJpegs.index(self.selected[-1])
        self.showImage()
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
        tmplist = self.AllJpegs[:self.iCurrentImg]
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
        self.iCurrentImg = self.AllJpegs.index(self.selected[0])
        self.showImage()
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

################################################################################
# # # # # # # fin de la classe interface graphique # # # # # #
################################################################################

#
#def MessageError(text, Message=gtk.MESSAGE_ERROR):
#    dialog = gtk.MessageDialog(None, 0, Message, gtk.BUTTONS_OK, text)
#    dialog.set_default_response(gtk.BUTTONS_OK)
#    dialog.run()
#    dialog.destroy()

#
#class MinimumRatingWindow(gtk.Window):
#    def __init__(self, upperIface):
#        gtk.Window.__init__(self)
#        self.set_title("Note minimale")
#        self.upperIface = upperIface
#        layout = gtk.VBox()
#        self.add(layout)
#        self.slider = gtk.HScale()
#        self.adj_Rate = gtk.Adjustment(0, 0, 5, 1)
#        self.slider.set_adjustment(self.adj_Rate)
#        self.slider.set_value(upperIface.min_mark)
#        self.slider.connect("value_changed", self.mark_changed)
#        layout.pack_start(self.slider, True, True, 0)
#        self.close = gtk.Button(stock=gtk.STOCK_CLOSE)
#        self.close.connect("clicked", self.kill_window)
#        layout.pack_start(self.close, True, True, 0)
#
#    def mark_changed(self, *args):
#        self.upperIface.min_mark = self.slider.value()
#
#    def kill_window(self, *args):
#        """
#        send the signal to close the window
#        """
#        self.upperIface.min_mark = 0
#        try:
#            self.destroy()
#        except:
#            pass


class RenameDay(object):
    """prompt a windows and asks for a name for the day"""
    def __init__(self, filename, AllPhotos, selected, callback=None):
        """
        @param filename: name of the currenty displayed image
        @param AllPhotos: list of all photos filenames
        @param selected: list of selected photos.
        """
        self.initialFilename = filename
        self.newFilename = self.initialFilename
        self.dayname = os.path.dirname(filename)
        self.callback = callback

        self.commentfile = os.path.join(config.DefaultRepository, self.dayname, config.CommentFile)
        self.comment = AttrFile(self.commentfile)
        if os.path.isfile(self.commentfile):
            try:
                self.comment.read()
            except:
                pass
        try:
            self.timetuple = time.strptime(self.dayname[:10], "%Y-%m-%d")
        except:
            print("something is wrong with this name : %s" % self.dayname)
            return
        self.comment["date"] = time.strftime("%A, %d %B %Y", self.timetuple).capitalize().decode(config.Coding)
        if self.comment.has_key("title"):
            self.name = self.comment["title"]
        elif len(self.dayname) > 10:
            self.name = self.dayname[11:].decode(config.Coding)
            self.comment["title"] = self.name.decode(config.Coding)
        else:
            self.name = u""
            self.comment["title"] = self.name.decode(config.Coding)
        self.comment["image"] = os.path.split(filename)[1].decode(config.Coding)
        if not self.comment.has_key("comment"):
            self.comment["comment"] = u""
        self.AllPhotos = AllPhotos
        self.selected = selected
        self.gui = buildUI("Renommer")
#        signals = {self.gui.Renommer_destroy': self.destroy,
#                   self.gui.cancel, 'clicked()', self.destroy,
#                   self.gui.ok, 'clicked()', self.continu}
        self.gui.connect_signals(signals)
        self.gui.date.setText(self.comment["date"].encode("UTF-8"))
        self.gui.Commentaire.setText(self.comment["title"].encode("UTF-8"))
        self.DescObj = self.gui.Description.get_buffer()
        comment = self.comment["comment"].encode("UTF-8").strip().replace("<BR>", "\n",)
        self.DescObj.setText(comment)

    def continu(self, *args):
        """just distroy the window and goes on ...."""

        self.newname = self.gui.Commentaire.getText().strip().decode("UTF-8")
        self.comment["title"] = self.newname
        if self.newname == "":
            self.newdayname = time.strftime("%Y-%m-%d", self.timetuple)
        else:
            self.newdayname = time.strftime("%Y-%m-%d", self.timetuple) + "-" + unicode2ascii(self.newname.encode("latin1")).replace(" ", "_",)
        self.newFilename = os.path.join(self.newdayname, os.path.basename(self.initialFilename))

        self.newcommentfile = os.path.join(config.DefaultRepository, self.newdayname, config.CommentFile)
        if not os.path.isdir(os.path.join(config.DefaultRepository, self.newdayname)):
            mkdir(os.path.join(config.DefaultRepository, self.newdayname))
        if self.DescObj.get_modified():
            self.comment["comment"] = self.DescObj.get_text(self.DescObj.get_start_iter(), self.DescObj.get_end_iter()).strip().decode("UTF-8").replace("\n", "<BR>")
        self.comment.write()


        if self.newname != self.name:
            idx = 0
            for photofile in self.AllPhotos:
                if os.path.dirname(photofile) == self.dayname:
                    newphotofile = os.path.join(self.newdayname, os.path.split(photofile)[-1])
                    if os.path.isfile(os.path.join(config.DefaultRepository, newphotofile)):
                        base = os.path.splitext(os.path.join(config.DefaultRepository, newphotofile))
                        count = 0
                        for i in os.listdir(os.path.join(config.DefaultRepository, self.newdayname)):
                            if i.find(base) == 0:count += 1
                        newphotofile = os.path.splitext(newphotofile) + "-%i.jpg" % count
                    print("%s -> %s" % (photofile, newphotofile))
                    myPhoto = Photo(photofile)
                    myPhoto.renameFile(newphotofile)
                    self.AllPhotos[idx] = newphotofile

#                    os.rename(os.path.join(config.DefaultRepository, photofile), os.path.join(config.DefaultRepository, newphotofile))
                    if photofile in self.selected:
                        self.selected[self.selected.index(photofile)] = newphotofile
                idx += 1
# move or remove the comment file if necessary
            if os.path.isfile(self.commentfile):  # and not  os.path.isfile(self.newcommentfile):
                os.rename(self.commentfile, self.newcommentfile)
#            elif os.path.isfile(self.commentfile) and os.path.isfile(self.newcommentfile):
#                 os.remove(self.commentfile)
            if len(os.listdir(os.path.join(config.DefaultRepository, self.dayname))) == 0:
                os.rmdir(os.path.join(config.DefaultRepository, self.dayname))
        self.gui.Renommer.close
        if self.callback is not None:
            self.callback(self)

    def destroy(self, *args):
        """destroy clicked by user -> quit the program"""
        try:
            self.gui.Renommer.close
        except:
            pass
        flush()


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


class AskMediaSize:
    """prompt a windows and asks for the size of the backup media"""
    def __init__(self):
        self.gui = buildUI("TailleCD")
#        signals = {self.gui.TailleCD_destroy': self.destroy,
#                   self.gui.cancel, 'clicked()', self.destroy,
#                   self.gui.ok, 'clicked()', self.continu}
#        self.gui.connect_signals(signals)
        self.gui.TailleMo.setText(str(config.MediaSize))

    def continu(self, *args):
        """just distroy the window and goes on ...."""
        txt = self.gui.TailleMo.text().strip().decode("UTF-8").encode(config.Coding)
        try:
            config.MediaSize = abs(float(txt))
        except:
            print("%s does not seem to be the size of a media" % txt)
        self.gui.TailleCD.close()

    def destroy(self, *args):
        """destroy clicked by user -> quit the program"""
        try:
            self.gui.TailleCD.close()
        except:
            pass
        flush()


class Synchronize:
    """
    Class for file synchronization between different repositories
    """
    def __init__(self, current, AllPhotos, selected):
        """

        """
        logger.debug("Synchronize.init(%i,%i,%i)" % (current, len(AllPhotos), len(selected)))
        logger.debug("Recorded Synchronize type: %s" % config.SynchronizeType)
        self.current = current
        self.AllPhotos = AllPhotos
        self.selected = selected
        self.initST = config.SynchronizeType
        self.gui = buildUI("Synchroniser")
#        signals = {self.gui.Synchroniser_destroy': self.destroy,
#                   self.gui.ok4, 'clicked()', self.synchronize,
#                   self.gui.apply4, 'clicked()', self.apply_conf
#                   }
#        self.gui.connect_signals(signals)
        self.gui.SyncCommand.setText(config.SynchronizeRep.decode(config.Coding).encode("UTF-8"))
        if config.SynchronizeType.lower() == "newer":
            self.gui.SyncOlder.set_active(0)
            self.gui.SyncAll.set_active(0)
            self.gui.SyncSelected.set_active(0)
            self.gui.SyncNewer.set_active(1)
        elif config.SynchronizeType.lower() == "older" :
            self.gui.SyncNewer.set_active(0)
            self.gui.SyncAll.set_active(0)
            self.gui.SyncSelected.set_active(0)
            self.gui.SyncOlder.set_active(1)
        elif config.SynchronizeType.lower() == "all":
            self.gui.SyncSelected.set_active(0)
            self.gui.SyncOlder.set_active(0)
            self.gui.SyncNewer.set_active(0)
            self.gui.SyncAll.set_active(1)
        elif config.SynchronizeType.lower() == "selected":
            self.gui.SyncOlder.set_active(0)
            self.gui.SyncAll.set_active(0)
            self.gui.SyncNewer.set_active(0)
            self.gui.SyncSelected.set_active(1)
        else:
            self.gui.SyncAll.set_active(0)
            self.gui.SyncOlder.set_active(0)
            self.gui.SyncNewer.set_active(0)
            self.gui.SyncSelected.set_active(1)
#        signals = {self.gui.SyncAll_toggled': self.SetSyncAll,
#                       self.gui.SyncNewer_toggled': self.SetSyncNewer,
#                       self.gui.SyncOlder_toggled': self.SetSyncOlder,
#                       self.gui.SyncSelected_toggled': self.SetSyncSelected}
#        self.gui.connect_signals(signals)
        flush()


    def SetSyncAll(self, *args):
        logger.debug("Synchronize.SetSyncAll activated")
        config.SynchronizeType = "All"


    def SetSyncOlder(self, *args):
        logger.debug("Synchronize.SetSyncOld activated")
        config.SynchronizeType = "Older"


    def SetSyncNewer(self, *args):
        logger.debug("Synchronize.SetSyncNew activated")
        config.SynchronizeType = "Newer"


    def SetSyncSelected(self, *args):
        logger.debug("Synchronize.SetSyncSel activated")
        config.SynchronizeType = "Selected"


    def read_conf_GUI(self):
        """read config from GUI"""
        logger.debug("Synchronize.Read activated")
        config.SynchronizeRep = self.gui.SyncCommand.text().strip().decode("UTF-8").encode(config.Coding)
        self.initST = config.SynchronizeType


    def apply_conf(self, *args):
        self.read_conf_GUI()
        self.destroy()


    def synchronize(self, *args):
        self.read_conf_GUI()
        logger.debug("Synchronize.synchronize with mode %s" % config.SynchronizeType)
        synchrofile = os.path.join(config.DefaultRepository, ".synchro")
        synchro = []
        if config.SynchronizeType.lower() == "selected":
            logger.debug("Synchronize.synchronize: exec selected")
            synchro = self.selected
        elif config.SynchronizeType.lower() == "newer":
            logger.debug("Synchronize.synchronize: exec newer")
            synchro = self.AllPhotos[self.current:]
        elif config.SynchronizeType.lower() == "older":
            logger.debug("Synchronize.synchronize: exec older")
            synchro = self.AllPhotos[:self.current + 1]
        else:
            logger.debug("Synchronize.synchronize: exec all")
            synchro = self.AllPhotos
        synchro.append(config.Selected_save)
        days = []
        for photo in synchro:
            day = os.path.split(photo)[0]
            if not day in days:
                days.append(day)
                if os.path.isfile(os.path.join(config.DefaultRepository, day, config.CommentFile)):synchro.append(os.path.join(day, config.CommentFile))
        f = open(synchrofile, "w")
        for i in synchro: f.write(i + "\n")
        f.close()
        # TODO: MVC
        os.system("rsync -v --files-from=%s %s/ %s" % (synchrofile, config.DefaultRepository, config.SynchronizeRep))
        self.destroy()


    def destroy(self, *args):
        """
        destroy clicked by user -> quit the program
        """
        config.SynchronizeType = self.initST
        try:
            self.gui.Synchroniser.close()
        except:
            pass
        flush()



class SelectDay:
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
        self.upperIface.showImage()
        self.gui.ChangeDir.close()

    def destroy(self, *args):
        """destroy clicked by user -> quit the program"""
        try:
            self.gui.ChangeDir.close()
        except:
            pass
        flush()
