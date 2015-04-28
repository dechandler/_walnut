#!/usr/bin/python


import time
import gi
import logging
import sqlite3
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GObject
GObject.threads_init()
Gst.init(None)

from player import Player

ONE_BILLION = 1000000000

null_log = logging.getLogger("null")

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

        self.btn_play_song = Gtk.Button(label="Play Song")
        self.btn_play_song.connect("clicked", self.play_song)
        self.pack_start(self.btn_play_song, False, False, 2)

        self.playlist = Playlist("main", "/home/david/walnut/gb.db")
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

    def play_song(x):
        self.player.load_media_file("/home/david/usr/dropbox/Coding/walnut/1.mp3")
        self.play()

class Playlist(Gtk.TreeView):

    def __init__(self, name, db_file, conf={}, db_log=null_log, log=null_log):

        self.conf = {
            'sort_key': "index",
            'sort_order': "desc",
            'hidden': False,
            'headers': ['artist', 'title', 'duration']
        }
        self.conf.update(conf)

        self.columns = ['playlist_index', 'file_path', 'artist', 'title',
                        'genre', 'duration', 'bpm', 'comments', 'rating',
                        'year']
        self.initialize_db(name, db_file)

        self.store = Gtk.ListStore(*[str for c in self.columns])
        super(Playlist, self).__init__(self.store)

        selection = self.get_selection()
        #selection.set_mode(Gtk.SELECTION_SINGLE)
        #ui = {}
        #selection.connect("changed", self._on_selection_changed, ui)
        #selection.connect("row-activated", self.)

        self.load_playlist()

        if not self.conf['hidden']:
            self.render()

    def initialize_db(self, name, db_file):
        self.conn = sqlite3.connect(db_file)
        self.c = self.conn.cursor()
        self.db_table = "playlist__{}".format(name)
        db_columns = ", ".join(["{} text".format(c) for c in self.columns])

        # Need to escape db_table
        sql = '''CREATE TABLE IF NOT EXISTS {} ({})'''.format(
                                                    self.db_table, db_columns)
        print(sql)
        #self.c.execute(sql, (self.db_table,))
        self.c.execute(sql)
        self.conn.commit()


    def load_playlist(self):

        self.store.clear()
        sql = '''SELECT * FROM {}'''.format(self.db_table)
        for i in self.c.execute(sql):
            print(i)
            self.store.append(i)

    def render(self):

        for header in self.conf['headers']:
            renderer = Gtk.CellRendererText()  # may need to be in loop
            index = self.columns.index(header)
            print(header, index)
            column = Gtk.TreeViewColumn(header.title(), renderer, text=index)
            column.set_sort_column_id(index)
            self.append_column(column)

    def playlist_view(self):
        pass
        """
        cur.execute('''SELECT * FROM playlist''')
        itemlist = cur.fetchall()
        store = gtk.ListStore(*coltypes)
        for act in itemlist:
            store.append(act)

        Now create columns for the TreeView (let's say it's called 'tree'):

        for index, item in enumerate(colnames):
            rendererText = gtk.CellRendererText()
            column = gtk.TreeViewColumn(item, rendererText, text=index)
            column.set_sort_column_id(index)
            tree.append_column(column)
        """


    def _on_selection_changed(self, selection, data=None):
        treeview = selection.get_tree_view()
        (model, iter) = selection.get_selected()
        #data['button_top'].set_sensitive(iter is not None)
        #data['button_up'].set_sensitive(iter is not None)
        #data['button_down'].set_sensitive(iter is not None)
        #data['button_last'].set_sensitive(iter is not None)
        #data['button_edit'].set_sensitive(iter is not None)
        #
        #data['button_delete'].set_sensitive(iter is not None)


if __name__ == "__main__":
    win = Main()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
