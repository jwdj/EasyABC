from midi.MidiOutStream import MidiOutStream    # downloaded from: http://www.mxm.dk/products/public/pythonmidi
from midi.MidiInFile import MidiInFile
from midi.DataTypeConverters import fromBytes

class NoteOnHandler(MidiOutStream):

    def __init__(self):
        MidiOutStream.__init__(self)
        self.reset_time()
        self.CC = {}              # last CC value for every MIDI CC number
        self.offsets = []         # [(row, col, millisecond_midi_offset), ...]

    def reset_time(self):
        MidiOutStream.reset_time(self)
        self.abs_time_ms = 0      # time offset in milliseconds

    def update_time(self, new_time=0, relative=1):
        MidiOutStream.update_time(self, new_time, relative)
        if relative:
            if new_time != 0:     # ignore the 0 case since the tempo may not yet have been defined at that time
                self.abs_time_ms += self.tempo_value * new_time / (self.division * 1000.0)
        else:
            self.abs_time_ms = self.tempo_value * new_time / (self.division * 1000.0)

    def header(self, format=0, nTracks=1, division=96):
        self.division = division

    def tempo(self, value):
        self.tempo_value = value # tempo in us/quarternote

    def continuous_controller(self, channel, controller, value):
        if 110 <= controller <= 114:
            self.CC[controller] = value
        if controller == 114:
            row = (self.CC[110] << 14) | (self.CC[111] << 7) | (self.CC[112])
            col = (self.CC[113] << 7) | (self.CC[114])
            col -= 1   # make column zero-based
            self.offsets.append((row, col, self.abs_time_ms))

def midi_to_meta_data(midi_file_path):
    ''' returns a list: [(row, col, millisecond_midi_offset), ...] '''
    event_handler = NoteOnHandler()
    midi_in = MidiInFile(event_handler, midi_file_path)
    midi_in.read()
    return event_handler.offsets