#!/usr/bin/env python

#FAU 20201229: file copied and modified from original one of mplay to interface with EasyABC

from __future__ import absolute_import, division, print_function

import sys
import os
from time import time, sleep


if sys.platform == 'darwin':
    from mplay.darwinmidi import midiDevice
#elif sys.platform == 'win32':
#    from mplay.win32midi import midiDevice
#elif sys.platform == 'linux2':
#    from mplay.linux2midi import midiDevice

debug = False
gm1 = True

instruments = (
    'Piano 1', 'Piano 2', 'Piano 3', 'Honky-tonk',
    'E.Piano 1', 'E.Piano 2', 'Harpsichord', 'Clav.',
    'Celesta', 'Glockenspl', 'Music Box', 'Vibraphone',
    'Marimba', 'Xylophone', 'Tubularbell', 'Santur',
    'Organ 1', 'Organ 2', 'Organ 3', 'Church Org1',
    'Reed Organ', 'Accordion F', 'Harmonica', 'Bandoneon',
    'Nylon Gt.', 'Steel Gt.', 'Jazz Gt.', 'Clean Gt.',
    'Muted Gt.', 'OverdriveGt', 'Dist.Gt.', 'Gt.Harmonix',
    'Acoustic Bs', 'Fingered Bs', 'Picked Bass', 'Fretless Bs',
    'Slap Bass 1', 'Slap Bass 2', 'Syn.Bass 1', 'Syn.Bass 2',
    'Violin', 'Viola', 'Cello', 'Contrabass',
    'Tremolo Str', 'Pizzicato', 'Harp', 'Timpani',
    'Strings', 'SlowStrings', 'SynStrings1', 'SynStrings2',
    'Choir Aahs', 'Voice Oohs', 'SynVox', 'Orchest.Hit',
    'Trumpet', 'Trombone', 'Tuba', 'MuteTrumpet',
    'French Horn', 'Brass 1', 'Syn.Brass 1', 'Syn.Brass 2',
    'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'BaritoneSax',
    'Oboe', 'EnglishHorn', 'Bassoon', 'Clarinet',
    'Piccolo', 'Flute', 'Recorder', 'Pan Flute',
    'Bottle Blow', 'Shakuhachi', 'Whistle', 'Ocarina',
    'Square Wave', 'Saw Wave', 'SynCalliope', 'ChifferLead',
    'Charang', 'Solo Vox', '5th Saw', 'Bass & Lead',
    'Fantasia', 'Warm Pad', 'Polysynth', 'Space Voice',
    'Bowed Glass', 'Metal Pad', 'Halo Pad', 'Sweep Pad',
    'Ice Rain', 'Soundtrack', 'Crystal', 'Atmosphere',
    'Brightness', 'Goblin', 'Echo Drops', 'Star Theme',
    'Sitar', 'Banjo', 'Shamisen', 'Koto',
    'Kalimba', 'Bagpipe', 'Fiddle', 'Shanai',
    'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock',
    'Taiko', 'Melo. Tom 1', 'Synth Drum', 'Reverse Cym',
    'Gt.FretNoiz', 'BreathNoise', 'Seashore', 'Bird',
    'Telephone 1', 'Helicopter', 'Applause', 'Gun Shot')

families = (
    'Piano', 'Chromatic Percussion', 'Organ', 'Guitar',
    'Bass', 'Strings', 'Ensemble', 'Brass',
    'Reed', 'Pipe', 'Synth Lead', 'Synth Pad',
    'Synth Effects', 'Ethnic', 'Percussive', 'Sound Effects')

drum_instruments = (
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', 'Acoustic Bass Drum',
    'Bass Drum 1', 'Side Stick', 'Acoustic Snare', 'Hand Clap',
    'Electric Snare', 'Low Floor Tom', 'Closed Hi-Hat', 'High Floor Tom',
    'Pedal Hi-Hat', 'Low Tom', 'Open Hi-Hat', 'Low-Mid Tom',
    'Hi-Mid Tom', 'Crash Cymbal 1', 'High Tom', 'Ride Cymbal 1',
    'Chinese Cymbal', 'Ride Bell', 'Tambourine', 'Splash Cymbal',
    'Cowbell', 'Crash Cymbal 2', 'Vibraslap', 'Ride Cymbal 2',
    'Hi Bongo', 'Low Bongo', 'Mute Hi Conga', 'Open Hi Conga',
    'Low Conga', 'High Timbale', 'Low Timbale', 'High Agogo',
    'Low Agogo', 'Cabasa', 'Maracas', 'Short Whistle',
    'Long Whistle', 'Short Guiro', 'Long Guiro', 'Claves',
    'Hi Wood Block', 'Low Wood Block', 'Mute Cuica', 'Open Cuica',
    'Mute Triangle', 'Open Triangle', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')

keys = ('Cb', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', ' F',
        ' C', ' G', ' D', ' A', ' E', ' B', 'F#',
        'C#', '*/')
modes = (' ', 'm', '*')

notes = ('C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B')

chords = {
    0b000010010001: '',
    0b000010100001: 'sus',
    0b000001010001: '-5',
    0b000100010001: '+5',
    0b001010010001: '6',
    0b010010010001: '7',
    0b100010010001: 'maj7',
    0b000010010101: 'add9',
    0b100010010101: 'maj9',
    0b001010010101: '6/9',
    0b010010100001: '7/4',
    0b011010010001: '7/6',
    0b010100010001: '7/+5',
    0b010001010001: '7/-5',
    0b010010010101: '7/9',
    0b010011010001: '7/+9',
    0b010010010011: '7-9',
    0b010001010011: '7-9-5',
    0b001001001001: 'dim',
    0b000100010101: '9+5',
    0b000001010101: '9-5',
    0b010100010011: '7-9+5',
    0b000010001001: 'm',
    0b001010001001: 'm6',
    0b010010001001: 'm7',
    0b100010001001: 'mmaj7',
    0b010001001001: 'm7-5',
    0b000010001101: 'm9',
    0b000010101001: 'm11'}

messages = (
    'Note Off', 'Note  On', 'Key Pressure', 'Control Change',
    'Program Change', 'Channel Pressure', 'Pitch Wheel')

meta = (
    'Sequence Number', 'Text', 'Copyright', 'Sequence Name',
    'Instrument', 'Lyric', 'Marker', 'Cue Point')


def dbg(message):
    print(message)


def printable(chars):
    result = ''
    for b in chars:
        if b == 10:
            result += '\\n'
        elif b == 13:
            result += '\\r'
        elif b < ord(' '):
            result += '\\%03o' % b
        else:
            result += chr(b)
    return result


class SMF:
    def __init__(self):
        self.path = None
        self.device = None
        self.format = 0
        self.tracks = 0
        self.mf = bytearray(0)
        self.off = 0
        self.ev = []
        self.status = 0
        self.midi_clock = 0
        self.next = 0
        self.start = None
        self.elapsed_time = 0
        self.pause = 0
        self.division = 384
        self.bpm = 120
        #FAU 20201229: multibpm added for EasyABC
        self.multibpm = 1.0
        self.playing_time = 0
        self.line = self.text = ''
        self.chord = ''
        self.notes = []
        self.tempo = 60000000 / self.bpm
        self.numerator = self.denominator = 4
        self.clocks_per_beat = 24
        self.notes_per_quarter = 8
        self.key = 8
        self.key_shift = 0
        self.mode = 2
        self.channel = []
        for ch in range(16):
            self.channel.append({'used': False,
                                 'muted': False,
                                 'name': '',
                                 'instrument': 0,
                                 'family': '',
                                 'variation': 0,
                                 'level': 100,
                                 'pan': 64,
                                 'reverb': 40,
                                 'chorus': 0,
                                 'delay': 0,
                                 'sense': 64,
                                 'shift': 64,
                                 'velocity': 0,
                                 'intensity': 0,
                                 'notes': []})

    def bytes(self, n):
        return self.mf[self.off: self.off + n]

    def extractbyte(self):
        value = self.mf[self.off]
        self.off += 1
        return value

    def extractbytes(self, n):
        values = []
        for i in range(n):
            values.append(self.mf[self.off])
            self.off += 1
        return values

    def extractshort(self):
        value = (self.mf[self.off] << 8) + self.mf[self.off + 1]
        self.off += 2
        return value

    def extractnumber(self):
        value = 0
        if self.mf[self.off] & 0x80:
            while True:
                value = (value << 7) + (self.mf[self.off] & 0x7f)
                if self.mf[self.off] & 0x80:
                    self.off += 1
                else:
                    break
        else:
            value = self.mf[self.off]
        self.off += 1
        return value

    def readevents(self):
        state = 0
        at = 0
        while True:
            delta = self.extractnumber()
            at += delta
            me = self.extractbyte()
            if me == 0xf0 or me == 0xf7:
                num_bytes = self.extractnumber()
                self.off += num_bytes
                if debug:
                    dbg('%06d System Exclusive (%d bytes)' % (at, num_bytes))
            elif me == 0xff:
                me_type = self.extractbyte()
                num_bytes = self.extractnumber()
                if me_type < 8:
                    text = self.extractbytes(num_bytes)
                    self.ev.append([at, me, me_type, text])
                    if debug:
                        dbg('%06d %s: %s' % (at, meta[me_type],
                                             printable(text)))
                elif me_type <= 0x0f:
                    self.ev.append(
                        [at, me, me_type, self.extractbytes(num_bytes)])
                elif me_type == 0x20:
                    byte1 = self.extractbyte()
                    self.ev.append([at, me, me_type, byte1])
                    if debug:
                        dbg('%06d Channel Prefix 0x%02x' % (at, byte1))
                elif me_type == 0x21:
                    byte1 = self.extractbyte()
                    self.ev.append([at, me, me_type, byte1])
                    if debug:
                        dbg('%06d Port Number 0x%02x' % (at, byte1))
                elif me_type == 0x2f:
                    if debug:
                        dbg('%06d End of Track' % at)
                    return
                elif me_type == 0x51:
                    data = self.extractbytes(3)
                    self.ev.append([at, me, me_type, data])
                    if debug:
                        tempo = (data[0] << 16) | (data[1] << 8) | data[2]
                        dbg('%06d Tempo 0x%02x 0x%02x 0x%02x (%d, %d bpm)' %
                            (at, data[0], data[1], data[2],
                             tempo, 60000000 // tempo))
                elif me_type == 0x58:
                    data = self.extractbytes(4)
                    self.ev.append([at, me, me_type, data])
                    if debug:
                        dbg('%06d Time 0x%02x 0x%02x 0x%02x 0x%02x' %
                            (at, data[0], data[1], data[2], data[3]))
                elif me_type == 0x59:
                    data = self.extractbytes(2)
                    self.ev.append([at, me, me_type, data])
                    if debug:
                        dbg('%06d Key 0x%02x 0x%02x' % (at, data[0], data[1]))
                else:
                    self.off += num_bytes
                    if debug:
                        dbg('%06d Meta Event 0x%02x (%d bytes)' %
                            (at, me_type, num_bytes))
            else:
                byte1 = me
                if byte1 & 0x80:
                    chan = byte1 & 0x0f
                    state = (byte1 >> 4) & 0x07
                    byte1 = self.extractbyte() & 0x7f
                if state < 7:
                    message = 0x80 | (state << 4) | chan
                    if state != 4 and state != 5:
                        byte2 = self.extractbyte() & 0x7f
                    else:
                        byte2 = 0
                    self.ev.append([at, message, byte1, byte2])
                    if debug:
                        if state in [0, 1]:
                            if chan != 9:
                                s = ' (%s%d)' % (notes[byte1 % 12], byte1 / 12)
                            else:
                                s = ' (%s)' % drum_instruments[byte1]
                        else:
                            s = ''
                        if state in [0, 1, 2, 3, 6]:
                            dbg('%06d %s 0x%02x 0x%02x 0x%02x%s' %
                                (at, messages[state], chan, byte1, byte2, s))
                        else:
                            dbg('%06d %s 0x%02x 0x%02x' %
                                (at, messages[state], chan, byte1))
                else:
                    print('Corrupt MIDI file')

    def read(self, path):
        self.path = os.path.basename(path)
        stream = open(path, 'rb')
        self.mf = bytearray(stream.read())
        if self.bytes(4) == b'MThd':
            self.off += 8
            self.format = self.extractshort()
            self.tracks = self.extractshort()
            self.division = self.extractshort()
        if debug:
            dbg('Format: %d, Tracks: %d, Division: %d' %
                (self.format, self.tracks, self.division))
        for track in range(self.tracks):
            if self.bytes(4) == b'MTrk':
                self.off += 8
                self.readevents()
            else:
                print('Missing track')
        stream.close()
        self.ev = sorted(self.ev, key=lambda tup: tup[0])
        self.playing_time = 0
        at = start = 0
        tempo = self.tempo
        for ev in self.ev:
            (at, message, me_type, data) = ev
            if message == 0xff and me_type == 0x51:
                self.playing_time += (at - start) * tempo / self.division / 1000
                start = at
                tempo = (data[0] << 16) | (data[1] << 8) | data[2]
        self.playing_time += (at - start)  * tempo / self.division / 1000

    def fileinfo(self):
        hsecs = self.playing_time // 10
        secs = hsecs // 100
        mins = secs // 60
        secs %= 60
        hsecs %= 100
        return \
            '%-12s     Format:  %d     Tracks:  %d    ' \
            'Playing Time:  %02d:%02d.%02d     Key:  %2s%1s/%-3d' % (
                self.path, self.format, self.tracks, mins, secs, hsecs,
                keys[self.key + 7], modes[self.mode],
                self.key_shift)

    def songinfo(self):
        if self.pause != 0:
            now = (self.pause - self.elapsed_time) * 1000
        else:
            now = (time() - self.elapsed_time) * 1000
        ticks = int(now * self.division * 1000 / self.tempo)
        hsecs = now / 10
        secs = hsecs / 100
        mins = secs / 60
        secs %= 60
        hsecs %= 100
        return \
            'Clock:  %02d:%02d.%02d   Song Position:  %04d:%02d:%03d   ' \
            'Tempo:  %3d bpm   Time:  %02d/%02d  %02d/%02d' % (
                mins, secs, hsecs,
                ticks / self.division / 4 + 1,
                ticks / self.division % self.numerator + 1,
                ticks * 1000 / self.division % 1000,
                self.bpm, self.numerator, self.denominator,
                self.clocks_per_beat, self.notes_per_quarter)

    # FAU 20201229: getsongposition added for EasyABC
    def getsongposition(self):
        if self.pause != 0:
            now = (self.pause - self.elapsed_time) * 1000
        else:
            now = (time() - self.elapsed_time) * 1000
        ticks = int(now * self.division * 1000 / self.tempo)
        return int(ticks)

    def beatinfo(self):
        if self.pause != 0:
            now = (self.pause - self.elapsed_time) * 1000
        else:
            now = (time() - self.elapsed_time) * 1000
        return int(now * 1000 / self.tempo)

    def lyrics(self):
        return '%-80s' % self.text

    def chordinfo(self):
        keys_pressed = 0
        for channel in range(16):
            info = self.channel[channel]
            if channel != 9 and info['family'] != 'Bass':
                for note in info['notes']:
                    keys_pressed |= (1 << (note % 12))
        if bin(keys_pressed).count("1") in [3, 4, 5]:
            for key in range(12):
                if keys_pressed in chords:
                    self.chord = '%-10s' % (
                        notes[key] + chords[keys_pressed] + '   ')
                    self.notes = []
                    for note in range(12):
                        if keys_pressed & (1 << note):
                            self.chord += '  %s' % notes[(key + note) % 12]
                            self.notes.append(60 + key + note)
                    self.chord = '%-50s' % self.chord
                    break
                if keys_pressed & 1:
                    keys_pressed |= (1 << 12)
                keys_pressed = (keys_pressed >> 1) & 0xfff
        return self.chord, self.notes

    def channelinfo(self, channel):
        return self.channel[channel]

    def writemidi(self, buf):
        start = 0
        if not gm1 and buf[0] < 0xf0:
            if buf[0] == self.status:
                start += 1
            else:
                self.status = buf[0]
        self.device.midievent(buf[start:])
        if debug:
            s = sep = ''
            for byte in buf[start:]:
                s += sep + '0x%02x' % byte
                sep = ' '
            print("%.3f %s" % (time() - self.start, s))

    def allnotesoff(self, channel):
        for note in self.channel[channel]['notes']:
            self.writemidi([0x80 + channel, note, 0])
        self.channel[channel]['notes'] = []

    def songposition(self, beat):
        self.next = 0
        for ev in self.ev:
            (at, message, byte1, byte2) = ev
            if at > beat * self.division:
                self.elapsed_time = time() - at / self.division / 1000000.0 * \
                    self.tempo
                break
            self.next += 1

    def gotosongposition(self, song_position):
        #Need to turn off all currently note played otherwise will keep sounding
        for ch in range(16):
            self.allnotesoff(ch)
        self.songposition(song_position)
        if self.pause != 0:
            self.pause = time()

    
    def setsong(self, **info):
        #print("FAU setsong")
        if 'shift' in info:
            for ch in range(16):
                self.allnotesoff(ch)
            self.key_shift += info['shift']
        elif 'bpm' in info:
            self.bpm += info['bpm']
            now = time()
            tempo = self.tempo
            self.tempo = 60000000 / self.bpm * 4 / self.denominator
            self.elapsed_time = now - (now - self.elapsed_time) * \
                self.tempo / tempo
        #FAU 20201229: option multibpm added for tempo multiplier of EasyABC
        elif 'multibpm' in info:
            #print("New Multi {}".format(info['multibpm']))
            self.bpm = self.bpm * info['multibpm'] / self.multibpm
            self.multibpm = info['multibpm']
            now = time()
            tempo = self.tempo
            self.tempo = 60000000 / self.bpm #* 4 / self.denominator
            self.elapsed_time = now - (now - self.elapsed_time) * \
                self.tempo / tempo
        elif 'goto' in info:
            self.gotosongposition(info['goto']/self.division)
        elif 'bar' in info:
            now = (time() - self.elapsed_time) * 1000
            beat = int(now * 1000 / self.tempo)
            beat += 4 * info['bar'] - (beat % 4)
            self.gotosongposition(beat)
        elif 'action' in info:
            if info['action'] == 'exit':
                for ch in range(16):
                    self.allnotesoff(ch)
                self.device.close()
            elif info['action'] == 'pause':
                #print("FAU pause/unpause {}".format(self.pause))
                if self.pause == 0:
                    self.pause = time()
                    self.writemidi([0xfc])
                    for ch in range(16):
                        self.allnotesoff(ch)
                else:
                    self.elapsed_time += time() - self.pause
                    self.pause = 0
                    self.writemidi([0xfb])

    def setchannel(self, channel, **info):
        if 'muted' in info:
            self.channel[channel]['muted'] = info['muted']
            if info['muted']:
                self.allnotesoff(channel)
        elif 'solo' in info:
            for ch in range(16):
                self.channel[ch]['muted'] = True if ch != channel else False
                if self.channel[ch]['muted']:
                    self.allnotesoff(ch)
        elif 'level' in info:
            self.channel[channel]['level'] = info['level']
            self.writemidi([0xb0 + channel, 7, info['level']])
        elif 'sense' in info:
            self.channel[channel]['sense'] = info['sense']
            block = (1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 10, 11, 12, 13, 14, 15)
            self.device.mididataset1(0x40101a + block[channel] << 8,
                                     info['sense'])
            sleep(0.04)
        elif 'delay' in info:
            self.channel[channel]['delay'] = info['delay']
            self.writemidi([0xb0 + channel, 94, info['delay']])
        elif 'chorus' in info:
            self.channel[channel]['chorus'] = info['chorus']
            self.writemidi([0xb0 + channel, 93, info['chorus']])
        elif 'reverb' in info:
            self.channel[channel]['reverb'] = info['reverb']
            self.writemidi([0xb0 + channel, 91, info['reverb']])
        elif 'pan' in info:
            self.channel[channel]['pan'] = info['pan']
            self.writemidi([0xb0 + channel, 10, info['pan']])
        elif 'instrument' in info:
            self.channel[channel]['instrument'] = info['instrument']
            self.channel[channel]['name'] = instruments[info['instrument']]
            self.writemidi([0xc0 + channel, info['instrument']])

    def timing(self, at):
        if at >= self.midi_clock:
            self.writemidi([0xf8])
            self.midi_clock += self.division / 24

    def play(self, dev, wait=True):
        if not self.start:
            self.device = dev
            self.device.mididataset1(0x40007f, 0x00)
            sleep(0.04)
            self.start = time()
            self.writemidi([0xfc, 0xfa])
            self.elapsed_time = self.start
            self.line = ''
        if self.pause != 0:
            return 0.04
        for ev in self.ev[self.next:]:
            (at, message, byte1, byte2) = ev
            now = time() - self.elapsed_time
            while at > now * self.division * 1000000 / self.tempo:
                self.timing(at)
                delta = (at - now * self.division * 1000000 / self.tempo) / \
                    1000
                delta = min(delta, 1.0 / (self.division / 24))
                if wait:
                    sleep(delta)
                    now = time() - self.elapsed_time
                else:
                    return delta
            self.timing(at)
            if message == 0xff:
                (at, message, me_type, data) = ev
                if me_type == 0x05:
                    if data[0] in [13, 10]:
                        self.line = ''
                    else:
                        if data[-1] in [13, 10]:
                            self.text = self.line + printable(data[:-1])
                            self.line = ''
                        else:
                            self.line += printable(data)
                            self.text = self.line
                elif me_type == 0x51:
                    now = time()
                    tempo = self.tempo
                    self.tempo = (data[0] << 16) | (data[1] << 8) | data[2]
                    self.tempo = self.tempo / self.multibpm
                    self.bpm = 60000000 / self.tempo * self.denominator / 4
                    self.elapsed_time = now - (now - self.elapsed_time) * \
                        self.tempo / tempo
                elif me_type == 0x58:
                    self.numerator = data[0]
                    self.denominator = 1 << data[1]
                    self.clocks_per_beat = data[2]
                    self.notes_per_quarter = data[3]
                elif me_type == 0x59:
                    self.key = data[0]
                    self.mode = data[1]
                    if self.key < -7 or self.key > 8:
                        self.key = 8
                    if self.mode < 0 or self.mode > 2:
                        self.mode = 2
            else:
                me_type = message & 0xf0
                channel = message & 0x0f
                info = self.channel[channel]
                info['used'] = True
                if me_type in [0x80, 0x90] and channel != 9:
                    byte1 += self.key_shift
                if me_type == 0x80:
                    if byte1 in info['notes']:
                        info['notes'].remove(byte1)
                    info['velocity'] = 0
                elif me_type == 0x90:
                    if byte2 != 0:
                        if byte1 in info['notes']:
                            print('Note retriggered')
                        else:
                            info['notes'].append(byte1)
                        if not info['muted']:
                            info['intensity'] = byte2
                    elif byte1 in info['notes']:
                        info['notes'].remove(byte1)
                    info['velocity'] = byte2
                elif me_type == 0xb0:
                    if byte1 == 0:
                        info['variation'] = byte2
                    elif byte1 == 32:
                        byte2 = 2
                    elif byte1 == 7:
                        info['level'] = byte2
                    elif byte1 == 10:
                        info['pan'] = byte2
                    elif byte1 == 91:
                        info['reverb'] = byte2
                    elif byte1 == 93:
                        info['chorus'] = byte2
                    elif byte1 == 94:
                        info['delay'] = byte2
                elif me_type == 0xc0:
                    info['name'] = instruments[byte1]
                    info['instrument'] = byte1
                    info['family'] = families[byte1 // 8]
                if not info['muted']:
                    if me_type != 0xc0:
                        self.writemidi([message, byte1, byte2])
                    else:
                        self.writemidi([message, byte1])
            self.next += 1
        self.writemidi([0xfc])
        return 0


def read(path):
    midi = SMF()
    midi.read(path)
    return midi


def play(midi, dev, wait=True):
    return midi.play(dev, wait)

#FAU20250125: Added to seek to a position
#songposition (time-elapsed_time)*1000*division*1000/tempo
#beat (time-elapsedtime)*1000*1000/tempo
#playing_time (at_fin - at_start) / self.division * tempo / 1000
    
def songposition(midi, song_position):
    return midi.songposition(song_position/midi.division)

def fileinfo(midi):
    return midi.fileinfo()


def songinfo(midi):
    return midi.songinfo()


def beatinfo(midi):
    return midi.beatinfo()


def lyrics(midi):
    return midi.lyrics()


def chordinfo(midi):
    return midi.chordinfo()


def setsong(midi, **info):
    midi.setsong(**info)


def channelinfo(midi, channel):
    return midi.channelinfo(channel)


def setchannel(midi, channel, **info):
    midi.setchannel(channel, **info)


if __name__ == '__main__':
    midi_file = read(sys.argv[1])
    midi_device = midiDevice()
    midi_device.mididataset1(0x400130, 0x04)
    play(midi_file, midi_device)
