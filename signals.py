""" Provide Signal class.

A signals implementation.

Example usage
=============

>>> class Button:
...     def __init__(self):
...         # Creating a signal as a member of a class
...         self.sigClick = Signal()

>>> class Listener:
...     # a sample method that will be connected to the signal
...     def onClick(self):
...         print "onClick ", repr(self)

>>> # a sample function to connect to the signal
>>> def listenFunction():
...     print "listenFunction"

>>> # a function that accepts arguments
>>> def listenWithArgs(text):
...     print "listenWithArgs: ", text

>>> b = Button()
>>> l = Listener()

>>> b.sigClick.connect(l.onClick)
>>> b.sigClick()
onClick  <__main__.Listener instance at 0x4024cf2c>

>>> # Disconnecting all signals
>>> b.sigClick.disconnectAll()
>>> b.sigClick()

>>> # connecting multiple functions to a signal
>>> l2 = Listener()
>>> b.sigClick.connect(l.onClick)
>>> b.sigClick.connect(l2.onClick)
>>> b.sigClick()
onClick  <__main__.Listener instance at 0x4024cf2c>
onClick  <__main__.Listener instance at 0x4024ce0c>

>>> # disconnecting individual functions
>>> b.sigClick.disconnect(l.onClick)
>>> b.sigClick.connect(listenFunction)
>>> b.sigClick()
onClick  <__main__.Listener instance at 0x4024ce0c>
listenFunction

>>> # signals disconnecting automatically
>>> b.sigClick.disconnectAll()
>>> b.sigClick.connect(l.onClick)
>>> b.sigClick.connect(l2.onClick)
>>> del l2    
>>> b.sigClick()
onClick  <__main__.Listener instance at 0x4024cf2c>

>>> # example with arguments and a local signal
>>> sig = Signal()
>>> sig.connect(listenWithArgs)
>>> sig("Hello, World!")
listenWithArgs:  Hello, World!


Based on a Patrick Chasco's code.

@author: Benjamin Longuet
@author: Frederic Mantegazza
@author: Cyrille Boullier
@copyright: 2003-2005
@organization: CEA-Grenoble
@license: GPL
"""

__revision__ = "$Id$"

import weakref
import inspect


class Signal(object):
    """ class Signal.

    A simple implementation of the Signal/Slot pattern. To use, simply 
    create a Signal instance. The instance may be a member of a class, 
    a global, or a local; it makes no difference what scope it resides 
    within. Connect slots to the signal using the "connect()" method. 
    The slot may be a member of a class or a simple function. If the 
    slot is a member of a class, Signal will automatically detect when
    the method's class instance has been deleted and remove it from 
    its list of connected slots.
    """
    def __init__(self):
        """ Init the Signal object.
        """
        self.__slots = []

        # for keeping references to _WeakMethod_FuncHost objects.
        # If we didn't, then the weak references would die for
        # non-method slots that we've created.
        self.__funchost = []

    def __call__(self, *args, **kwargs):
        """
        """
        for i in xrange(len(self.__slots)):
            slot = self.__slots[i]
            if slot != None:
                slot(*args, **kwargs)
            else:
                del self.__slots[i]

    def emit(self, *args, **kwargs):
        """
        """
        self.__call__(*args, **kwargs)

    def connect(self, slot): # , keepRef=False):
        """
        """
        self.disconnect(slot)
        if inspect.ismethod(slot):
            #if keepRef:
                #self.__slots.append(slot)
            #else:
            self.__slots.append(WeakMethod(slot))
        else:
            o = _WeakMethod_FuncHost(slot)
            self.__slots.append(WeakMethod(o.func))

            # we stick a copy in here just to keep the instance alive
            self.__funchost.append(o)

    def disconnect(self, slot):
        """
        """
        try:
            for i in xrange(len(self.__slots)):
                wm = self.__slots[i]
                if inspect.ismethod(slot):
                    if wm.f == slot.im_func and wm.c() == slot.im_self:
                        del self.__slots[i]
                        return
                else:
                    if wm.c().hostedFunction == slot:
                        del self.__slots[i]
                        return
        except:
            pass

    def disconnectAll(self):
        """
        """
        del self.__slots
        del self.__funchost
        del self.__methodhost
        self.__slots = []
        self.__funchost = []
        self.__methodhost = []


class _WeakMethod_FuncHost:
    """
    """
    def __init__(self, func):
        self.hostedFunction = func

    def func(self, *args, **kwargs):
        self.hostedFunction(*args, **kwargs)


class WeakMethod:
    """ This class was generously donated by a poster on ASPN

    see aspn.activestate.com
    """
    def __init__(self, f):
        self.f = f.im_func
        self.c = weakref.ref(f.im_self)

    def __call__(self, *args, **kwargs):
        if self.c() == None:
            return
        self.f(self.c(), *args, **kwargs)

