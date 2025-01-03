from __future__ import unicode_literals
import re
import os
import io
import sys
PY3 = sys.version_info.major > 2

try:
    from urllib.parse import quote # py3
    from urllib.request import urlopen
    from urllib.error import HTTPError, URLError
except ImportError: # py2
    from urllib import quote
    from urllib2 import urlopen, HTTPError, URLError

import logging
from collections import namedtuple
from wx import GetTranslation as _
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2

from abc_character_encoding import abc_text_to_unicode

if PY3:
    unichr = chr

# this file contains many regular expression patterns
# for understanding these regular expressions:
# https://regex101.com/#python

#  http://abcnotation.com/wiki/abc:standard:v2.1#information_field_definition
# keyword | name |file header | tune header | tune body | inline | type
abc_keywords = """\
A:|area                  |yes    |yes    |no     |no     |string
B:|book                  |yes    |yes    |no     |no     |string
C:|composer              |yes    |yes    |no     |no     |string
D:|discography           |yes    |yes    |no     |no     |string
F:|file url              |yes    |yes    |no     |no     |string
G:|group                 |yes    |yes    |no     |no     |string
H:|history               |yes    |yes    |no     |no     |string
I:|instruction           |yes    |yes    |yes    |yes    |instruction
K:|key                   |no     |last   |yes    |yes    |instruction
L:|unit note length      |yes    |yes    |yes    |yes    |instruction
M:|meter                 |yes    |yes    |yes    |yes    |instruction
m:|macro                 |yes    |yes    |yes    |yes    |instruction
N:|notes                 |yes    |yes    |yes    |yes    |string
O:|origin                |yes    |yes    |no     |no     |string
P:|parts                 |no     |yes    |yes    |yes    |instruction
Q:|tempo                 |no     |yes    |yes    |yes    |instruction
R:|rhythm                |yes    |yes    |yes    |yes    |string
r:|remark                |yes    |yes    |yes    |yes    |string
S:|source                |yes    |yes    |no     |no     |string
s:|symbol line           |no     |no     |yes    |no     |instruction
T:|tune title            |no     |second |yes    |no     |string
U:|user defined          |yes    |yes    |yes    |yes    |instruction
V:|voice                 |no     |yes    |yes    |yes    |instruction
W:|words (at the end)    |no     |yes    |yes    |no     |string
w:|words (note aligned)  |no     |no     |yes    |no     |string
X:|reference number      |no     |first  |no     |no     |instruction
Z:|transcription         |yes    |yes    |no     |no     |string
"""

clef_name_pattern = 'treble|bass3|bass|tenor|auto|baritone|soprano|mezzosoprano|alto2|alto1|alto|perc|none|C[1-5]|F[1-5]|G[1-5]'
simple_note_pattern = "[a-gA-G][',]*"
clef_pattern = r' *?(?P<clef>(?: (?P<clefprefix>(?:clef=)?)(?P<clefname>{1})(?P<stafftranspose>(?:[+^_-]8)?))?) *?(?P<octave>(?: octave=-?\d+)?) *?(?P<stafflines>(?: stafflines=\d+)?) *?(?P<playtranspose>(?: transpose=-?\d+)?) *?(?P<score>(?: score={0}{0})?) *?(?P<sound>(?: sound={0}{0})?) *?(?P<shift>(?: shift={0}{0})?) *?(?P<instrument>(?: instrument={0}(?:/{0})?)?)'.format(simple_note_pattern, clef_name_pattern)
key_ladder = 'Fb Cb Gb Db Ab Eb Bb F C G D A E B F# C# G# D# A# E# B#'.split(' ')
whitespace_chars = u' \r\n\t'

abc_inner_pattern = {
    'K:': r' ?(?:(?P<tonic>(?:[A-G][b#]?|none)) ??(?P<mode>(?:[MmDdPpLl][A-Za-z]*)?)(?P<accidentals>(?: +(?P<accidental>_{1,2}|=|\^{1,2})(?P<note>[a-g]))*)'+clef_pattern+')?',
    'Q:': r'(?P<pre_text>(?: ?"(?P<pre_name>(?:\\"|[^"])*)")?)(?P<metronome>(?: ?(?P<note1>\d+/\d+) ?(?P<note2>\d+/\d+)? ?(?P<note3>\d+/\d+)? ?(?P<note4>\d+/\d+)?=(?P<bpm>\d+))?)(?P<post_text>(?: ?"(?P<post_name>\w*)")?)',
    'V:': r' ?(?P<name>\w+)' + clef_pattern
}

name_to_display_text = {
    'staves'                  : _('Staff layout'     ),
    'area'                    : _('Area'             ),
    'book'                    : _('Book'             ),
    'composer'                : _('Composer'         ),
    'discography'             : _('Discography'      ),
    'file url'                : _('File url'         ),
    'group'                   : _('Group'            ),
    'history'                 : _('History'          ),
    'instruction'             : _('Instruction'      ),
    'key'                     : _('Key'              ),
    'unit note length'        : _('Unit note length' ),
    'meter'                   : _('Meter'            ),
    'macro'                   : _('Macro'            ),
    'notes'                   : _('Notes'            ),
    'origin'                  : _('Origin'           ),
    'parts'                   : _('Parts'            ),
    'tempo'                   : _('Tempo'            ),
    'rhythm'                  : _('Rhythm'           ),
    'remark'                  : _('Remark'           ),
    'source'                  : _('Source'           ),
    'symbol line'             : _('Symbol line'      ),
    'tune title'              : _('Tune title'       ),
    'user defined'            : _('User defined'     ),
    'voice'                   : _('Voice'            ),
    'words (note aligned)'    : _('Words (note aligned)'),
    'words (at the end)'      : _('Words (at the end)'),
    'reference number'        : _('Reference number' ),
    'transcription'           : _('Transcription'    ),
}

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    if PY3:
        return type('Enum', (), enums)
    else:
        return type(b'Enum', (), enums)

TuneScope = enum('FullText', 'SelectedText', 'SelectedLines', 'TuneHeader', 'TuneBody', 'Tune', 'TuneUpToSelection', 'BodyUpToSelection', 'BodyAfterSelection', 'LineUpToSelection', 'FileHeader', 'PreviousLine', 'MatchText', 'InnerText', 'PreviousCharacter', 'NextCharacter')
TuneScopeInfo = namedtuple('TuneScopeInfo', 'text start stop encoded_text')
InnerMatch = namedtuple('InnerMatch', 'match offset')

class ValueDescription(object):
    def __init__(self, value, description, common=True, show_value=False, alternate_values=None):
        super(ValueDescription, self).__init__()
        self.value = value
        self.description = description
        self.show_value = show_value
        self.common = common
        self.alternate_values = alternate_values or []

class CodeDescription(ValueDescription):
    def __init__(self, value, description, common=True, alternate_values=None):
        super(CodeDescription, self).__init__(value, description, common=common, show_value=True, alternate_values=alternate_values)

class ValueImageDescription(ValueDescription):
    def __init__(self, value, image_name, description, common=True, show_value=False):
        super(ValueImageDescription, self).__init__(value, description, common=common, show_value=show_value)
        self.image_name = image_name

class CodeImageDescription(ValueImageDescription):
    def __init__(self, value, image_name, description, common=True):
        super(CodeImageDescription, self).__init__(value, image_name, description, common=common, show_value=True)

decoration_aliases = {
    '!>!'       : '!accent!',
    '!^!'       : '!marcato!',
    '!emphasis!': '!accent!',
    '!<(!'      : '!crescendo(!',
    '!<)!'      : '!crescendo)!',
    '!>(!'      : '!diminuendo(!',
    '!>)!'      : '!diminuendo)!',
    '!+!'       : '!plus!',
}

decoration_to_description = {
    '.'                : _('staccato mark'),
    '~'                : _('Irish roll'),
    'H'                : _('fermata'),
    'L'                : _('accent or emphasis'),
    'M'                : _('lowermordent'),
    'O'                : _('coda'),
    'P'                : _('uppermordent'),
    'S'                : _('segno'),
    'T'                : _('trill'),
    'u'                : _('down-bow'),
    'v'                : _('up-bow'),
    '!trill!'          : _('trill'),
    '!trill(!'         : _('start of an extended trill'),
    '!trill)!'         : _('end of an extended trill'),
    '!lowermordent!'   : _('lower mordent'),
    '!uppermordent!'   : _('upper mordent'),
    '!mordent!'        : _('mordent'),
    '!pralltriller!'   : _('pralltriller'),
    '!roll!'           : _('Irish roll'),
    '!turn!'           : _('turn or gruppetto'),
    '!turnx!'          : _('a turn mark with a line through it'),
    '!invertedturn!'   : _('an inverted turn mark'),
    '!invertedturnx!'  : _('an inverted turn mark with a line through it'),
    '!arpeggio!'       : _('arpeggio'),
    '!>!'              : _('accent or emphasis'),
    '!accent!'         : _('accent or emphasis'),
    '!emphasis!'       : _('accent or emphasis'),
    '!^!'              : _('marcato'),
    '!marcato!'        : _('marcato'),
    '!fermata!'        : _('fermata or hold'),
    '!invertedfermata!': _('upside down fermata'),
    '!tenuto!'         : _('tenuto'),
    '!0!'              : _('no finger'),
    '!1!'              : _('thumb'),
    '!2!'              : _('index finger'),
    '!3!'              : _('middle finger'),
    '!4!'              : _('ring finger'),
    '!5!'              : _('little finger'),
    '!+!'              : _('left-hand pizzicato'),
    '!plus!'           : _('left-hand pizzicato'),
    '!snap!'           : _('snap-pizzicato'),
    '!slide!'          : _('slide up to a note'),
    '!wedge!'          : _('staccatissimo or spiccato'),
    '!upbow!'          : _('up-bow'),
    '!downbow!'        : _('down-bow'),
    '!open!'           : _('open string or harmonic'),
    '!thumb!'          : _('cello thumb symbol'),
    '!breath!'         : _('breath mark'),
    '!pppp!'           : _('pianissimo possibile'),
    '!ppp!'            : _('pianississimo'),
    '!pp!'             : _('pianissimo'),
    '!p!'              : _('piano'),
    '!mp!'             : _('mezzopiano'),
    '!mf!'             : _('mezzoforte'),
    '!f!'              : _('forte'),
    '!ff!'             : _('fortissimo'),
    '!fff!'            : _('fortississimo'),
    '!ffff!'           : _('fortissimo possibile'),
    '!sfz!'            : _('sforzando'),
    '!crescendo(!'     : _('start of a < crescendo mark'),
    '!<(!'             : _('start of a < crescendo mark'),
    '!crescendo)!'     : _('end of a < crescendo mark'),
    '!<)!'             : _('end of a < crescendo mark'),
    '!diminuendo(!'    : _('start of a > diminuendo mark'),
    '!>(!'             : _('start of a > diminuendo mark'),
    '!diminuendo)!'    : _('end of a > diminuendo mark'),
    '!>)!'             : _('end of a > diminuendo mark'),
    '!segno!'          : _('segno'),
    '!coda!'           : _('coda'),
    '!D.S.!'           : _('the letters D.S. (=Da Segno)'),
    '!D.C.!'           : _('the letters D.C. (=either Da Coda or Da Capo)'),
    '!dacoda!'         : _('the word "Da" followed by a Coda sign'),
    '!dacapo!'         : _('the words "Da Capo"'),
    '!D.C.alcoda!'     : _('the words "D.C. al Coda"'),
    '!D.C.alfine!'     : _('the words "D.C. al Fine"'),
    '!D.S.alcoda!'     : _('the words "D.S. al Coda"'),
    '!D.S.alfine!'     : _('the words "D.S. al Fine"'),
    '!fine!'           : _('the word "fine"'),
    '!shortphrase!'    : _('vertical line on the upper part of the staff'),
    '!mediumphrase!'   : _('vertical line on the upper part of the staff, extending down to the centre line'),
    '!longphrase!'     : _('vertical line on the upper part of the staff, extending 3/4 of the way down'),
    '!ped!'            : _('sustain pedal down'),
    '!ped-up!'         : _('sustain pedal up'),
    '!editorial!'      : _('editorial accidental above note'),
    '!courtesy!'       : _('courtesy accidental between parentheses'),
}

ABC_TUNE_HEADER_NO = 0
ABC_TUNE_HEADER_FIRST = 1
ABC_TUNE_HEADER_SECOND = 2
ABC_TUNE_HEADER_YES = 3
ABC_TUNE_HEADER_LAST = 4
tune_header_lookup = {'no': ABC_TUNE_HEADER_NO, 'first': ABC_TUNE_HEADER_FIRST, 'second': ABC_TUNE_HEADER_SECOND, 'yes': ABC_TUNE_HEADER_YES, 'last': ABC_TUNE_HEADER_LAST}

AbcSection = enum('FileHeader', 'TuneHeader', 'TuneBody', 'OutsideTune')
ABC_SECTIONS = [
    AbcSection.FileHeader,
    AbcSection.TuneHeader,
    AbcSection.TuneBody,
    AbcSection.OutsideTune
]

chord_notes = {
    ''        : ( 0, 4, 7 ),                   # 'Major'
    'm'       : ( 0, 3, 7 ),                   # 'Minor'
    'dim'     : ( 0, 3, 6 ),                   # 'Diminished'
    '+'       : ( 0, 4, 8 ),                   # 'Augmented'
    'sus'     : ( 0, 5, 7 ),                   # 'Suspended'
    'sus2'    : ( 0, 2, 7 ),                   # 'Suspended (2nd)
    '7'       : ( 0, 4, 7, 10 ),               # 'Seventh'
    'M7'      : ( 0, 4, 7, 11 ),               # 'Major seventh'
    'mM7'     : ( 0, 3, 7, 11 ),               # 'Minor-major seventh'
    'm7'      : ( 0, 3, 7, 10 ),               # 'Minor seventh'
    'augM7'   : ( 0, 4, 8, 11 ),               # 'Augmented-major seventh'
    'aug7'    : ( 0, 4, 8, 10 ),               # 'Augmented seventh'
    '6'       : ( 0, 4, 7, 9  ),               # 'Major sixth'
    'm6'      : ( 0, 3, 7, 9  ),               # 'Minor sixth'
    'm7b5'    : ( 0, 3, 6, 10 ),               # 'Half-diminished seventh'
    'dim7'    : ( 0, 3, 6, 9 ),                # 'Diminished seventh'
    '7b5'     : ( 0, 4, 6, 10 ),               # 'Seventh flat five'
    '5'       : ( 0, 7 ),                      # 'Power-chord (no third
    '7sus'    : ( 0, 5, 7, 10 ),               # 'Seventh suspended'
    '7sus2'   : ( 0, 2, 7, 10 ),               # 'Seventh suspended (2nd
    'M9'      : ( 0, 4, 7, 11, 14 ),           # 'Major 9th'
    '9'       : ( 0, 4, 7, 10, 14 ),           # 'Dominant 9th'
    'mM9'     : ( 0, 3, 7, 11, 14 ),           # 'Minor Major 9th'
    'm9'      : ( 0, 3, 7, 10, 14 ),           # 'Minor Dominant 9th'
    '+M9'     : ( 0, 4, 8, 11, 14 ),           # 'Augmented Major 9th'
    '+9'      : ( 0, 4, 8, 10, 14 ),           # 'Augmented Dominant 9th'
    'o/9'     : ( 0, 3, 6, 10, 14 ),           # 'Half-Diminished 9th'
    'o/9b'    : ( 0, 3, 6, 10, 13 ),           # 'Half-Diminished Minor 9th'
    'dim9'    : ( 0, 3, 6, 9, 14 ),            # 'Diminished 9th'
    'dim9b'   : ( 0, 3, 6, 9, 13 ),            # 'Diminished Minor 9th'
    '11'      : ( 0, 4, 7, 10, 14, 17 ),       # 'Dominant 11th'
}

def replace_text(text, replacements):
    """
    :param text: text that requires replacements
    :param replacements: A sequence of tuples in the form (compiled regular expression object, replacement value)
    :return: the original text with all replacements applied
    """
    for regex, replace_value in replacements:
        text = regex.sub(replace_value, text)
    return text

def remove_named_groups(pattern):
    """
    :param pattern: regular expression pattern
    :return: regular expression pattern where named groups are removed
    """
    return re.sub(r'(?<=\(\?)P<[^>]+>', ':', pattern)

def replace_named_group(pattern, old_group, new_group=None):
    """
    :param pattern: regular expression pattern (containing named groups)
    :param old_group: original groupname
    :param new_group: desired groupname
    :return: regular expression pattern where named group old_group is replaced by new_group
    """
    if new_group is None:
        replace_value = ':'
    else:
        replace_value = 'P<{0}>'.format(new_group)
    return re.sub(r'(?<=\(\?)P<{0}>'.format(old_group), replace_value, pattern)

def get_html_from_url(url):
    result = u''
    try:
        result = urlopen(url).read()
    except HTTPError as ex:
        pass
    except URLError as ex:
        pass
    return result


class AbcElement(object):
    """
    Base class for each element in abc-code where element is a piece of structured abc-code
    """
    rest_of_line_pattern = r'(?P<inner>.*?)(?:(?<!\\)%.*)?$'

    def __init__(self, name, keyword=None, display_name=None, description=None, validation_pattern=None):
        self.name = name
        self.keyword = keyword
        if display_name is None:
            self.__display_name = name_to_display_text.get(name, name[:1].upper() + name[1:])
        else:
            self.__display_name = display_name
        self.description = description
        self.mandatory = False
        self.default = None
        self.rest_of_line_pattern = AbcElement.rest_of_line_pattern
        self._search_pattern = {}
        self._search_re = {} # compiled regex
        self.params = []
        self.validation_pattern = validation_pattern
        self.__validation_re = None
        self.supported_values = None
        self.tune_scope = TuneScope.SelectedLines
        self.visible_match_group = None
        self.removable_match_groups = {}

    @staticmethod
    def get_inline_pattern(keyword):
        return r'\[' + re.escape(keyword) + r'([^\]\n\r]*)\]'

    def freeze(self):
        for section in ABC_SECTIONS:
            pattern = self._search_pattern.get(section, None)
            if pattern is not None:
                self._search_re[section] = re.compile(pattern)

        if self.validation_pattern is not None:
            self.__validation_re = re.compile(self.validation_pattern)

    @property
    def valid_sections(self):
        return [section for section in ABC_SECTIONS if self._search_pattern.get(section) is not None]

    def matches(self, context):
        regex = self._search_re.get(context.abc_section, None)
        if regex is None:
            return None

        result = None
        scope_info = context.get_scope_info(self.tune_scope)
        encoded_text = scope_info.encoded_text
        text = scope_info.text
        p1, p2 = context.get_selection_within_scope(self.tune_scope)
        if len(text) != len(encoded_text):
            p1 = len(encoded_text[:p1].decode('utf-8'))
            p2 = len(encoded_text[:p2].decode('utf-8'))

        if p1 == p2 and 0 < p1 <= len(text) and text[p1 - 1] not in whitespace_chars:
            p1 -= 1
            for m in regex.finditer(text):
                if m.start() <= p1 < m.end():
                    result = m
                    break
        else:
            # if p1 > len(text):
            #     print(u'Selection ({0}) past length ({1})'.format(p1, len(text)))
            for m in regex.finditer(text):
                if m.start() <= p1 <= p2 <= m.end():
                    result = m
                    break
        return result

    def get_regex_for_section(self, section):
        return self._search_re.get(section, None)

    def matches_text(self, context, text):
        regex = self._search_re.get(context.abc_section, None)
        if regex is not None:
            return regex.search(text)
        return None

    def replace_text(self, context, text, replace_value):
        return self._search_re[context.abc_section].sub(replace_value, text)

    @property
    def display_name(self):
        return self.__display_name

    def get_description_url(self, context):
        return None

    def get_header_text(self, context):
        return self.__display_name

    def get_description_text(self, context):
        return self.description

    def get_description_html(self, context):
        result = None
        url = self.get_description_url(context)
        if url:
            result = get_html_from_url(url)
        if not result:
            result = u'<h1>%s</h1>' % escape(self.get_header_text(context))
            description = self.get_description_text(context)
            if description:
                result += u'{0}<br>'.format(escape(description))

            if self.visible_match_group is not None:
                # groups = context.current_match.groups()
                # element_text = context.match_text
                # if len(groups) == 1 and groups[0]:
                #    element_text = groups[0]
                element_text = context.get_matchgroup(self.visible_match_group)
                if element_text:
                    element_text = abc_text_to_unicode(element_text).strip()
                    if element_text:
                        result += u'<code>{0}</code><br>'.format(escape(element_text))

            #for matchtext in context.current_match.groups():
            #    if matchtext:
            #        result += '<code>%s</code><br>' % escape(matchtext)
        return result

    def get_inner_element(self, context):
        return self


class CompositeElement(AbcElement):
    def __init__(self, name, keyword=None, display_name=None, description=None):
        super(CompositeElement, self).__init__(name, keyword, display_name=display_name, description=description)
        self._elements = {}

    def add_element(self, element):
        if element.keyword:
            self._elements[element.keyword] = element
        else:
            raise Exception('Element has no keyword')

    def get_element(self, keyword):
        return self._elements.get(keyword)

    def get_element_from_context(self, context):
        inner_text = context.current_match.group(1)
        if inner_text is None:
            inner_text = context.current_match.group(2)
        return self.get_element_from_inner_text(inner_text)

    def get_element_from_inner_text(self, inner_text):
        parts = inner_text.split(' ', 1)
        keyword = parts[0]
        result = self._elements.get(keyword)
        if isinstance(result, CompositeElement) and len(parts) > 1:
            subelement = result.get_element_from_inner_text(parts[1])
            if subelement is not None:
                result = subelement
        return result

    def get_header_text(self, context):
        element = self.get_element_from_context(context)
        if element:
            return element.get_header_text(context)
        return super(CompositeElement, self).get_header_text(context)

    def get_description_text(self, context):
        element = self.get_element_from_context(context)
        if element:
            return element.get_description_text(context)
        return super(CompositeElement, self).get_description_text(context)

    def get_inner_element(self, context):
        return self.get_element_from_context(context) or self


class AbcUnknown(AbcElement):
    pattern = ''
    def __init__(self):
        super(AbcUnknown, self).__init__('Unknown', display_name=_('Unknown'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcUnknown.pattern


class AbcInformationField(AbcElement):
    def __init__(self, keyword, name, file_header, tune_header, tune_body, inline, inner_pattern=None):
        super(AbcInformationField, self).__init__(name, keyword)
        self.file_header = file_header
        self.tune_header = tune_header
        self.tune_body = tune_body
        self.inline = inline
        self.inner_pattern = inner_pattern
        self.inner_re = None
        self.visible_match_group = 1
        if inner_pattern:
            self.visible_match_group = 0

        line_pattern = r'(?m)^' + re.escape(self.keyword) + self.rest_of_line_pattern
        if file_header:
            self._search_pattern[AbcSection.FileHeader] = line_pattern
        if tune_header in [ABC_TUNE_HEADER_YES, ABC_TUNE_HEADER_FIRST, ABC_TUNE_HEADER_SECOND, ABC_TUNE_HEADER_LAST]:
            self._search_pattern[AbcSection.TuneHeader] = line_pattern
        if tune_body or inline:
            pattern = line_pattern
            if inline:
                pattern += '|' + self.get_inline_pattern(keyword)
            self._search_pattern[AbcSection.TuneBody] = pattern

    def freeze(self):
        super(AbcInformationField, self).freeze()
        if self.inner_pattern:
            self.inner_re = re.compile(self.inner_pattern)

    def matches(self, context):
        match = super(AbcInformationField, self).matches(context)
        result = match
        if self.inner_re and match is not None:
            i = 1
            inner_text = match.group(i)
            if inner_text is None:
                i += 1
                inner_text = match.group(i)
            m = self.inner_re.search(inner_text)
            if m:
                result = (match, InnerMatch(m, match.start(i)))

        return result


class AbcDirective(CompositeElement):
    def __init__(self):
        super(AbcDirective, self).__init__('Stylesheet directive', display_name=_('Stylesheet directive'), description=_('A stylesheet directive is a line that starts with %%, followed by a directive that gives instructions to typesetting or player programs.'))
        pattern = r'(?m)^(?:%%|I:)(?!%)' + self.rest_of_line_pattern + '|' + self.get_inline_pattern('I:')
        for section in ABC_SECTIONS:
            self._search_pattern[section] = pattern


class AbcStringField(AbcInformationField):
    def __init__(self, keyword, name, file_header, tune_header, tune_body, inline):
        super(AbcStringField, self).__init__(name, keyword, file_header, tune_header, tune_body, inline)


class AbcInstructionField(AbcInformationField):
    def __init__(self, keyword, name, file_header, tune_header, tune_body, inline, inner_pattern=None):
        super(AbcInstructionField, self).__init__(name, keyword, file_header, tune_header, tune_body, inline, inner_pattern)


class AbcMidiDirective(CompositeElement):
    def __init__(self):
        super(AbcMidiDirective, self).__init__('MIDI directive', 'MIDI', display_name=_('MIDI directive'), description=_('A directive that gives instructions to player programs.'))


class AbcMidiProgramDirective(AbcElement):
    pattern = r'(?m)^(?:%%|I:)MIDI program(?P<channel>(?:\s+\d+(?=\s+\d))?)(?:(?P<instrument>\s*\d*))?' + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiProgramDirective, self).__init__('MIDI_program', display_name=_('Instrument'), description=_('Sets the instrument for a MIDI channel.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiProgramDirective.pattern

class AbcMidiChordProgramDirective(AbcElement):
    pattern = r'(?m)^(?:%%|I:)MIDI chordprog(?:(?P<instrument>\s*\d*))?' + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiChordProgramDirective, self).__init__('MIDI_chordprog', display_name=_('Chord instrument'), description=_('Sets the instrument for playing chords.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiChordProgramDirective.pattern

class AbcMidiBaseProgramDirective(AbcElement):
    pattern = r'(?m)^(?:%%|I:)MIDI bassprog(?:(?P<instrument>\s*\d*))?' + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiBaseProgramDirective, self).__init__('MIDI_bassprog', display_name=_('Bass instrument'), description=_('Sets the instrument for the base.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiBaseProgramDirective.pattern


class AbcMidiChannelDirective(AbcElement):
    pattern = r'(?m)^(?:%%|I:)MIDI channel(?P<channel>\s*\d*)' + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiChannelDirective, self).__init__('MIDI_channel', display_name=_('Channel'), description=_('Sets the MIDI channel for the current voice.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiChannelDirective.pattern


class AbcMidiDrumMapDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)(?:MIDI drummap|percmap)\s+(?P<note>[_^]*\w[,']*)\s+(?P<druminstrument>\d+)" + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiDrumMapDirective, self).__init__('MIDI_drummap', display_name=_('Drum mapping'), description=_('Maps a note to an instrument.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiDrumMapDirective.pattern


class AbcMidiVolumeDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)MIDI (?:control 7|chordvol|bassvol)\s+(?P<volume>\d*)" + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiVolumeDirective, self).__init__('MIDI_volume', display_name=_('Volume'), description=_('Volume for current voice.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiVolumeDirective.pattern


class AbcMidiGuitarChordDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)MIDI gchord (?P<pattern>\w*)" + AbcElement.rest_of_line_pattern
    def __init__(self):
        super(AbcMidiGuitarChordDirective, self).__init__('MIDI_gchord', display_name=_('Guitar chords'), description=_('Play guitar chords'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcMidiGuitarChordDirective.pattern


class ScoreDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)(?:score|staves)\b"+ AbcElement.rest_of_line_pattern
    def __init__(self):
        super(ScoreDirective, self).__init__('score', display_name=_('Score layout'), description=_('Defines which staves are displayed.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = ScoreDirective.pattern


class MeasureNumberDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)(?:measurenb|barnumbers) (?P<interval>-?\d*)"+ AbcElement.rest_of_line_pattern
    def __init__(self):
        super(MeasureNumberDirective, self).__init__('measurenb', display_name=_('Measure numbering'), description=_('Defines if and how measures are numbered.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = MeasureNumberDirective.pattern


class HideFieldsDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)writefields\s+(?P<fields>[A-Za-z_]+)\s+(?:0|false)"+ AbcElement.rest_of_line_pattern
    def __init__(self):
        super(HideFieldsDirective, self).__init__('hide_fields', display_name=_('Hide fields'), description=_('Defines which fields should be hidden.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = HideFieldsDirective.pattern


class ShowFieldsDirective(AbcElement):
    pattern = r"(?m)^(?:%%|I:)writefields\s+(?P<fields>[A-Za-z]+)"+ AbcElement.rest_of_line_pattern
    def __init__(self):
        super(ShowFieldsDirective, self).__init__('show_fields', display_name=_('Show fields'), description=_('Defines which fields should be shown.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = ShowFieldsDirective.pattern


class Abcm2psDirective(AbcElement):
    """ Elements defined by abcm2ps """
    anchor_replacement = (re.compile('<a (?:href|name)="[^"]*">|</a>', re.IGNORECASE), '')
    table_replacement = (re.compile('<table>.*?</table>', re.IGNORECASE | re.DOTALL), '')

    def __init__(self, keyword, name, description=None):
        super(Abcm2psDirective, self).__init__(keyword, name, description=description)
        self.html_replacements = [
            Abcm2psDirective.anchor_replacement,
            Abcm2psDirective.table_replacement
        ]

    def get_description_url(self, context):
        return 'http://moinejf.free.fr/abcm2ps-doc/%s.xhtml' % quote(self.name)

    def get_html_from_url(self, url):
        result = get_html_from_url(url)
        result = replace_text(result, self.html_replacements)
        return result


class AbcVersionDirective(AbcElement):
    pattern = r'^%abc-(?P<version>[\d\.]+)'
    def __init__(self):
        super(AbcVersionDirective, self).__init__('abcversion', display_name=_('ABC version'), description=_('It starts with the version of the ABC specification this file conforms to.'))
        self._search_pattern[AbcSection.FileHeader] = AbcVersionDirective.pattern


class AbcComment(AbcElement):
    #pattern = r'(?<!\\|^)%\s*(.*)|^%(?!%)\s*(.*)$'
    pattern = r'(?<!\\)%\s*(.*)$'
    def __init__(self):
        super(AbcComment, self).__init__('Comment', '%', display_name=_('Comment'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcComment.pattern
        self.visible_match_group = 1

    def get_header_text(self, context):
        if context.match_text and context.match_text.startswith('%%'):
            return _('Stylesheet directive')
        else:
            return super(AbcComment, self).get_header_text(context)

    def get_description_text(self, context):
        if context.match_text and context.match_text.startswith('%%'):
            return _('A stylesheet directive is a line that starts with %%, followed by a directive that gives instructions to typesetting or player programs.')
        else:
            return super(AbcComment, self).get_description_text(context)

    def remove_comments(self, abc):
        return self._search_re[AbcSection.TuneBody].sub('', abc)


class AbcBeam(AbcElement):
    pattern = r'`+'
    def __init__(self):
        super(AbcBeam, self).__init__('Beam', '`', display_name=_('Beam'), description=_('Back quotes ` may be used freely between notes to be beamed, to increase legibility.'))
        self._search_pattern[AbcSection.TuneBody] = AbcBeam.pattern


class AbcEmptyDocument(AbcElement):
    pattern = r'^$'
    def __init__(self):
        super(AbcEmptyDocument, self).__init__('empty_document', display_name=_('Welcome to EasyABC'),
            description=_('Creating an abc-file from scratch can be difficult. This assist panel tries to help by providing hints and actions. But remember, typing is usually faster.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcEmptyLine.pattern
        self.tune_scope = TuneScope.FullText

    def matches(self, context):
        if context.contains_text:
            return None
        else:
            regex = self._search_re.get(context.abc_section, None)
            return regex.match('')


class AbcEmptyLine(AbcElement):
    pattern = r'^\s*$'
    def __init__(self):
        super(AbcEmptyLine, self).__init__('empty_line', display_name=_('Empty line'), description=_('An empty line separates tunes.'))
        for section in ABC_SECTIONS:
            self._search_pattern[section] = AbcEmptyLine.pattern


class AbcEmptyLineWithinTuneHeader(AbcElement):
    def __init__(self):
        super(AbcEmptyLineWithinTuneHeader, self).__init__('empty_line_header', display_name=_('Empty line in header'), description=_('More directives can be added here in the tune header. After K: the music code begins.'))
        self._search_pattern[AbcSection.TuneHeader] = AbcEmptyLine.pattern


class AbcEmptyLineWithinTuneBody(AbcElement):
    def __init__(self):
        super(AbcEmptyLineWithinTuneBody, self).__init__('empty_line_tune', display_name=_('Empty line'), description=_('Notes, rests, or directives can be added.'))
        self._search_pattern[AbcSection.TuneBody] = AbcEmptyLine.pattern


class AbcEmptyLineWithinFileHeader(AbcElement):
    def __init__(self):
        super(AbcEmptyLineWithinFileHeader, self).__init__('empty_line_file_header', display_name=_('File header'), description=_('Everything above the first X: is the file header. The directives here apply to all the tunes that follow.'))
        self._search_pattern[AbcSection.FileHeader] = AbcEmptyLine.pattern


class AbcBodyElement(AbcElement):
    def __init__(self, name, pattern, display_name=None, description=None):
        super(AbcBodyElement, self).__init__(name, display_name=display_name, description=description)
        self._search_pattern[AbcSection.TuneBody] = pattern
        self.pattern = pattern


class AbcSpace(AbcBodyElement):
    pattern = r'\s+'
    def __init__(self):
        super(AbcSpace, self).__init__('Whitespace', AbcSpace.pattern, display_name=_('Whitespace'), description=_('Space is used to improve legibility and to prevent notes from sharing the same beam.'))


class AbcAnnotation(AbcBodyElement):
    pattern = r'(?P<annotation>"(?P<pos>[\^_<>@])(?P<text>(?:\\"|[^"])*)")'
    def __init__(self):
        super(AbcAnnotation, self).__init__('Annotation', AbcAnnotation.pattern, display_name=_('Annotation'))
        self.visible_match_group = 'text'


class AbcChordOrAnnotation(AbcBodyElement):
    pattern = r'"(?P<pos>[\^_<>@])?(?P<text>(?:\\"|[^"])*)"'
    def __init__(self):
        super(AbcChordOrAnnotation, self).__init__('Chord or annotation', AbcChordOrAnnotation.pattern, display_name=_('Chord symbol or annotation'))


class AbcSlur(AbcBodyElement):
    pattern = r'(?P<dash>\.?)\((?!\d)|\)'
    def __init__(self):
        super(AbcSlur, self).__init__('Slur', AbcSlur.pattern, display_name=_('Slur'))


class TypesettingSpace(AbcBodyElement):
    pattern = 'y'
    def __init__(self):
        super(TypesettingSpace, self).__init__('Typesetting extra space', TypesettingSpace.pattern, display_name=_('Typesetting extra space'), description=_('y can be used to add extra space between the surrounding notes; moreover, chord symbols and decorations can be attached to it, to separate them from notes.'))


class RedefinableSymbol(AbcBodyElement):
    pattern = '[H-Wh-w~]'
    def __init__(self):
        super(RedefinableSymbol, self).__init__('Redefinable symbol', RedefinableSymbol.pattern, display_name=_('Redefinable symbol'), description=_('The letters H-W and h-w and the symbol ~ can be assigned with the U: field to provide a shortcut for the !symbol! syntax. For example, to assign the letter T to represent the trill, you can write: U: T = !trill!'))


class AbcDecoration(AbcBodyElement):
    pattern = r"!([^!]+)!|\+([^!]+)\+|\."
    values = decoration_to_description
    def __init__(self, name=None, subset=None, display_name=None):
        if name is None:
            name = 'Decoration'
        if subset is None:
            pattern = AbcDecoration.pattern
        else:
            with_exclamation = '|'.join(re.escape(value[1:-1]) for value in subset if value[0] == '!')
            without_exclamation = '|'.join(re.escape(value) for value in subset if value[0] != '!')
            if without_exclamation:
                without_exclamation = '|' + without_exclamation
            pattern = r'(?P<decoration>(?P<decomark>\+|!)(?P<deconame>{0})(?P=decomark){1})'.format(with_exclamation, without_exclamation)
        super(AbcDecoration, self).__init__(name, pattern, display_name=display_name)

    def get_description_html(self, context):
        html = super(AbcDecoration, self).get_description_html(context)
        html += '<br>'
        symbol = context.match_text
        if symbol and symbol[0] == symbol[-1] == '+': # convert old notation to new
            symbol = '!%s!' % symbol[1:-1]
        html += escape(decoration_to_description.get(symbol, _('Unknown symbol')))
        html += '<br>'
        return html


class AbcDynamicsDecoration(AbcDecoration):
    values = [
        '!ffff!', '!fff!', '!ff!', '!f!', '!mf!', '!mp!', '!p!', '!pp!', '!ppp!', '!pppp!', '!sfz!',
        '!crescendo(!',  '!<(!',
        '!crescendo)!',  '!<)!',
        '!diminuendo(!', '!>(!',
        '!diminuendo)!', '!>)!'
    ]
    def __init__(self):
        super(AbcDynamicsDecoration, self).__init__('Dynamics', AbcDynamicsDecoration.values, display_name=_('Dynamics'))


class AbcFingeringDecoration(AbcDecoration):
    values = ['!0!', '!1!', '!2!', '!3!', '!4!', '!5!']
    def __init__(self):
        super(AbcFingeringDecoration, self).__init__('Fingering', AbcFingeringDecoration.values, display_name=_('Fingering'))


class AbcOrnamentDecoration(AbcDecoration):
    values = [
        '!trill!',
        '!trill(!',
        '!trill)!',
        '!mordent!', #'!lowermordent!',
        '!pralltriller!', #'!uppermordent!',
        '!roll!',
        '!turn!',
        '!turnx!',
        '!invertedturn!',
        '!invertedturnx!',
        '!arpeggio!'
    ]
    def __init__(self):
        super(AbcOrnamentDecoration, self).__init__('Ornament', AbcOrnamentDecoration.values, display_name=_('Ornament'))


class AbcDirectionDecoration(AbcDecoration):
    values = [
        '!segno!',
        '!coda!',
        '!D.S.!',
        '!D.C.!',
        '!dacoda!',
        '!dacapo!',
        '!D.C.alcoda!',
        '!D.C.alfine!',
        '!D.S.alcoda!',
        '!D.S.alfine!',
        '!fine!'
    ]
    def __init__(self):
        super(AbcDirectionDecoration, self).__init__('Direction', AbcDirectionDecoration.values, display_name=_('Direction'))


class AbcArticulationDecoration(AbcDecoration):
    values = [
        '.',
        '!tenuto!',
        '!accent!', '!>!', '!emphasis!',
        '!marcato!', '!^!',
        '!wedge!',
        '!invertedfermata!',
        '!fermata!',
        '!plus!', '!+!',
        '!snap!',
        '!slide!',
        '!upbow!',
        '!downbow!',
        '!open!',
        '!thumb!',
        '!breath!',
        '!ped!',
        '!ped-up!',
    ]
    def __init__(self):
        super(AbcArticulationDecoration, self).__init__('Articulation', AbcArticulationDecoration.values, display_name=_('Articulation'))


class AbcBrokenRhythm(AbcBodyElement):
    pattern = r'\<+|\>+'
    def __init__(self):
        super(AbcBrokenRhythm, self).__init__('Broken rhythm', AbcBrokenRhythm.pattern)

    def get_description_html(self, context):
        html = super(AbcBrokenRhythm, self).get_description_html(context)
        if '>' in context.match_text:
            html += 'The previous note is dotted, the next note halved'
        else: # if '<' in context.match_text:
            html += 'The previous note is halved, the next dotted'
        return html


class AbcTuplet(AbcBodyElement):
    pattern = r"\([1-9](?:\:[1-9]?)?(?:\:[1-9]?)?"
    def __init__(self):
        super(AbcTuplet, self).__init__('Tuplet', AbcTuplet.pattern, display_name=_('Tuplet'), description=_('Duplets, triplets, quadruplets, etc.'))


class AbcBar(AbcBodyElement):
    pattern = r"(?:\.?\|\||:*\|\]|\[\|:*|::|:+\||\|:+|\.?\||\[\|\])[1-9]?"
    def __init__(self):
        super(AbcBar, self).__init__('Bar', AbcBar.pattern, display_name=_('Bar'), description=_('Separates measures.'))


class AbcVariantEnding(AbcBodyElement):
    pattern = r'\[[1-9](?:[,-][1-9])*|\|[1-9]'
    def __init__(self):
        super(AbcVariantEnding, self).__init__('Variant ending', AbcVariantEnding.pattern, display_name=_('Variant ending'), description=_('To play a different ending each time'))


class AbcVoiceOverlay(AbcBodyElement):
    pattern = '&'
    def __init__(self):
        super(AbcVoiceOverlay, self).__init__('Voice overlay', AbcVoiceOverlay.pattern, display_name=_('Voice overlay'), description=_("The & operator may be used to temporarily overlay several voices within one measure. Each & operator sets the time point of the music back by one bar line, and the notes which follow it form a temporary voice in parallel with the preceding one. This may only be used to add one complete bar's worth of music for each &. "))


class AbcInvalidCharacter(AbcBodyElement):
    pattern = r'[^\d\w\s%s]' % re.escape(r'!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~')
    def __init__(self):
        super(AbcInvalidCharacter, self).__init__('Invalid character', AbcInvalidCharacter.pattern, display_name=_('Invalid character'), description=_("This character is not allowed within the body of an abc tune."))


class AbcChordSymbol(AbcBodyElement):
    basic_pattern = r'(?P<chordsymbol>"(?P<chordname>[^\^_<>@"\\](?:[^"\\]|\\.)*)")'
    #pattern = ur'(?P<chordsymbol>"(?P<chordnote>[A-G][b#\u266D\u266E\u266F]?)(?P<quality>[^/\d]*)(?P<th>2|4|5|6|7|9|11|13)?(?P<sus>sus[2|4|9]?)?(?P<additional>.*?)(?P<bassnote>(?:/[A-Ga-g][b#\u266D\u266E\u266F]?)?)")'
    pattern = r'"(?P<chordsymbol>(?P<chordnote>(?:[A-G][b#\u266D\u266E\u266F]?)?)(?P<chordname>.*?)(?P<bassnote>(?:/[A-Ga-g][b#\u266D\u266E\u266F]?)?))"'
    def __init__(self):
        super(AbcChordSymbol, self).__init__('Chord symbol', AbcChordSymbol.pattern, display_name=_('Chord symbol'))


class AbcBaseNote(AbcBodyElement):
    accidental_pattern = r'(?P<accidental>(?:[_^](?:3/2?|1?/2?)|\^{1,2}|_{1,2}|=)?)?'
    length_pattern = r'(?P<length>\d{0,3}(?:/\d{0,3})*)'
    octave_pattern = r"(?P<octave>[',]*)"
    pair_pattern = r'(?P<pair>(?:\s*>+|\s*<+)?)'
    tie_pattern = r'(?P<tie>-?)'

    basic_note_pattern_without_len = r'{0}(?P<note>[A-Ga-g]){1}'.format(accidental_pattern, octave_pattern)
    basic_note_pattern = basic_note_pattern_without_len + length_pattern

    basic_rest_pattern_without_len = r'(?P<rest>[zx])'
    basic_rest_pattern = basic_rest_pattern_without_len + length_pattern

    basic_note_or_rest_pattern = r'(?:{0}|{1})'.format(basic_note_pattern_without_len, basic_rest_pattern_without_len) + length_pattern
    basic_measure_rest_pattern = r'(?P<rest>[ZX])(?P<length>(?:[1-9][0-9]*)?)'

    def __init__(self, name, pattern, display_name=None, description=None):
        super(AbcBaseNote, self).__init__(name, pattern, display_name=display_name, description=description)


class AbcGraceNotes(AbcBaseNote):
    pattern = r'(?P<grace>{(?P<acciaccatura>/?)(?P<gracenote>[^}]*)})'
    def __init__(self):
        super(AbcBaseNote, self).__init__('Grace notes', AbcGraceNotes.pattern, display_name=_('Grace notes'))
        self.visible_match_group = 'gracenote'


class AbcNoteGroup(AbcBaseNote):
    note_group_pattern_prefix = r'(?P<gracenotes>{0}?)(?P<chordsymbols>{1}?)(?P<decoanno>(?P<decorations>{2})|(?P<annotations>{3})*)'.format(
                                AbcGraceNotes.pattern, AbcChordSymbol.basic_pattern, AbcDecoration.pattern, AbcAnnotation.pattern)
    note_group_pattern_postfix = AbcBaseNote.pair_pattern + AbcBaseNote.tie_pattern

    note_pattern = note_group_pattern_prefix + AbcBaseNote.basic_note_pattern + note_group_pattern_postfix
    normal_rest_pattern = note_group_pattern_prefix + AbcBaseNote.basic_rest_pattern + AbcBaseNote.pair_pattern
    note_or_rest_pattern = note_group_pattern_prefix + AbcBaseNote.basic_note_or_rest_pattern

    chord_pattern = r'(?P<chord>{0}\[(?:{1}\s*)*\])'.format(note_group_pattern_prefix, remove_named_groups(note_or_rest_pattern)) + AbcBaseNote.length_pattern + note_group_pattern_postfix
    note_or_chord_pattern = r'({0}|{1})'.format(remove_named_groups(note_or_rest_pattern), remove_named_groups(chord_pattern)) + note_group_pattern_postfix
    def __init__(self):
        super(AbcNoteGroup, self).__init__('Note group', AbcNoteGroup.note_or_chord_pattern, display_name=_('Note group')) # '^{0}$'.format(AbcNoteGroup.pattern))
        #self.exact_match_required = True
        self.visible_match_group = 1


class AbcNoteOrChord(AbcBaseNote):
    pattern = AbcNoteGroup.note_or_chord_pattern
    def __init__(self):
        super(AbcBaseNote, self).__init__('Note or chord', AbcNoteOrChord.pattern, display_name=_('Note or chord'))


class AbcChord(AbcBaseNote):
    pattern = AbcNoteGroup.chord_pattern
    def __init__(self):
        super(AbcBaseNote, self).__init__('Chord', AbcChord.pattern, display_name=_('Chord'))
        self.visible_match_group = 'chord'


class AbcNote(AbcBaseNote):
    pattern = AbcNoteGroup.note_pattern
    def __init__(self):
        super(AbcNote, self).__init__('Note', '({0})'.format(AbcNote.pattern), display_name=_('Note'))
        self.removable_match_groups = {
            'grace': _('Grace notes'),
            'chordsymbol': _('Chord symbol'),
            'annotations': _('Annotation')
        }
        self.visible_match_group = 1


class AbcNormalRest(AbcBaseNote):
    pattern = AbcNoteGroup.normal_rest_pattern
    def __init__(self):
        super(AbcNormalRest, self).__init__('Rest', AbcNormalRest.pattern, display_name=_('Rest'))
        self.visible_match_group = 0


class AbcMeasureRest(AbcBaseNote):
    pattern = AbcBaseNote.basic_measure_rest_pattern
    def __init__(self):
        super(AbcMeasureRest, self).__init__('Measure rest', AbcMeasureRest.pattern, display_name=_('Measure rest')) # _('This rest spans one or more measures.')
        self.visible_match_group = 0


class AbcMultipleNotesAndChords(AbcBaseNote):
    pattern = '(?:' +  AbcNoteGroup.note_or_chord_pattern + '[ `]*){2,}'
    def __init__(self):
        super(AbcMultipleNotesAndChords, self).__init__('Multiple notes/chords', '^{0}$'.format(AbcMultipleNotesAndChords.pattern), display_name=_('Multiple notes/chords'))
        self.tune_scope = TuneScope.SelectedText # a line always contains multiple notes so limit to selected text


class AbcMultipleNotes(AbcBaseNote):
    pattern = '(?:' + AbcNoteGroup.note_or_rest_pattern + '[ `]*){2,}'
    def __init__(self):
        super(AbcMultipleNotes, self).__init__('Multiple notes', '^{0}$'.format(AbcMultipleNotes.pattern), display_name=_('Multiple notes'))
        self.tune_scope = TuneScope.SelectedText # a line always contains multiple notes so limit to selected text


class AbcBackslash(AbcBodyElement):
    pattern = r'\\[ \t]*$'
    def __init__(self):
        super(AbcBackslash, self).__init__('Backslash', AbcBackslash.pattern, display_name=_('Backslash'), description=_('In abc music code, by default, line-breaks in the code generate line-breaks in the typeset score and these can be suppressed by using a backslash.'))


class AbcStructure(object):
    # static variables
    replace_regexes = None
    valid_directive_re = None
    from_to_directive_re = None
    abc_field_re = None

    @staticmethod
    def get_sections(cwd):
        # [1.3.6.2 [JWDJ] bugfix This fixes 'str>ng' in Fields and Command Reference
        reference_content = io.open(os.path.join(cwd, 'reference.txt'), 'r', encoding='latin-1').read()
        if AbcStructure.replace_regexes is None:
            AbcStructure.replace_regexes = [
                (re.compile(r'\bh((?:bass/chord|length|logical|string|int|fl-?\n?oat\s?|command|str|text|vol|h|n|char|clef|bass|chord)\d*\s?(?: (?:string|int|float)\d*?)*)i\b'), r'<\1>'),  # enclose types with < and >
                (re.compile(r'\[((?:bass/chord|length|logical|string|int|float|command|str|text|vol)\d*)\]'), r'<\1>'),  # replace types enclosed [ and ] with < and >
                (re.compile(r'(?m)\b(?<![- ])1\d\d[\s\n]+[A-Z]+[A-Z\s\.&]+$'), ''),  # strip left page header
                (re.compile(r'\bA\.\d+\.[\s\n]+[A-Z &]*1\d\d\b'), ''),  # strip right page header
                (re.compile(r'[\.,;]\s[\w\n\s]+Section\s(\d\.|[\d\w\s&:])*\.'), '.'),  # removes references to sections
                (re.compile(r' as was seen in Section \d+(\.\d+)*\.'), '.'),  # removes references to sections
                (re.compile(r'(?m)^(\w:)\s+((?:[a-z]+\s(?:in|of)\s)?(?:header(?:,\s?body)?|body))\s+(.*)$'), r'\1 \3 (\2)'),  # places where-field at the end of description
                (re.compile(r'\bh(\d+-\d+)i\b'), '(\1)')  # fix midi numbers (0-127)
            ]
            AbcStructure.valid_directive_re = re.compile(r'^%%\w+(\s[^:\n]*|\.\.\.[^:\n]*)?:')  # 1.3.6.2 [JWDJ] 2015-03 fixes false positives
            AbcStructure.from_to_directive_re = re.compile(r'(%%\w+)\.\.\.(%%\w+)')
            AbcStructure.abc_field_re = re.compile(r'[A-Za-z]:')

        reference_content = reference_content.replace(unichr(150), '-')
        reference_content = replace_text(reference_content, AbcStructure.replace_regexes)

        lines = reference_content.splitlines()

        for i in range(len(lines)):
            lines[i] = lines[i].replace('hinti', '<int>')
            lines[i] = lines[i].replace('%%MIDI drumoff turns', '%%MIDI drumoff: turns')
            lines[i] = lines[i].replace('%%MIDI drumon turns', '%%MIDI drumon: turns')

        sections = []
        cur_section = []
        abc_fields_done = False
        for line in lines:
            line = line.rstrip()
            if line.startswith('A.'):
                title = line.split(' ', 1)[1]
                cur_section = []
                sections.append((title, cur_section))
            elif AbcStructure.valid_directive_re.search(line): # 1.3.6.2 [JWDJ] 2015-03 fixes false positives
                abc_fields_done = True
                cur_section.append(line)
            elif not abc_fields_done and AbcStructure.abc_field_re.match(line):
                cur_section.append(line)
            elif cur_section: # join two lines
                if cur_section[-1].endswith('-'):
                    cur_section[-1] = cur_section[-1][:-1] + line
                else:
                    cur_section[-1] = cur_section[-1] + ' ' + line

        for i in range(len(sections)):
            section_name, lines = sections[i]
            tuples = []
            for line in lines:
                if AbcStructure.abc_field_re.match(line):
                    name, desc = line.split(' ', 1)
                    tuples.append((name, desc))
                elif len(line.split(': ', 1)) == 2:
                    name, desc = tuple(line.split(': ', 1))
                    m = AbcStructure.from_to_directive_re.match(name)
                    if m:
                        tuples.append((m.group(1), desc))
                        tuples.append((m.group(2), desc))
                    else:
                        tuples.append((name, desc))

            sections[i] = section_name, tuples
        return sections


    @staticmethod
    def generate_abc_elements(cwd):
        directive = AbcDirective()
        midi_directive = AbcMidiDirective()
        directive.add_element(midi_directive)

        # [JWDJ] the order of elements in result is very important, because they get evaluated first to last
        result = [
            AbcEmptyDocument(),
            AbcEmptyLineWithinTuneHeader(),
            AbcEmptyLineWithinTuneBody(),
            AbcEmptyLineWithinFileHeader(),
            AbcEmptyLine(),
            AbcVersionDirective(),
            AbcMidiProgramDirective(),
            AbcMidiChordProgramDirective(),
            AbcMidiBaseProgramDirective(),
            AbcMidiChannelDirective(),
            AbcMidiDrumMapDirective(),
            AbcMidiVolumeDirective(),
            AbcMidiGuitarChordDirective(),
            ScoreDirective(),
            MeasureNumberDirective(),
            HideFieldsDirective(),
            ShowFieldsDirective(),
            directive,
            AbcComment(),
            AbcBeam(),
            AbcBackslash(),
        ]

        elements_by_keyword = {}
        lines = abc_keywords.splitlines()
        for line in lines:
            parts = line.split('|')
            keyword = parts[0].strip()
            name = parts[1].strip()
            file_header = parts[2].strip() == 'yes'
            tune_header = tune_header_lookup[parts[3].strip()]
            tune_body = parts[4].strip() == 'yes'
            inline = parts[5].strip() == 'yes'
            abc_type = parts[6].strip()
            if abc_type == 'instruction':
                element = AbcInstructionField(name, keyword, file_header, tune_header, tune_body, inline, abc_inner_pattern.get(keyword, '.*'))
            elif abc_type == 'string':
                element = AbcStringField(name, keyword, file_header, tune_header, tune_body, inline)
            else:
                raise Exception('Unknown abc-type')
            result.append(element)
            elements_by_keyword[element.keyword] = element

        for (title, fields) in AbcStructure.get_sections(cwd):
            for (field_name, description) in fields:
                parts = field_name.split('<', 1)
                keyword = parts[0].rstrip()
                name = keyword
                element_holder = None
                if name.startswith('%%'):
                    name = name[2:]
                    if name[0:4] == 'MIDI':
                        element_holder = midi_directive
                        name = name[5:]
                        keyword = name
                    else:
                        element_holder = directive

                if element_holder:
                    existing_element = element_holder.get_element(keyword)
                else:
                    existing_element = elements_by_keyword.get(keyword)

                if existing_element is not None:
                    element.description = description
                else:
                    if element_holder:
                        if element_holder ==  midi_directive:
                            element = AbcElement(field_name, name, description=description)
                            midi_directive.add_element(element)
                        else:
                            element = Abcm2psDirective(field_name, name, description=description)
                            directive.add_element(element)
                    else:
                        if len(name) == 2 and name[-1] == ':':
                            element = AbcElement(field_name, name, description=description)
                            elements_by_keyword[keyword] = element
                            result.append(element)

                    for part in parts[1:]:
                        param = part.strip()
                        if param[-1] == '>':
                            param = param[:-1]
                        element.params.append(param)

        # elements = sorted(elements, key=lambda element: -len(element.keyword))  # longest match first

        symbol_line = [element for element in result if element.keyword == 's:'][0]
        result = [element for element in result if element.keyword != 's:']

        # [JWDJ] the order of elements in result is very important, because they get evaluated first to last
        result += [
            AbcAnnotation(),
            AbcChordSymbol(),
            AbcChordOrAnnotation(),
            AbcTuplet(),
            AbcVariantEnding(),
            AbcBar(),
            AbcDynamicsDecoration(),
            AbcFingeringDecoration(),
            AbcOrnamentDecoration(),
            AbcDirectionDecoration(),
            AbcArticulationDecoration(),
            AbcDecoration(),
            symbol_line,
            AbcGraceNotes(),
            AbcSlur(),
            AbcMultipleNotes(),
            AbcMultipleNotesAndChords(),
            AbcChord(),
            AbcNote(),
            AbcNormalRest(),
            AbcMeasureRest(),
            AbcVoiceOverlay(),
            AbcBrokenRhythm(),
            AbcInvalidCharacter(),
            TypesettingSpace(),
            RedefinableSymbol(),
            AbcSpace(),
            AbcUnknown()
        ]

        elements_by_keyword['V:'].visible_match_group = 'name'

        for element in result:
            try:
                element.freeze()
            except Exception as ex:
                print('Exception in element {0}: {1}'.format(element.name, ex))
                logging.exception(ex)

        return result
