#!/usr/bin/python


import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GObject
GObject.threads_init()
Gst.init(None)

from player import Player

ONE_BILLION = 1000000000

class Main(Gtk.Window):
    def __init__(self):

        super(Main, self).__init__()

        #paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        self.speaker_out = Prod()
        print "things"
        self.add(self.speaker_out)
        print "stuff"

        #self.panes = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)

        # add the first image to the left pane
        #paned.add1(image1)
        # add the second image to the right pane
        #paned.add2(speaker_out)

        # add the panes to the window
        #self.add(paned)


class Prod(Gtk.Box):
    def __init__(self):

        super(Prod, self).__init__(orientation=Gtk.Orientation.VERTICAL)

        self.player = Player(device=0)

        self.controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # play/pause toggle
        #self.btn_play_pause = Gtk.ToggleButton(label="P/P")
        #self.btn_play_pause.connect("toggled", self.play_pause_toggle, "2")
        #self.controls.pack_start(self.btn_play_pause, False, False, 2)

        # play button
        self.btn_play = Gtk.Button(label="Play")
        self.controls.pack_start(self.btn_play, False, False, 2)

        # pause button
        self.btn_pause = Gtk.Button(label="Pause")
        self.controls.pack_start(self.btn_pause, False, False, 2)

        # stop button
        self.btn_stop = Gtk.Button(label="Stop")
        self.controls.pack_start(self.btn_stop, False, False, 2)

        # the time display
        self.time = Gtk.Label("0:00 | 0:00 | 0:00")
        self.controls.pack_start(self.time, True, True, 5)

        # output lock toggle
        self.btn_lock = Gtk.ToggleButton(label="Lock")
        self.btn_lock.connect("toggled", self.lock_toggle, "2")
        self.controls.pack_end(self.btn_lock, False, False, 2)

        #self.controls.set_homogeneous(True)
        self.pack_start(self.controls, False, False, 2)



        self.info = Gtk.Label("Herp Derp")
        self.info.set_alignment(0, 0)
        self.pack_start(self.info, False, False, 5)

        self.slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.slider.set_draw_value(False)
        self.slider.set_range(0, 100)
        #self.slider.set_increments(1, 10)
        self.pack_start(self.slider, False, True, 5)

        def play_song(x):
            self.player.load_media_file("/home/david/usr/dropbox/Coding/walnut/1.mp3")
            self.play()

        self.btn_play_song = Gtk.Button(label="Play Song")
        self.btn_play_song.connect("clicked", play_song)
        self.pack_start(self.btn_play_song, False, False, 2)

        self.playlist = Playlist()
        #self.playlist = Gtk.Label(label="Playlist Placeholder")
        self.pack_start(self.playlist, True, True, 0)

        self.locked = False
        self.c = [1, 2, 3, 4]
        self.unlock_buttons()

    def unlock_buttons(self):

        if self.c:
            c = self.c
            self.btn_play.disconnect(c[0])
            self.btn_pause.disconnect(c[1])
            self.btn_stop.disconnect(c[2])
            self.slider.disconnect(c[3])
        else:
            c = []

        c[0] = self.btn_play.connect("clicked", lambda x: self.play())
        c[1] = self.btn_pause.connect("clicked", lambda x: self.player.pause())
        c[2] = self.btn_stop.connect("clicked", lambda x: self.stop())
        c[3] = self.slider.connect("change-value", self.slider_set_position)
        self.c = c

    def lock_buttons(self):

        if self.c:
            c = self.c
            self.btn_play.disconnect(c[0])
            self.btn_pause.disconnect(c[1])
            self.btn_stop.disconnect(c[2])
            self.slider.disconnect(c[3])
        else:
            c = []

        c[0] = self.btn_play.connect("clicked", lambda x: self.lock_deny())
        c[1] = self.btn_pause.connect("clicked", lambda x: self.lock_deny())
        c[2] = self.btn_stop.connect("clicked", lambda x: self.lock_deny())
        c[3] = self.slider.connect("change-value", lambda a,b,c: self.lock_deny())
        self.c = c

    def lock_deny(self):

        pass

    def update_position(self):

        if self.player.playing == False:
           return False # cancel timeout

        position_ns, duration_ns = self.player.get_position()
        position_s = int(position_ns) / ONE_BILLION
        duration_s = int(duration_ns) / ONE_BILLION
        remaining_s = duration_s - position_s


        #block seek handler so we don't seek when we set_value()
        #self.slider.handler_block_by_func(self.slider_set_position)

        self.slider.set_range(0, duration_ns)
        self.slider.set_value(position_ns)

        self.time.set_text(" | ".join([
            "{}:{:02}".format(position_s/60, position_s%60),
            "{}:{:02}".format(duration_s/60, duration_s%60),
            "{}:{:02}".format(remaining_s/60, remaining_s%60)
        ]))

        #self.slider.handler_unblock_by_func(self.slider_set_position)

        return True

    def slider_set_position(self, a, b, value):
        self.slider.set_value(value)
        self.player.seek(value)
        #self.update_position()

    def play(self):
        GObject.timeout_add(500, self.update_position)
        self.player.playing = True
        self.player.play()

    def stop(self):
        self.slider.set_value(0)
        self.time.set_text("0:00 | 0:00 | 0:00")
        self.player.playing = False
        self.player.stop()

    def lock_toggle(self, button, name):
        if button.get_active() == True:
            self.lock_buttons()
            self.locked = True
        else:
            self.unlock_buttons()
            self.locked = False

class Playlist(Gtk.TreeView):
    def __init__(self):

        self.store = Gtk.ListStore(str, str, str, str)
        super(Playlist, self).__init__(self.store)

        ui = {}

        selection = self.get_selection()
        #selection.set_mode(Gtk.SELECTION_SINGLE)
        selection.connect("changed", self._on_selection_changed, ui)
        selection.connect("row-activated", self.)

        self.columns = ['Title', 'Artist']

        dummy_store_data = [ {
            'artist': "edIT", 'title': "Certified Air Raid Material",
            'length': "366", 'path': "/home/david/walnut/1.mp3"
        },{
            'artist': "ABBA", 'title': "Waterloo",
            'length': "162", 'path': "/home/david/walnut/2.mp3"
        } ]


        for entry in dummy_store_data:
            self.store.append([entry['artist'], entry['title'], entry['length'], entry['path']])

        renderer = Gtk.CellRendererText()

        column = Gtk.TreeViewColumn("Artist", renderer, text=0)
        self.append_column(column)
        column = Gtk.TreeViewColumn("Title", renderer, text=1)
        self.append_column(column)
        column = Gtk.TreeViewColumn("Length", renderer, text=2)
        self.append_column(column)

    def _on_selection_changed(self,selection, data=None):
        treeview = selection.get_tree_view()
        (model, iter) = selection.get_selected()
        #data['button_top'].set_sensitive(iter is not None)
        #data['button_up'].set_sensitive(iter is not None)
        #data['button_down'].set_sensitive(iter is not None)
        #data['button_last'].set_sensitive(iter is not None)
        #data['button_edit'].set_sensitive(iter is not None)
        #
          2data['button_delete'].set_sensitive(iter is not None)


if __name__ == "__main__":
    win = Main()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
