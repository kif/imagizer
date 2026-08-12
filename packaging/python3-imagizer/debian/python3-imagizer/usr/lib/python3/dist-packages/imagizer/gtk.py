from __future__ import with_statement, division, print_function, absolute_import

try:  # this is for gtk3 but we are not yet there ...
#     from gi.repository import Gtk as gtk
#     from gi.repository import GObject as gobject
#     from gi.repository import Gdk as gdk
#     from gi.repository import GdkPixbuf
#     gtkInterpolation = [GdkPixbuf.InterpType.NEAREST, GdkPixbuf.InterpType.TILES,
#                         GdkPixbuf.InterpType.BILINEAR, GdkPixbuf.InterpType.HYPER]
    import gtk  # IGNORE:E0601
    import gobject
    import gtk.gdk as gdk  # IGNORE:E0601
    gtkInterpolation = [gdk.INTERP_NEAREST, gdk.INTERP_TILES, gdk.INTERP_BILINEAR, gdk.INTERP_HYPER]
    GTKglade = None
except ImportError:
#     try:
        import pygtk ; pygtk.require('2.0')  # IGNORE:F0401
        import gtk  # IGNORE:E0601
#         print(gtk)
        gdk = gtk.gdk  # IGNORE:E0601
        import gtk.glade as GTKglade  # IGNORE:E0611
        gtkInterpolation = [gdk.INTERP_NEAREST, gdk.INTERP_TILES, gdk.INTERP_BILINEAR, gdk.INTERP_HYPER]

#     except ImportError:  # GTK3
#             raise ImportError("Selector needs Gtk and glade available from http://www.pygtk.org/")

# About interpolation (from documentation)
# NEAREST    Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
# TILES    This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
# BILINEAR    Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
# HYPER    This is the slowest and highest quality reconstruction function. It is derived from the hyperbolic filters in Wolberg's "Digital Image Warping", and is formally defined as the hyperbolic-filter sampling the ideal hyperbolic-filter interpolated image (the filter is designed to be idempotent for 1:1 pixel mapping).


def buildUI(windows_name="Principale"):
    """
    Create the glade object compatible with both GTK2 & GTK3 style
    @param: window name as define  in glade file
    @return: builder instance
    """
    if GTKglade:
        xml = GTKglade.XML(unifiedglade, root=windows_name)
        xml.connect_signals = xml.signal_autoconnect
        xml.get_object = xml.get_widget
    else:
        xml = gtk.Builder()
        xml.add_objects_from_file(unifiedglade, (windows_name,))
    return xml

def gtkFlush():
    """
    Flush all graphics stuff (outside main loop)
    """
    while gtk.events_pending():  # IGNORE:E1101
        gtk.main_iteration()  # IGNORE:E1101
