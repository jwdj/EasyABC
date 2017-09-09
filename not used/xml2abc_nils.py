#!/usr/bin/python
#
#    xml2abc - a MusicXML to ABC converter - version 0.96
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
#    Usage:
#    >> python xml2abc.py mytune.xml
#
#   Version history:
#   2011-03-30: V0.90 - first version released into the wild
#   2011-04-02: V0.91 - added support for lyrics (only first voice used)
#                       ABC titles are extracted also from credits and work-title
#   2011-04-03: V0.92 - fixed identification of K-field. Now it also works for
#                       mixolydian, dorian, phrygian, lydian and locrian scales
#   2011-04-14: V0.93 - fixed bug due to incorrect indentation of debug statement.
#   2011-05-29: V0.94 - handle endings whose numbers have a trailing . (eg. '1.' instead of '1')
#   2011-08-07: V0.95 - take better care of stripping white-space from what will end up as T: fields
#   2012-05-08: V.0.96 - added support for Q-field
#                      - " characters in text annotations are now properly escaped
#

try:
    from xml.etree.ElementTree import ElementTree
except:
    from cElementTree import ElementTree # if python version < 2.5  (download this module from http://effbot.org/downloads/#celementtree)
import StringIO
from collections import defaultdict
from fraction import Fraction
import re
import os.path
import sys
import codecs
import types
import zipfile
stdout = codecs.getwriter('latin-1')(sys.stdout)

steps = 'C D E F G A B'.split()

# lookup xml duration name -> fraction of quarter note
name2duration = dict([(name, Fraction(1, 256)*2**i) for (i, name) in enumerate('256th,128th,64th,32nd,16th,eighth,quarter,half,whole,breve,long'.split(','))])

# maps from xml key/mode values to the corresponding ABC key mode
# and assuming a starting position of a normal major key how many scale notes to move up (positive) or down (negative)
# to reach the right base note of the key
key_mode_map = {
    'major':       ('',    0),
    'ionian':      ('',    0),
    'aeolian':     ('m',  -2),
    'minor':       ('m',  -2),
    'mixolydian':  ('Mix', 4),
    'dorian':      ('Dor', 1),
    'phrygian':    ('Phr', 2),
    'lydian':      ('Lyd', 3),
    'locrian':     ('Loc',-1),
}

# maps from xml ornaments/dynamics/fingering/technique etc (path relative to a note) to corresponding ABC markup
note_ornamentation_map = {
    'notations/ornaments/trill-mark':       'T',
    'notations/ornaments/mordent':          'M',
    'notations/ornaments/inverted-mordent': 'P',
    'notations/ornaments/turn':             '!turn!',
    'notations/ornaments/inverted-turn':    '!invertedturn!',
    'notations/dynamics/f':                 '!f!',
    'notations/dynamics/ff':                '!ff!',
    'notations/dynamics/fff':               '!fff!',
    'notations/dynamics/p':                 '!p!',
    'notations/dynamics/pp':                '!pp!',
    'notations/dynamics/ppp':               '!ppp!',
    'notations/technical/up-bow':           'u',
    'notations/technical/down-bow':         'v',
    'notations/technical/harmonic':         '!open!',
    'notations/technical/open-string':      '!open!',
    'notations/technical/stopped':          '!plus!',
    'notations/articulations/accent':       '!>!',
    'notations/articulations/strong-accent':'!>!',  # compromise
    'notations/articulations/staccato':     '.',
    'notations/articulations/staccatissimo':'!wedge!',    
    'notations/fermata':                    '!fermata!',
    'notations/articulations/tenuto':       '!tenuto!',
    'notations/articulations/staccatissimo':'!wedge!', # not sure whether this is the right translation
    'notations/articulations/spiccato':     '!wedge!', # not sure whether this is the right translation
    'notations/articulations/breath-mark':  '!breath!', # this may need to be tested to make sure it appears on the right side of the note
    'notations/articulations/detached-legato': '!tenuto!.',
    
}

harmony_kind_map = {
    'major' : '',
    'minor' : 'm',
    'diminished' : 'dim',
    'augmented' : '+',
    'suspended-fourth' : 'sus4',
    'suspended-second' : 'sus2',
    'dominant' : '',
    #'7','9'
}

chord_pattern = re.compile(r'^[A-G] ?([mM]aj|[mM]in|[mM]|[dD]im)?(5|6|7|9|aug|aug7|\+|dim|dim9|sus|sus9|7sus4|sus|sus9)?$')  # not perfect by any means, but should catch common chords

default_len = Fraction(1, 16)

class Note: # (or rest)
    def __init__(self, note_name, duration, displayed_duration, bar_number, bar_offset, is_grace_note, grace_slash):
        self.note_name = note_name
        self.duration = duration
        self.displayed_duration = displayed_duration  # eg. if this note is an eighth triplet then displayed_dur = eight and duration is the real duration
        self.bar_number = bar_number
        self.bar_offset = bar_offset
        self.accidental = ''
        self.is_grace_note = is_grace_note
        self.grace_slash = grace_slash
        self.tie = ''
        self.broken_rythm = ''
        self.slur_begin = ''
        self.slur_end = ''
        self.grace_begin = '' # not used
        self.grace_end = ''   # not used
        self.tuplet_begin = ''
        self.tuplet_end = False
        self.ornaments = ''
        self.trailing_space = ''  # a space or empty string

    def scale_duration_by(self, factor):
        self.duration = self.duration * factor
        self.displayed_duration = self.displayed_duration * factor

    def get_before_string(self):
        return u''.join(map(unicode, [self.grace_begin, self.slur_begin, self.tuplet_begin, self.ornaments]))
    def get_after_string(self):
        return u''.join(map(unicode, [self.tie, self.broken_rythm, self.slur_end, self.grace_end, self.trailing_space]))
        
    def __unicode__(self):
        global default_len
        if self.note_name in 'zx':
            n = self.note_name
        else:
            n, octave = re.match(r'^(.*?)(\d+)$', self.note_name).groups()
            octave = int(octave) - 4
            if octave > 0:
                if octave >= 1:
                    n = n.lower()
                if octave > 1:
                    n = n + "'" * (octave - 1)
            elif octave < 0:
                if abs(octave) >= 1:
                    n = n + "," * abs(octave)

        s = u''.join(map(unicode, [self.get_before_string(), 
                                   self.accidental, n, duration2abc(self.displayed_duration / default_len),
                                   self.get_after_string()]))        
        return s

class Chord(object):
    def __init__(self, notes):
        self.notes = notes
        self.before_string = u''
        self.after_string = u''

    def add(self, note):
        self.notes.append(note)

    def move_extras_outside_chord(self):
        for n in self.notes:
            self.before_string = self.before_string + n.get_before_string()
            self.after_string = self.after_string + n.get_after_string()
            n.grace_begin = ''
            n.slur_begin = ''
            n.tuplet_begin = ''
            n.ornaments = ''
            n.tie = ''
            n.broken_rythm = ''
            n.slur_end = ''
            n.grace_end = ''
            n.trailing_space = ''            
        
    @property
    def trailing_space(self):        
        return self.notes[0].trailing_space # all numbers should be the same so we use that of first note                

    @property
    def bar_number(self):        
        return self.notes[0].bar_number # all numbers should be the same so we use that of first note        

    @property
    def bar_offset(self):        
        return self.notes[0].bar_offset # all offsets should be the same so we use that of first note

    @property
    def duration(self):        
        return max([n.duration for n in self.notes])

    @property
    def displayed_duration(self):        
        return max([n.displayed_duration for n in self.notes])

    def scale_duration_by(self, factor):
        for n in self.notes:
            n.scale_duration_by(factor)

    def __unicode__(self):
        return '%s[%s]%s' % (self.before_string, ''.join(map(unicode, self.notes)), self.after_string)      

class Field:
    def __init__(self, field_name, field_value):        
        self.field_name = field_name
        lines = field_value.split('\n')
        self.field_value = u'\\\n'.join([x.strip() for x in lines])
    def __unicode__(self):        
        return '[%s:%s]' % (self.field_name, self.field_value)

def duration2abc(f):
    if f == Fraction(1,1):
        return ''
    elif f == Fraction(1,2):
        return '/'
    elif f == Fraction(1,4):
        return '//'    
    elif f.numerator == '1':
        return '/%d' % f.denumerator
    else:
        return str(f)

def get_accidentals(fifths):
    # determine the accidentals for one octave
    one_octave = [0] * 7
    if fifths > 0:
        for i in range(fifths):
            one_octave[(3 + i*4) % 7] = 1
    else:
        for i in range(fifths+1, 1):
            one_octave[(6 + i*4) % 7] = -1

    # use the same for all octaves
    accidentals = {}            
    for octave in range(1, 7):
        for step in range(7):            
            note = '%s%s' % (steps[step], octave)  # eg. G4
            accidentals[note] = one_octave[step]
    return accidentals

def get_key_name(fifths, base_note_distance):
    accidentals = get_accidentals(fifths)    
    base_note = (-fifths * 3 + base_note_distance + 7) % 7    
    note_name = steps[base_note] + '4' # (the 4 is since we need to specify some octave in the accidentals lookup)
    result = steps[base_note]
    if accidentals[note_name] == -1:
        result = result + 'b'
    elif accidentals[note_name] == 1:
        result = result + '#'
    return result

def introduce_grace_starts_and_ends(note_elements):    
    ''' add { } around grace notes and remove any explicit () sluring since this is implicit with ABC '''
    global default_len
    grace_mode = False               # currently inside { } ?
    slur_start_inside_grace = False  # was a slur started inside the last seen grace group
    result = []
    notes_in_current_grace_group = []
    for n in note_elements:
        if isinstance(n, Note):
            if n.is_grace_note and not grace_mode:
                if n.grace_slash:
                    result.append('{/')
                else:
                    result.append('{')
                slur_start_inside_grace = False
                
            elif not n.is_grace_note and grace_mode:
                result.append('}')                
                for n2 in notes_in_current_grace_group:                    
                    # special treatment of duration is needed since grace notes are independant of the default_len
                    #   a single grace note is displayed as 8th, and if there are more they are displayed as 16ths
                    if len(notes_in_current_grace_group) == 1:
                        n2.displayed_duration = n2.displayed_duration * default_len * 8
                    else:
                        n2.displayed_duration = n2.displayed_duration * default_len * 16                   
                notes_in_current_grace_group = []
                
            grace_mode = n.is_grace_note            

            if grace_mode and n.slur_begin:                
                n.slur_begin = ''
                slur_start_inside_grace = True
            elif not grace_mode and n.slur_end and slur_start_inside_grace:
                n.slur_end = n.slur_end.replace(')', '', 1)  # delete one ending slur
                slur_start_inside_grace = False
            if grace_mode:
                n.trailing_space = ''
                notes_in_current_grace_group.append(n)
            
        result.append(n)
    return result

def fix_chords(note_elements):
    for n in note_elements:
        if isinstance(n, Chord):
            n.move_extras_outside_chord()

def reset_whitespace(note_elements, introduce_new_lines=True):
    result = []
    last_note = None
    num_bars_on_line = 0
    for n in note_elements:
        result.append(n)
        if isinstance(n, Note):            
            n.trailing_space = ''
            if n.is_grace_note:
                continue            
            if last_note and last_note.bar_number == n.bar_number and int(n.bar_offset*4) != int(last_note.bar_offset*4):
                last_note.trailing_space = ' '
            last_note = n
        elif type(n) in (str, unicode) and '|' in n:
            num_bars_on_line += 1
            if num_bars_on_line > 4 and introduce_new_lines:
                result.append('\n')
                num_bars_on_line = 0
    note_elements[:] = result
            

def fix_slurs_before_repeat_ends(note_elements):
    last_note = None    
    for n in note_elements:
        if isinstance(n, Note):
            last_note = n
        elif type(n) in [str, unicode] and ':|' in n and last_note and last_note.slur_begin:
            last_note.slur_end = ''            

def introduce_broken_rythms(note_elements):
    prev = None
    result = []
    for n in note_elements:
        if hasattr(n, 'displayed_duration'):            
            if prev and not prev.trailing_space and n.bar_number == prev.bar_number:                
                if n.displayed_duration == prev.displayed_duration / 3:                    
                    prev.broken_rythm = '>'
                    prev.scale_duration_by(Fraction(2, 3))
                    n.scale_duration_by(Fraction(2, 1))
                elif n.displayed_duration == prev.displayed_duration * 3:                    
                    prev.broken_rythm = '<'
                    prev.scale_duration_by(Fraction(2, 1))
                    n.scale_duration_by(Fraction(2, 3))                                
            prev = n

def fix_barlines(note_elements):    
    result = []
    prev = None
    count = 0
    for n in note_elements:        
        if isinstance(n, types.StringTypes) and ('|' in n or '::' in n): # if bar ine
            count += 1
            if isinstance(prev, Note):
                prev.trailing_space = ''            
            elif isinstance(prev, types.StringTypes) and ('|' in prev or '::' in prev): # if bar ine
                result.pop()
                n = prev.strip(' ') + n                
                n = n.replace(':||:', '::').replace('||', '|').replace('|[', '|')                
                count -= 1

                if prev.strip(' ').endswith('\n'):            
                    n = n.replace('|1', '[1')                    
                    n = n.replace('|2', '[2')
            n = ' %s ' % n.strip(' ')
            ##if count % 4 == 0:
            ##    n = n + '\n'            
        result.append(n)
        prev = n    
    return result

def fix_tuplets(note_elements):    
    ''' if there are things like triplets with 4 notes in them use the proper 4:3:2 syntax '''            
    tuplet_notes = []
    for n in note_elements:
        if isinstance(n, Note):
            if n.tuplet_begin:
                tuplet_notes = [n]                
                slur_start_inside_grace = False
                
            elif tuplet_notes:                
                tuplet_notes.append(n)
                if n.tuplet_end:
                    first = tuplet_notes[0]
                    if tuplet_notes[0].tuplet_begin == '(3' and len(tuplet_notes) != 3:
                        # put 3 notes into the time of 2 for the next len(tuplet_notes) notes
                        tuplet_notes[0].tuplet_begin = '(3:2:%d' % len(tuplet_notes)                        
                    tuplet_notes = []
    return note_elements

def xml_harmony_to_abc(harmony_element):
    chord = ''
    harmony = harmony_element
    root = harmony.find('root')
    if root is not None:
        chord = root.findtext('root-step')
        alter = root.findtext('root-alter')
        if alter == '-1':
            chord = chord + 'b'
        elif alter == '1':
            chord = chord + '#'
        elif alter == '0':
            chord = chord + '='
    else:
        raise Exception('unknown harmony: %s' % harmony)
    chord = chord + (harmony.find('kind').get('text', '') or harmony_kind_map[harmony.findtext('kind')])
    return '"%s"' % chord

def debug_print(msg):
    pass
    #stdout.write(msg)

def mxl_to_xml(filename):
    ''' returns a file object pointing to the musicxml file inside the given .mxl file (zip file) '''
    zf = zipfile.ZipFile(filename)            
    first_file = ''
    # if there is any file with musicxml media-type, then use that. Otherwise load the first file.
    for rootfile in ElementTree().parse(zf.open('META-INF/container.xml')).findall('rootfiles/rootfile'):  # parse meta-data
        if 'musicxml' in rootfile.attrib.get('media-type', ''):
            return zf.open(rootfile.attrib['full-path'])
        else:
            first_file = first_file or rootfile.attrib['full-path']
    return zf.open(first_file)             

def process_early_directions(root):
    # In some XML files generated nwc2xml there are text directions that
    # come before the first clef/key/metre info. This goes against some assumptions
    # in the main code, so here we move all direction elements that come before the
    # first element that is neither <direction> nor <attributes> to just after that element.
    for part_no, part in enumerate(root.findall('part')):        
        measure = part.find('measure')
        if measure:
            extracted_direction_elements = []
            i = 0  # where to insert extracted elements
            for element in measure.getchildren()[:]:
                if element.tag == 'direction':
                    measure.remove(element)
                    i -= 1
                    extracted_direction_elements.append(element)                
                elif element.tag != 'attributes':
                    for de in reversed(extracted_direction_elements):
                        measure.insert(i, de)
                    break
                i += 1                                        

def xml_to_abc(filename):
    global default_len
    if os.path.splitext(filename)[1].lower() == '.mxl':        
        root = ElementTree().parse(mxl_to_xml(filename))
    else:
        root = ElementTree().parse(filename)    
        
    debug = False
    results_for_different_L_fields = []

    # Files converted from Noteworthy Composer (.nwc format) may have incorrect beams.
    # These files do not use begin/continue/end but rather just begin/continue for beams.
    encoding_software = root.find('identification/encoding/software')
    noteworthy_composer_mode = encoding_software is not None and encoding_software.text == 'Noteworthy Composer'
    if noteworthy_composer_mode:        
        process_early_directions(root)

    for L in [Fraction(1, 8), Fraction(1, 16)]:
        default_len = L
        tune_fields = []
        parts = []

        if root.findtext('work/work-title', ''):
            tune_fields.append(Field('T', root.findtext('work/work-title', '').strip()))
        if root.findtext('movement-title', ''):
            tune_fields.append(Field('T', root.findtext('movement-title', '').strip()))        
        for credit in root.findall('credit'):
            credits = ''.join(e.text or '' for e in credit.findall('credit-words'))
            credits = credits.translate(None, '\r\n')
            if credits.strip():
                tune_fields.append(Field('T', credits))        
        for creator in root.findall('identification/creator'):
            if creator.text:
                if creator.get('type') == 'composer':
                    for line in creator.text.split('\n'):
                        tune_fields.append(Field('S', line.strip()))
                elif creator.get('type') in ('lyricist', 'transcriber'):
                    text = creator.text
                    for line in text.split('\n'):
                        tune_fields.append(Field('Z', line.strip()))
        if noteworthy_composer_mode:  # no line breaks in xml from NoteWorthy Composer so use continueall
            tune_fields.append(Field('I', 'continueall'))

        num_parts = len(list(root.findall('part')))

        for part_no, part in enumerate(root.findall('part')):            
            accidentals = defaultdict(lambda: 0)
            measure_accidentals = accidentals
            cur_divisions = 768    
            bar_number = 0
            bar_offset = 0            

            lyric_numbers = sorted(set(lyric.get('number', '1') for lyric in part.findall('*/note/lyric')))
            lyrics = dict((lyric_number, []) for lyric_number in lyric_numbers)
            
            voice_names = sorted([voice.text for voice in part.findall('measure/note/voice')])
            if voice_names:
                first_voice = voice_names[0]
            else:
                first_voice = None
            voices = defaultdict(list)            
                
            num_staves = int(root.findtext('part/measure/attributes/staves', '1'))    
            for measure in part.findall('measure'):
                bar_number += 1
                bar_offset = 0
                last_measure_accidentals = measure_accidentals
                measure_accidentals = accidentals.copy()
                notes_with_accidentals_in_this_measure = set()                                
                
                for measure_element in measure.getchildren():        

                    # fields        
                    if measure_element.tag == 'attributes':
                        attributes = measure_element
                        for element in attributes.getiterator():
                            if element.tag == 'key':
                                # determine modal scale
                                mode, base_note_distance = key_mode_map.get(element.findtext('mode') or 'major', '')
                                
                                # insert new key in all voices
                                fifths = int(element.findtext('fifths'))
                                key_name = get_key_name(fifths, base_note_distance) + mode
                                field = Field('K', key_name)
                                if voices:
                                    for voice in voices.values():
                                        voice.append(field)
                                elif part_no == 0:                                    
                                    tune_fields.append(field)
                                    
                                # update accidentals
                                accidentals = get_accidentals(fifths)
                                measure_accidentals = accidentals.copy()
                                
                            elif element.tag == 'time':
                                metre = '%s/%s' % (element.findtext('beats'), element.findtext('beat-type'))
                                field = Field('M', metre)
                                if voices:
                                    for voice in voices.values():
                                        voice.append(field)
                                elif part_no == 0:
                                    tune_fields.append(field)                            
                                    
                            elif element.tag == 'divisions':
                                cur_divisions = int(element.text)

                    # tempo in BPM
                    elif measure_element.tag == 'sound':                        
                        if 'tempo' in measure_element.attrib:
                            tune_fields.append(Field('Q', measure_element.attrib['tempo']))                                

                    # notes                    
                    elif measure_element.tag == 'note':
                        note = measure_element
                        voice = note.findtext('voice')                        
                        
                        # name
                        if note.get('print-object') == 'no':
                            note_name = 'x'
                        elif note.find('rest') is not None:                  
                            note_name = 'z'
                        else:
                            note_name = note.findtext('pitch/step') + note.findtext('pitch/octave')

                        # duration and whether it's a grace note
                        is_grace_note = note.find('grace') is not None                
                        grace_slash = False
                        if is_grace_note:
                            duration = name2duration[note.findtext('type')]
                            grace_slash = note.find('grace').get('slash') == 'yes'                    
                        else:
                            duration = Fraction(int(note.findtext('duration')), cur_divisions) / 4
                            duration.reduce()

                        # find any time-modifications (due to tuplets) and rescale displayed duration accordingly
                        actual_notes = note.findtext('time-modification/actual-notes')
                        normal_notes = note.findtext('time-modification/normal-notes')
                        if actual_notes and normal_notes: # if time modification
                            time_modification = Fraction(int(actual_notes), int(normal_notes))
                        else:
                            time_modification = Fraction(1, 1)
                        displayed_duration = duration * time_modification

                        # create Note object                
                        n = Note(note_name, duration, displayed_duration, bar_number, bar_offset, is_grace_note, grace_slash)            

                        # tuplet                
                        tuplet = note.find('notations/tuplet')
                        if tuplet is not None:
                            if tuplet.get('type') == 'start':
                                actual_notes, normal_notes = int(actual_notes), int(normal_notes)
                                if actual_notes == 3 and normal_notes == 2:
                                    n.tuplet_begin = '(3'
                                elif actual_notes == 5:
                                    n.tuplet_begin = '(5'
                                else:
                                    raise Exception('unrecognized tuplet: %d/%d' % (actual_notes, normal_notes))
                                #n.tuplet_begin = '(%d' % int(Fraction(actual_notes, normal_notes) * 2)  # TODO: make more generally applicable
                            elif tuplet.get('type') == 'stop':
                                n.tuplet_end = True

                        # accidental
                        if not note_name in 'zx': # unless rest or invisible rest
                            alter = int(note.findtext('pitch/alter', '0'))                
                            if alter != measure_accidentals[note_name] or note.find('accidental') is not None:
                                n.accidental = {-2: '__',
                                                -1: '_',
                                                 0: '=',
                                                 1: '^',
                                                 2: '^^'}[alter]                                
                                measure_accidentals[note_name] = alter
                                notes_with_accidentals_in_this_measure.add(note_name)

                        # tie            
                        tie = note.find('tie')
                        if tie is not None and tie.get('type') == 'start':
                            n.tie = '-'

                        # slurs
                        for slur in note.findall('notations/slur'):
                            if slur.get('type') == 'start':
                                n.slur_begin = n.slur_begin + '('
                            if slur.get('type') == 'stop':
                                n.slur_end = n.slur_end + ')'                    

                        # ornaments
                        for key, value in note_ornamentation_map.items():
                            if note.find(key) is not None:
                                n.ornaments = n.ornaments + value

                        # fingering                                                
                        fingering = note.find('notations/technical/fingering')
                        if fingering is not None:
                            n.ornaments = '!%s!' % fingering.text + n.ornaments

                        # string
                        string = note.find('notations/technical/string')
                        if string is not None and string.text:
                            # add as a text annotation
                            if string.attrib.get('placement', 'above') == 'above':
                                n.before_string = '"^%s"' % string.text.strip() + n.before_string
                            else:
                                n.before_string = '"_%s"' % string.text.strip() + n.before_string
                            
                        # spacing due to beam ends or long notes
                        if not is_grace_note:
                            beams = [beam for beam in note.findall('beam') if beam.text in ['begin', 'continue', 'end']]
                            all_beams_end_here = beams and not [b for b in beams if b.text != 'end']                
                            if all_beams_end_here or duration >= Fraction(1, 4) or (duration < Fraction(1, 4) and len(beams)==0):
                                n.trailing_space = ' '
                                ##if duration < Fraction(1, 4) and len(beams)==0:
                                ##    n.trailing_space = ' !%s!' % len(beams)

                        # chord
                        if note.find('chord') is not None:
                            n.trailing_space = ''  # beam detection only works for first chord note, so erase any incorrectly generated space
                            last = voices[voice].pop()
                            if not isinstance(last, Chord):
                                last = Chord([last])
                            last.add(n)
                            n = last

                        # lyrics 
                        elif voice == first_voice and not is_grace_note and note_name not in 'zx':                            
                            for lyric_number in lyric_numbers:
                                lyrics_text = '*' # skip this note unless we find a lyric element that matches the current lyrics number
                                for lyric in note.findall('lyric'):                                                                        
                                    if lyric_number == lyric.get('number', '1'):
                                        # match found, so get the lyrics text (replace spaces and elision elements by '~')
                                        lyrics_text = ''
                                        for lyr_element in lyric:
                                            if lyr_element.tag == 'elision':
                                                lyrics_text = lyrics_text + '~'
                                            elif lyr_element.tag == 'text':
                                                lyrics_text = lyrics_text + (lyr_element.text or '').replace('-', r'\-').replace(' ', '~') # escape '-' characters
                                        # add - and _ characters
                                        if lyric.findtext('syllabic') in ['begin', 'middle']:
                                            lyrics_text = lyrics_text + '-'                                    
                                        if lyric.find('extend') is not None:                                        
                                            lyrics_text = lyrics_text.replace('*', '') + '_'
                                # if the current element is silence and the last element was '_', then discard the silence since the '_' covers this
                                if lyrics_text == '*' and lyrics[lyric_number] and lyrics[lyric_number][-1].endswith('_'):
                                    lyrics[lyric_number].append('')  # adding '' ensures that the if condition is not true next time around
                                else:
                                    lyrics[lyric_number].append(lyrics_text)                                                                
                        
                        # add note/chord to its voice            
                        voices[voice].append(n)                        
                                            
                        if not is_grace_note:
                            bar_offset += n.duration

                    # backup
                    elif measure_element.tag == 'backup':
                        duration = Fraction(int(measure_element.findtext('duration')), cur_divisions) / 4
                        duration.reduce()
                        bar_offset -= duration

                    elif measure_element.tag == 'barline':
                        for voice_name, voice in voices.items():                            
                            barline = measure_element
                            location = barline.get('location')
                            bar_style = barline.findtext('bar-style')
                            if bar_style == 'light-light':
                                s = '|-|'
                            elif bar_style == 'light-heavy':
                                s = '|]'
                            else:
                                s = '|'
                            repeat = barline.find('repeat')
                            if repeat is not None:
                                if repeat.get('direction') == 'forward':
                                    s = '|:'
                                else:
                                    s = ':|'                        

                            # handle segno, coda, fermata
                            ornament = None
                            if barline.find('segno'):
                                ornament = 'S'
                            elif barline.find('coda'):
                                ornament = 'O'
                            elif barline.find('fermata'):
                                ornament = 'H'
                            if ornament:
                                for voice in voices.values():
                                    voice.append(ornament)
                            
                            ending = barline.find('ending')
                            if ending is not None:
                                if ending.get('type') == 'start':                                    
                                    if part_no == 0 and voice_name == first_voice: # only read endings for first part since this is the way ABC handles it                                                
                                        text = ending.text or ending.get('number')
                                        if text is None:
                                            text = ''
                                        elif text.strip() in '1 2 3 4 5 6 1. 2. 3. 4. 5. 6.':
                                            text = text.replace('.', '') # delete any trailing dot after the ending number
                                        else:
                                            text = '"%s"' % text
                                        s = s + '[' + text
                                else:
                                    s = s + '|-|'
                                    
                            voice.append(s)                    
                            debug_print(s)

                    elif measure_element.tag == 'direction':
                        direction = measure_element
                        s = None
                        if direction.find('direction-type/coda') is not None:
                            s = 'O'
                        elif direction.find('direction-type/segno') is not None:
                            s = 'S'
                        elif direction.find('direction-type/words') is not None:
                            words = direction.find('direction-type/words')
                            offset = words.get('default-y')
                            text = direction.findtext('direction-type/words', '').strip()

                            # if this is just a numbering of the voice and it comes before key signature och metre info, then ignore it                            
                            if not voices and text.replace('"', '') == str(part_no+1):
                                text = ''                                
                            
                            text = text.replace('"', r'\u0022')  # add escape code for " characters
                            ##if text.lower() == 'fine':
                            ##    s = '!fine!'
                            ##elif text.upper() == 'D.C.':
                            ##    s = '!D.C.!'
                            ##elif text.upper() == 'D.S.':
                            ##    s = '!D.S.!'
                            
                            # up/down instruction encoded as a text direction
                            if noteworthy_composer_mode and text == 'u':
                                s = 'v'
                            elif noteworthy_composer_mode and text == 'd':
                                s = 'u'
                            # chord encoded as text
                            elif chord_pattern.match(text) and noteworthy_composer_mode:
                                s = '"%s"' % text

                            # Sibelius sometimes seems to use this for segno                                
                            elif text == '$':  
                                s = 'S'                            
                            elif offset and int(offset) < 0:
                                s = '"_%s"' % text
                            else:
                                s = '"^%s"' % text 
                            s = s.replace('\n', ' ')                                                            
                        if s:
                            #if s.startswith('"'):
                            voices[first_voice].append(s)
                            #else:                            
                            #    voices[voice].append(n)  

                    elif measure_element.tag == 'harmony':
                        voices['1'].append(xml_harmony_to_abc(measure_element))

                    elif measure_element.tag == 'print':
                        print_element = measure_element                
                        if print_element is not None and print_element.get('new-system') == 'yes':
                            for voice in voices.values():
                                voice[-1] = voice[-1] + '\n'
                            for lyrics_number in lyrics:
                                lyrics[lyrics_number].append('\n')

                for voice in voices.values():
                    voice.append('|')            
                debug_print('|')
                        
            for voice in voices:                
                fix_chords(voices[voice])
                fix_tuplets(voices[voice])
                voices[voice] = introduce_grace_starts_and_ends(voices[voice])
                voices[voice] = fix_barlines(voices[voice])                
                fix_slurs_before_repeat_ends(voices[voice])
                introduce_broken_rythms(voices[voice])                
                if noteworthy_composer_mode:  # beams in the XML aren't reliable in this case, so make it so that beams are always broken at quarters (might not be optimal for all metres)
                    reset_whitespace(voices[voice], introduce_new_lines = not any(lyrics.values()))                
            
            for voice_name, voice in sorted(voices.items()):
                if not voice_name and not voice:
                    continue
                s = ''.join(map(unicode, voice))                
                s = s.replace('|-|', '||').replace(':|||:', '::').replace('||:', '|:').replace(':||', ':|').replace('||[', '|[').replace('||[', '|[').replace('|-|', '||').replace('|||', '||').replace('|||', '||').replace(']|', ']').replace('|]|', '|]').strip()                
                if s.endswith('||'):
                    s = s[0:-2] + '|]'
                if s.startswith('"^"'):
                    s = s[3:]
                if num_parts > 1:
                    if voice_name:
                        voice_name = part.get('id') + '_' + str(voice_name)
                    else:
                        voice_name = part.get('id')
                # if this is the first voice, then pair up each line of note output with the lyrics lines (if there are any)
                if voice_name == first_voice:
                    result = []
                    notes_lines = s.split('\n')
                    lines_for_each_lyrics = [' '.join(lyrics[lyrics_number]).split('\n')
                                             for (lyrics_number, lyrics_parts) in sorted(lyrics.items())]
                    for line_no in range(len((notes_lines))):
                        result.append(notes_lines[line_no])                        
                        for lines in lines_for_each_lyrics:                            
                            if re.search(r'[^-*_ ]', lines[line_no]):  # if line is not empty
                                result.append('w: %s' % lines[line_no])                    
                    s = '\n'.join(result)
                parts.append(('V:%s' % str(voice_name), s))            


        file_numbers = [int(x) for x in re.findall(r'(\d+)', filename)]
        if file_numbers and 0 <= file_numbers[-1] <= 100000:
            tune_fields.insert(0, Field('X', str(file_numbers[-1])))
        else:
            tune_fields.insert(0, Field('X', '1'))
        tune_fields.append(Field('L', str(default_len)))
        ##tune_fields.append(Field('R', ''))
        ##tune_fields.append(Field('O', ''))
        output = StringIO.StringIO(u'')
        for f in tune_fields:
            if f.field_name != 'K':
                output.write(unicode(f).replace('[', '').replace(']', '') + '\n')        
        for f in tune_fields:
            if f.field_name == 'K':
                output.write(unicode(f).replace('[', '').replace(']', '') + '\n')
        if not [f for f in tune_fields if f.field_name == 'K']:
            output.write('K:C\n')
        for pname, p in parts:
            if len(parts) > 1 and pname:
                output.write(pname + '\n')
            lines = p.split('\n')
            for line in lines:
                output.write(line.strip() + '\n')
        results_for_different_L_fields.append(output.getvalue())

    # use the L-field that gives the shortest output (but add some extra penalty for using many '/' characters) 
    len_and_texts = [(len(s) + s.count('/')*0.15, s) for s in results_for_different_L_fields]  
    len_and_texts.sort()
    return len_and_texts[0][1]

if __name__ == '__main__':            
    for filename in sys.argv[1:]:        
        stdout.write(xml_to_abc(filename) + '\n\n')