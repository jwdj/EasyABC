from __future__ import unicode_literals
import re
import os
import io
import os.path
import time
import sys
PY3 = sys.version_info.major > 2
from midiplayer import MidiPlayer
import fluidsynth as F

class FluidSynthPlayer(MidiPlayer):
    def __init__(self, sf2_path):
        super(FluidSynthPlayer, self).__init__()
        self.fs = F.Synth(bsize=2048) # make a synth
        self.driver_name = F.onLinux and 'pulseaudio' or 'dsound'
        self.fs.start(self.driver_name)  # set default output driver and start clock
        self.sfid = self.fs.sfload(sf2_path)
        self.fs.program_select(0, self.sfid, 0, 0)
        self.p = F.Player(self.fs)   # make a new player
        self.duration_in_ticks = 0               # length of midi file
        self.pause_time = 0        # time in midi ticks where player stopped
        self.set_gain(0.7)
    
    def set_soundfont(self, sf2_path):         # load another sound font
        self.sf2 = sf2_path
        if self.sfid >= 0:
            self.fs.sfunload(self.sfid)
        self.sfid = self.fs.sfload(sf2_path)
        if self.sfid < 0: return 0     # not a sf2 file
        self.fs.program_select(0, self.sfid, 0, 0)
        self.pause_time = 0       # resume playing at time == 0
        return 1

    def Load(self, path):          # load a midi file
        self.reset()              # reset the player, empty the playlist
        self.pause_time  = 0       # resume playing at time == 0
        if os.path.exists(path):
            self.p.add(path)           # add file to playlist
            self.p.load()             # load first file from playlist
            self.duration_in_ticks = max([self.p.get_length(i) for i in range (16)])  # get max length of all tracks
            if self.p.get_status() == 2:  # not a midi file
                return False
            self.OnAfterLoad.fire()
            return True
        return False

    def reset(self):              # the only way to empty the playlist ...
        self.p.delete()           # delete player
        self.p = F.Player(self.fs)   # make a new one

    def Play(self):
        if self.is_playing:
            return
        self.p.play(self.pause_time)

    def Pause(self):
        if self.is_playing:
            self.pause_time = self.p.stop()

    def Stop(self):
        if self.is_playing:
            self.p.stop()
            self.OnAfterStop.fire()
        self.pause_time = 0

    def Seek(self, time):         # go to time (in midi ticks)
        if time > self.duration_in_ticks or time < 0: 
            return
        ticks = self.p.seek(time)
        self.pause_time = time
        return ticks

    def Tell(self):
        return self.p.get_ticks() # get play position in midi ticks
        
    def dispose(self):             # free some memory
        self.p.delete()
        self.fs.delete()

    @property
    def is_playing(self):             
        return self.p.get_status() == 1  # 0 = ready, 1 = playing, 2 = finished

    @property
    def is_paused(self):
        return self.pause_time > 0

    def set_gain(self, gain):  # gain between 0.0 and 1.0
        self.p.set_gain(gain)

    def Length(self):
        return self.duration_in_ticks

    @property
    def unit_is_midi_tick(self):
        return True