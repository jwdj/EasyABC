import uuid  # 1.3.6.3 [JWdJ] 2015-04-22
from fractions import Fraction
import re

field_pattern = r'[A-Za-z\+]:'
meter_pattern = r'M:\s*(?:(\d+)/(\d+)|(C\|?))'
unitlength_pattern = r'^L:\s*(\d+)/(\d+)'

meter_re = re.compile(meter_pattern)
unitlength_re = re.compile(unitlength_pattern)
inline_meter_re = re.compile('\[{0}\]'.format(meter_pattern))
inline_unitlength_re = re.compile('\[{0}\]'.format(unitlength_pattern))
abc_field_re = re.compile(field_pattern)


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
        self.determine_abc_structure(abc_code)
        self.__tune_id = None

    def determine_abc_structure(self, abc_code):
        abc_lines = abc_code.splitlines()
        while len(abc_lines) > 0 and abc_lines[-1].strip() == '':
            abc_lines = abc_lines[:-1]  # remove empty lines at bottom

        abc_lines_enum = enumerate(abc_lines)

        x_found = False
        key_found = False

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
                    key_found = True
                    break

        if key_found:
            match_abc_field = abc_field_re.match
            note_line_indices = [i for i, line in abc_lines_enum if not line.startswith('%') and not match_abc_field(line)]
        else:
            note_line_indices = []

        if note_line_indices:
            self.first_note_line_index = note_line_indices[0]
        else:
            self.first_note_line_index = len(abc_lines)

        self.abc_lines = abc_lines
        self.note_line_indices = note_line_indices

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

