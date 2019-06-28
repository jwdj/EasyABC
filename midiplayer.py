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

class MidiPlayer(object):
    def __init__(self):
        super(MidiPlayer, self).__init__()
        self.OnAfterStop = None
        self.OnAfterLoad = None  

    def Seek(self, pos_in_ms):
        pass

    def Play(self):
        pass

    def Stop(self):
        pass

    def Pause(self):
        pass

    def Load(self, path):
        return True

    def Length(self):
        return 0

    def Tell(self):
        return 0

    @property
    def is_playing(self):
        return False

    @property
    def is_paused(self):
        return False


class DummyMidiPlayer(MidiPlayer):
    def __init__(self):
        super(DummyMidiPlayer, self).__init__()


class WxMediaPlayer(MidiPlayer):
    def __init__(self, parent_window, backend=None):
        super(WxMediaPlayer, self).__init__()
        self.mc = wx.media.MediaCtrl(parent_window, szBackend=backend)
        self.mc.Hide()  
        self.is_really_playing = False    
        self.loop_midi_playback = False

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

    def OnMediaLoaded(self, evt):
        # print('OnMediaLoaded')
        if self.OnAfterLoad is not None:
            self.OnAfterLoad()

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
        elif self.OnAfterStop is not None:
            # print('Media OnAfterStop')
            self.OnAfterStop()

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
         


class FluidSynthPlayer(MidiPlayer):
    def __init__(self, sf2_path):
        super(FluidSynthPlayer, self).__init__()
        import fluidsynth as F
        self.fs = F.Synth(bsize=2048) # make a synth
        self.driver_name = F.onLinux and 'pulseaudio' or 'dsound'
        self.fs.start(self.driver_name)  # set default output driver and start clock
        self.sf2 = sf2_path
        self.sfid = self.fs.sfload(self.sf2)
        self.fs.program_select(0, self.sfid, 0, 0)
        self.p = F.Player(self.fs)   # make a new player
        self.fnm = ''              # current midi file
        self.dur = 0               # lenght of midi file
        self.playing = 0
        self.pause_time = 0        # time in midi ticks where player stopped
        self.set_gain(0.2)
    
    def set_soundfont(self, sf2_path):         # load another sound font
        self.sf2 = sf2_path
        if self.sfid >= 0:
            self.fs.sfunload(self.sfid)
        self.sfid = self.fs.sfload(sf2_path)
        if self.sfid < 0: return 0     # not a sf2 file
        self.fs.program_select(0, self.sfid, 0, 0)
        self.pause_time = 0       # resume playing at time == 0
        return 1

    def load(self, path):          # load a midi file
        self.reset()              # reset the player, empty the playlist
        self.pause_time  = 0       # resume playing at time == 0
        self.p.add(path)           # add file to playlist
        self.p.load()             # load first file from playlist
        self.dur = max ([self.p.get_length (i) for i in range (16)])  # get max length of all tracks
        if self.p.get_status() == 2:  # not a midi file
            return False
        return True

    def reset(self):              # the only way to empty the playlist ...
        self.p.delete()           # delete player
        self.p = F.Player(self.fs)   # make a new one

    def play(self):
        if self.playing:
            self.pause_time = self.p.stop()
            self.playing = 0
        else:
            self.p.play(self.pause_time)
            self.playing = 1

    def Seek(self, time):         # go to time (in midi ticks)
        if time > self.dur or time < 0: return
        ticks = self.p.seek (time)
        self.pause_time = time
        return ticks

    def Tell(self):
        return self.p.get_ticks() # get play position in midi ticks
        
    def delete(self):             # free some memory
        self.p.delete()
        self.fs.delete()

    def is_playing(self):             
        return self.p.get_status() == 1  # 0 = ready, 1 = playing, 2 = finished

    def set_gain(self, gain):
        self.p.set_gain(gain)
