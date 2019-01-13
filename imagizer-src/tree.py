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
"""
Buils a tree view on the list of files
"""

from __future__ import with_statement, division, print_function, absolute_import


__author__ = "Jérôme Kieffer"
__version__ = "2.0.0"
__contact__ = "imagizer@terre-adelie.org"
__date__ = "29/10/2016"
__license__ = "GPL"

MONTH = {"01": u"Janvier",
         "02": u"Février",
         "03": u"Mars",
         "04": u"Avril",
         "05": u"Mai",
         "06": u"Juin",
         "07": u"Juillet",
         "08": u"Août",
         "09": u"Septembre",
         "10": u"Octobre",
         "11": u"Novembre",
         "12": u"Décembre",
         }
from . import qt
import os
from .utils import timeit
from .photo import Photo
try:
    from ._tree import TreeItem
except:
    class TreeItem(object):
        """
        Node of a tree ...

        Contains:
        self.order: depth from root
        add name: reconstitute the full name
        add comment field for dirname and filenames
        add reorder command which will sort all sub-trees
        add size property which calculate the size of the subtree
        add a next/previous method
        """
        def __init__(self, label=None, parent=None):
            self.children = []
            self.parent = parent
            self.label = label
            if parent:
                parent.add_child(self)
                self.order = parent.order + 1
            else:
                self.order = 0
            self.extra = None

        def add_child(self, child):
            self.children.append(child)

        def has_child(self, label):
            return label in [i.label for i in self.children]

        def get(self, label):
            for i in self.children:
                if i.label == label:
                    return i

        def __repr__(self):
            if self.parent:
                return "TreeItem %s->%s with children: " % (self.parent.label, self.label) + ", ".join([i.label for i in self.children])
            else:
                return "TreeItem %s with children: " % (self.label) + ", ".join([i.label for i in self.children])

        def sort(self):
            for child in self.children:
                child.sort()
            self.children.sort(key=lambda x:x.label)

        @property
        def name(self):
            if not self.parent:
                return self.label or ""
            elif self.order == 1:
                return self.label or ""
            elif self.order == 4:
                return os.path.join(self.parent.name, self.label)
            else:
                return "%s-%s" % (self.parent.name, self.label)

        def next(self):
            if self.parent is None:
                raise IndexError("Next does not exist")
            idx = self.parent.children.index(self)
            if idx < len(self.parent.children) - 1:
                return self.parent.children[idx + 1]
            else:
                return self.parent.next().children[0]

        def previous(self):
            if self.parent is None:
                raise IndexError("Previous does not exist")
            idx = self.parent.children.index(self)
            if idx > 0:
                return self.parent.children[idx - 1]
            else:
                return self.parent.previous().children[-1]

        def first(self):
            if self.children:
                return self.children[0].first()
            else:
                return self

        def last(self):
            if self.children:
                return self.children[-1].last()
            else:
                return self

        @property
        def size(self):
            if self.children:
                return sum([child.size for child in self.children])
            else:
                return 1


@timeit
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
            child = element.get(item)
            if not child:
                child = TreeItem(item, element)
            element = child
    return root


class TreeModel(qt.QAbstractItemModel):
    def __init__(self, root_item, win):
        super(TreeModel, self).__init__(win)
        self._root_item = root_item
        self._win = win
        self._current_branch = None

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        pitem = parent.internalPointer()
        if not parent.isValid():
            pitem = self._root_item
        return len(pitem.children)

    def columnCount(self, parent):
        return 2

    def flags(self, midx):
#        if midx.column()==1:
        return qt.Qt.ItemIsEnabled

    def index(self, row, column, parent):
        pitem = parent.internalPointer()
        if not parent.isValid():
            pitem = self._root_item
        try:
            item = pitem.children[row]
        except IndexError:
            return qt.QModelIndex()
        return self.createIndex(row, column, item)

    def data(self, midx, role):
        """
        What to display depending on model_index and role
        """
        leaf = midx.internalPointer()
        if midx.column() == 0 and role == qt.Qt.DisplayRole:
            if leaf.order == 2:
                if leaf.extra is None:
                    leaf.extra = MONTH.get(leaf.label)
                return leaf.extra
            else:
                return leaf.label

        if midx.column() == 1 and role == qt.Qt.DisplayRole:
            if leaf.order == 4:
                if leaf.extra is None:
                    data = Photo(leaf.name).readExif()
                    leaf.extra = data["title"]
                return leaf.extra

    def headerData(self, section, orientation, role):
        if role == qt.Qt.DisplayRole and orientation == qt.Qt.Horizontal:
            return ["Image", "Titre"][section]

    def parent(self, midx):
        pitem = midx.internalPointer().parent
        if pitem is self._root_item:
            return qt.QModelIndex()
        row_idx = pitem.parent.children.index(pitem)
        return self.createIndex(row_idx, 0, pitem)


class TreeWidget(qt.QWidget):
    def __init__(self, root, parent=None):
        super(TreeWidget, self).__init__(parent)
        self.root = root
        self.view = qt.QTreeView()
        self.model = TreeModel(root, self)
        self.view.setModel(self.model)
        lay = qt.QVBoxLayout(self)
        lay.addWidget(self.view)
        self.view.setColumnWidth(0, 300)
        self.view.setAlternatingRowColors(True)
        self.view.doubleClicked.connect(self.goto)
        self.callback = None
        if parent is None:
            self.setWindowTitle("Navigation")
            self.setGeometry(0, 0, 500, 500)

    def goto(self, midx):
        """
        Return the name of the image clicked.
        """
        leaf = midx.internalPointer()
        if leaf.order == 4:
            value = leaf.name
        else:
            value = leaf.first().name
        print(value)
        if self.callback:
            self.callback(value)


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
    mainw.setCentralWidget(TreeWidget(tree, mainw))
    mainw.show()
    app.exec_()

if __name__ == "__main__":
    main()
