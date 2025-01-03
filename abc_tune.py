import uuid  # 1.3.6.3 [JWdJ] 2015-04-22
from fractions import Fraction
from abc_character_encoding import abc_text_to_unicode, decode_abc
from collections import defaultdict
import re
import sys
PY3 = sys.version_info.major >= 3
if PY3:
    unicode = str

field_pattern = r'[A-Za-z\+]:'
meter_pattern = r'M:\s*(?:(\d+)/(\d+)|(C\|?))'
unitlength_pattern = r'^L:\s*(\d+)/(\d+)'
voice_pattern = r'(?m)(?:^V:\s*(?P<voice_id>\w+).*$|\[V:\s*(?P<inline_voice_id>\w+)[^\]]*\])'
comment_pattern = r'(?m)(?<!\\)%.*$'
empty_line_pattern = r'(?m)^\s*$'

meter_re = re.compile(meter_pattern)
unitlength_re = re.compile(unitlength_pattern)
inline_meter_re = re.compile(r'\[{0}\]'.format(meter_pattern))
inline_unitlength_re = re.compile(r'\[{0}\]'.format(unitlength_pattern))
abc_field_re = re.compile(field_pattern)
voice_re = re.compile(voice_pattern)
comment_re = re.compile(comment_pattern)
empty_line_re = re.compile(empty_line_pattern)


def find_start_of_tune(abc_text, pos):
    """ A tune always starts with X: """
    while pos > 0:
        pos = abc_text.rfind('X:', 0, pos)
        if pos <= 0 or abc_text[pos - 1] == '\n':
            break
    return pos

def find_end_of_tune(abc_text, pos):
    """ A tune ends with an empty line or when end of file """
    match = empty_line_re.search(abc_text, pos)
    if match:
        return match.start()
    return len(abc_text)

def strip_comments(abc_text):
    return comment_re.sub('', abc_text)

def get_tune_title_at_pos(abc_text, pos):
    title = ''
    title_tag = '\nT:'
    title_start = abc_text.find(title_tag, pos)
    while title_start >= 0:
        title_start += len(title_tag)
        end_of_line = abc_text.find('\n', title_start)
        line = abc_text[title_start:end_of_line]
        if title:
            title += ' - '
        title += strip_comments(line).strip()

        title_start = -1
        if abc_text[end_of_line:end_of_line + len(title_tag)] == title_tag:
            title_start = end_of_line
    return decode_abc(title)

def match_to_meter(m, default):
    metre = default
    if m.group(1) is not None:
        metre = Fraction(int(m.group(1)), int(m.group(2)))
    elif m.group(3) == 'C':
        metre = Fraction(4, 4)
    elif m.group(3) == 'C|':
        metre = Fraction(2, 2)
    return metre

base_notes = 'C D E F G A B c d e f g a b'.split()

def note_to_number(abc_note):
    num = base_notes.index(abc_note[0])
    for i in range(1, len(abc_note)):
        if abc_note[i] == '\'':
            num += 7
        elif abc_note[i] == ',':
            num -= 7
    return num

def number_to_note(num):
    octaves_up = 0
    octaves_down = 0
    while num < 0:
        octaves_down += 1
        num += 7
    while num >= len(base_notes):
        octaves_up += 1
        num -= 7
    return base_notes[num] + '\'' * octaves_up + ',' * octaves_down

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
        abc_lines = abc_code.strip().splitlines()
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

    def get_voice_ids(self):
        return [m.group('voice_id') or m.group('inline_voice_id') for m in voice_re.finditer('\n'.join(self.tune_header))]

    def get_abc_per_voice(self):
        if self.__abc_per_voice is None:
            if self.tune_body_start_line_index:
                abc_body = '\n'.join(self.tune_body)
                voices = defaultdict(unicode)
                last_voice_id = ''
                start_index = 0
                for m in voice_re.finditer(abc_body):
                    voice_id = m.group('voice_id') or m.group('inline_voice_id')
                    abc = abc_body[start_index:m.start()]
                    voices[last_voice_id] += abc
                    start_index = m.end()
                    last_voice_id = voice_id

                abc = abc_body[start_index:]
                voices[last_voice_id] += abc
                self.__abc_per_voice = voices
            else:
                self.__abc_per_voice = {}

        return self.__abc_per_voice

    @property
    def tune_id(self):
        if self.__tune_id is None:
            self.__tune_id = uuid.uuid4()
        return self.__tune_id

    @property
    def tune_body(self):
        return self.abc_lines[self.tune_body_start_line_index:]

    @property
    def tune_header(self):
        end_line = None
        if self.tune_body_start_line_index is not None:
            end_line = self.tune_body_start_line_index
        return self.abc_lines[self.tune_header_start_line_index:end_line]

    @property
    def initial_tonic_and_mode(self):
        key_line = self.tune_header[-1]
        m = re.match(r'K: ?(?P<tonic>(?:[A-G][b#]?|none)) ?(?P<mode>(?:[MmDdPpLl][A-Za-z]*)?)', key_line)
        if m:
            return (m.group('tonic'), m.group('mode'))

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

        try:
            if self.is_gracenote_at(row, col):
                return None # abcm2ps does not mark notes within braces

            start_of_chord = self.get_start_of_chord(row, col)
            if start_of_chord:
                return start_of_chord - 1 # svg_col is 1-based

            if line[col-1] in '~.HIJKLMNOPQRSTUVWhijklmnopqrstuvw':
                return col # in case of one letter symbol: abc2midi marks the symbol, abcm2ps marks the after note after the dot

            return col-1
        except:
            return None
