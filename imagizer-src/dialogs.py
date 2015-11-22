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
Dialog Graphical interfaces for selector.
"""
__author__ = "Jérôme Kieffer"
__version__ = "2.0.0"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "22/11/2015"
__license__ = "GPL"

import os
import logging
import time
import sys
import subprocess
logger = logging.getLogger("imagizer.dialogs")
from .config import config
from .qt import QtCore, QtGui, buildUI
from .parser import AttrFile
from .photo import Photo
from .encoding import unicode2ascii
from .fileutils import mkdir
PY3 = sys.version_info[0] > 2

if PY3:
    unicode = str
    to_unicode = str
else:
    def to_unicode(text):
        if isinstance(text, str):
            return text.decode(config.Coding)
        else:
            return unicode(text)

def message_box(parent=None, title="title", text="blabla"):
    """
    Simple dialog asking for leavind the program
    @param text: some text to display
    @param parent: parent window
    @return: True if accepted
    """
    QtGui.QMessageBox.about(parent, to_unicode(title), to_unicode(text))

def quit_dialog(parent=None):
    """
    Simple dialog asking for leavind the program

    @param parent: parent window
    @return: True if accepted
    """
    dialog = QtGui.QDialog(parent)
    lay = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom, dialog)
    lab = QtGui.QLabel("Voulez vous vraiment quitter ce programme ?", dialog)
    lay.addWidget(lab)
    buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, dialog)
    lay.addWidget(buttonBox)
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    result = dialog.exec_()
    return result == QtGui.QDialog.Accepted

def ask_media_size():
    """
    @return: the size of the media in MB
    """
    gui = buildUI("dialog_tailleCD")
    gui.TailleMo.setText(str(config.MediaSize))
    result = gui.exec_()
    if result == QtGui.QDialog.Accepted:
        txt = str(gui.TailleMo.text()).strip()
        try:
            config.MediaSize = abs(float(txt))
        except Exception as err:
            logger.warning("%s does not seem to be the size of a media: %s" % (txt, err))



def rename_day(filename, all_photos, selected):
    """prompt a windows and asks for a name for the day

    @param filename: name of the curenty displayed image
    @param all_photos: list of all photos filenames
    @param selected: list of selected photos.
    @return: renamed filename if objects were modified

    Note this modifies in place all_photos and selected
    """
    initial_fname = filename
    new_fname = initial_fname
    dayname, image  = os.path.split(filename)

    comment_fn = os.path.join(config.DefaultRepository, dayname, config.CommentFile)
    comment = AttrFile(comment_fn)
    if os.path.isfile(comment_fn):
        try:
            comment.read()
        except:
            pass
    try:
        timetuple = time.strptime(dayname[:10], "%Y-%m-%d")
    except:
        logger.warning("something is wrong with this name : %s" % dayname)
        return
    comment["date"] = to_unicode(time.strftime("%A, %d %B %Y", timetuple).capitalize())
    if "title" in comment:
        title = comment["title"]
    elif len(dayname) > 10:
        title = to_unicode(dayname[11:])
        comment["title"] = title
    else:
        title = to_unicode("")
        comment["title"] = title

    comment["image"] = to_unicode(image)

    if "comment" not in comment:
        comment["comment"] = to_unicode("")

    gui = buildUI("dialog_renommer")
    signals = {gui.buttonBox.accepted: gui.accept,
               gui.buttonBox.rejected: gui.reject}
    for signal, slot in signals.items():
        signal.connect(slot)
    gui.date.setText(comment["date"])
    gui.Commentaire.setText(comment["title"])
    gui.Description.setPlainText(comment["comment"].strip().replace("<BR>", "\n",))

    result = gui.exec_()
    if result == QtGui.QDialog.Accepted:
        newname = to_unicode(gui.Commentaire.text()).strip()
        comment["title"] = newname
        if newname == to_unicode(""):
            newdayname = time.strftime("%Y-%m-%d", timetuple)
        else:
            newdayname = time.strftime("%Y-%m-%d", timetuple) + "-" + unicode2ascii(newname).replace(" ", "_",)
        new_fname = os.path.join(newdayname, image)

        newcommentfile = os.path.join(config.DefaultRepository, newdayname, config.CommentFile)
        if not os.path.isdir(os.path.join(config.DefaultRepository, newdayname)):
            mkdir(os.path.join(config.DefaultRepository, newdayname))

        comment["comment"] = to_unicode(gui.Description.toPlainText()).strip().replace("\n", "<BR>")
        comment.write()

        if newname != title:
            for idx, photofile in enumerate(all_photos[:]):
                if os.path.dirname(photofile) == dayname:
                    newphotofile = os.path.join(newdayname, os.path.split(photofile)[-1])
                    if os.path.isfile(os.path.join(config.DefaultRepository, newphotofile)):
                        base = os.path.splitext(os.path.join(config.DefaultRepository, newphotofile))
                        count = 0
                        for i in os.listdir(os.path.join(config.DefaultRepository, newdayname)):
                            if i.find(base) == 0:count += 1
                        newphotofile = os.path.splitext(newphotofile) + "-%i.jpg" % count
                    print("%s -> %s" % (photofile, newphotofile))
                    myPhoto = Photo(photofile)
                    myPhoto.renameFile(newphotofile)
                    all_photos[idx] = newphotofile
                    if photofile in selected:
                        selected[selected.index(photofile)] = newphotofile
# move or remove the comment file if necessary
            if os.path.isfile(comment_fn):  # and not  os.path.isfile(self.newcommentfile):
                os.rename(comment_fn, newcommentfile)
            if len(os.listdir(os.path.join(config.DefaultRepository, dayname))) == 0:
                os.rmdir(os.path.join(config.DefaultRepository, dayname))
            return new_fname


def synchronize_dialog(current, AllPhotos, selected):
    """
    @param current: index of current image
    @param AllPhotos: list of all photos
    @param selected: list of selected photos
    """
    logger.debug("synchronize_dialog(%i,%i,%i)" % (current, len(AllPhotos), len(selected)))
    logger.debug("Recorded Synchronize type: %s" % config.SynchronizeType)
    gui = buildUI("dialog_synchro")
    PERFORM_SYNCRO = 3
    #Note that accept and reject are already coded into the GUI
    gui.synchoniser.clicked.connect(lambda: gui.done(PERFORM_SYNCRO))
    gui.SyncCommand.setText(config.SynchronizeRep)
    param = {"newer":gui.SyncNewer,
             "older":gui.SyncOlder,
             "all":  gui.SyncAll,
             "selected": gui.SyncSelected}
    what = config.SynchronizeType.lower()
    for key, widget in param.items():
        widget.setChecked(key == what)

    res = gui.exec_()
    logger.debug(res)
    if res in (QtGui.QDialog.Accepted, PERFORM_SYNCRO):
        config.SynchronizeRep = to_unicode(gui.SyncCommand.text()).strip()
        for key, widget in param.items():
            if widget.isChecked():
                config.SynchronizeType = key
    if res == PERFORM_SYNCRO:
        synchrofile = os.path.join(config.DefaultRepository, ".synchro")
        synchro = []
        if config.SynchronizeType == "selected":
            logger.debug("Synchronize.synchronize: exec selected")
            synchro = selected
        elif config.SynchronizeType == "newer":
            logger.debug("Synchronize.synchronize: exec newer")
            synchro = AllPhotos[current:]
        elif config.SynchronizeType.lower() == "older":
            logger.debug("Synchronize.synchronize: exec older")
            synchro = AllPhotos[:current + 1]
        else:
            logger.debug("Synchronize.synchronize: exec all")
            synchro = AllPhotos
        synchro.append(config.Selected_save)
        days = set([os.path.dirname(photo) for photo in synchro])
        for day in days:
            dest = os.path.join(config.DefaultRepository, day, config.CommentFile)
            if os.path.isfile(dest):
                synchro.append(os.path.join(day, config.CommentFile))

        with open(synchrofile, "w") as f:
            for fn in synchro:
                f.write(fn + "\n")
        # TODO: MVC
        if logger.getEffectiveLevel() <= logging.INFO:
            stdout = subprocess.PIPE
            stderr = subprocess.STDOUT
        else:
            stdout = stderr = None
        p = subprocess.Popen(["rsync", "-v", "--files-from=" + synchrofile, config.DefaultRepository + "/", config.SynchronizeRep ],
                             bufsize=4096, stdout=stdout, stderr=stderr)
#        os.system("rsync -v --files-from=%s %s/ %s" % (synchrofile, config.DefaultRepository, config.SynchronizeRep))
        if logger.getEffectiveLevel() <= logging.INFO:
            line = p.stdout.readline()
            while p.returncode is None or line:
                logger.info(line)
                line = p.stdout.readline()
        logger.info("Rsync finished with returncode %s"%(p.wait()))


def slideshow_dialog():
    """pop up a windows and asks for the setup of the slide show
    @return True if the slideshow should start immediately
    """
    START_DIAPO = 3
    gui = buildUI("dialog_diaporama")
    gui.startdiapo.clicked.connect(lambda: gui.done(START_DIAPO))
    MODES = {"chronological":gui.radiochrono,
             "antichronological":gui.radioantichrono,
             "random":gui.radiorandom}
    if config.SlideShowType not in MODES:
        config.SlideShowType = MODES.keys()[0]
    for key, widget in MODES.items():
        widget.setChecked(key == config.SlideShowType)

    gui.delai.setValue(float(config.SlideShowDelay))
    gui.rating.setValue(float(config.SlideShowMinRating))

    res = gui.exec_()
    logger.debug(res)

    if res in (QtGui.QDialog.Accepted, START_DIAPO):
        config.SlideShowDelay = gui.delai.value()
        config.SlideShowMinRating = gui.rating.value()
        for key, widget in MODES.items():
            if widget.isChecked():
                config.SlideShowType = key
    return res == START_DIAPO


def test():
    import imagizer.imagizer, imagizer.dialogs
    all = imagizer.imagizer.rangeTout("/tmp", fast=True)[0]
    selected = all[:5]
    imagizer.dialogs.rename_day('2012-02-23/07h58m53-_WB510__VLUU_WB500__SAMSUNG_HZ10W-AutoWB.jpg', all, selected)

