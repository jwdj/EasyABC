'''
    Some Python bindings for FluidSynth
    Released under the LGPL
    Copyright 2012, Willem Vree

    Synth Class, partially copied from pyFluidSynth, Copyright 2008 Nathan Whitehead

    Modified February 2024 S.M.Blinkhorn to pass pointer arguments into CDLL as c_void_p types
    thereby avoiding Undefined Behaviours leading to access violations on some OSs,
    notably, 64bit Windows.
'''

import time
from ctypes import c_int, c_uint, c_double, c_float, c_char_p, c_wchar_p, c_void_p, byref, CDLL
# from ctypes.util import find_library

import sys
PY3 = sys.version_info.major > 2
if PY3:
    def b(s):
        return s.encode("latin-1")
else:
    def b(s):
        return s

import os
import platform
from utils import *

revModels = ['Model 1','Model 2', 'Model 3','Model 4','Model 5']
# room size (0.0-1.2), damping (0.0-1.0), width (0.0-100.0), level (0.0-1.0)
revmods = { revModels [0]: (0.2, 0.0, 0.5, 0.9), revModels [1]: (0.4, 0.2, 0.5, 0.8),
            revModels [2]: (0.6, 0.4, 0.5, 0.7), revModels [3]: (0.8, 0.7, 0.5, 0.6),
            revModels [4]: (0.8, 0.0, 0.5, 0.5)}

# F = CDLL (..) makes all API functions avalable as F.<api-function>

if platform.system() == 'Windows':
    fluidsynth_lib_path = get_application_path() + '\\bin\\fluidsynth'
    if is_running_32bit():
        fluidsynth_lib_path += '\\X86'

    append_to_envpath(fluidsynth_lib_path)
    lib = fluidsynth_lib_path + '\\libfluidsynth-3.dll'
    if not os.path.isfile(lib):
        lib = fluidsynth_lib_path + '\\libfluidsynth-2.dll'
    lib_locations = [lib]
else:
    lib_locations = ['./libfluidsynth.so.3', 'libfluidsynth.so.3', './libfluidsynth.so.2', 'libfluidsynth.so.2']

i = 0
while i < len(lib_locations):
    try:
        lib = lib_locations[i]
        F = CDLL(lib)
        # print("Library %s" % lib)
        break
    except:
        i += 1

if i == len(lib_locations):
    raise ImportError("Couldn't find the FluidSynth library: " + lib)

class Synth:            # interface for the FluidSynth synthesizer
    def __init__(self, gain=0.2, samplerate=44100.0, bsize=64, output_path=None):
        self.handle = c_void_p
        F.new_fluid_settings.restype = self.handle
        F.new_fluid_synth.restype = self.handle
        self.settings = F.new_fluid_settings()
        # print("Settings: %s" % hex(self.settings))
        self.setting_setnum('synth.gain', gain)
        # self.setting_setnum('synth.sample-rate', samplerate)
        # self.setting_setint('audio.period-size', bsize)
        # self.setting_setint('audio.periods', 2)
        if output_path:
            # specify the file to store the audio to
            # make sure you compiled fluidsynth with libsndfile to get a real wave file
            # otherwise this file will only contain raw s16 stereo PCM
            self.setting_setstr("audio.file.name", output_path)
            # use number of samples processed as timing source, rather than the system timer
            self.setting_setstr("player.timing-source", "sample")
            # since this is a non-realtime scenario, there is no need to pin the sample data
            self.setting_setint("synth.lock-memory", 0)
        self.synth = F.new_fluid_synth((c_void_p(self.settings)))
        self.audio_driver = None

    def setting_setstr(self, name, value):
        F.fluid_settings_setstr(c_void_p(self.settings), c_char_p(b(name)), c_char_p(b(value)))

    def setting_setint(self, name, value):
        F.fluid_settings_setint(c_void_p(self.settings), c_char_p(b(name)), c_int(value))

    def setting_setnum(self, name, value):
        F.fluid_settings_setnum(c_void_p(self.settings), c_char_p(b(name)), c_double(value))

    def setting_getint(self, name):
        n = c_int()
        F.fluid_settings_getint(c_void_p(self.settings), c_char_p(b(name)), byref(n))
        return n

    def start(self, driver=None):   # initialize the audio driver
        if driver is not None:
            assert(driver in ['alsa', 'oss', 'jack', 'portaudio', 'sndmgr', 'coreaudio', 'dsound', 'pulseaudio'])
            self.setting_setstr('audio.driver', driver)
        self.audio_driver = F.new_fluid_audio_driver(c_void_p(self.settings), c_void_p(self.synth))
        if not self.audio_driver:   # API returns 0 on error (not None)
            self.audio_driver = None
        # else:   # print some info
            # psize = self.setting_getint('audio.period-size')
            # nper = self.setting_getint('audio.periods')
            # print 'audio.period-size:', psize.value, 'audio.periods:', nper.value, 'latency:', nper.value * psize.value * 1000 / 44100, 'msec'

    def delete(self):              # release all memory
        if self.audio_driver is not None:
            F.delete_fluid_audio_driver(c_void_p(self.audio_driver))
        F.delete_fluid_synth(c_void_p(self.synth))
        F.delete_fluid_settings(c_void_p(self.settings))
        self.settings = self.synth = self.audio_driver = None

    def sfload(self, filename, update_midi_preset=0):  # load soundfont
        return F.fluid_synth_sfload(c_void_p(self.synth), c_char_p(b(filename)), update_midi_preset)

    def sfunload(self, sfid, update_midi_preset=0):    # clear soundfont
        return F.fluid_synth_sfunload(c_void_p(self.synth), sfid, update_midi_preset)

    def program_select(self, chan, sfid, bank, preset):
        return F.fluid_synth_program_select(c_void_p(self.synth), chan, sfid, bank, preset)

    def set_reverb(self, roomsize, damping, width, level):     # change reverb model parameters
        return F.fluid_synth_set_reverb(c_void_p(self.synth), c_double(roomsize), c_double(damping), c_double(width), c_double(level))

    def set_chorus(self, nr, level, speed, depth_ms, type):    # change chorus model pararmeters
        return F.fluid_synth_set_chorus(c_void_p(self.synth), nr, c_double(level), c_double(speed), c_double(depth_ms), type)

    def set_reverb_level(self, level):                     # set the amount of reverb (0-127) on all midi channels
        n = F.fluid_synth_count_midi_channels(self.synth)
        for chan in range(n):
            F.fluid_synth_cc(c_void_p(self.synth), chan, 91, level) # midi control change #91 == reverb level

    def set_chorus_level(self, level):                     # set the amount of chorus (0-127) on all midi channels
        n = F.fluid_synth_count_midi_channels(self.synth)
        for chan in range(n):
            F.fluid_synth_cc(c_void_p(self.synth), chan, 93, level) # midi control change #93 == chorus level

    def set_gain(self, gain):
        self.setting_setnum('synth.gain', gain)

    def set_buffer(self, size=0, driver=None):
        if self.audio_driver is not None:   # remove current audio driver
            F.delete_fluid_audio_driver(self.audio_driver)
        if size:
            self.setting_setint('audio.period-size', size)
        self.start(driver)   # create new driver


class Player:               # interface for the FluidSynth internal midi player
    LOOP_INFINITELY = -1

    def __init__(self, flsynth):
        self.handle = c_void_p
        F.new_fluid_player.restype = self.handle
        self.flsynth = flsynth # an instance of class Synth
        self.player = F.new_fluid_player(c_void_p(self.flsynth.synth))

    def add(self, midifile):  # add midifile to the playlist
        return F.fluid_player_add(c_void_p(self.player), c_char_p(b(midifile))) == 0

    def play(self, offset=0): # start playing at time == offset in midi ticks
        self.seek(offset)
        F.fluid_player_play(c_void_p(self.player))

    def set_loop(self, loops = LOOP_INFINITELY):
        F.fluid_player_set_loop(c_void_p(self.player), loops)

    def stop(self):           # stop playing and return position in midi ticks
        F.fluid_player_stop(c_void_p(self.player))
        F.fluid_synth_all_notes_off(c_void_p(self.flsynth.synth), -1)   # -1 == all channels
        return self.get_ticks()

    def wait(self):           # wait until player is finished
        F.fluid_player_join(c_void_p(self.player))

    def get_status(self):     # 1 == playing, 2 == player finished
        return F.fluid_player_get_status(c_void_p(self.player))

    def get_ticks(self):      # get current position in midi ticks
        # oldFluid #  t = F.fluid_player_get_ticks(self.player)
        t = F.fluid_player_get_current_tick(c_void_p(self.player))
        return t

    def seek(self, ticks_p):  # go to position ticks_p (in midi ticks)
        F.fluid_synth_all_notes_off(c_void_p(self.flsynth.synth), -1)   # -1 == all channels
        ticks = F.fluid_player_seek(c_void_p(self.player), ticks_p)
        return ticks

    def seekW(self, ticks_p): # go to position ticks_p (in midi ticks) and wait until seeked
        ticks = self.seek(ticks_p)
        n = 0
        while abs(ticks - ticks_p) > 100 and n < 100:
            time.sleep(0.01)
            ticks = self.get_ticks()
            n += 1          # time out after 1 sec
        return ticks

    def get_length(self):  # get duration of a midi track in ticks
        return F.fluid_player_get_total_ticks(c_void_p(self.player))

    def delete(self):
        F.delete_fluid_player(c_void_p(self.player))

    def renderLoop(self, callback=None):       # render midi file to audio file
        self.handle = c_void_p
        F.new_fluid_file_renderer.restype = self.handle
        renderer = F.new_fluid_file_renderer(c_void_p(self.flsynth.synth))
        if not renderer:
            print('failed to create file renderer')
            return
        k = self.flsynth.setting_getint('audio.period-size')         # get block size (samples are rendered one block at a time)
        samples = 0               # sample counter
        while self.get_status() == 1:
            if F.fluid_file_renderer_process_block(c_void_p(renderer)) != 0: # render one block
                print('renderer_loop error')
                break
            samples += k.value    # increment with block size
            if callback: callback(samples)   # for progress reporting
        self.stop()  # just for sure: stop the playback explicitly and wait until finished
        F.fluid_player_join(c_void_p(self.player))
        F.delete_fluid_file_renderer(c_void_p(renderer))
        return samples

    def set_render_mode(self, file_name, file_type):  # set audio file and audio type
        st = self.flsynth                     # should be called before the renderLoop
        st.setting_setstr("audio.file.name", file_name)
        st.setting_setstr("audio.file.type", file_type)
        st.setting_setstr("player.timing-source", "sample")
        st.setting_setint("synth.parallel-render", 1)

    def set_reverb(self, name):   # change reverb model parameters
        roomsize, damp, width, level = revmods.get(name, revmods [name])
        self.flsynth.set_reverb(roomsize, damp, width, level)

    def set_chorus(self, nr, level, speed, depth_ms, type):    # change chorus model pararmeters
        self.flsynth.set_chorus(nr, level, speed, depth_ms, type)

    def set_reverb_level(self, newlev): # set reverb level 0-127 on all midi channels
        self.flsynth.set_reverb_level(newlev)

    def set_chorus_level(self, newlev): # set chorus level 0-127 on all midi channels
        self.flsynth.set_chorus_level(newlev)

    def set_gain(self, gain): # set master volume 0-10
        self.flsynth.set_gain(gain)
