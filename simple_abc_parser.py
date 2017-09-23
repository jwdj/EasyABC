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

from fractions import Fraction

key_data = \
       {'c':  ('#', 0), 'am':  ('#', 0), 'ddor':   ('#', 0),
        'f':  ('b', 1), 'dm':  ('b', 1), 'gdor':   ('#', 1),
        'bb': ('b', 2), 'gm':  ('b', 2), 'cdor':   ('#', 2),
        'eb': ('b', 3), 'cm':  ('b', 3), 'bbdor':  ('#', 3),
        'ab': ('b', 4), 'fm':  ('b', 4), 'ebdor':  ('#', 4),
        'db': ('b', 5), 'bbm': ('b', 5), 'abdor':  ('#', 5),
        'gb': ('b', 6), 'ebm': ('b', 6), 'abdor':  ('#', 6),
        'cb': ('b', 7), 'abm': ('b', 7), 'dbdor':  ('#', 7),
        'g':  ('#', 1), 'em':  ('#', 1), 'ador':   ('#', 0),
        'd':  ('#', 2), 'bm':  ('#', 2), 'edor':   ('#', 0),
        'a':  ('#', 3), 'f#m': ('#', 3), 'bdor':   ('#', 0),
        'e':  ('#', 4), 'c#m': ('#', 4), 'f#dor':  ('#', 0),
        'b':  ('#', 5), 'g#m': ('#', 5), 'c#dor':  ('#', 0),
        'f#': ('#', 6), 'd#m': ('#', 6), 'g#dor':  ('#', 0),
        'c#': ('#', 7), 'a#m': ('#', 7), 'c#dor':  ('#', 0),}

def get_base_note_for_key(key):
    key = key[:2]
    #print key, notes_sharp, notes_flat
    if key in notes_sharp:
        return notes_sharp.index(key)
    if key in notes_flat:
        return notes_flat.index(key)
    key = key[:1]
    if key in notes_sharp:
        return notes_sharp.index(key)
    if key in notes_flat:
        return notes_flat.index(key)
    raise Exception("error, incorrect key:%s" % key)

def get_best_key_for_midi_notes(notes):
    notes = [n % 12 for n in notes]
    penalty_key_tuples = []
    for key in key_data:
        accidentals = get_accidentals_for_key(key)
        basic_notes_in_key = [x+y for x,y in zip(doremi2chromatic, accidentals)]
        penalty = len([note for note in notes if not note in basic_notes_in_key])
        if notes[-1] != get_base_note_for_key(key):
            penalty += 2
        if key.endswith('dor'):
            penalty += 1
        penalty_key_tuples.append((penalty, key))
    penalty_key_tuples.sort()
    #print '\n'.join((str(x) for x in penalty_key_tuples))
    #print 'notes[-1]=', notes[-1]
    #print 'penalty', penalty_key_tuples[0][0]
    return penalty_key_tuples[0][1]  # key of the first (and best) item

def update_extra_accidentals_for_note(basic_accidentals, extra_accidentals, note):
    # merge the basic and extra accidentals and let the later have precedence over the former
    accidentals = [b if b is not None else a for a, b in zip(basic_accidentals, extra_accidentals)]

    basic_notes_in_key   = [x+y for x,y in zip(doremi2chromatic, basic_accidentals)]
    current_notes_in_key = [x+y for x,y in zip(doremi2chromatic, accidentals)]

    change = None

    #if not note in current_notes_in_key:
    #    if

    return { None: '',
             0:    '=',
            -1:    '_',
             1:     '^'}[change]

# map from do-re-mi scale index to chromatic interval
doremi2chromatic = [0, 2, 4, 5, 7, 9, 11, 13]

# map from note name to note number in a C scale
note2number = 'cdefgab'

notes_sharp = 'c c# d d# e f f# g g# a a# b'.split()
notes_flat  = 'c db d eb e f gb g ab a bb b'.split()

def get_accidentals(fifths):
    # determine the accidentals for one octave
    steps = 'C D E F G A B'.split()
    one_octave = [0] * 7
    if fifths > 0:
        for i in range(fifths):
            one_octave[(3 + i*4) % 7] = 1
    else:
        for i in range(fifths+1, 1):
            one_octave[(6 + i*4) % 7] = -1
    scale = []
    for i in range(7):
        scale.append(steps[i] + {-1: 'b', 0: '', 1:'#'}[one_octave[i]])
    print(' '.join(scale))

    # use the same for all octaves
    accidentals = {}
    for octave in range(1, 7):
        for step in range(7):
            note = '%s%s' % (steps[step], octave)  # eg. G4
            accidentals[note] = one_octave[step]
    return accidentals

def get_accidentals_for_key(key):
    ''' returns a list of seven values corresponding to the notes in the C scale. 1 means #, -1 means b, and 0 means no change. '''
    key = key.lower().strip().strip()
    sharp_or_flat, number = key_data[key]
    # initially no of the seven notes are flat or sharp (0=neutral)
    accidentals = [0] * 7
    # add accidentals
    for i in range(number):
        if sharp_or_flat == '#':
            accidentals[(3 - 3*i) % 7] = 1
        else:
            accidentals[(6 + 3*i) % 7] = -1
    return accidentals

class Note:
    def __init__(self, note, duration, ties_to_next=False, broken_rythm=''):
        self.note = note                   # number of semitones from centre note
        self.duration = duration           # duration expressed as a Fraction object
        self.ties_to_next = ties_to_next   # whether the abc representation of this note ended with '-' representing a tie to the next note
        self.broken_rythm = broken_rythm   # the ABC broken rythm symbol or an empty string
                                           # (used when the duration of the next note is established)
    def __repr__(self):
        ''' returns a string representation of this Note object '''
        notes = ('c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b')
        n = notes[self.note % 12].upper()
        octave = self.note / 12
        if octave > 0:
            if octave >= 1:
                n = n.lower()
            if octave > 1:
                n = n + "'" * (octave - 1)
        elif octave < 0:
            if abs(octave) > 1:
                n = n + "," * abs(octave)
        return n #+ str(self.duration)

    def __str__(self):
        return repr(self)

#print get_best_key_for_midi_notes([0, 2, 4, 6, 6, 6, 7, 0])
#print get_base_note_for_key('c')