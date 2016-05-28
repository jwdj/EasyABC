import uuid  # 1.3.6.3 [JWdJ] 2015-04-22
from fractions import Fraction
import re


# 1.3.6.3 [JWdJ] renamed BaseTune to AbcTune and added functions
class AbcTune(object):
    """ Class for dissecting abc tune structure """
    def __init__(self, abc_code):
        self.__abc_code = abc_code
        self.__abc_lines = None
        self.__tune_header_start_line_index = None
        self.__first_note_line_index = None
        self.__tune_id = None

    @property
    def abc_code(self):
        return self.__abc_code

    @property
    def abc_lines(self):
        if self.__abc_lines is None:
            self.__abc_lines = self.abc_code.splitlines()
        return self.__abc_lines

    @property
    def first_note_line_index(self):
        if self.__first_note_line_index is None:
            line_no = 1  # start with 1 because body starts 1 line after K field
            for line in iter(self.abc_lines):
                if line.startswith('K:'):
                    self.__first_note_line_index = line_no
                    break
                line_no += 1

        return self.__first_note_line_index

    @property
    def tune_header_start_line_index(self):
        if self.__tune_header_start_line_index is None:
            line_no = 0  # start with 0 because header starts with the X field
            for line in iter(self.abc_lines):
                if line.startswith('X:'):
                    self.__tune_header_start_line_index = line_no
                    break
                line_no += 1
        return self.__tune_header_start_line_index

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
        meter_pattern = r'M:\s*(?:(\d+)/(\d+)|(C\|?))'
        for line in lines:
            m = re.match(r'^L:\s*(\d+)/(\d+)', line)
            if m:
                default_len = Fraction(int(m.group(1)), int(m.group(2)))
            m = re.search(r'^{0}'.format(meter_pattern), line)
            if m:
                # 1.3.7 [JWdJ] 2016-01-06
                if m.group(1) is not None:
                    metre = Fraction(int(m.group(1)), int(m.group(2)))
                elif m.group(3) == 'C':
                    metre = Fraction(4, 4)
                elif m.group(3) == 'C|':
                    metre = Fraction(2, 2)
            for m in re.finditer(r'\[{0}\]'.format(meter_pattern), line):
                if m.group(1) is not None:
                    metre = Fraction(int(m.group(1)), int(m.group(2)))
                elif m.group(3) == 'C':
                    metre = Fraction(4, 4)
                elif m.group(3) == 'C|':
                    metre = Fraction(2, 2)
            for m in re.finditer(r'\[L:\s*(\d+)/(\d+)\]', line):
                default_len = Fraction(int(m.group(1)), int(m.group(2)))
        return metre, default_len

