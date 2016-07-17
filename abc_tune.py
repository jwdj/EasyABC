import uuid  # 1.3.6.3 [JWdJ] 2015-04-22
from fractions import Fraction
from abc_character_encoding import abc_text_to_unicode
from collections import defaultdict
import re
import sys
PY3 = sys.version_info.major > 2
if PY3:
    unicode = str

field_pattern = r'[A-Za-z\+]:'
meter_pattern = r'M:\s*(?:(\d+)/(\d+)|(C\|?))'
unitlength_pattern = r'^L:\s*(\d+)/(\d+)'
voice_pattern = r'(?m)(?:^V:\s*(?P<name>\w+).*$\n|\[V:\s*(?P<inlinename>\w+)[^\]]*\])'

meter_re = re.compile(meter_pattern)
unitlength_re = re.compile(unitlength_pattern)
inline_meter_re = re.compile('\[{0}\]'.format(meter_pattern))
inline_unitlength_re = re.compile('\[{0}\]'.format(unitlength_pattern))
abc_field_re = re.compile(field_pattern)
voice_re = re.compile(voice_pattern)

def match_to_meter(m, default):
    metre = default
    if m.group(1) is not None:
        metre = Fraction(int(m.group(1)), int(m.group(2)))
    elif m.group(3) == 'C':
        metre = Fraction(4, 4)
    elif m.group(3) == 'C|':
        metre = Fraction(2, 2)
    return metre


# 1.3.6.3 [JWdJ] renamed BaseTune to AbcTune and added functions
class AbcTune(object):
    """ Class for dissecting abc tune structure """
    def __init__(self, abc_code):
        self.abc_code = abc_code
        self.x_number = None
        self.tune_header_start_line_index = None
        self.tune_body_start_line_index = None
        self.determine_abc_structure(abc_code)
        self.__tune_id = None
        self.__abc_per_voice = None

    def determine_abc_structure(self, abc_code):
        abc_lines = abc_code.splitlines()
        while len(abc_lines) > 0 and abc_lines[-1].strip() == '':
            abc_lines = abc_lines[:-1]  # remove empty lines at bottom

        abc_lines_enum = enumerate(abc_lines)

        x_found = False
        body_start_line_index = None

        for i, line in abc_lines_enum:
            if line.startswith('X:'):
                m = re.search(r'\d+', line)
                if m:
                    self.x_number = int(m.group(0))
                self.tune_header_start_line_index = i
                x_found = True
                break

        if x_found:
            for i, line in abc_lines_enum:
                if line.startswith('K:'):
                    body_start_line_index = i + 1 # K-field is the last line of the header
                    break

        if body_start_line_index is not None:
            match_abc_field = abc_field_re.match
            note_line_indices = [i for i, line in abc_lines_enum if not line.startswith('%') and not match_abc_field(line)]
        else:
            note_line_indices = []

        if note_line_indices:
            self.first_note_line_index = note_line_indices[0]
        else:
            self.first_note_line_index = len(abc_lines)

        self.tune_body_start_line_index = body_start_line_index
        self.abc_lines = abc_lines
        self.note_line_indices = note_line_indices
        
    def get_abc_per_voice(self):
        if self.__abc_per_voice is None:
            if self.tune_body_start_line_index:
                abc_body = '\n'.join(self.abc_lines[self.tune_body_start_line_index:])
                voices = defaultdict(unicode)
                last_voice_name = ''
                start_index = 0
                for m in voice_re.finditer(abc_body):
                    name = m.group('name') or m.group('inlinename')
                    abc = abc_body[start_index:m.start()]
                    voices[last_voice_name] += abc
                    start_index = m.end()
                    last_voice_name = name

                abc = abc_body[start_index:]
                voices[last_voice_name] += abc
                self.__abc_per_voice = voices
            else:
                self.__abc_per_voice = {}

        return self.__abc_per_voice

    @property
    def tune_id(self):
        if self.__tune_id is None:
            self.__tune_id = uuid.uuid4()
        return self.__tune_id

    def get_metre_and_default_length(self):
        lines = self.abc_lines
        default_len = Fraction(1, 8)
        metre = Fraction(4, 4)
        # 1.3.7 [JWdJ] 2016-01-06
        for line in lines:
            m = meter_re.match(line)
            if m:
                metre = match_to_meter(m, metre)

            for m in inline_meter_re.finditer(line):
                metre = match_to_meter(m, metre)

            m = unitlength_re.match(line)
            if m:
                default_len = Fraction(int(m.group(1)), int(m.group(2)))

            for m in inline_unitlength_re.finditer(line):
                default_len = Fraction(int(m.group(1)), int(m.group(2)))

        return metre, default_len

    def is_equal(self, abc_tune):
        if not isinstance(abc_tune, AbcTune):
            return False
        return self.x_number == abc_tune.x_number \
               and self.tune_header_start_line_index == abc_tune.tune_header_start_line_index \
               and self.first_note_line_index == abc_tune.first_note_line_index
    
    def is_gracenote_at(self, row, col):
        line = self.abc_lines[row-1]
        i = col - 1
        while i >= 0:
            ch = line[i]
            if ch == '}' or ch == '|':
                return False
            if ch == '{':
                return True
            i -= 1
        return False

    def get_start_of_chord(self, row, col):
        line = self.abc_lines[row-1]
        i = col - 1
        while i >= 0:
            ch = line[i]
            if ch == ']' or ch == '|':
                return None
            elif ch == '[':
                return i + 1
            i -= 1
        return None
    
    @staticmethod
    def byte_to_unicode_index(text, index):
        return len(abc_text_to_unicode(text[:index]).encode('utf-8'))
    
    def midi_col_to_svg_col(self, row, col):
        line = self.abc_lines[row-1]
        col = self.byte_to_unicode_index(line, col-1) + 1 # compensate for encoding differences
        
        if self.is_gracenote_at(row, col):
            return None # abcm2ps does not mark notes within braces 

        start_of_chord = self.get_start_of_chord(row, col) 
        if start_of_chord:
            return start_of_chord - 1 # svg_col is 1-based
        
        if line[col-1] in '~.HIJKLMNOPQRSTUVWhijklmnopqrstuvw':
            return col # in case of one letter symbol: abc2midi marks the symbol, abcm2ps marks the after note after the dot
            
        return col-1
            
