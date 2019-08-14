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

    def __init__(self, str label=None, TreeItem parent=None, object extra=None):
        self.children = []
        self.parent = parent
        self.label = label
        if parent:
            parent.add_child(self)
            self.order = parent.order + 1
        else:
            self.order = 0
        self.extra = extra

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
        cdef:
            int idx
        if self.parent is None:
            raise IndexError("Next does not exist")
        idx = self.parent.children.index(self)
        if idx < len(self.parent.children) - 1:
            return self.parent.children[idx + 1]
        else:
            return self.parent.next().children[0]

    cpdef TreeItem previous(self):
        cdef:
            int idx
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

    cdef int _size(self):
        "Cython way of calculating size"
        cdef:
            int s = 0
            TreeItem child
        if self.children:
            for child in self.children:
                s += child._size()
            return s
        else:
            return 1

    property size:
        def __get__(self):
            return self._size()

    property name:
        def __get__(self):
            if self.order <= 1:
                return self.label or ""
            elif self.order == 4:
                return self.parent.name + os.sep + self.label
            else:
                return self.parent.name + "-" + self.label

    cpdef int sub_index(self):
        cdef:
            int s, in_list
            TreeItem brother

        if self.parent is None:
            return 0
        else:
            in_list = self.parent.children.index(self)
            s = 0
            for brother in self.parent.children[:in_list]:
                s+=brother._size()
            return s

    cpdef TreeItem _getitem(self, int idx):
        "List emulation mode, retrieve index, return self when no children"
        cdef:
            int size, sum_,
            TreeItem child, element
        if self.children:
            sum_ = 0
            for child in self.children:
                child_size = child._size()
                if sum_ + child_size <= idx:
                    sum_ += child_size
                else:
                    return child._getitem(idx - sum_)
        else:
            return self


cdef class TreeRoot(TreeItem):
    "TreeRoot has some additional methods"
    cpdef TreeItem find_leaf(self, str name):
        "Find an element in the tree, return None if not present"
        cdef TreeItem element, child
        day, hour = os.path.split(name)
        ymd = day.split("-", 2)
        ymd.append(hour)
        element = self
        for item in ymd:
            child = element.get(item)
            if child is None:
                logger.error("Node %s from %s does not exist, cannot remove", item, name)
            element = child
        return element

    cpdef add_leaf(self, str name, object extra=None):
        "Add a new leaf to the tree, only available from root"
        day, hour = os.path.split(name)
        ymd = day.split("-", 2)
        ymd.append(hour)
        element = self
        for level, item in enumerate(ymd):
            child = element.get(item)
            if child is None:
                if level == 3:
                    child = TreeItem(item, element, extra)
                else:
                    child = TreeItem(item, element)
            element = child

    cpdef del_leaf(self, str name):
        "Remove a leaf from the tree, only available from root"
        cdef:
            TreeItem element, child
        element = self.find_leaf(name)
        if element:
            # Now start deleting:
            while element.parent is not None:
                element.parent.children.remove(element)
                if not element.parent.children:
                    element = element.parent
                else:
                    return

    cpdef int index(self, str name):
        "Calculate the index of an item as if it was a list"
        cdef:
            int idx=0
            TreeItem element
        element = self.find_leaf(name)
        if element is None:
            return -1
        while element:
            idx += element.sub_index()
            element = element.parent
        return idx

    def  __getitem__(self, idx):
        "x.__getitem__(y) <==> x[y]"
        cdef:
            int size
        size = self._size()
        if idx<0:
            idx = size + idx
        if idx>=size:
            raise IndexError("list index out of range")
        return self._getitem(idx).name

