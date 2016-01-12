import re
import os
import sys
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
#import urlparse
from aligner import bar_sep, get_bar_length

UrlTuple = namedtuple('UrlTuple', 'url content')

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

def path2url(path):
    #url_path = urlparse.urljoin('file:', urllib.pathname2url(path))
    #url_path = re.sub(r'(/[A-Z]:/)/', r'\1', url_path) # replace double slash after drive letter with single slash
    #return url_path
    return path # wx.HtmlWindow can only handle regular path-name and not file:// notation

def html_enclose(tag, content, attributes=None):
    if attributes is None:
        return u'<{0}>{1}</{0}>'.format(tag, content)
    else:
        attr_text = u''
        for attribute in attributes:
            value = attributes[attribute]
            if value is None:
                attr_text += ' {0}'.format(attribute)
            else:
                attr_text += ' {0}="{1}"'.format(attribute, value)
        return u'<{0}{1}>{2}</{0}>'.format(tag, attr_text, content)

def html_enclose_attr(tag, attributes, content):
    return html_enclose(tag, content, attributes)

def url_tuple_to_href(value):
    if type(value) == UrlTuple:
        return html_enclose_attr('a', { 'href': value.url }, value.content)
    return value

def html_enclose_item(tag, item, attributes=None):
    item = url_tuple_to_href(item)
    return html_enclose(tag, item, attributes)

def html_enclose_items(tag, items, attributes=None):
    items = url_tuple_to_href(items)
    #if isinstance(items, CodeDescription):
    #    items = (html_enclose('code', escape(items.code)), escape(items.description))

    if isinstance(items, (list, tuple)):
        result = u''
        for item in items:
            result += html_enclose_item(tag, item, attributes)
    elif isinstance(items, dict):
        result = u''
        for item in items:
            result += html_enclose_items(tag, items[item], attributes)
    else:
        result = html_enclose_item(tag, items, attributes)
    return result

def html_table(rows, headers=None, cellpadding=0, row_has_td=False, indent=0, width=None):
    result = u''
    if headers:
        result = html_enclose_items('th', headers)
    for row in rows:
        if not row_has_td:
            row = html_enclose_items('td', row, { 'nowrap': None, 'align': 'left' })
        if indent:
            row = html_enclose('td', '', { 'width': indent}) + row
        result += html_enclose('tr', row)
    attributes = { 'cellpadding': cellpadding, 'cellspacing': 0, 'border': 0, 'align': 'left'}
    if width is not None:
        attributes['width'] = width
    return html_enclose_attr('table', attributes, result)


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
        self.relative_selection = None

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
        if self.relative_selection is not None:
            context.set_relative_selection(self.relative_selection)

    def is_action_allowed(self, context):
        valid_sections = self.valid_sections
        if valid_sections is None and context.current_element:
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
        rows = []
        if self.display_name:
            row = html_enclose('b', escape(self.display_name))
            rows.append(row)

        row = self.get_values_html(context)
        rows.append(row)
        return html_table(rows)

    def get_values(self, context):
        return self.supported_values

    def enclose_action_url(self, action_url, value):
        if action_url is not None:
            return UrlTuple(action_url, value)
        return value

    def get_values_html(self, context):
        rows = []
        show_value_column = False
        for value in self.get_values(context):
            if isinstance(value, ValueDescription):
                if value.show_value:
                    show_value_column = True
                    break

        for value in self.get_values(context):
            if isinstance(value, (CodeDescription, ValueDescription, CodeImageDescription, ValueImageDescription)):
                if value.common:
                    desc = escape(value.description)
                    params = {'value': value.value}
                    can = self.can_execute(context, params)
                    action_url = None
                    if can:
                        action_url = self.get_action_url(params)
                    columns = []
                    if show_value_column:
                        if value.show_value: #isinstance(value, (CodeDescription, CodeImageDescription)):
                            columns += [html_enclose('code', escape(value.value))]
                        else:
                            columns += [html_enclose('code', '')]

                    if isinstance(value, ValueImageDescription):
                        image_html = ''
                        image_path = '{0}/img/{1}.png'.format(application_path, value.image_name)
                        if os.path.exists(image_path):
                            image_html = '<img src="{0}" border="0" alt="{1}">'.format(path2url(image_path), desc)
                        columns += [self.enclose_action_url(action_url, image_html)]

                    if can:
                        columns += [self.enclose_action_url(action_url, desc)]
                    else:
                        columns += [self.html_selected_item(context, value.value, desc)]

                    rows.append(tuple(columns))
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
                rows.append(row)
            else:
                params = {'value': value}
                desc = escape(value)
                if self.can_execute(context, params):
                    t = UrlTuple(self.get_action_url(params), desc)
                else:
                    t = self.html_selected_item(context, value, desc)
                rows.append(t)

        result = html_table(rows, cellpadding=2, indent=20)
        if result is None:
            result = ''
        return result

    @staticmethod
    def html_selected_item(context, value, description):
        # if self.is_current_value(context, value):
        #    return html_enclose('b', description)  # to make selected item bold
        return description


class InsertValueAction(ValueChangeAction):
    def __init__(self, name, supported_values, valid_sections=None, display_name=None, matchgroup=None):
        super(InsertValueAction, self).__init__(name, supported_values, valid_sections=valid_sections, display_name=display_name, matchgroup=matchgroup)

    def can_execute(self, context, params=None):
        return True

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


class DirectiveChangeAction(ValueChangeAction):
    def __init__(self, directive_name, name, supported_values, valid_sections=None, display_name=None, matchgroup=None):
        super(DirectiveChangeAction, self).__init__(name, supported_values, valid_sections=valid_sections, display_name=display_name, matchgroup=matchgroup)
        self.directive_name = directive_name


##################################################################################################
#  CHANGE ACTIONS
##################################################################################################


class AccidentalChangeAction(ValueChangeAction):
    accidentals = [
        CodeDescription('',   _('No accidental')),
        CodeDescription('=',  _('Natural')),
        CodeDescription('^',  _('Sharp')),
        CodeDescription('_',  _('Flat')),
        CodeDescription('^^', _('Double sharp'), common=False),
        CodeDescription('__', _('Double flat'), common=False),
        CodeDescription('^/', _('Half sharp'), common=False),
        CodeDescription('_/', _('Half flat'), common=False),
        CodeDescription('^3/2', _('Sharp and a half'), common=False),
        CodeDescription('_3/2', _('Flat and a half'), common=False)
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
    def __init__(self, values):
        super(DurationAction, self).__init__('Change duration', values)
        self.max_length_denominator = 128
        self.max_length_numerator = 16
        self.fraction_allowed = True

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
        elif value == '1':
            return context.get_matchgroup('length')
        elif value == '-':
            return context.get_matchgroup('rest') is None # a rest can not have a tie, chord and note can
        elif value in '<>':
            return True # not value in context.get_matchgroup('pair', '')
        elif value in ['z', 'Z']:
            return True
        else:
            frac = self.length_to_fraction(context.get_matchgroup('length'))
            if value == '/':
                if self.fraction_allowed:
                    return frac.denominator < self.max_length_denominator
                else:
                    return frac.numerator > 1 and frac.numerator % 2 == 0
            elif value in ['2', '+']:
                return frac.numerator < self.max_length_numerator
            elif value == '3':
                return self.is_power2(frac.numerator) and self.is_power2(frac.denominator)
            elif value == '=':
                return frac.numerator > 1


    def execute(self, context, params=None):
        value = params.get('value')
        if not value:
            context.replace_matchgroups([('length', ''), ('pair', '')])
        elif value == 'Z':
            match = context.get_matchgroup('rest')
            if match == 'z':
                new_value = 'Z'
            elif match == 'x':
                new_value = 'X'
            context.replace_matchgroups([('rest', new_value), ('length', ''), ('pair', '')])
        elif value == 'z':
            match = context.get_matchgroup('rest')
            if match == 'Z':
                new_value = 'z'
            elif match == 'X':
                new_value = 'x'
            context.replace_matchgroups([('rest', new_value), ('length', '')])
        elif value == '1':
            context.replace_matchgroups([('length', '')])
        elif value in '/23+=':
            frac = self.length_to_fraction(context.get_matchgroup('length'))
            if value == '/':
                frac.denominator *= 2
            elif value == '2':
                frac.numerator *= 2
            elif value == '3':
                frac.numerator *= 3
                frac.denominator *= 2
            elif value == '+':
                frac += 1
            elif value == '=':
                frac -= 1
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
            current_value = context.get_matchgroup('pair', '')
            if current_value == value:
                new_value = value * 2
            else:
                new_value = value
            context.replace_match_text(new_value, matchgroup='pair')
            #if len(current_value) < 2 or current_value[0] != new_value[0]:
            #    context.set_relative_selection(-1)
        elif value == '-':
            if context.get_matchgroup('tie') == value:
                context.replace_match_text('', matchgroup='tie')
            else:
                context.replace_match_text(value, matchgroup='tie')


class MeasureRestDurationAction(DurationAction):
    values = [
        ValueDescription('1', _('One measure')),
        ValueDescription('2', _('Double measures')),
        ValueDescription('/', _('Half measures')),
        ValueDescription('+', _('Increase measures')),
        ValueDescription('=', _('Decrease measures')),
        CodeDescription('z', _('Normal rest'))
    ]
    def __init__(self):
        super(MeasureRestDurationAction, self).__init__(MeasureRestDurationAction.values)
        self.max_length_denominator = 1
        self.max_length_numerator = 64
        self.fraction_allowed = False


class NoteDurationAction(DurationAction):
    values = [
        CodeDescription('', _('Default length')),
        CodeDescription('/', _('Halve note length')),
        CodeDescription('2', _('Double note length')),
        CodeDescription('3', _('Dotted note')),
        CodeDescription('>', _('This note dotted, next note halved')),
        CodeDescription('<', _('This note halved, next note dotted')),
        CodeDescription('-', _('Tie / untie'))
    ]
    def __init__(self):
        super(NoteDurationAction, self).__init__(NoteDurationAction.values)


class RestDurationAction(DurationAction):
    values = [
        CodeDescription('', _('Default length')),
        CodeDescription('/', _('Halve note length')),
        CodeDescription('2', _('Double note length')),
        CodeDescription('3', _('Dotted note')),
        CodeDescription('>', _('This note dotted, next note halved')),
        CodeDescription('<', _('This note halved, next note dotted')),
        CodeDescription('Z', _('Whole measure'))
    ]
    def __init__(self):
        super(RestDurationAction, self).__init__(RestDurationAction.values)


#class MeasureRestDurationChangeAction(ValueChangeAction):
#    values = [
#        CodeDescription('',  _('One measure')),
#        CodeDescription('2',  _('Two measures')),
#        CodeDescription('3',  _('Three measures')),
#        CodeDescription('4',  _('Four measures')),
#        CodeDescription('5',  _('Five measures'), common=False),
#        CodeDescription('6',  _('Six measures'), common=False),
#        CodeDescription('7',  _('Seven measures'), common=False),
#        CodeDescription('8',  _('Eight measures'), common=False)
#    ]
#    def __init__(self):
#        super(MeasureRestDurationChangeAction, self).__init__('Change duration', MeasureRestDurationChangeAction.values, 'measures')


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
        CodeDescription('.|', _('Dotted bar'), common=False),
        CodeDescription('[|', _('Thick-thin double bar line'), common=False),
        CodeDescription('|:', _('Start of repeated section')),
        CodeDescription(':|', _('End of repeated section')),
        CodeDescription('|1', _('First ending')),
        CodeDescription(':|2', _('Second ending')),
        CodeDescription('&',  _('Voice overlay'), common=False),
        CodeDescription('[|]', _('Invisible bar'), common=False)
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
        super(MeasureRestVisibilityChangeAction, self).__init__('Visibility', MeasureRestVisibilityChangeAction.values, 'rest')


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
        ValueDescription( 6, _('6 sharps'), common=False),
        ValueDescription( 5, _('5 sharps'), common=False),
        ValueDescription( 4, _('4 sharps')),
        ValueDescription( 3, _('3 sharps')),
        ValueDescription( 2, _('2 sharps')),
        ValueDescription( 1, _('1 sharp')),
        ValueDescription( 0, _('0 sharps/flats')),
        ValueDescription(-1, _('1 flat')),
        ValueDescription(-2, _('2 flats')),
        ValueDescription(-3, _('3 flats')),
        ValueDescription(-4, _('4 flats')),
        ValueDescription(-5, _('5 flats'), common=False),
        ValueDescription(-6, _('6 flats'), common=False),
        ValueDescription('none', _('None'), common=False),
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
        ValueDescription(0,  _('Dorian'), common=False),
        ValueDescription(-1, _('Mixolydian'), common=False),
        ValueDescription(2,  _('Phrygian'), common=False),
        ValueDescription(-3, _('Lydian'), common=False),
        ValueDescription(3,  _('Locrian'), common=False)
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
        ValueDescription('bass3', _('Baritone'), common=False),
        ValueDescription('tenor', _('Tenor'), common=False),
        ValueDescription('alto', _('Alto'), common=False),
        ValueDescription('alto2', _('Mezzosoprano'), common=False),
        ValueDescription('alto1', _('Soprano'), common=False),
        ValueDescription('perc', _('Percussion'), common=False),
        ValueDescription('none', _('None'), common=False)
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


class BaseDecorationChangeAction(ValueChangeAction):
    def __init__(self, name, decoration_values):
        values = []
        for mark in decoration_values:
            value = ValueImageDescription(mark, self.get_image_name(mark), decoration_to_description[mark])
            values.append(value)
        super(BaseDecorationChangeAction, self).__init__(name, values, 'decoration')
        #self.relative_selection = -1


    def is_current_value(self, context, value):
        match = self.get_match(context)
        current_value = match.group(self.matchgroup)
        current_value = decoration_aliases.get(current_value, current_value)
        return value == current_value

    def get_values(self, context):
        values = super(BaseDecorationChangeAction, self).get_values(context)
        return [v for v in values if decoration_aliases.get(v.value) is None]  # prevent doubles by filtering out aliases

    @staticmethod
    def get_image_name(mark):
        name_lookup = {
            '.': 'staccato',
            '!upbow!': 'v',
            '!downbow!': 'u',
            '!lowermordent!': 'mordent',
            '!uppermordent!': 'pralltriller'
        }
        image_name = name_lookup.get(mark)
        if image_name is None and mark[0] == '!':
            image_name = mark[1:-1]
        return image_name


class DynamicsDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(DynamicsDecorationChangeAction, self).__init__('Change dynamics mark', AbcDynamicsDecoration.values)


class FingeringDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(FingeringDecorationChangeAction, self).__init__('Change fingering', AbcFingeringDecoration.values)


class OrnamentDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(OrnamentDecorationChangeAction, self).__init__('Change ornament', AbcOrnamentDecoration.values)


class NavigationDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(NavigationDecorationChangeAction, self).__init__('Change navigation marker', AbcNavigationDecoration.values)


class ArticulationDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(ArticulationDecorationChangeAction, self).__init__('Change articulation marker', AbcArticulationDecoration.values)


class ChordChangeAction(ValueChangeAction):
    def __init__(self):
        super(ChordChangeAction, self).__init__('Change chord', [], 'chordsymbol')

    def get_values(self, context):
        values = [
            ValueDescription('', _('No chord'))
        ]
        return values


class RedefinableSymbolChangeAction(ValueChangeAction):
    def __init__(self):
        super(RedefinableSymbolChangeAction, self).__init__('Change redefinable symbol', [])

    def get_values(self, context):
        defaults = {
            '~': '!roll!',
            'H': '!fermata!',
            'L': '!accent!',
            'M': '!lowermordent!',
            'O': '!coda!',
            'P': '!uppermordent!',
            'S': '!segno!',
            'T': '!trill!',
            'u': '!upbow!',
            'v': '!downbow!'
        }
        values = []
        for symbol in defaults:
            decoration = defaults[symbol]
            image_name = BaseDecorationChangeAction.get_image_name(decoration)
            desc = decoration_to_description.get(decoration, '')
            values.append(CodeImageDescription(symbol, image_name, desc))
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
        return context.abc_section in [AbcSection.FileHeader, AbcSection.OutsideTune]

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


class NewNoteOrRestAction(InsertValueAction):
    values = ['z C D E F G A B c d e f g a b'.split(' ')]
    def __init__(self):
        super(NewNoteOrRestAction, self).__init__('New note/rest', supported_values=NewNoteOrRestAction.values, valid_sections=AbcSection.TuneBody)

    def execute(self, context, params=None):
        value = params['value']
        if AddBarAction.is_bar_expected(context):
            value = AddBarAction.get_bar_value(context) + value
        context.insert_text(value)


class InsertOptionalAccidental(InsertValueAction):
    values = [
        ValueDescription('"^"', _('Empty')),
        ValueDescription('"<(\u266f)"', _('Optional sharp'), common=False),
        ValueDescription('"<(\u266e)"', _('Optional natural'), common=False),
        ValueDescription('"<(\u266d)"', _('Optional flat'), common=False)
    ]
    def __init__(self):
        super(InsertOptionalAccidental, self).__init__('Insert annotation', InsertOptionalAccidental.values, matchgroup='decoanno')
        #self.relative_selection = -1


class AddDecorationAction(InsertValueAction):
    values = [
        ValueImageDescription('!mf!', 'mf', _('Dynamics')),
        ValueImageDescription('!trill!', 'trill', _('Ornament')),
        ValueImageDescription('!fermata!', 'fermata', _('Articulation')),
        ValueImageDescription('!segno!', 'segno', _('Navigation')),
        ValueImageDescription('!5!', '5', _('Fingering'), common=False)
    ]
    def __init__(self):
        super(AddDecorationAction, self).__init__('Insert decoration', AddDecorationAction.values, matchgroup='decoanno')
        #self.relative_selection = -1


class AddSlurAction(AbcAction):
    def __init__(self):
        super(AddSlurAction, self).__init__('Add slur')

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('({0})'.format(context.match_text))


class AddBarAction(AbcAction):
    def __init__(self):
        super(AddBarAction, self).__init__('Add bar')

    def can_execute(self, context, params=None):
        return self.is_action_allowed(context)

    def execute(self, context, params=None):
        text = self.get_bar_value(context)
        context.insert_text(text)

    @staticmethod
    def get_bar_value(context):
        prev_char = context.get_scope_info(TuneScope.PreviousCharacter).text
        next_char = context.get_scope_info(TuneScope.NextCharacter).text
        pre_space = ''
        post_space = ''
        if prev_char not in ' \r\n:':
            pre_space = ' '
        if next_char != ' ':
            post_space = ' '
        return '{0}|{1}'.format(pre_space, post_space)

    @staticmethod
    def is_action_allowed(context):
        if not context.abc_section in [AbcSection.TuneBody]:
            return False

    @staticmethod
    def get_metre_and_default_length(abc):
        lines = re.split('\r\n|\r|\n', abc)
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

    @staticmethod
    def is_bar_expected(context):
        text = context.get_scope_info(TuneScope.BodyUpToSelection).text
        last_bar_offset = max([0] + [m.end(0) for m in bar_sep.finditer(text)])  # offset of last bar symbol
        text = text[last_bar_offset:]  # the text from the last bar symbol up to the selection point
        metre, default_len = AddBarAction.get_metre_and_default_length(context.get_scope_info(TuneScope.TuneUpToSelection).text)

        if re.match(r"^[XZ]\d*$", text):
            duration = metre
        else:
            duration = get_bar_length(text, default_len, metre)

        result = duration >= metre
        return result



class CombineToChordAction(AbcAction):
    def __init__(self):
        super(CombineToChordAction, self).__init__('Combine to chord')

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('[{0}]'.format(context.match_text))


class MakeTripletsAction(AbcAction):
    notes_re = re.compile(AbcNoteGroup.note_or_chord_pattern)
    def __init__(self):
        super(MakeTripletsAction, self).__init__('Make triplets')

    def can_execute(self, context, params=None):
        note_matches = self.notes_re.findall(context.match_text)
        return len(note_matches) == 3

    def execute(self, context, params=None):
        context.replace_match_text('(3{0}'.format(context.match_text))


class PageFormatDirectiveChangeAction(ValueChangeAction):
    values = [
        ValueDescription('pagewidth', _('Page width')),
        ValueDescription('pageheight', _('Page height')),
        ValueDescription('topmargin', _('Top margin')),
        ValueDescription('botmargin', _('Bottom margin')),
        ValueDescription('leftmargin', _('Page width')),
        ValueDescription('rightmargin', _('Page width')),
        ValueDescription('staffwidth', _('Staff width')),
        ValueDescription('landscape', _('Landscape'))
    ]
    def __init__(self):
        super(PageFormatDirectiveChangeAction, self).__init__('Change page format', PageFormatDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader)


class MeasureNumberingChangeAction(DirectiveChangeAction):
    values = [
        ValueDescription('-1', _('None')),
        ValueDescription('0', _('Left of staff')),
        ValueDescription('1', _('Every bar')),
        ValueDescription('2', _('Every 2 bars')),
        ValueDescription('4', _('Every 4 bars')),
        ValueDescription('5', _('Every 5 bars')),
        ValueDescription('8', _('Every 8 bars')),
        ValueDescription('10', _('Every 10 bars'))
    ]
    def __init__(self):
        super(MeasureNumberingChangeAction, self).__init__('measurenb', 'Show measure numbers', MeasureNumberingChangeAction.values, valid_sections=AbcSection.TuneHeader)


class MeasureBoxChangeAction(DirectiveChangeAction):
    values = [
        ValueDescription('0', _('Normal')),
        ValueDescription('1', _('Boxed'))
    ]
    def __init__(self):
        super(MeasureBoxChangeAction, self).__init__('measurebox', 'Show measure box', MeasureBoxChangeAction.values, valid_sections=AbcSection.TuneHeader)


class FirstMeasureNumberChangeAction(DirectiveChangeAction):
    values = [
        ValueDescription('0', _('Zero')),
        ValueDescription('1', _('One'))
    ]
    def __init__(self):
        super(FirstMeasureNumberChangeAction, self).__init__('setbarnb', 'First measure number', MeasureNumberingChangeAction.values, valid_sections=AbcSection.TuneHeader)


class FontDirectiveChangeAction(ValueChangeAction):
    values = [
        ValueDescription('titlefont', _('Title font')),
        ValueDescription('subtitlefont', _('Subtitle font')),
        ValueDescription('composerfont', _('Composer font')),
        ValueDescription('partsfont', _('Parts font')),
        ValueDescription('tempofont', _('Tempo font')),
        ValueDescription('gchordfont', _('Guitar chord font')),
        ValueDescription('annotationfont', _('Annotation font')),
        ValueDescription('infofont', _('Info font')),
        ValueDescription('textfont', _('Text font')),
        ValueDescription('vocalfont', _('Vocal font')),
        ValueDescription('wordsfont', _('Words font')),
        ValueDescription('setfont-1', _('Custom font 1')),
        ValueDescription('setfont-2', _('Custom font 2')),
        ValueDescription('setfont-3', _('Custom font 3')),
        ValueDescription('setfont-4', _('Custom font 4'))
    ]
    def __init__(self):
        super(FontDirectiveChangeAction, self).__init__('Change font directive', FontDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader)


class ScaleDirectiveChangeAction(ValueChangeAction):
    values = [
        ValueDescription('scale', _('Page scale factor')),
        ValueDescription('staffscale', _('Staff scale factor'))
    ]
    def __init__(self):
        super(ScaleDirectiveChangeAction, self).__init__('Change scale directive', ScaleDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader)


class InsertDirectiveAction(InsertValueAction):
    values = [
        ValueDescription('MIDI', _('MIDI')),
        ValueDescription('pagewidth', _('Page layout')),
        ValueDescription('scale', _('Scale')),
        ValueDescription('titlefont', _('Font'))
    ]
    def __init__(self):
        super(InsertDirectiveAction, self).__init__('Insert directive', InsertDirectiveAction.values)


class InsertAlignSymbolAction(InsertValueAction):
    values = [
        CodeDescription('-', _('break between syllables within a word')),
        CodeDescription('_', _('previous syllable is to be held for an extra note')),
        CodeDescription('*', _('one note is skipped (* is equivalent to a blank syllable)')),
        CodeDescription('~', _('appears as a space; aligns multiple words under one note')),
        CodeDescription(r'\-', _('appears as hyphen; aligns multiple syllables under one note')),
        CodeDescription('|', _('advances to the next bar'))
    ]
    def __init__(self):
        super(InsertAlignSymbolAction, self).__init__('Insert align symbol', InsertAlignSymbolAction.values)

class ActionSeparator(AbcAction):
    def __init__(self):
        super(ActionSeparator, self).__init__('Separator')

    def get_action_html(self, context):
        return '<BR>'


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
        rows = []
        for action in self._actions_ordered:
            rows.append(action.get_action_html(context))
        return html_table(rows)


class AbcActionHandlers(object):
    def __init__(self, elements):
        self.default_action_handler = AbcActionHandler()
        self.action_handlers = {
            'Empty document'     : AbcActionHandler([NewTuneAction()]),
            'Empty line'         : AbcActionHandler([NewTuneAction(), NewNoteOrRestAction()]),
            'Whitespace'         : AbcActionHandler([NewNoteOrRestAction()]),
            'Note'               : AbcActionHandler([NewNoteOrRestAction(), ActionSeparator(), AccidentalChangeAction(), NoteDurationAction(), PitchAction(), AddDecorationAction(), InsertOptionalAccidental()]),
            'Rest'               : AbcActionHandler([NewNoteOrRestAction(), ActionSeparator(), RestDurationAction(), RestVisibilityChangeAction()]),
            'Measure rest'       : AbcActionHandler([NewNoteOrRestAction(), ActionSeparator(), MeasureRestDurationAction(), MeasureRestVisibilityChangeAction()]),
            'Bar'                : AbcActionHandler([BarChangeAction()]),
            'Annotation'         : AbcActionHandler([AnnotationPositionAction()]),
            'Chord'              : AbcActionHandler([NoteDurationAction(), ChordChangeAction()]),
            'Chord symbol'       : AbcActionHandler([ConvertToAnnotationAction()]),
            'Grace notes'        : AbcActionHandler([AppoggiaturaOrAcciaccaturaChangeAction()]),
            'Multiple notes'     : AbcActionHandler([AddSlurAction(), MakeTripletsAction(), CombineToChordAction()]),
            'Multiple notes/chords' : AbcActionHandler([AddSlurAction(), MakeTripletsAction()]),
            'Dynamics'           : AbcActionHandler([DynamicsDecorationChangeAction()]),
            'Articulation'       : AbcActionHandler([ArticulationDecorationChangeAction()]),
            'Ornament'           : AbcActionHandler([OrnamentDecorationChangeAction()]),
            'Navigation'         : AbcActionHandler([NavigationDecorationChangeAction()]),
            'Fingering'          : AbcActionHandler([FingeringDecorationChangeAction()]),
            'Redefinable symbol' : AbcActionHandler([RedefinableSymbolChangeAction()]),
            #'Stylesheet directive': AbcActionHandler([InsertDirectiveAction()]),
            'w:'                 : AbcActionHandler([InsertAlignSymbolAction()]),
            'K:'                 : AbcActionHandler([KeySignatureChangeAction(), KeyModeChangeAction()]),
            'L:'                 : AbcActionHandler([UnitNoteLengthChangeAction()]),
            'M:'                 : AbcActionHandler([MeterChangeAction()]),
            '%'                  : AbcActionHandler([FixCharactersAction()])
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

