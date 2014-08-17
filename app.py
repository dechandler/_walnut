#!/usr/bin/python


import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GObject
GObject.threads_init()
Gst.init(None)


class Main(object):
    def __init__(self):

        self.builder = Gtk.Builder()
        self.builder.add_from_file("1.glade")
        self.window = self.builder.get_object("window")
        self.dev = Dev( self.builder )
        self.prod = Prod( self.builder )

        self.handlers = {
            "onDeleteWindow": Gtk.main_quit,
            "dev_next": self.dev.next,
            #"dev_play_pause": self.dev.player.play_pause,
        }
        self.builder.connect_signals(self.handlers)

    def p_next(self, button):
        song = self.library.selection.next()
        self.p.load_media_file(song)
        self.p.play()

    def p_play_pause(self, button):
        """Preview play/pause toggle handler"""
        if self.p.get_state() == "GST_STATE_PLAYING":
            self.p.pause()
        else:
            self.p.play()
            GObject.timeout_add( 1000,
                lambda event: self.update_slider(event, self.dev) )

    def p_set_audio_position(self, position):  # position in nanoseconds
        self.p.seek_simple(Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position)





class Player(object):
    def __init__(self):
        pass

    def update_position(self, event, pane):

        if pane.player.playing == False:
           return False # cancel timeout

        position_ns = pane.audio.query_position(Gst.Format.TIME)[1]
        position_s = int(position_ns) / Gst.SECOND

        duration_ns = pane.audio.query_duration(Gst.Format.TIME)[1]
        duration_s = int(duration_ns) / Gst.SECOND

        remaining_s = duration_s - position_s

           # block seek handler so we don't seek when we set_value()
           # self.slider.handler_block_by_func(self.on_slider_change)

        #duration = float(duration_nanosecs) / Gst.SECOND
        #position = float(nanosecs) / Gst.SECOND

        pane.slider.set_range(0, duration_ns)
        pane.slider.set_value(position_ns)

        pane.time.set_text(" ".join([
            "{}:{:02}".format(remaining_s/60, remaining_s%60),
            "{}:{:02}".format(duration_s/60, duration_s%60),
            "{}:{:02}".format(position_s/60, position_s%60)
        ]))

           #self.slider.handler_unblock_by_func(self.on_slider_change)

        return True

    def next(self):
        song = self.get_next()
        self.player.load_media_file(song)
        self.player.play()




class Dev(Player):
    def __init__(self, builder):
        self.play_pause = builder.get_object("dev_play_pause")
        self.song_info = builder.get_object("dev_song_info")
        self.time = builder.get_object("dev_time")

        self.slider = builder.get_object("dev_slider")

        self.player = AudioPipe()
        self.audio = self.player  #.pipeline

        self.position = None


class Prod(Player):
    def __init__(self, builder):
        self.audio = AudioPipe()


class Library(object):
    """
    This will be the object that holds lists of songs
    Maybe have Playlist as a subclass
    """
    def __init__(self):
        self.list = [
            "/home/david/usr/dropbox/Coding/djx/1.mp3",
            "/home/david/Dropbox/dl-music/ZZ Ward - Til the Casket Drops - 04 - Home.mp3",
            "/home/david/Dropbox/dl-music/ZZ Ward - Til the Casket Drops - 05 - Cryin Wolf (feat. Kendrick Lamar).mp3",
            "/home/david/Dropbox/dl-music/ZZ Ward - Til the Casket Drops - 13 - 365 Days.mp3",
            "/home/david/Dropbox/dl-music/ZZ Ward - Til the Casket Drops - 11 - If I Could Be Her.mp3"
        ]

        self.selection = self.derp()

    def derp(self):
        for song in self.list:
            yield song


class Playlist(object):
    def __init__(self):
        self.list = [
            # list of filepaths
        ]

        self.playing_index = 0
        self.playing = self.list[self.playing_index]

    def set_next(self):
        pass


class PlaylistsTree(object):
    def __init__(self):
        pass



class AudioPipe(Gst.Pipeline):

    def __init__(self):

        self.playing = False

        self.elements = self.build_pipeline(0)

        # Connecting pipeline signals to methods
        #self.pipeline.connect("message::about-to-finish",  self.on_finished)

        self.pbus = self.get_bus()
        self.pbus.add_signal_watch()
        self.pbus.connect('message::eos', self.on_eos)
        self.pbus.connect('message::error', self.on_error)


    def build_pipeline(self, device):

        e = {}
        e['filesrc'] = Gst.ElementFactory.make("filesrc", "filesrc")
        e['decode'] = Gst.ElementFactory.make("decodebin", "decode")
        e['convert'] = Gst.ElementFactory.make("audioconvert", "convert")
        e['sink'] = Gst.ElementFactory.make("pulsesink", "sink")
        e['sink'].set_property("device", device)

        self.add(e['filesrc'])
        self.add(e['decode'])
        self.add(e['convert'])
        self.add(e['sink'])

        e['filesrc'].link(e['decode'])
        e['convert'].link(e['sink'])

        e['decode'].connect( 'pad-added', lambda d, pad:
                pad.link(e['convert'].get_static_pad("sink")) )

        return e

    def load_media_file(self, filepath):
        self.set_state(Gst.State.READY)
        self.elements['filesrc'].set_property('location', filepath)
        self.playing = False

    def play(self):
        """ """
        self.set_state(Gst.State.PLAYING)
        self.playing = True

    def pause(self):
        """ """
        self.set_state(Gst.State.PAUSED)
        self.playing = False

    def get_state(self):
        """"""
        return self.get_state.value_name

    def on_eos(self):
        self.set_state(Gst.State.READY)
        self.playing = False

    def on_error(self):
        pass

    def on_finished(self):
        pass


if __name__ == "__main__":
    win = Main()
    win.window.connect("delete-event", Gtk.main_quit)
    win.window.show_all()
    Gtk.main()
