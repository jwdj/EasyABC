import re
import os
from collections import namedtuple
from tune_elements import *
from wx import GetTranslation as _
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2
import urllib
import webbrowser
from fraction import Fraction

UrlTuple = namedtuple('UrlTuple', 'url content')
CodeDescription = namedtuple('CodeDescription', 'code description')


key_ladder = 'Fb Cb Gb Db Ab Eb Bb F C G D A E B F# C# G# D# A# E# B#'
key_mode = {
    _('Major'): -2,
    _('Minor'): 1,
    _('Ionian'): -2,
    _('Aeolian'): 1,
    _('Dorian'): 0,
    _('Mixolydian'): -1,
    _('Phrygian'): 2,
    _('Lydian'): -3,
    _('Locrian'): 3
}

key_base = {
    _('6 sharps'):  	 6,
    _('5 sharps'):       5,
    _('4 sharps'):       4,
    _('3 sharps'):       3,
    _('2 sharps'):       2,
    _('1 sharp'):  	     1,
    _('0 sharps/flats'): 0,
    _('1 flat'):       	-1,
    _('2 flats'):       -2,
    _('3 flats'):       -3,
    _('4 flats'):       -4,
    _('5 flats'):       -5,
    _('6 flats'):       -6,
}


def html_enclose(tag, content):
    return u'<%s>%s</%s>' % (tag, content, tag)

def html_enclose_attr(tag, attributes, content):
    attr_text = u''
    for attribute in attributes:
        attr_text += ' %s="%s"' % (attribute, attributes[attribute])
    return u'<%s%s>%s</%s>' % (tag, attr_text, content, tag)

def url_tuple_to_href(value):
    if type(value) == UrlTuple:   # isinstance(obj, tuple)
        return html_enclose_attr('a', { 'href': value.url }, value.content)
    return value

def html_enclose_item(tag, item):
    item = url_tuple_to_href(item)
    return html_enclose(tag, item)

def html_enclose_items(tag, items):
    items = url_tuple_to_href(items)
    if isinstance(items, CodeDescription):
        items = (html_enclose('code', escape(items.code)), escape(items.description))

    if isinstance(items, (list, tuple)):
        result = u''
        for item in items:
            result += html_enclose_item(tag, item)
    elif isinstance(items, dict):
        result = u''
        for item in items:
            result += html_enclose_items(tag, items[item])
    else:
        result = html_enclose_item(tag, items)
    return result

def html_table(rows, headers=None):
    result = u''
    if headers:
        result = html_enclose_items('th', headers)
    for row in rows:
        row_data = html_enclose_items('td', row)
        result += html_enclose('tr', row_data)

    return html_enclose('table', result)


class AbcAction(object):
    def __init__(self, name, display_name=None, group=None):
        self.name = name
        if display_name:
            self.display_name = display_name
        else:
            self.display_name = _(name)
        self.group = group

    def can_execute(self, context, params=None):
        return False

    def execute(self, context, params=None):
        pass

    def get_action_html(self, context):
        if self.can_execute(context):
            return u'<a href="%s">%s</a>' % (self.name, escape(self.display_name))
        return u''

    def get_action_url(self, params=None):
        if params is None:
            return self.name
        else:
            return '{0}?{1}'.format(self.name, urllib.urlencode(params))


class ValueChangeAction(AbcAction):
    def __init__(self, name, supported_values, matchgroup=None, display_name=None):
        super(ValueChangeAction, self).__init__(name, display_name=display_name)
        self.supported_values = supported_values
        self.matchgroup = matchgroup

    def can_execute(self, context, params=None):
        value = params.get('value', '')
        if self.matchgroup:
            if context.current_match:
                current_value = context.current_match.group(self.matchgroup)
                return value != current_value
        else:
            return value != context.match_text

    def execute(self, context, params=None):
        value = params.get('value', '')
        context.replace_match_text(value, self.matchgroup)

    def get_action_html(self, context):
        result = u''
        if self.display_name:
            result = html_enclose('h4', escape(self.display_name))
        html_values = []
        for value in self.supported_values:
            if isinstance(value, CodeDescription):
                params = {'value': value.code}
                if self.can_execute(context, params):
                    t = (html_enclose('code', escape(value.code)), UrlTuple(self.get_action_url(params), escape(value.description)))
                    html_values.append(t)
                else:
                    html_values.append(value)
            elif isinstance(value, list):
                columns = value
                row = []
                for column in columns:
                    params = {'value': column}
                    html_column = html_enclose('code', escape(column))
                    if self.can_execute(context, params):
                        t = UrlTuple(self.get_action_url(params), html_column)
                        row.append(t)
                    else:
                        row.append(html_column)
                html_values.append(row)
            else:
                params = {'value': value}
                if self.can_execute(context, params):
                    t = UrlTuple(self.get_action_url(params), escape(value))
                    html_values.append(t)
                else:
                    html_values.append(escape(value))
        result += html_table(html_values)
        return result

class InsertValueAction(ValueChangeAction):
    def __init__(self, name, supported_values, valid_sections=None, display_name=None):
        super(InsertValueAction, self).__init__(name, supported_values, display_name=display_name)
        self.valid_sections = valid_sections

    def can_execute(self, context, params=None):
        if self.valid_sections is None:
            return True
        if isinstance(self.valid_sections, list):
            return context.abc_section in self.valid_sections
        else:
            return context.abc_section == self.valid_sections

    def execute(self, context, params=None):
        context.insert_text(params['value'])

    def get_action_html(self, context):
        if self.can_execute(context):
            return super(InsertValueAction, self).get_action_html(context)
        return u''


class RemoveValueAction(AbcAction):
    def __init__(self, matchgroup=None):
        super(RemoveValueAction, self).__init__('Remove', matchgroups)
        self.matchgroups = matchgroups

    def can_execute(self, context, params=None):
        matchgroup = params.get('matchgroup', '')
        if matchgroup:
            return context.get_matchgroup(matchgroup)
        else:
            return True

    def execute(self, context, params=None):
        matchgroup = params.get('matchgroup', '')
        context.replace_match_text('', matchgroup)





##################################################################################################
#  CHANGE ACTIONS
##################################################################################################


class AccidentalChangeAction(ValueChangeAction):
    accidentals = [
        CodeDescription('',   _('No accidental')),
        CodeDescription('=',  _('Natural')),
        CodeDescription('^',  _('Sharp')),
        CodeDescription('_',  _('Flat')),
        CodeDescription('^^', _('Double sharp')),
        CodeDescription('__', _('Double flat'))
    ]
    def __init__(self):
        super(AccidentalChangeAction, self).__init__('Accidental', AccidentalChangeAction.accidentals, matchgroup='accidental')


class MeterChangeAction(ValueChangeAction):
    values = [
        CodeDescription('C',   _('Common time (4/4)')),
        CodeDescription('C|',  _('Cut time (2/2)')),
        CodeDescription('4/4', _('4/4')),
        CodeDescription('3/4', _('3/4')),
        CodeDescription('2/4', _('2/4')),
        CodeDescription('2/2', _('2/2')),
        CodeDescription('6/8', _('6/8'))
    ]
    def __init__(self):
        super(MeterChangeAction, self).__init__('Change meter', MeterChangeAction.values, matchgroup=1)


class UnitNoteLengthChangeAction(ValueChangeAction):
    values = [
        CodeDescription('1/2',  _('half note')),
        CodeDescription('1/4',  _('quarter note')),
        CodeDescription('1/8',  _('eighth note')),
        CodeDescription('1/16', _('sixteenth note'))
    ]
    def __init__(self):
        super(UnitNoteLengthChangeAction, self).__init__('Change note length', UnitNoteLengthChangeAction.values, matchgroup=1)

class PitchAction(ValueChangeAction):
    pitch_values = [
        CodeDescription("'", _('Octave up')),
        CodeDescription(",", _('Octave down')),
    ]
    def __init__(self):
        super(PitchAction, self).__init__('Pitch', PitchAction.pitch_values, matchgroup='octave')

    def can_execute(self, context, params=None):
        value = params.get('value')
        note = context.get_matchgroup('note')
        octave = self.octave_abc_to_number(note, context.get_matchgroup('octave'))
        if value == "'":
            return octave < 4
        elif value == ',':
            return octave > -4
        return False

    def execute(self, context, params=None):
        value = params.get('value')
        note = context.get_matchgroup('note')
        octave = context.get_matchgroup('octave')
        octave_no = self.octave_abc_to_number(note, octave)
        if value == "'":
            octave_no += 1
        elif value == ',':
            octave_no -= 1

        if octave_no > 0:
            note = note.lower()
        else:
            note = note.upper()

        if octave_no > 1:
            octave = "'" * (octave_no-1)
        elif octave_no < 0:
            octave = "," * -octave_no
        else:
            octave = ''

        context.replace_matchgroups([('note', note), ('octave', octave)])

    @staticmethod
    def octave_abc_to_number(note, abc_octave):
        result = 0
        if note.islower():
            result += 1
        if abc_octave:
            for ch in abc_octave:
                if ch == "'":
                    result += 1
                elif ch == ',':
                    result -= 1
        return result


class DurationAction(ValueChangeAction):
    denominator_re = re.compile('/(\d*)')
    duration_values = [
        CodeDescription('', _('Default length')),
        CodeDescription('/', _('Halve note length')),
        CodeDescription('2', _('Double note length')),
        CodeDescription('3', _('Dotted note')),
        CodeDescription('>', _('This note dotted, next note halved')),
        CodeDescription('<', _('This note halved, next note dotted'))
    ]
    def __init__(self):
        super(DurationAction, self).__init__('Duration', DurationAction.duration_values)

    @staticmethod
    def length_to_fraction(length):
        result = Fraction(1, 1)
        if length:
            parts = length.split('/', 1)
            numerator_part = parts[0].strip()
            denominator_part = ''
            if len(parts) > 1:
                denominator_part = '/'+parts[1].strip()
            if numerator_part:
                result = Fraction(int(numerator_part), 1)
            for m in DurationAction.denominator_re.finditer(denominator_part):
                divisor = m.groups()[0]
                if divisor:
                    divisor = int(divisor)
                else:
                    divisor = 2
                result = result * Fraction(1, divisor)
            result.reduce()
        return result

    @staticmethod
    def is_power2(num):
        return ((num & (num - 1)) == 0) and num != 0

    def can_execute(self, context, params=None):
        value = params.get('value')
        if not value:
            return context.get_matchgroup('pair') or context.get_matchgroup('length')
        elif value in '<>':
            return not value in context.get_matchgroup('pair', '')
        else:
            frac = self.length_to_fraction(context.get_matchgroup('length'))
            if value == '/':
                return frac.denominator < 128
            elif value == '2':
                return frac.numerator < 16
            elif value == '3':
                return self.is_power2(frac.numerator) and self.is_power2(frac.denominator)

    def execute(self, context, params=None):
        value = params.get('value')
        if not value:
            context.replace_matchgroups([('length', ''), ('pair', '')])
        elif value in '/23':
            frac = self.length_to_fraction(context.get_matchgroup('length'))
            if value == '/':
                frac.denominator *= 2
            elif value == '2':
                frac.numerator *= 2
            elif value == '3':
                frac.numerator *= 3
                frac.denominator *= 2
            frac.reduce()

            if frac.numerator == 1:
                text = ''
            else:
                text =str(frac.numerator)

            if frac.denominator != 1:
                if frac.denominator == 2:
                    text += '/'
                elif frac.denominator == 4:
                    text += '//'
                else:
                    text += '/{0}'.format(frac.denominator)
            context.replace_match_text(text, matchgroup='length')
        elif value in '<>':
            context.replace_match_text(value, matchgroup='pair')


class TempoChangeAction(ValueChangeAction):
    tempo_names = {
        'Larghissimo'  :  40,
        'Adagissimo'   :  44,
        'Lentissimo'   :  48,
        'Largo'        :  56,
        'Adagio'       :  59,
        'Lento'        :  62,
        'Larghetto'    :  66,
        'Adagietto'    :  76,
        'Andante'      :  88,
        'Andantino'    :  96,
        'Moderato'     : 104,
        'Allegretto'   : 112,
        'Allegro'      : 120,
        'Vivace'       : 168,
        'Vivo'         : 180,
        'Presto'       : 192,
        'Allegrissimo' : 208,
        'Vivacissimo'  : 220,
        'Prestissimo'  : 240,
    }
    def __init__(self):
        super(TempoChangeAction, self).__init__('Change tempo', TempoChangeAction.tempo_names, 1)


class AnnotationPositionAction(ValueChangeAction):
    values = [
        CodeDescription('^', _('Above')),
        CodeDescription('_', _('Below')),
        CodeDescription('<', _('Left')),
        CodeDescription('>', _('Right')),
        CodeDescription('@', _('Auto'))
    ]
    def __init__(self):
        super(AnnotationPositionAction, self).__init__('Position', AnnotationPositionAction.values, 'pos')


class BarChangeAction(ValueChangeAction):
    values = [
        CodeDescription('|',  _('Bar line')),
        CodeDescription('||', _('Double bar line')),
        CodeDescription('|]', _('Thin-thick double bar line')),
        CodeDescription('[|', _('Thick-thin double bar line')),
        CodeDescription('|:', _('Start of repeated section')),
        CodeDescription(':|', _('End of repeated section')),
        CodeDescription('|1', _('First ending')),
        CodeDescription(':|2', _('Second ending')),
        CodeDescription('&',  _('Voice overlay'))
    ]
    def __init__(self):
        super(BarChangeAction, self).__init__('Change bar', BarChangeAction.values)


class RestVisibilityChangeAction(ValueChangeAction):
    values = [
        CodeDescription('z',  _('Visible')),
        CodeDescription('x',  _('Hidden')),
    ]
    def __init__(self):
        super(RestVisibilityChangeAction, self).__init__('Change visibility', RestVisibilityChangeAction.values, 'rest')


class MeasureRestVisibilityChangeAction(ValueChangeAction):
    values = [
        CodeDescription('Z',  _('Visible')),
        CodeDescription('X',  _('Hidden')),
    ]
    def __init__(self):
        super(MeasureRestVisibilityChangeAction, self).__init__('Change visibility', MeasureRestVisibilityChangeAction.values, 'measurerest')

##################################################################################################
#  URL ACTIONS
##################################################################################################


class UrlAction(AbcAction):
    def __init__(self, url):
        super(AbcAction, self).__init__('link')
        self.url = url

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        webbrowser.open(href)

    def get_action_html(self, context):
        return _('Learn <a href="{0}">more</a>...').format(self.url)


class Abcm2psUrlAction(UrlAction):
    def __init__(self, keyword):
        url = 'http://moinejf.free.fr/abcm2ps-doc/{0}.xhtml'.format(urllib.quote(keyword))
        super(AbcAction, self).__init__(url)


class Abc2MidiUrlAction(UrlAction):
    def __init__(self, keyword):
        url = 'http://ifdo.pugmarks.com/~seymour/runabc/abcguide/abc2midi_body.html#{0}'.format(urllib.quote(keyword))
        super(AbcAction, self).__init__(url)


##################################################################################################
#  INSERT ACTIONS
##################################################################################################


class NewTuneAction(AbcAction):
    tune_re = re.compile(r'(?m)^X:\s*(\d+)')

    def __init__(self):
        super(NewTuneAction, self).__init__('abc_new_tune', display_name=_('New tune'))

    def can_execute(self, context, params=None):
        return context.previous_line is None or context.current_element.matches_text(context, context.previous_line) is not None

    def execute(self, context, params=None):
        last_tune_id = 0
        for m in NewTuneAction.tune_re.finditer(context.get_full_text()):
            last_tune_id = max(last_tune_id, int(m.group(1)))

        new_tune_id = last_tune_id + 1
        text = u'X:%d' % new_tune_id
        text += os.linesep + 'T:' + _('Untitled') + '%d' % new_tune_id
        text += os.linesep + 'C:' + _('Unknown composer')
        text += os.linesep + 'M:4/4'
        text += os.linesep + 'L:1/4'
        text += os.linesep + 'K:C' + os.linesep
        context.insert_text(text)


class NewNoteAction(InsertValueAction):
    values = ['c d e f g a b'.split(' '), 'C D E F G A B'.split(' ')]
    def __init__(self):
        super(NewNoteAction, self).__init__('abc_new_note', supported_values=NewNoteAction.values,
                                            valid_sections=ABC_SECTION_TUNE_BODY, display_name=_('Add note'))


class NewRestAction(InsertValueAction):
    values = [
        CodeDescription('z', _('Normal rest')),
        CodeDescription('Z', _('Measure rest')),
        CodeDescription('x', _('Invisible rest')),
    ]
    def __init__(self):
        super(NewRestAction, self).__init__('abc_new_rest', supported_values=NewRestAction.values,
                                            valid_sections=ABC_SECTION_TUNE_BODY, display_name=_('Add rest'))


class InsertOptionalAccidental(InsertValueAction):
    values = [
        CodeDescription('"<(\u266f)"', _('Optional sharp')),
        CodeDescription('"<(\u266e)"', _('Optional natural')),
        CodeDescription('"<(\u266d)"', _('Optional flat'))
    ]
    def __init__(self):
        super(InsertOptionalAccidental, self).__init__('Insert annotation', InsertOptionalAccidental.values)


##################################################################################################
#  REMOVE ACTIONS
##################################################################################################





##################################################################################################
#  ACTION HANDLERS
##################################################################################################


class AbcActionHandler(object):
    def __init__(self, actions = None):
        self._actions_by_name = {}
        self._actions_ordered = []
        if actions is not None:
            for action in actions:
                self.add_action(action)

    def add_action(self, action):
        self._actions_ordered.append(action)
        self._actions_by_name[action.name] = action

    def get_action(self, name):
        return self._actions_by_name.get(name)

    def get_action_html(self, context):
        result = u''
        for action in self._actions_ordered:
            result += action.get_action_html(context)
        return result


class KeyActionHandler(AbcActionHandler):
    def __init__(self):
        super(KeyActionHandler, self).__init__()
        action = AbcAction('c', 'hallo')
        self.add_action(action)

    def row(self, content):
        return html_enclose('tr', content)

    def get_action_html(self, context):
        headers = (_('Tonic'), _('Mode'), _('Sharps/flats'))
        result = self.row(html_enclose_items('th', headers))
        return html_enclose('table', result)


class AbcActionHandlers(object):
    def __init__(self):
        self.default_action_handler = AbcActionHandler()
        self.action_handlers = {
            'K:'         : KeyActionHandler(),
            'Empty line' : AbcActionHandler([NewTuneAction(), NewNoteAction(), NewRestAction()]),
            'Whitespace' : AbcActionHandler([NewNoteAction(), NewRestAction()]),
            'Note'       : AbcActionHandler([AccidentalChangeAction(), DurationAction(), PitchAction(),
                                             InsertOptionalAccidental()]),
            'Rest'       : AbcActionHandler([DurationAction(), RestVisibilityChangeAction()]),
            'Measure rest': AbcActionHandler([MeasureRestVisibilityChangeAction()]),
            'Bar'        : AbcActionHandler([BarChangeAction()]),
            'M:'         : AbcActionHandler([MeterChangeAction()]),
            'Q:'         : AbcActionHandler([TempoChangeAction()]),
            'Annotation' : AbcActionHandler([AnnotationPositionAction()]),
            'L:'         : AbcActionHandler([UnitNoteLengthChangeAction()]),

        }

    def get_action_handler(self, element):
        if element:
            key = element.keyword or element.name
            return self.action_handlers.get(key, self.default_action_handler)
        return self.default_action_handler

