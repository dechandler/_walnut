#!/usr/bin/env python2

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

GObject.threads_init()
Gst.init(None)


class Player(object):

    def __init__(self, device=None):

        self.audio = self.build_pipeline(device)

        self.bus = self.audio.get_bus()
        self.bus.add_signal_watch()

        # Connecting pipeline signals to methods
        #self.audio.connect("message::about-to-finish",  self.on_finished)
        self.bus.connect('message::eos', self._on_eos)
        self.bus.connect('message::error', self._on_error)

        self.playing = False

    def build_pipeline(self, device):
        """
        Chains together all the needed gstreamer elements and creates the
        audio pipeline
        """
        audio = Gst.Pipeline()

        self.filesrc = Gst.ElementFactory.make("filesrc", "filesrc")
        self.decode = Gst.ElementFactory.make("decodebin", "decode")
        self.convert = Gst.ElementFactory.make("audioconvert", "convert")
        self.sink = Gst.ElementFactory.make("pulsesink", "sink")

        self.sink.set_property("device", device)

        audio.add( self.filesrc )
        audio.add( self.decode )
        audio.add( self.convert )
        audio.add( self.sink )

        self.filesrc.link( self.decode )
        self.convert.link( self.sink )

        self.decode.connect( 'pad-added', lambda d, pad:
                pad.link(self.convert.get_static_pad("sink")) )

        return audio

    def load_media_file(self, filepath):
        self.audio.set_state(Gst.State.READY)
        self.filesrc.set_property('location', filepath)
        self.playing = False

    def play(self):
        """ """
        self.audio.set_state(Gst.State.PLAYING)
        self.playing = True

    def pause(self):
        """ """
        self.audio.set_state(Gst.State.PAUSED)
        self.playing = False

    def stop(self):
        self.audio.set_state(Gst.State.NULL)
        self.playing = False

    def get_state(self):
        """ """
        return self.audio.get_state(0)[1].value_name

    def get_position(self):

        one_billion = 1000000000  # nanoseconds in a second

        position_ns = self.audio.query_position(Gst.Format.TIME)[1]
        duration_ns = self.audio.query_duration(Gst.Format.TIME)[1]

        return position_ns, duration_ns

    def seek(self, position):  # position is in nanoseconds

        self.audio.set_state(Gst.State.PAUSED)
        self.audio.seek_simple( Gst.Format.TIME,
                    Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, position )
        if self.playing:
            self.audio.set_state(Gst.State.PLAYING)

    def _on_eos(self):
        self.stop()

    def _on_error(self):
        self.stop()

    def _on_finished(self):
        self.stop()


if __name__ == "__main__":

    from gi.repository import Gtk
    from time import sleep

    class Main(Gtk.Window):
        def __init__(self):

            super(Main, self).__init__(title="Player Test")

            player = Player(device=0)
            player.load_media_file("/home/david/usr/dropbox/Coding/walnut/1.mp3")
            player.play()
            print player.get_state()
            sleep(.03)
            print player.get_state()
            print "play"
            sleep(1)
            player.pause()
            print player.get_state()
            print "pause"
            sleep(1)
            player.play()
            print player.get_state()

            print "play"
            sleep(1)
            player.stop()
            print player.get_state()

            print "stop"
            sleep(1)
            player.play()
            print player.get_state()

            print "play"
            sleep(1)
            player.pause()
            print player.get_state()

            print "pause"


    win = Main()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()


