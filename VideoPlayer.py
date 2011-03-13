#original author: Loupmagic
import pygtk
pygtk.require('2.0')
import gtk
import os

twindow = gtk.EXPAND | gtk.FILL | gtk.SHRINK

PATH_mkfifo = '/tmp/mplayer'

class Pymplayer(gtk.Socket):
    """Classe d'interface entre mplayer et le programme"""
    def __init__(self, id):
        gtk.Socket.__init__(self)
        self.tube = PATH_mkfifo + str(id)
        try:
            #Supprimer le fichier tube si présent.
            os.unlink(self.tube)
        except:
            pass
        #On crée le tube, son nom est mplayer+id
        os.mkfifo(self.tube)
        os.chmod(self.tube, 0666)

    #On écrit dans le tube la commande en mode slave
    def execmplayer(self, cmd):
        open(self.tube, 'w').write(cmd + "\n")

    #On lance mplayer en lui précisant l'id de la widget à utiliser(cf mplayer doc pour le reste)
    def setwid(self, wid):
        os.system("mplayer -nojoystick -nolirc -slave -vo x11 -wid %s -vf scale=400:200 -idle -input file=%s &" % (wid, self.tube))

    def loadfile(self, filename):
        self.execmplayer("loadfile %s" % (filename))
        self.execmplayer("change_rectangle w=100:h=100")

    def pause(self, parent):
        self.execmplayer("pause")

    def forward(self, parent):
        self.execmplayer("seek +10 0")

    def backward(self, parent):
        self.execmplayer("seek -10 0")

    def quit(self):
        self.execmplayer("quit")



class Panel(gtk.Table):
    """ Elle definie le player, càd l'écran, et ses widgets(play, forward, backward...)"""

    def __init__(self, id):
        gtk.Table.__init__(self, 4, 2)
        #self.resize(4, 2)
        self.set_col_spacings(10)
        self.set_row_spacings(10)

        self.Ecran = Pymplayer(id)
        self.Ecran.set_size_request(100, 200)
        self.attach(self.Ecran, 0, 4, 0, 1, twindow, twindow, 5, 5)

        #Bouton Open file
        Bopenfile = gtk.Button(stock="gtk-open")
        Bopenfile.connect("clicked", self.openfile)
        self.attach(Bopenfile, 0, 1, 1, 2, twindow, twindow, 5, 5)

        #Bouton previous         
        Brewind = gtk.Button(stock="gtk-media-rewind")
        Brewind.connect("clicked", self.Ecran.backward)
        self.attach(Brewind, 1, 2, 1, 2, twindow, twindow, 5, 5)

        #Bouton play
        Bplay = gtk.Button(stock="gtk-media-play")
        Bplay.connect("clicked", self.Ecran.pause)
        self.attach(Bplay, 2, 3, 1, 2, twindow, twindow, 5, 5)

        #Bouton next         
        Bforward = gtk.Button(stock="gtk-media-forward")
        Bforward.connect("clicked", self.Ecran.forward)
        self.attach(Bforward, 3, 4, 1, 2, twindow, twindow, 5, 5)


    #Boite de dialogue qui permet à l'utilisateur de choisir un fichire
    def openfile(self, parent):
        dialog = gtk.FileChooserDialog("Select file", gtk.Window(), gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.connect("destroy", lambda w:dialog.destroy())
        dialog.set_default_response(gtk.RESPONSE_OK)

        statut = dialog.run()
        if statut == gtk.RESPONSE_OK:
            #Ok nous avons le fichier, ouvrons le avec mplayer!
                    self.Ecran.loadfile(dialog.get_filename())
        dialog.destroy()


class guiPymplayer:
    """ Classe maitre, qui inclut toutes les autres classes"""

    def __init__(self):
        self.gui = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.gui.set_title("Using plug and socket : mplayer in python, by loupmagic")
        self.gui.set_default_size(550, 400)
        self.gui.set_position(gtk.WIN_POS_CENTER)

        self.global_panel()

        self.gui.connect("destroy", self.do_quit)
        self.gui.show_all()

        #Envoie des id seulement après l'affichage des widgets à l'aide de show_all()
        self.Panel1.Ecran.setwid(long(self.Panel1.Ecran.get_id()))
        self.Panel2.Ecran.setwid(long(self.Panel2.Ecran.get_id()))
        self.Panel3.Ecran.setwid(long(self.Panel3.Ecran.get_id()))
        self.Panel4.Ecran.setwid(long(self.Panel4.Ecran.get_id()))


    def global_panel(self):
        #Table d'organisation des widgets
        table = gtk.Table(3, 3, False)

        self.Panel1 = Panel(1)
        table.attach(self.Panel1, 0, 1, 0, 1, twindow, twindow, 5, 5)

        self.Panel2 = Panel(2)
        table.attach(self.Panel2, 2, 3, 0, 1, twindow, twindow, 5, 5)

        self.Panel3 = Panel(3)
        table.attach(self.Panel3, 0, 1, 2, 3, twindow, twindow, 5, 5)

        self.Panel4 = Panel(4)
        table.attach(self.Panel4, 2, 3, 2, 3, twindow, twindow, 5, 5)

        ligneH = gtk.HSeparator()
        table.attach(ligneH, 0, 3, 1, 2)
        ligneV = gtk.VSeparator()
        table.attach(ligneV, 1, 2, 0, 3)

        self.gui.add(table)

    def do_quit(self, widget):
        if __name__ == '__main__':
            #Fermer les processus mplayer!
            self.Panel1.Ecran.quit()
            self.Panel2.Ecran.quit()
            self.Panel3.Ecran.quit()
            self.Panel4.Ecran.quit()
            gtk.main_quit()

    def loop(self):
        gtk.main()

multivideos = guiPymplayer()
multivideos.loop()


