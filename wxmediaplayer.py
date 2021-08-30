from __future__ import unicode_literals
import re
import os
import io
import os.path
import wx
import wx.media
import time
import sys
PY3 = sys.version_info.major > 2
from midiplayer import MidiPlayer


class WxMediaPlayer(MidiPlayer):
    def __init__(self, parent_window, backend=None):
        super(WxMediaPlayer, self).__init__()
        if backend is not None:
            self.mc = wx.media.MediaCtrl(parent_window, szBackend=backend)
        else:
            self.mc = wx.media.MediaCtrl(parent_window)
        self.mc.Hide()
        self.is_really_playing = False

        parent_window.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded)
        # Bind other event to be sure to act on the first one that occurs (evenif they should be almost at the same time)
        parent_window.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnMediaFinished)
        parent_window.Bind(wx.media.EVT_MEDIA_STOP, self.OnMediaStop)

    def Play(self):
        # print('Play')
        if wx.Platform != "__WXMAC__":
            try: self.mc.Volume = 0.9
            except: pass

        if wx.Platform == "__WXMAC__":
            time.sleep(0.4) # to fix first notes being skipped
        self.mc.Play()
        self.is_really_playing = True

    def Stop(self):
        # print('Stop')
        self.is_really_playing = False
        self.mc.Stop()
        self.mc.Load('NONEXISTANT_FILE____.mid') # be sure the midi file is released 2014-10-25 [SS]

    def Pause(self):
        self.mc.Pause()

    def Seek(self, pos_in_ms):
        self.mc.Seek(pos_in_ms)

    def Load(self, path):
        return self.mc.Load(path)

    def Length(self):
        return self.mc.Length()

    def Tell(self):
        return self.mc.Tell()

    @property
    def PlaybackRate(self):
        return self.mc.PlaybackRate

    @PlaybackRate.setter
    def PlaybackRate(self, value):
        if self.is_playing or wx.Platform != "__WXMAC__": # after setting playbackrate on Windows the self.mc.GetState() becomes MEDIASTATE_STOPPED
            self.mc.PlaybackRate = value

    @property
    def is_playing(self):
        return self.mc.GetState() == wx.media.MEDIASTATE_PLAYING

    @property
    def is_paused(self):
        return self.mc.GetState() == wx.media.MEDIASTATE_PAUSED

    @property
    def supports_tempo_change_while_playing(self):
        return True

    def OnMediaLoaded(self, evt):
        self.OnAfterLoad.fire()

    def OnMediaStop(self, evt):
        # print('Media stopped')
        # if media is finished but playback as a loop was used relaunch the playback immediatly
        # and prevent media of being stop (event is vetoed as explained in MediaCtrl documentation)
        if self.loop_midi_playback:
            self.last_playback_rate = self.mc.PlaybackRate
            evt.Veto()  # does not work on Windows, music stops always
            wx.CallAfter(self.play_again)

    def OnMediaFinished(self, evt):
        # print('Media finished')
        # if media is finished but playback as a loop was used relaunch the playback immediatly
        # (OnMediaStop should already have restarted it if required as event STOP arrive before FINISHED)
        self.is_really_playing = False
        if self.loop_midi_playback:
            self.play_again()
        else:
            self.OnAfterStop.fire()

    def play_again(self):
        if self.is_playing:
            self.Seek(0)
        else:
            self.Seek(0)
            self.Play()
            self.set_playback_rate(self.last_playback_rate)
            #self.update_playback_rate()
            self.is_really_playing = True

    def set_playback_rate(self, playback_rate):
        if self.mc and (self.is_playing or wx.Platform != "__WXMAC__"): # after setting playbackrate on Windows the self.mc.GetState() becomes MEDIASTATE_STOPPED
            self.mc.PlaybackRate = playback_rate


