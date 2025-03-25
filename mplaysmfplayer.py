#!/usr/bin/env python

#FAU 20201229: Build a midiplayer for EasyABC based on mplay, to be used on Mac

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
from mplay.smf_easyabc import read, play, fileinfo, songinfo, beatinfo, lyrics, chordinfo, \
    setsong, channelinfo, setchannel, families, instruments, songposition

if sys.platform == 'darwin':
    from mplay.darwinmidi import midiDevice
#elif sys.platform == 'win32':
#    from mplay.win32midi import midiDevice
#elif sys.platform == 'linux2':
#    from mplay.linux2midi import midiDevice



class MPlaySMFPlayer(MidiPlayer):
    def __init__(self, parent_window=None, backend=None):
        super(MPlaySMFPlayer, self).__init__()

        #self.win = win
        #self.midi = read(path)
        self.device = midiDevice()
        #self.muted = 16 * [False]
        #self.solo = 16 * [False]
        #self.width = width
        #self.height = height
        #self.button = False
        #self.selection = None
        self.pause = False
        self.midi_file = None
        
        self.is_play_started = False
        #self.loop_midi_playback = False
        self.__PlaybackRate = 1.0


        #parent_window.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded)
        # Bind other event to be sure to act on the first one that occurs (evenif they should be almost at the same time)
        #parent_window.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnMediaFinished)
        #parent_window.Bind(wx.media.EVT_MEDIA_STOP, self.OnMediaStop)

    def Load(self, path):
        if os.path.exists(path):
            self.midi_file = read(path)
            #FAU:MIDIPLAY: 20250125 Add the call to the EasyABC event
            self.OnAfterLoad.fire()
            return True
        return False

    def Play(self):
        #if self.is_really_playing:
        #    return 0.04
        if not self.is_play_started:
            delta = play(self.midi_file, self.device, False)
            self.is_play_started = True
            return delta
        else:
            self.Pause()
            return 0.04

    #FAU 20201229: Function is added to allow playing on timer Play() is used to keep same interface for EasyABC for the pause feature
    def IdlePlay(self):
        if self.is_playing:
            delta = play(self.midi_file, self.device, False)
            self.is_really_playing = True
            #if delta == 0:
            #    self.OnAfterStop.fire()
            return delta
        else:
            return 0.04
        
    def Pause(self):
        setsong(self.midi_file, action='pause')
        self.pause = not self.pause

    def Stop(self):
        if self.midi_file ==None:
            return
        self.is_play_started = False
        setsong(self.midi_file, action='exit')
        self.pause = False

    def Seek(self, time):
        if time > self.Length() or time < 0:
            return
        setsong(self.midi_file, goto=time)
        
    def Length(self):
        return self.midi_file.playing_time-960

    def Tell(self):
        return self.midi_file.getsongposition()

    @property
    def PlaybackRate(self):
        return self.__PlaybackRate

    @PlaybackRate.setter
    def PlaybackRate(self, value):
        if self.is_playing or wx.Platform != "__WXMAC__": # after setting playbackrate on Windows the self.mc.GetState() becomes MEDIASTATE_STOPPED
            self.__PlaybackRate = value
            setsong(self.midi_file, multibpm=value)

    @property
    def is_playing(self):
        return self.is_play_started and not self.is_paused

    @property
    def is_paused(self):
        return self.pause

    @property
    def supports_tempo_change_while_playing(self):
        return True

    @property
    def unit_is_midi_tick(self):
        return True
    
    @property
    def get_songinfo(self):
        return songinfo(self.midi_file)
    
    


