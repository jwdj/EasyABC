'''
    Some Python bindings for FluidSynth
    Released under the LGPL
    Copyright 2012-2021, Willem Vree

    Synth Class, partially copied from pyFluidSynth, Copyright 2008 Nathan Whitehead
'''
import time, os, sys, glob
from ctypes import c_int, c_double, c_char_p, byref, CDLL, c_void_p
from ctypes.util import find_library

#VERSION = 15

python3 = sys.version_info [0] > 2
revModels = ['Model 1','Model 2', 'Model 3','Model 4','Model 5']
# room size (0.0-1.2), damping (0.0-1.0), width (0.0-100.0), level (0.0-1.0)
revmods = { revModels [0]: (0.2, 0.0, 0.5, 0.9), revModels [1]: (0.4, 0.2, 0.5, 0.8),
            revModels [2]: (0.6, 0.4, 0.5, 0.7), revModels [3]: (0.8, 0.7, 0.5, 0.6),
            revModels [4]: (0.8, 0.0, 0.5, 0.5)}

onLinux = 'linux' in sys.platform

#FAU 20240105: py2app and py2exe sets variable sys.frozen
#FAU 20240105: py2app sets also environment variable RESOURCEPATH to point to Resources folder
#FAU 20240105: Use of this information to either look for the libraries side to easy_abc or in the app folder
#
if sys.platform=='darwin' and getattr(sys, "frozen", None) and os.environ.get('RESOURCEPATH'):
    _libdir = os.path.join(os.path.dirname(os.environ["RESOURCEPATH"]),'Frameworks')
else:
    _libdir = os.path.join('.', '**')

xs = glob.glob (os.path.join(_libdir, 'libfluidsynth*'), recursive=True) # prefer a local installation
if len (xs) > 0: 
    lib = xs [0]
else:
    lib = find_library ('fluidsynth') or find_library ('libfluidsynth') or find_library ('libfluidsynth-2')
    
    
try:    F = CDLL (lib)   # load fluidsynth and make all API functions avalable as F.<api-function>
except: raise ImportError ("Couldn't find the FluidSynth library in the program directory.")

x, y, z = c_int (), c_int (), c_int ()
F.fluid_version (byref (x), byref (y), byref (z))
print ('%s loaded, version: %d.%d.%d' % (lib, x.value, y.value, z.value))
if x.value < 2: print ('*** Version >= 2 of fluidsyth is needed ***'); sys.exit ()

def bs (reeks):
    return reeks.encode ('utf-8') if python3 or type (reeks) == unicode else reeks

def getFnObj (name, *args): # call F.name (*args), which returns a function
    f = F [name]
    f.restype = c_void_p    # standard result type is int
    return c_void_p (f (*args)) # still need to cast the result

class Synth:            # interface for the FluidSynth synthesizer
    def __init__(self, gain=0.2, samplerate=44100, bsize=64):
        st = getFnObj ('new_fluid_settings')
        F.fluid_settings_setnum (st, bs('synth.gain'), c_double (gain))
        F.fluid_settings_setnum (st, bs('synth.sample-rate'), c_double (samplerate))
        F.fluid_settings_setint (st, bs('audio.period-size'), bsize)
        F.fluid_settings_setint (st, bs('audio.periods'), 2)
        self.settings = st
        self.synth = getFnObj ('new_fluid_synth', st)
        self.audio_driver = None        

    def start (self, driver=None):   # initialize the audio driver
        if driver is not None:
            assert (driver in ['alsa', 'oss', 'jack', 'portaudio', 'sndmgr', 'coreaudio', 'dsound', 'pulseaudio']) 
            F.fluid_settings_setstr (self.settings, bs('audio.driver'), bs(driver))
        self.audio_driver = getFnObj ('new_fluid_audio_driver', self.settings, self.synth)
        if not self.audio_driver:   # API returns 0 on error (not None)
            self.audio_driver = None
        else:   # print some info
            psize = c_int ()    # integer for parameter passing by reference
            F.fluid_settings_getint (self.settings, bs('audio.period-size'), byref (psize))
            nper = c_int ()
            F.fluid_settings_getint (self.settings, bs('audio.periods'), byref (nper))
            print ('audio.period-size:', psize.value, 'audio.periods:', nper.value, 'latency:', nper.value * psize.value * 1000 / 44100, 'msec')

    def delete (self):              # release all memory
        if self.audio_driver is not None:
            F.delete_fluid_audio_driver (self.audio_driver)
        F.delete_fluid_synth (self.synth)
        F.delete_fluid_settings (self.settings)
        self.settings = self.synth = self.audio_driver = None

    def sfload (self, filename, update_midi_preset=0):  # load soundfont
        return F.fluid_synth_sfload (self.synth, c_char_p (bs (filename)), update_midi_preset)

    def sfunload (self, sfid, update_midi_preset=0):    # clear soundfont
        return F.fluid_synth_sfunload (self.synth, sfid, update_midi_preset)

    def program_select (self, chan, sfid, bank, preset):
        return F.fluid_synth_program_select (self.synth, chan, sfid, bank, preset)

    def set_reverb (self, roomsize, damping, width, level):     # change reverb model parameters
        return F.fluid_synth_set_reverb (self.synth, c_double (roomsize), c_double (damping), c_double (width), c_double (level))

    def set_chorus (self, nr, level, speed, depth_ms, type):    # change chorus model pararmeters
        return F.fluid_synth_set_chorus (self.synth, nr, c_double (level), c_double (speed), c_double (depth_ms), type)

    def set_reverb_level (self, level):                     # set the amount of reverb (0-127) on all midi channels
        n = F.fluid_synth_count_midi_channels (self.synth)
        for chan in range (n):
            F.fluid_synth_cc (self.synth, chan, 91, level); # midi control change #91 == reverb level

    def set_chorus_level (self, level):                     # set the amount of chorus (0-127) on all midi channels
        n = F.fluid_synth_count_midi_channels (self.synth)
        for chan in range (n):
            F.fluid_synth_cc (self.synth, chan, 93, level); # midi control change #93 == chorus level

    def set_gain (self, gain):
        F.fluid_settings_setnum (self.settings, bs('synth.gain'), c_double (gain))
    def set_buffer (self, size=0, driver=None):
        if self.audio_driver is not None:   # remove current audio driver
            F.delete_fluid_audio_driver (self.audio_driver)
        if size:
            F.fluid_settings_setint (self.settings, bs('audio.period-size'), size)
        self.start (driver)   # create new driver


class Player:               # interface for the FluidSynth internal midi player
    LOOP_INFINITELY = -1

    def __init__ (s, flsynth):
        s.flsynth = flsynth # an instance of class Synth
        s.player = getFnObj ('new_fluid_player', s.flsynth.synth)

    def add (s, midifile):  # add midifile to the playlist
        F.fluid_player_add (s.player, c_char_p (bs (midifile)))

    def play (s, offset=0): # start playing at time == offset in midi ticks
        ticks = s.seek (offset);
        F.fluid_player_play (s.player)

    def set_loop(s, loops = LOOP_INFINITELY):
        F.fluid_player_set_loop(s.player, loops)

    def stop (s):           # stop playing and return position in midi ticks
        F.fluid_player_stop (s.player)
        F.fluid_synth_all_notes_off (s.flsynth.synth, -1)   # -1 == all channels
        return s.get_ticks ()

    def wait (s):           # wait until player is finished
        F.fluid_player_join (s.player)

    def get_status (s):     # 1 == playing, 2 == player finished 
        return F.fluid_player_get_status (s.player)

    def get_ticks (s):      # get current position in midi ticks
        t = F.fluid_player_get_current_tick (s.player)
        return t

    def seek (s, ticks_p):  # go to position ticks_p (in midi ticks)
        F.fluid_synth_all_notes_off (s.flsynth.synth, -1)   # -1 == all channels
        F.fluid_player_seek (s.player, ticks_p);
        return s.get_ticks ()

    def seekW (s, ticks_p): # go to position ticks_p (in midi ticks) and wait until seeked
        F.fluid_synth_all_notes_off (s.flsynth.synth, -1)   # -1 == all channels
        ticks = F.fluid_player_seek (s.player, ticks_p)
        n = 0
        while abs (ticks - ticks_p) > 10 and n < 100:
            time.sleep (0.01)
            ticks = s.get_ticks ()
            n += 1          # time out after 1 sec
        return ticks

    def get_length (s):  # get duration of a midi track in ticks
        return F.fluid_player_get_total_ticks (s.player)

    def delete (s):
        F.delete_fluid_player (s.player)

    def renderLoop (s, quality = 0.5, callback=None):       # render midi file to audio file
        renderer = getFnObj ('new_fluid_file_renderer', s.flsynth.synth)
        if not renderer:
            print ('failed to create file renderer')
            return
        F.fluid_file_set_encoding_quality (renderer, c_double (quality))
        k = c_int()         # get block size (samples are rendered one block at a time)
        F.fluid_settings_getint (s.flsynth.settings, bs('audio.period-size'), byref (k))
        n = 0               # sample counter
        while s.get_status () == 1:
            if F.fluid_file_renderer_process_block (renderer) != 0: # render one block
                print ('renderer_loop error')
                break
            n += k.value    # increment with block size
            if callback: callback (n)   # for progress reporting
        F.delete_fluid_file_renderer (renderer)
        return n

    def set_render_mode (s, file_name, file_type):  # set audio file and audio type
        st = s.flsynth.settings                     # should be called before the renderLoop
        F.fluid_settings_setstr (st, bs('audio.file.name'), c_char_p (bs (file_name)))
        F.fluid_settings_setstr (st, bs('audio.file.type'), c_char_p (bs (file_type)))
        F.fluid_settings_setstr (st, bs('player.timing-source'), bs('sample'));
        F.fluid_settings_setint (st, bs('synth.parallel-render'), 1)

    def set_reverb (s, name):   # change reverb model parameters
        roomsize, damp, width, level = revmods.get (name, revmods [name])
        s.flsynth.set_reverb (roomsize, damp, width, level)

    def set_chorus (s, nr, level, speed, depth_ms, type):    # change chorus model pararmeters
        s.flsynth.set_chorus (nr, level, speed, depth_ms, type)

    def set_reverb_level (s, newlev): # set reverb level 0-127 on all midi channels
        s.flsynth.set_reverb_level (newlev)

    def set_chorus_level (s, newlev): # set chorus level 0-127 on all midi channels
        s.flsynth.set_chorus_level (newlev)

    def set_gain (s, gain): # set master volume 0-10
        s.flsynth.set_gain (gain)
