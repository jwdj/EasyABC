#!/usr/bin/python
#
#    Copyright (C) 2011 Nils Liberg (mail: kotorinl at yahoo.co.uk)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#    New in version 0.2:
#    better handling of accidentals in keys with many flats and sharps

from midi.MidiOutStream import MidiOutStream
from midi.MidiInFile import MidiInFile
from fractions import Fraction
import os
import os.path
import sys
import getopt
import math
from simple_abc_parser import get_best_key_for_midi_notes, get_accidentals_for_key
from io import StringIO

num_quarter_notes_per_bar = 3
bars_per_line = 4

usage = '''PyMidi2Abc version 0.1 May 30 2008, usage:

python pymidi2abc.py <options>
        [-f] <input file>
        -o <output file>
        -k <key signature> key name, or -6 to 6 sharps
        -l <default note length (L: field)>
        -m <time signature>
        --nbb no beam breaks
        --aux=<denominator of L: unit length>
        --nt Do not look for triplets or broken rhythm
        --s8 insert slurs on groups of 8th notes
        --s16 insert slurs on groups of 16th notes
        --bpl=<number> of bars printed per line
        --title=<string> Adds T: field containing string
        --origin=<string> Adds O: field containing string
'''


def time_to_note_length(time):
    # corresponds to the length of a 16th note (one forth of a quarter which corresponds to 1.0)
    unit_time = 0.25
    num = int(round(time / unit_time))
    length = Fraction(1, 16) * num
    return length


class Note:
    def __init__(self, start, end, note):
        self.start = start
        self.end = end
        self.note = note
        self.length = time_to_note_length(self.end - self.start)


class MidiHandler(MidiOutStream):
    def __init__(self, first_channel, last_channel):
        MidiOutStream.__init__(self)
        self.division = None
        self.first_channel = first_channel
        self.last_channel = last_channel
        self.noteon_time = {}
        self.notes = []

    def sysex_event(self, data):
        pass

    def time_signature(self, nn, dd, cc, bb):
        sig = Fraction(nn, 2**dd)

    def header(self, format=0, nTracks=1, division=96):
        self.division = division

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        if self.first_channel <= channel <= self.last_channel:
            self.noteon_time[note] = float(self.abs_time()) / self.division

    def note_off(self, channel=0, note=0x40, velocity=0x40):
        if self.first_channel <= channel <= self.last_channel:
            if note in self.noteon_time:
                end_time = float(self.abs_time()) / self.division
                self.notes.append(Note(self.noteon_time[note], end_time, note))


def is_triplet(notes):
    if len(notes) < 3:
        return False
    tolerance = 0.025
    for total_len in [1.0, 0.5]:
        if abs(notes[0].end - notes[1].start) < tolerance and \
           abs(notes[1].end - notes[2].start) < tolerance and \
           abs(notes[2].end - notes[0].start - total_len) < tolerance and \
           abs(notes[1].start - notes[0].start - total_len / 3) < tolerance:
            return True
    return False


def bar(time):
    global num_quarter_notes_per_bar
    return int(time / num_quarter_notes_per_bar + 0.003)


def bar_residue(time):
    global num_quarter_notes_per_bar
    return time - bar(time) * float(num_quarter_notes_per_bar)


def duration2abc(f):
    if f == Fraction(1, 1):
        return ''
    elif f == Fraction(1, 2):
        return '/'
    elif f == Fraction(1, 4):
        return '//'
    elif f.numerator == '1':
        return '/%d' % f.denumerator
    else:
        return str(f)


def note_to_string(note, duration, default_len, key_accidentals, cur_accidentals):
    n_accidentals = sum(key_accidentals)
    accidentals_to_scale = {
        7: '^B ^C ^^C ^D ^^D ^E ^F ^^F ^G ^^G ^A =B',
        6: '^B ^C ^^C ^D =E ^E ^F ^^F ^G ^^G ^A B',
        5: '^B ^C ^^C ^D E ^E ^F ^^F ^G =A ^A B',
        4: '^B ^C =D ^D E ^E ^F ^^F ^G A ^A B',
        3: '^B ^C D ^D E ^E ^F =G ^G A ^A B',
        2: '=C ^C D ^D E ^E ^F G ^G A ^A B',
        1: 'C ^C D ^D E =F ^F G ^G A ^A B',
        0: 'C ^C D ^D E F ^F G ^G A _B =B',
        -1: 'C ^C D _E =E F ^F G ^G A _B =B',
        -2: 'C ^C D _E =E F ^F G _A =A _B =B',
        -3: 'C _D =D _E =E F ^F G _A =A _B =B',
        -4: 'C _D =D _E =E F _G =G _A =A _B =B',
        -5: '=C _D =D _E =E F _G =G _A =A _B _C',
        -6: '=C _D =D _E _F =F _G =G _A =A _B _C',
        -7: '=C _D =D _E _F =F _G =G _A __B _B _C', }

    scale = accidentals_to_scale[n_accidentals].split()
    notes = [n.lower().translate(str.maketrans('', '', '_=^'))
             for n in scale]   # for semitone: the name of the note
    # for semitone: 0 if white key, -1 or -2 if flat, 1 or 2 if sharp
    accidentals = [n.count('^') - n.count('_') for n in scale]

    note_scale = 'CDEFGAB'
    middle_C = 60
    octave_note = (note - middle_C) % 12

    n = notes[octave_note].upper()
    accidental_num = accidentals[octave_note]
    accidental_string = ''
    scale_number = note_scale.index(n)
    if cur_accidentals[scale_number] != accidental_num:
        cur_accidentals[scale_number] = accidental_num
        accidental_string = {-1: '_', -2: '__',
                             0: '=', 1: '^', 2: '^^'}[accidental_num]

    octave = (note - middle_C) // 12

    # handle the border cases of Cb and B# to make sure that we use the right octave
    if octave_note == 11 and accidental_num == -1:
        octave += 1
    elif octave_note == 0 and accidental_num == 1:
        octave -= 1

    if octave > 0:
        if octave >= 1:
            n = n.lower()
        if octave > 1:
            n = n + "'" * int(octave - 1)
    elif octave < 0:
        if abs(octave) >= 1:
            n = n + "," * abs(octave)
    result = accidental_string + n
    shown_duration = duration / default_len
    if shown_duration != Fraction(1, 1):
        result = result + duration2abc(shown_duration)
    return result


def is_at_even(time, note_value):
    offset_in_16ths = time_to_note_length(bar_residue(time)) / note_value
    return offset_in_16ths.denominator == 1


def fix_lengths(notes):
    for i1 in range(0, len(notes)):
        for i2 in range(i1 + 1, len(notes)):
            # if the i2 note starts at a later time and there is a sufficiently large difference between either start times or end times
            if notes[i2].start > notes[i1].start and abs(notes[i2].start - notes[i1].start) + abs(notes[i2].end - notes[i1].end) > 0.25:
                notes[i1].end = notes[i2].start
                notes[i1].length = time_to_note_length(
                    notes[i1].end - notes[i1].start)  # update length
                break


def midi_to_abc(filename=None, notes=None, key=None, metre=Fraction(3, 4), default_len=Fraction(1, 16), bars_per_line=4, title='', source='', no_triplets=False, no_broken_rythms=False, slur_8th_pairs=False, slur_16th_pairs=False, slur_triplets=True, no_beam_breaks=False, index='1', anacrusis_notes=0):
    global num_quarter_notes_per_bar
    num_quarter_notes_per_bar = metre * 4  # int(metre * 4)

    if filename and not notes:
        # read midi notes
        handler1 = MidiHandler(0, 15)  # channels 0-15
        # handler1 = MidiHandler(0, 0)  # channels 0-15
        MidiInFile(handler1, filename).read()
        notes = handler1.notes
    elif not filename and not notes:
        raise Exception(
            'midi_to_abc needs to be passed either a filename or a notes argument')

    # sequence of Note(start, end, note)
    notes = sorted(notes, key=lambda n: n.start)
    fix_lengths(notes)

    # determine key and accidentals
    if not key:
        key = get_best_key_for_midi_notes([note.note for note in notes])
    key_accidentals = get_accidentals_for_key(key)
    cur_accidentals = key_accidentals[:]

    output = StringIO()
    output.write(u'X:%s\n' % index)
    if source:
        output.write(u'S:%s\n' % source)
    if title:
        output.write(u'T:%s\n' % title)
    output.write(u'M:%s\n' % metre)
    output.write(u'L:%s\n' % default_len)
    output.write(u'K:%s\n' % key.capitalize())

    # initialize variables used in loop
    last_note_start = -1.0
    bow_started = False
    broken_rythm_factor = Fraction(1, 1)
    num_notes = len(notes)
    bar_num = -1

    if anacrusis_notes:
        time_shift = 4 * float(metre) - notes[anacrusis_notes].start
        # print notes[0].start, notes[1].start, notes[2].start
        # print 'shift', time_shift
        for n in notes:
            n.start += time_shift
            n.end += time_shift

    # don't count the first bar if it's an upbeat (to get equal number of bars on each line)
    inside_upbeat = (notes and bar_residue(
        notes[0].start) > 1.0) or anacrusis_notes

    while notes:
        # if current note is in a different bar than the last one, emit '|'
        if bar(notes[0].start) > bar(last_note_start):
            if len(notes) != num_notes:
                output.write(u' |')
                cur_accidentals = key_accidentals[:]
            if not inside_upbeat:
                bar_num += 1
            inside_upbeat = False
            if bar_num % bars_per_line == 0 and bar_num > 0:
                output.write(u'\n')

        # if we have advanced the length of a quarter note, emit space (for note grouping)
        br = bar_residue(notes[0].start)
        if is_at_even(notes[0].start, Fraction(1, 4)) and not no_beam_breaks:
            output.write(u' ')

        # check if next three notes can be interpreted as a triplet
        if is_triplet(notes) and not no_triplets:
            length = time_to_note_length(notes[2].end - notes[0].start)
            _notes = [n.note for n in notes[:3]]

            # convert notes to string representation
            s = u'(3' + ''.join([note_to_string(n.note, n.length * 2,
                                                default_len, key_accidentals, cur_accidentals) for n in notes[:3]])
            if slur_triplets:
                s = u'(' + s + ')'
            output.write(s)

            last_note_start = notes[0].start
            notes = notes[3:]

        # else handle notes one by one or as a chord
        else:
            is_four_16th_notes = len(
                [n for n in notes[0:4] if n.length == Fraction(1, 16)]) == 4
            # either two eights or two eights with broken rythm
            is_two_8th_notes = (len([n for n in notes[0:2] if n.length == Fraction(1, 8)]) == 2 or
                                len(notes) >= 2 and (notes[0].length, notes[1].length) in [(Fraction(3, 16), Fraction(1, 16)),
                                                                                           (Fraction(1, 16), Fraction(3, 16))])

            note = notes.pop(0)
            last_note_start = note.start

            # build a chord from notes near each other in time (will result in just one element in the non-chord case)
            chord_notes = [note.note]
            while notes and abs(notes[0].start - note.start) < 1.0 / 50:
                chord_notes.append(notes.pop(0).note)

            # let the duration of the first note determine the chord's duration (for simplicity)
            length = note.length

            # if the current note is the first of four 16th notes then add a bow on the two first notes
            bow_started_here = False
            if notes and abs(br - int(br)) < 1.0 / 20 and not bow_started and is_four_16th_notes and slur_16th_pairs:
                bow_started_here = True
                bow_started = True
                output.write(u'(')
            elif notes and abs(br - int(br)) < 1.0 / 20 and not bow_started and is_two_8th_notes and slur_8th_pairs and br < 2.0:
                bow_started_here = True
                bow_started = True
                output.write(u'(')

            # check if it's possible to use a broken rytm (< or >) between the current and next note/chord
            broken_rythm_symbol = ''
            if not no_broken_rythms:
                # a broken rythm was activated at the previous note
                if broken_rythm_factor != Fraction(1, 1):
                    length = length * broken_rythm_factor
                    broken_rythm_factor = Fraction(1, 1)
                elif notes and is_at_even(last_note_start, Fraction(1, 8)) and bar(last_note_start) == bar(notes[0].start):
                    # use > between this and next note
                    if notes[0].length == length / 3:
                        broken_rythm_symbol = '>'
                        length = length * Fraction(2, 3)
                        broken_rythm_factor = Fraction(2, 1)
                    # use < between this and next note
                    if notes[0].length == length * 3:
                        broken_rythm_symbol = '<'
                        length = length * Fraction(2, 1)
                        broken_rythm_factor = Fraction(2, 3)

            # convert notes to string representation and output
            s = u''.join([note_to_string(n, length, default_len,
                                         key_accidentals, cur_accidentals) for n in chord_notes])
            if len(chord_notes) > 1:
                s = u'[' + s + ']'  # wrap chord
            output.write(s)

            # output broken rythm symbol if set
            if broken_rythm_symbol:
                output.write(str(broken_rythm_symbol))

            # if a bow was previously started end it here
            if bow_started and not bow_started_here:
                output.write(u')')
                bow_started = False

            # print 'note', note.start, length, chord_notes, '%.2f' % last_note_start, bar(last_note_start), '%.2f' % bar_residue(last_note_start)#, note.note

    output.write(u' |')
    output.write(u'\n')

    # left strip lines
    lines = output.getvalue().split('\n')
    lines = [l.lstrip() for l in lines]
    return u'\n'.join(lines)


def main(argv):
    # setup default values
    filename = ''
    output_filename = ''
    key = None
    default_len = Fraction(1, 16)
    metre = Fraction(3, 4)
    bars_per_line = 4
    title = ''
    source = ''
    no_triplets = False
    no_broken_rythms = False
    slur_8th_pairs = False
    slur_16th_pairs = False
    no_beam_breaks = False

    # if a single parameter was given and it's a path to an existing file use it as filename
    if len(argv) == 1 and os.path.exists(argv[0]):
        filename = argv[0]

    # otherwise interpret options
    else:
        try:
            opts, args = getopt.getopt(argv, 'hm:k:f:o:l:', ['help', 'metre=', 'key=', 'bpl=',
                                                             'file=', 'outfile=', 'length=', 'bpl=',
                                                             'title=', 'source=', 'nbb', 'nt', 's8', 's16', 'aux='])
        except getopt.GetoptError:
            print(usage)
            sys.exit(2)

        for opt, arg in opts:
            try:
                if opt in ('-h', '--help'):
                    print(usage)
                    sys.exit()
                elif opt in ('-m', '--metre'):
                    x, y = map(int, arg.split('/'))
                    metre = Fraction(x, y)
                elif opt in ('-k', '--key'):
                    try:
                        k = int(arg)
                        key = {-7: 'cb',
                               -6: 'gb',
                               -5: 'db',
                               -4: 'ab',
                               -3: 'eb',
                               -2: 'bb',
                               -1: 'f',
                               0: 'c',
                               1: 'g',
                               2: 'd',
                               3: 'a',
                               4: 'e',
                               5: 'b',
                               6: 'f#',
                               7: 'c#'}[k]
                    except ValueError:
                        key = arg.lower()
                elif opt in ('--bpl',):
                    bars_per_line = int(arg)
                elif opt in ('--title',):
                    title = arg
                elif opt in ('--source',):
                    source = arg
                elif opt in ('--aux',):
                    default_len = Fraction(1, int(arg))
                elif opt in ('-l', '--length',):
                    x, y = map(int, arg.split('/'))
                    default_len = Fraction(x, y)
                elif opt in ('--nt'):
                    no_triplets = True
                    no_broken_rythms = True
                elif opt in ('--nbb'):
                    no_beam_breaks = True
                elif opt in ('--s8'):
                    slur_8th_pairs = True
                elif opt in ('--s16'):
                    slur_16th_pairs = True
                elif opt in ('-f',):
                    filename = arg
                elif opt in ('-o',):
                    output_filename = arg
            except Exception:
                print('Error parsing argument: %s' % opt)
                print(usage)
                sys.exit(2)

    if not filename:
        print('Error: filename (-f) required!')
        print(usage)
        sys.exit(2)

    # do midi to abc conversion
    result = midi_to_abc(filename, None, key, metre, default_len, bars_per_line, title, source,
                         no_triplets, no_broken_rythms, slur_8th_pairs, slur_16th_pairs, no_beam_breaks=no_beam_breaks)

    # output to stdout or file
    if output_filename:
        open(output_filename, 'w').write(result)
    else:
        print(result)


if __name__ == '__main__':
    main(sys.argv[1:])
