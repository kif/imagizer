import logging
logger = logging.getLogger(__name__)
import cython
import os

cdef class TreeItem(object):
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
    cdef public list children
    cdef public TreeItem parent
    cdef public str label
    cdef public int order
    cdef public object extra

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

    cpdef add_child(self, TreeItem child):
        self.children.append(child)

    cpdef bint has_child(self,str label):
        return label in [i.label for i in self.children]

    cpdef TreeItem get(self, str label):
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

    cpdef TreeItem next(self):
        cdef int idx
        if self.parent is None:
            raise IndexError("Next does not exist")
        idx = self.parent.children.index(self)
        if idx < len(self.parent.children) - 1:
            return self.parent.children[idx + 1]
        else:
            return self.parent.next().children[0]

    cpdef TreeItem previous(self):
        cdef int idx
        if self.parent is None:
            raise IndexError("Previous does not exist")
        idx = self.parent.children.index(self)
        if idx > 0:
            return self.parent.children[idx - 1]
        else:
            return self.parent.previous().children[-1]

    cpdef TreeItem first(self):
        if self.children:
            return self.children[0].first()
        else:
            return self

    cpdef TreeItem last(self):
        if self.children:
            return self.children[-1].last()
        else:
            return self

    property size:
        def __get__(self):
            cdef int s = 0
            cdef TreeItem child
            if self.children:
                for child in self.children:
                    s += child.size
                return s
            else:
                return 1

    property name:
        def __get__(self):
            if self.order <= 1:
                return self.label or ""
            elif self.order == 4:
                return self.parent.name + os.sep + self.label
            else:
                return self.parent.name + "-" + self.label

    def add_leaf(self, name):
        "Add a new leaf to the tree, only available from root"
        if self.parent is None:
            day, hour = os.path.split(name)
            ymd = day.split("-", 2)
            ymd.append(hour)
            element = self
            for item in ymd:
                child = element.get(item)
                if child is None:
                    child = TreeItem(item, element)
                element = child
        else:
            logger.error("add_leaf is only possible from the root of the tree")

    def del_leaf(self, name):
        "Remove a leaf from the tree, only available from root"
        if self.parent is None:
            day, hour = os.path.split(name)
            ymd = day.split("-", 2)
            ymd.append(hour)
            element = self
            for item in ymd:
                child = element.get(item)
                if child is None:
                    logger.error("Node %s from %s does not exist, cannot remove", item, name)
                element = child
            # Now start deleting:
            while element.parent is not None:
                element.parent.children.remove(element)
                if not element.parent.children:
                    element = element.parent
                else:
                    return
        else:
            logger.error("add_leaf is only possible from the root of the tree")