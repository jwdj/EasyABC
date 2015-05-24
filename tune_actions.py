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

def html_enclose(tag, content):
    return u'<{0}>{1}</{0}>'.format(tag, content)

def html_enclose_attr(tag, attributes, content):
    attr_text = u''
    for attribute in attributes:
        attr_text += ' {0}="{1}"'.format(attribute, attributes[attribute])
    return u'<{0}{1}>{2}</{0}>'.format(tag, attr_text, content)

def url_tuple_to_href(value):
    if type(value) == UrlTuple:
        return html_enclose_attr('a', { 'href': value.url }, value.content)
    return value

def html_enclose_item(tag, item):
    item = url_tuple_to_href(item)
    return html_enclose(tag, item)

def html_enclose_items(tag, items):
    items = url_tuple_to_href(items)
    #if isinstance(items, CodeDescription):
    #    items = (html_enclose('code', escape(items.code)), escape(items.description))

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
            return u'<br>' + html_enclose_attr('a', { 'href': self.name }, escape(self.display_name))
        return u''

    def get_action_url(self, params=None):
        if params is None:
            return self.name
        else:
            return '{0}?{1}'.format(self.name, urllib.urlencode(params))


class ValueChangeAction(AbcAction):
    def __init__(self, name, supported_values, matchgroup=None, display_name=None, valid_sections=None, use_inner_match=False):
        super(ValueChangeAction, self).__init__(name, display_name=display_name)
        self.supported_values = supported_values
        self.matchgroup = matchgroup
        self.use_inner_match = use_inner_match
        self.valid_sections = valid_sections

    def can_execute(self, context, params=None):
        value = params.get('value', '')
        return not self.is_current_value(context, value)

    def is_current_value(self, context, value):
        current_value = None
        if self.matchgroup:
            match = self.get_match(context)
            if match:
                current_value = match.group(self.matchgroup)
        else:
            current_value = context.match_text
        return value == current_value

    def get_match(self, context):
        if self.use_inner_match:
            return context.inner_match
        else:
            return context.current_match

    def get_tune_scope(self):
        if self.use_inner_match:
            return TuneScope.InnerText
        else:
            return TuneScope.MatchText

    def execute(self, context, params=None):
        value = params.get('value', '')
        context.replace_match_text(value, self.matchgroup, tune_scope=self.get_tune_scope())

    def is_action_allowed(self, context):
        valid_sections = self.valid_sections
        if valid_sections is None:
           valid_sections = context.current_element.valid_sections
        if valid_sections is not None:
            if isinstance(valid_sections, list):
                if not context.abc_section in valid_sections:
                    return False
            else:
                if context.abc_section != valid_sections:
                    return False

        match = self.get_match(context)
        if match is None:
            return False
        elif self.matchgroup is not None:
            try:
                start = match.start(self.matchgroup)
            except IndexError:
                start = -1
            if start == -1:
                return False # don't show action if matchgroup not present in match
        return True

    def get_action_html(self, context):
        result = u''
        if not self.is_action_allowed(context):
            return result

        if self.display_name:
            result = html_enclose('h4', escape(self.display_name))
        else:
            result = '<br>'

        result += self.get_values_html(context)
        return result

    def get_values(self, context):
        return self.supported_values

    def get_values_html(self, context):
        result = u''
        html_values = []
        for value in self.get_values(context):
            if isinstance(value, CodeDescription):
                params = {'value': value.code}
                code_html = html_enclose('code', escape(value.code))
                desc = escape(value.description)
                if self.can_execute(context, params):
                    t = (code_html, UrlTuple(self.get_action_url(params), desc))
                else:
                    t = (code_html, self.html_selected_item(context, value.code, desc))
                html_values.append(t)
            elif isinstance(value, ValueDescription) or isinstance(value, ValueImageDescription):
                params = {'value': value.value}
                desc = escape(value.description)
                if self.can_execute(context, params):
                    if isinstance(value, ValueImageDescription):
                        image_src = 'img/{0}.png'.format(value.image_name)
                        image_html = '<img src="{0}" border="0" alt="{1}">'.format(image_src, desc)
                        t = UrlTuple(self.get_action_url(params), image_html)
                    else:
                        t = UrlTuple(self.get_action_url(params), desc)
                else:
                    t = self.html_selected_item(context, value, desc)
                html_values.append(t)
            elif isinstance(value, list):
                columns = value
                row = []
                for column in columns:
                    params = {'value': column}
                    desc = escape(column)
                    html_column = html_enclose('code', desc)
                    if self.can_execute(context, params):
                        t = UrlTuple(self.get_action_url(params), html_column)
                        row.append(t)
                    else:
                        row.append(html_column)
                html_values.append(row)
            else:
                params = {'value': value}
                desc = escape(value)
                if self.can_execute(context, params):
                    t = UrlTuple(self.get_action_url(params), desc)
                else:
                    t = self.html_selected_item(context, value, desc)
                html_values.append(t)
        result += html_table(html_values)
        return result

    @staticmethod
    def html_selected_item(context, value, description):
        # if self.is_current_value(context, value):
        #    return html_enclose('b', description)  # to make selected item bold
        return description


class InsertValueAction(ValueChangeAction):
    def __init__(self, name, supported_values, valid_sections=None, display_name=None, matchgroup=None):
        super(InsertValueAction, self).__init__(name, supported_values, valid_sections=valid_sections, display_name=display_name, matchgroup=matchgroup)
        self.relative_selection = None

    def execute(self, context, params=None):
        value = params['value']
        if self.matchgroup:
            text = context.get_matchgroup(self.matchgroup)
            text += value
            context.replace_match_text(text, self.matchgroup)
        else:
            context.insert_text(value)
        if self.relative_selection is not None:
            context.set_relative_selection(self.relative_selection)


class RemoveValueAction(AbcAction):
    def __init__(self, matchgroups=None):
        super(RemoveValueAction, self).__init__('Remove')
        self.matchgroups = matchgroups

    def can_execute(self, context, params=None):
        matchgroup = params.get('matchgroup', '')
        if self.matchgroups is not None:
            return matchgroup in self.matchgroups and context.get_matchgroup(matchgroup)
        else:
            return True

    def execute(self, context, params=None):
        matchgroup = params.get('matchgroup', '')
        context.replace_match_text('', matchgroup)


class ConvertToAnnotationAction(AbcAction):
    def __init__(self):
        super(ConvertToAnnotationAction, self).__init__('Convert to annotation')
        self.matchgroup = 'chordname'

    def can_execute(self, context, params=None):
        chord = context.get_matchgroup(self.matchgroup)
        return chord and chord[0].lower() not in 'cdefgab'

    def execute(self, context, params=None):
        annotation = '^' + context.get_matchgroup(self.matchgroup)
        context.replace_match_text(annotation, matchgroup=self.matchgroup)


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
        super(AccidentalChangeAction, self).__init__('Change accidental', AccidentalChangeAction.accidentals, matchgroup='accidental')


class MeterChangeAction(ValueChangeAction):
    values = [
        CodeDescription('C',   _('Common time (4/4)')),
        CodeDescription('C|',  _('Cut time (2/2)')),
        CodeDescription('2/4', _('2/4')),
        CodeDescription('3/4', _('3/4')),
        CodeDescription('4/4', _('4/4')),
        CodeDescription('6/4', _('6/4')),
        CodeDescription('6/8', _('6/8')),
        CodeDescription('9/8', _('9/8')),
        CodeDescription('12/8', _('12/8'))
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


class TempoNoteLengthChangeAction(ValueChangeAction):
    values = [
        CodeDescription('1/2',  _('half note')),
        CodeDescription('1/4',  _('quarter note')),
        CodeDescription('1/8',  _('eighth note')),
        CodeDescription('1/16', _('sixteenth note'))
    ]
    def __init__(self):
        super(TempoNoteLengthChangeAction, self).__init__('Change note length', TempoNoteLengthChangeAction.values, matchgroup='notelength')


class PitchAction(ValueChangeAction):
    pitch_values = [
        ValueDescription('noteup', _('Note up')),
        ValueDescription('notedown', _('Note down')),
        ValueDescription("'", _('Octave up')),
        ValueDescription(",", _('Octave down'))
    ]
    all_notes = 'CDEFGABcdefgab'
    def __init__(self):
        super(PitchAction, self).__init__('Change pitch', PitchAction.pitch_values)

    def can_execute(self, context, params=None):
        value = params.get('value')
        note = context.get_matchgroup('note')
        octave = context.get_matchgroup('octave')
        note_no = self.octave_abc_to_number(note, octave)
        if value == "'" or value == 'noteup':
            return note_no < 4*7
        elif value == ',' or value == 'notedown':
            return note_no > -4*7
        return False

    def execute(self, context, params=None):
        value = params.get('value')
        note = context.get_matchgroup('note')
        octave = context.get_matchgroup('octave')
        note_no = self.octave_abc_to_number(note, octave)
        if value == 'noteup':
            note_no += 1
        elif value == 'notedown':
            note_no -= 1
        elif value == "'":
            note_no += 7
        elif value == ',':
            note_no -= 7

        offset = 0
        if note_no >= 7:
            offset = 7
        note = PitchAction.all_notes[(note_no % 7) + offset]

        octave_no = note_no // 7
        if octave_no > 1:
            octave = "'" * (octave_no-1)
        elif octave_no < 0:
            octave = "," * -octave_no
        else:
            octave = ''

        context.replace_matchgroups([('note', note), ('octave', octave)])

    @staticmethod
    def octave_abc_to_number(note, abc_octave):
        result = PitchAction.all_notes.index(note)
        if abc_octave:
            for ch in abc_octave:
                if ch == "'":
                    result += 7
                elif ch == ',':
                    result -= 7
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
        super(DurationAction, self).__init__('Change duration', DurationAction.duration_values)

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
        super(RestVisibilityChangeAction, self).__init__('Visibility', RestVisibilityChangeAction.values, 'rest')


class MeasureRestVisibilityChangeAction(ValueChangeAction):
    values = [
        CodeDescription('Z',  _('Visible')),
        CodeDescription('X',  _('Hidden')),
    ]
    def __init__(self):
        super(MeasureRestVisibilityChangeAction, self).__init__('Visibility', MeasureRestVisibilityChangeAction.values, 'measurerest')


class AppoggiaturaOrAcciaccaturaChangeAction(ValueChangeAction):
    values = [
        CodeDescription('',   _('Appoggiatura')),
        CodeDescription('/',  _('Acciaccatura')),
    ]
    def __init__(self):
        super(AppoggiaturaOrAcciaccaturaChangeAction, self).__init__('Type', AppoggiaturaOrAcciaccaturaChangeAction.values, 'acciaccatura')


class KeyChangeAction(ValueChangeAction):
    _key_ladder = 'Fb Cb Gb Db Ab Eb Bb F C G D A E B F# C# G# D# A# E# B#'.split(' ')
    _mode_to_num = {
        '':    -2,
        'm':   +1,
        'loc': +3,
        'phr': +2,
        'min': +1,
        'dor':  0,
        'mix': -1,
        'maj': -2,
        'lyd': -3
    }

    @staticmethod
    def abc_mode_to_number(mode, default=None):
        if mode is None:
            return default
        mode = mode[:3].lower()
        return KeyChangeAction._mode_to_num.get(mode, default)


class KeySignatureChangeAction(KeyChangeAction):
    values = [
        ValueDescription( 6, _('6 sharps')),
        ValueDescription( 5, _('5 sharps')),
        ValueDescription( 4, _('4 sharps')),
        ValueDescription( 3, _('3 sharps')),
        ValueDescription( 2, _('2 sharps')),
        ValueDescription( 1, _('1 sharp')),
        ValueDescription( 0, _('0 sharps/flats')),
        ValueDescription(-1, _('1 flat')),
        ValueDescription(-2, _('2 flats')),
        ValueDescription(-3, _('3 flats')),
        ValueDescription(-4, _('4 flats')),
        ValueDescription(-5, _('5 flats')),
        ValueDescription(-6, _('6 flats')),
        ValueDescription('none', _('None')),
    ]
    def __init__(self):
        super(KeySignatureChangeAction, self).__init__('Signature', KeySignatureChangeAction.values, 1, use_inner_match=True)

    def is_action_allowed(self, context):
        return True

    def can_execute(self, context, params=None):
        if context.inner_match is None:
            return True
        tonic = context.get_matchgroup('tonic')

        value = params.get('value')
        if value == 'none':
            return tonic != value
        else:
            value = int(value)
            middle_idx = len(KeyChangeAction._key_ladder) // 2
            try:
                tonic_idx = KeyChangeAction._key_ladder.index(tonic)
            except ValueError:
                return True

            mode = context.get_matchgroup('mode')
            mode_idx = self.abc_mode_to_number(mode)
            if mode_idx is None:
                return False

            if tonic_idx >= 0 and mode_idx is not None:
                current_value = tonic_idx - middle_idx - mode_idx
                return current_value != value
            else:
                return True

    def execute(self, context, params=None):
        value = params.get('value')
        if value == 'none':
            context.replace_match_text(value, tune_scope=TuneScope.InnerText)
        else:
            value = int(value)
            middle_idx = len(KeyChangeAction._key_ladder) // 2
            new_value = middle_idx + value

            mode = context.get_matchgroup('mode')
            mode_idx = self.abc_mode_to_number(mode)
            if mode_idx is None:
                new_value -= 2 # assume major scale
                tonic = KeyChangeAction._key_ladder[new_value]
                context.replace_match_text(tonic, tune_scope=TuneScope.InnerText)
            else:
                new_value += mode_idx
                tonic = KeyChangeAction._key_ladder[new_value]
                context.replace_match_text(tonic, matchgroup='tonic')

class KeyModeChangeAction(KeyChangeAction):
    values = [
        ValueDescription(-2, _('Major (Ionian)')),
        ValueDescription(1,  _('Minor (Aeolian)')),
        ValueDescription(0,  _('Dorian')),
        ValueDescription(-1, _('Mixolydian')),
        ValueDescription(2,  _('Phrygian')),
        ValueDescription(-3, _('Lydian')),
        ValueDescription(3,  _('Locrian'))
    ]
    def __init__(self):
        super(KeyModeChangeAction, self).__init__('Mode', KeyModeChangeAction.values, 'mode', use_inner_match=True)

    def is_action_allowed(self, context):
        if context.inner_match is None:
            return False
        tonic = context.get_matchgroup('tonic')
        return tonic in KeyChangeAction._key_ladder

    def can_execute(self, context, params=None):
        tonic = context.get_matchgroup('tonic')
        if tonic in KeyChangeAction._key_ladder:
            value = int(params.get('value'))
            mode = context.get_matchgroup(self.matchgroup)
            current_value = self.abc_mode_to_number(mode)
            return value != current_value
        else:
            return False

    def execute(self, context, params=None):
        value = int(params.get('value'))
        tonic = context.get_matchgroup('tonic')
        mode = context.get_matchgroup(self.matchgroup)
        current_mode = self.abc_mode_to_number(mode)
        ladder = KeyChangeAction._key_ladder
        tonic = ladder[ladder.index(tonic) - current_mode + value]
        for mode, num in KeyChangeAction._mode_to_num.iteritems():
            if num == value:
                context.replace_matchgroups([('tonic', tonic), ('mode', mode)])
                break


class ClefChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Default')),
        ValueDescription('treble', _('Treble')),
        ValueDescription('bass', _('Bass')),
        ValueDescription('bass3', _('Baritone')),
        ValueDescription('tenor', _('Tenor')),
        ValueDescription('alto', _('Alto')),
        ValueDescription('alto2', _('Mezzosoprano')),
        ValueDescription('alto1', _('Soprano')),
        ValueDescription('perc', _('Percussion')),
        ValueDescription('none', _('None'))
    ]
    def __init__(self):
        super(ClefChangeAction, self).__init__('Clef', ClefChangeAction.values, 'clef', use_inner_match=True)

    def can_execute(self, context, params=None):
        if super(ClefChangeAction, self).can_execute(context, params):
            value = params.get('value', '')
            match = self.get_match(context)
            return match is None or value != match.group('clefname')
        return False

    def execute(self, context, params=None):
        value = params.get('value', '')
        if value and context.inner_match and context.inner_match.start('clefname') >= 0:
            context.replace_match_text(value, 'clefname', tune_scope=self.get_tune_scope())
        else:
            if value:
                params['value'] = ' clef=' + value
            super(ClefChangeAction, self).execute(context, params)


class StaffTransposeChangeAction(ValueChangeAction):
    values = [
        ValueDescription('',   _('Default')),
        ValueDescription('+8', _('Octave higher (8va)')),
        ValueDescription('-8', _('Octave lower (8va bassa)')),
    ]
    def __init__(self):
        super(StaffTransposeChangeAction, self).__init__('Staff transpose', StaffTransposeChangeAction.values, 'stafftranspose', use_inner_match=True)


class PlaybackTransposeChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Default')),
        ValueDescription(' transpose=12', _('Octave up')),
        ValueDescription(' transpose=-12', _('Octave down')),
    ]
    def __init__(self):
        super(PlaybackTransposeChangeAction, self).__init__('Playback transpose', PlaybackTransposeChangeAction.values, 'playtranspose', use_inner_match=True, valid_sections=AbcSection.TuneHeader)


class AbcOctaveChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Default')),
        ValueDescription(' octave=1', _('Octave up')),
        ValueDescription(' octave=-1', _('Octave down')),
    ]
    def __init__(self):
        super(AbcOctaveChangeAction, self).__init__('Octave shift', AbcOctaveChangeAction.values, 'octave', use_inner_match=True)


class DynamicsDecorationChangeAction(ValueChangeAction):
    def __init__(self):
        values = []
        for mark in AbcDynamicsDecoration.values:
            value = ValueImageDescription(mark, mark, decoration_to_description['!{0}!'.format(mark)])
            values.append(value)
        super(DynamicsDecorationChangeAction, self).__init__('Change dynamics mark', values, 'dynmark')


class ChordChangeAction(ValueChangeAction):
    def __init__(self):
        super(ChordChangeAction, self).__init__('Change chord', [], 'chordsymbol')

    def get_values(self, context):
        values = [
            ValueDescription('', _('No chord'))
        ]
        return values


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
        for m in NewTuneAction.tune_re.finditer(context.get_scope_info(TuneScope.FullText).text):
            last_tune_id = max(last_tune_id, int(m.group(1)))

        new_tune_id = last_tune_id + 1
        text = u'X:%d' % new_tune_id
        text += os.linesep + 'T:' + _('Untitled') + '%d' % new_tune_id
        text += os.linesep + 'C:' + _('Unknown composer')
        text += os.linesep + 'M:4/4'
        text += os.linesep + 'L:1/4'
        text += os.linesep + 'K:C' + os.linesep
        context.insert_text(text)


class NewVoiceAction(AbcAction):
    voice_re = re.compile(r'(?m)^V:\s*(\d+)')
    def __init__(self):
        super(NewVoiceAction, self).__init__('add_voice', display_name=_('Add voice'))

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        last_voice_id = 0
        for m in NewVoiceAction.voice_re.finditer(context.get_scope_info(TuneScope.TuneHeader).text):
            last_voice_id = max(last_voice_id, int(m.group(1)))

        text = u'V:{0} clef=treble'.format(last_voice_id + 1)
        context.insert_text(text)


class FixCharactersAction(AbcAction):
    def __init__(self):
        super(FixCharactersAction, self).__init__('fix_characters', display_name=_('Replace invalid characters'))

    def can_execute(self, context, params=None):
        text = context.get_scope_info(TuneScope.MatchText).text
        new_text = unicode_text_to_abc(text)
        return text != new_text

    def execute(self, context, params=None):
        scope_info = context.get_scope_info(TuneScope.MatchText)
        text = scope_info.text
        new_text = unicode_text_to_abc(text)
        context.replace_selection(new_text, scope_info.start, scope_info.start + len(text.encode('utf-8')))


class NewNoteAction(InsertValueAction):
    values = ['c d e f g a b'.split(' '), 'C D E F G A B'.split(' ')]
    def __init__(self):
        super(NewNoteAction, self).__init__('Add note', supported_values=NewNoteAction.values, valid_sections=AbcSection.TuneBody)


class NewRestAction(InsertValueAction):
    values = [
        CodeDescription('z', _('Normal rest')),
        CodeDescription('Z', _('Measure rest')),
        CodeDescription('x', _('Invisible rest')),
    ]
    def __init__(self):
        super(NewRestAction, self).__init__('Add rest', supported_values=NewRestAction.values, valid_sections=AbcSection.TuneBody)


class InsertOptionalAccidental(InsertValueAction):
    values = [
        ValueDescription('"^"', _('Empty')),
        ValueDescription('"<(\u266f)"', _('Optional sharp')),
        ValueDescription('"<(\u266e)"', _('Optional natural')),
        ValueDescription('"<(\u266d)"', _('Optional flat'))
    ]
    def __init__(self):
        super(InsertOptionalAccidental, self).__init__('Insert annotation', InsertOptionalAccidental.values, matchgroup='decoanno')
        self.relative_selection = -1


class AddDecorationAction(InsertValueAction):
    def __init__(self):
        super(AddDecorationAction, self).__init__('Insert decoration', AbcDecoration.values, matchgroup='decoanno')
        self.relative_selection = -1

    def get_action_html(self, context):
        return u''

    def get_action_html(self, context):
        result = u''
        return result
#<img src="img/fermata.png">

        for value in self.supported_values:
            if isinstance(value, CodeDescription):
                params = {'value': value.code}
                if self.can_execute(context, params):
                    t = (html_enclose('code', escape(value.code)), UrlTuple(self.get_action_url(params), escape(value.description)))
                    html_values.append(t)
                else:
                    html_values.append(value)
            elif isinstance(value, ValueDescription):
                params = {'value': value.value}
                if self.can_execute(context, params):
                    t = UrlTuple(self.get_action_url(params), escape(value.description))
                    html_values.append(t)
                else:
                    html_values.append(escape(value.description))
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


        if self.can_execute(context):
            return super(InsertValueAction, self).get_action_html(context)
        return u''


class AddSlurAction(AbcAction):
    def __init__(self):
        super(AddSlurAction, self).__init__('Add slur')

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('({0})'.format(context.match_text))

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


class AbcActionHandlers(object):
    def __init__(self, elements):
        self.default_action_handler = AbcActionHandler()
        self.action_handlers = {
            'Empty document': AbcActionHandler([NewTuneAction()]),
            'Empty line'    : AbcActionHandler([NewTuneAction(), NewNoteAction(), NewRestAction()]),
            'Whitespace'    : AbcActionHandler([NewNoteAction(), NewRestAction()]),
            'Note'          : AbcActionHandler([AccidentalChangeAction(), DurationAction(), PitchAction(), AddDecorationAction(), InsertOptionalAccidental()]),
            'Rest'          : AbcActionHandler([DurationAction(), RestVisibilityChangeAction()]),
            'Measure rest'  : AbcActionHandler([MeasureRestVisibilityChangeAction()]),
            'Bar'           : AbcActionHandler([BarChangeAction()]),
            'Annotation'    : AbcActionHandler([AnnotationPositionAction()]),
            'Chord'         : AbcActionHandler([DurationAction(), ChordChangeAction()]),
            'Chord symbol'  : AbcActionHandler([ConvertToAnnotationAction()]),
            'Grace notes'   : AbcActionHandler([AppoggiaturaOrAcciaccaturaChangeAction()]),
            'Multiple notes': AbcActionHandler([AddSlurAction()]),
            'K:'            : AbcActionHandler([KeySignatureChangeAction(), KeyModeChangeAction()]),
            'L:'            : AbcActionHandler([UnitNoteLengthChangeAction()]),
            'M:'            : AbcActionHandler([MeterChangeAction()]),
            '%'             : AbcActionHandler([FixCharactersAction()]),
            'Dynamics'      : AbcActionHandler([DynamicsDecorationChangeAction()])
        }

        for key in ['V:', 'K:']:
            self.add_actions(key, [ClefChangeAction(), StaffTransposeChangeAction(), PlaybackTransposeChangeAction(), AbcOctaveChangeAction()]) # ClefLineChangeAction()

        #for key in ['X:', 'T:']:
        #    self.add_actions(key, [NewVoiceAction()])

        for element in elements:
            if type(element) == AbcStringField:
                key = element.keyword or element.name
                self.add_actions(key, [FixCharactersAction()])


    def get_action_handler(self, element):
        if element:
            key = element.keyword or element.name
            return self.action_handlers.get(key, self.default_action_handler)
        return self.default_action_handler

    def add_actions(self, key, actions):
        action_handler = self.action_handlers.get(key)
        if action_handler is None:
            self.action_handlers[key] = AbcActionHandler(actions)
        else:
            for action in actions:
                action_handler.add_action(action)

