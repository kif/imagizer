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
Buils a tree view on the list of files
"""

__author__ = "Jérôme Kieffer"
__version__ = "2.0.0"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "20141210"
__license__ = "GPL"


from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc
import os

class TreeItem(object):
    def __init__(self, label=None, parent=None):
        self.children = []
        self.parent = parent
        self.label = label
        if parent:
            parent.add_child(self)

    def add_child(self, child):
        self.children.append(child)

    def has_child(self, label):
        return label in [i.label for i in self.children]

    def get_child(self, label):
        for i in self.children:
            if i.label == label:
                return i

    def __repr__(self):
        if self.parent:
            return "TreeItem %s->%s with children: " % (self.parent.label, self.label) + ", ".join([i.label for i in self.children])
        else:
            return "TreeItem %s with children: " % (self.label) + ", ".join([i.label for i in self.children])

def build_tree(big_list):
    """
    """
    root = TreeItem()
    for line in big_list:
        day, hour = os.path.split(line)
        ymd = day.split("-", 2)
        ymd.append(hour)
        element = root
        for item in ymd:
            child = element.get_child(item)
            if not child:
                child = TreeItem(item, element)
            element = child
    return root

class TreeModel(qtc.QAbstractItemModel):
    def __init__(self, root_item, win):
        super(TreeModel, self).__init__(win)
        self._root_item=root_item
        self._win = win
        self._current_branch=None

    def rowCount(self, parent):
        if parent.column()>0:
            return 0
        pitem = parent.internalPointer()
        if not parent.isValid():
            pitem = self._root_item
        return len(pitem.children)

    def columnCount(self, parent):
        return 2

    def flags(self, midx):
#        if midx.column()==1:
        return qtc.Qt.ItemIsEnabled

    def index(self, row, column, parent):
        pitem = parent.internalPointer()
        if not parent.isValid():
            pitem = self._root_item
        try:
            item = pitem.children[row]
        except IndexError:
            return qtc.QModelIndex()
        return self.createIndex(row,column,item)
    def data(self, midx, role):
        if midx.column()==0 and role == qtc.Qt.DisplayRole:
            return midx.internalPointer().label

    def parent(self, midx):
        pitem = midx.internalPointer().parent
        if pitem is self._root_item:
            return qtc.QModelIndex()
        row_idx = pitem.parent.children.index(pitem)
        return self.createIndex(row_idx, 0, pitem)

class TreeWidget(qt.QWidget):
    def __init__(self, root, parent=None):
        super(TreeWidget, self).__init__(parent)
        self.root=root
        print(root)
        self.view = qt.QTreeView()
#        self.view.header().hide()
        self.model = TreeModel(root, self)
        self.view.setModel(self.model)
        lay = qt.QVBoxLayout(self)
        lay.addWidget(self.view)


class ColumnWidget(qt.QWidget):
    def __init__(self, root, parent=None):
        super(ColumnWidget, self).__init__(parent)
        self.root = root
        print(root)
        self.view = qt.QColumnView(self)
#        self.view.header().hide()
        self.model = TreeModel(root, self)
        self.view.setModel(self.model)
        lay = qt.QVBoxLayout(self)
        lay.addWidget(self.view)

class TreeColWidget(qt.QWidget):
    def __init__(self, root, parent=None):
        super(TreeColWidget, self).__init__(parent)
        self.root = root
        print(root)
        self.view1 = qt.QTreeView()
        self.model = TreeModel(root, self)
        self.view1.setModel(self.model)
        lay = qt.QVBoxLayout(self)
        lay.addWidget(self.view1)

        self.view2 = qt.QColumnView(self)
        self.view2.setModel(self.model)
        lay.addWidget(self.view2)



def main():
    import imagizer.imagizer
    big_lst = imagizer.imagizer.rangeTout("/home/photo", bUseX=False, fast=True)[0]
    tree = build_tree(big_lst)
    app = qt.QApplication([])
    mainw = qt.QMainWindow()
    mainw.setCentralWidget(TreeColWidget(tree, mainw))
    mainw.show()
    app.exec_()

if __name__ == "__main__":
    main()
