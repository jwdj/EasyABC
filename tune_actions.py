from __future__ import unicode_literals
import re
import os
import sys

PY3 = sys.version_info.major > 2

from collections import namedtuple
from wx import GetTranslation as _
from tune_elements import *
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2

try:
    from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl, quote # py3
    from urllib.request import urlopen, Request, urlretrieve
    from urllib.error import HTTPError, URLError
except ImportError:
    from urlparse import urlparse, urlunparse, parse_qsl # py2
    from urllib import urlencode, urlretrieve, quote
    from urllib2 import urlopen, Request, HTTPError, URLError


from fractions import Fraction
from aligner import get_bar_length
from generalmidi import general_midi_instruments
from abc_tune import AbcTune

if PY3:
    basestring = str
    def unicode(value):
        return value

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

def html_image(image_name, description):
    image_path = u'{0}/img/{1}.png'.format(application_path, image_name)
    image_html = ''
    if os.path.exists(image_path):
        image_html = u'<img src="{0}" border="0" alt="{1}">'.format(path2url(image_path), description or '')
    return image_html


class AbcAction(object):
    def __init__(self, name, display_name=None, group=None):
        self.name = name
        if display_name:
            self.display_name = display_name
        else:
            self.display_name = name
        self.group = group

    def can_execute(self, context, params=None):
        return False

    def execute(self, context, params=None):
        pass

    def get_action_html(self, context):
        if self.can_execute(context):
            html = u'<br>' + html_enclose_attr('a', { 'href': self.name }, escape(self.display_name))
            return html
        return u''

    def get_action_url(self, params=None):
        if params is None:
            return self.name
        else:
            for param in list(params):
                value = params[param]
                if isinstance(value, basestring):
                    params[param] = value.encode('utf-8')  # urlencode only accepts ascii
            return '{0}?{1}'.format(self.name, urlencode(params))


class ValueChangeAction(AbcAction):
    def __init__(self, name, supported_values, matchgroup=None, display_name=None, valid_sections=None, use_inner_match=False):
        super(ValueChangeAction, self).__init__(name, display_name=display_name)
        self.supported_values = supported_values
        self.matchgroup = matchgroup
        self.use_inner_match = use_inner_match
        self.valid_sections = valid_sections
        self.relative_selection = None
        self.show_non_common = False

    def can_execute(self, context, params=None):
        show_non_common = params.get('show_non_common')
        if show_non_common is not None:
            return True
        value = params.get('value', '')
        return not self.is_current_value(context, value)

    def is_current_value(self, context, value):
        current_value = None
        if self.matchgroup:
            match = self.get_match(context)
            if match:
                current_value = match.group(self.matchgroup)
        elif self.use_inner_match:
            current_value = context.inner_text
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
        show_non_common = params.get('show_non_common')
        if show_non_common is not None:
            self.show_non_common = show_non_common == 'True'
            context.invalidate()
        else:
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
            row = self.add_options(row)
            rows.append(row)

        row = self.get_values_html(context)
        rows.append(row)
        return html_table(rows)

    def get_values(self, context):
        return self.supported_values

    def contains_only_common(self, values):
        for value in values:
            if isinstance(value, ValueDescription):
                if not value.common:
                    return False
            elif not isinstance(value, basestring) and hasattr(value, '__iter__'):
                if not self.contains_only_common(value):
                    return False
        return True

    def add_options(self, row):
        only_common = self.contains_only_common(self.supported_values)
        if only_common:
            return row
        else:
            action_url = self.get_action_url({'show_non_common': not self.show_non_common})
            if self.show_non_common:
                url_tuple = UrlTuple(action_url, html_image('arrow-up', _('Less options')))
            else:
                url_tuple = UrlTuple(action_url, html_image('arrow-down', _('More options')))
            return html_table([[row + '&nbsp;', url_tuple_to_href(url_tuple)]])

    @staticmethod
    def enclose_action_url(action_url, value):
        if action_url is not None:
            return UrlTuple(action_url, value)
        return value

    def get_columns_for_value(self, context, value, show_value_column, fixed_font=True):
        columns = []
        if isinstance(value, ValueDescription):
            if value.common or self.show_non_common:
                desc = escape(value.description)
                params = {'value': value.value}
                can = self.can_execute(context, params)
                action_url = None
                if can:
                    action_url = self.get_action_url(params)
                if show_value_column:
                    if value.show_value: #isinstance(value, (CodeDescription, CodeImageDescription)):
                        columns.append(html_enclose('code', escape(value.value)))
                    else:
                        columns.append(html_enclose('code', ''))

                if isinstance(value, ActionValue):
                    action_html = value.get_action_html()
                    if action_html:
                        columns.append(action_html)
                else:
                    if isinstance(value, ValueImageDescription):
                        image_html = html_image(value.image_name, desc)
                        columns.append(self.enclose_action_url(action_url, image_html))
                    if can:
                        columns.append(self.enclose_action_url(action_url, desc))
                    else:
                        columns.append(self.html_selected_item(context, value.value, desc))
        elif isinstance(value, list):
            for v in value:
                columns += self.get_columns_for_value(context, v, show_value_column, fixed_font=fixed_font)
        else:
            params = {'value': value}
            desc = escape(value)
            if fixed_font:
                desc = html_enclose('code', desc)
            if self.can_execute(context, params):
                t = UrlTuple(self.get_action_url(params), desc)
                columns.append(t)
            else:
                columns.append(desc) # self.html_selected_item(context, value, desc)

        return columns

    def get_values_html(self, context):
        rows = []
        show_value_column = False
        values = self.get_values(context)
        for value in values:
            if isinstance(value, ValueDescription):
                if value.show_value:
                    show_value_column = True
                    break

        for value in values:
            if isinstance(value, list):
                values = value
                row = []
                for v in values:
                    columns = self.get_columns_for_value(context, v, show_value_column)
                    row += columns
                if row:
                    rows.append(html_table([row], cellpadding=2))
            else:
                columns = self.get_columns_for_value(context, value, show_value_column)
                if columns:
                    rows.append(tuple(columns))

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
        self.caret_after_matchgroup = False

    def can_execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            return super(InsertValueAction, self).can_execute(context, params)
        else:
            return True

    def execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            super(InsertValueAction, self).execute(context, params)
        else:
            if self.matchgroup:
                text = context.get_matchgroup(self.matchgroup)
                text += value
                context.replace_match_text(text, self.matchgroup, caret_after_matchgroup=self.caret_after_matchgroup)
            else:
                context.insert_text(value)
            if self.relative_selection is not None:
                context.set_relative_selection(self.relative_selection)


# class RemoveValueAction(AbcAction):
#     def __init__(self, matchgroups=None):
#         super(RemoveValueAction, self).__init__('remove_match', display_name=_('Remove'))
#         self.matchgroups = matchgroups
#
#     def can_execute(self, context, params=None):
#         matchgroup = params.get('matchgroup', '')
#         if self.matchgroups is not None:
#             return matchgroup in self.matchgroups and context.get_matchgroup(matchgroup)
#         else:
#             return True
#
#     def execute(self, context, params=None):
#         matchgroup = params.get('matchgroup', '')
#         context.replace_match_text('', matchgroup)


class ConvertToAnnotationAction(AbcAction):
    def __init__(self):
        super(ConvertToAnnotationAction, self).__init__('convert_to_annotation', display_name=_('Convert to annotation'))

    def can_execute(self, context, params=None):
        chord = context.get_matchgroup('chordnote')
        return chord is None # and chord[0].lower() not in 'abcdefg'

    def execute(self, context, params=None):
        annotation = '^' + context.get_matchgroup(self.matchgroup)
        context.replace_match_text(annotation, matchgroup=self.matchgroup)


class DirectiveChangeAction(ValueChangeAction):
    def __init__(self, directive_name, name, supported_values, valid_sections=None, display_name=None, matchgroup=None):
        super(DirectiveChangeAction, self).__init__(name, supported_values, valid_sections=valid_sections, display_name=display_name, matchgroup=matchgroup)
        self.directive_name = directive_name


class ActionValue(ValueDescription):
    def __init__(self, action_name, description='', common=True):
        super(ActionValue, self).__init__(action_name, description, common=common, show_value=False)
        self.action_name = action_name

    def get_action_html(self):
        html = html_enclose_attr('a', { 'href': self.action_name }, escape(self.description))
        return html

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
        super(AccidentalChangeAction, self).__init__('change_accidental', AccidentalChangeAction.accidentals, matchgroup='accidental', display_name=_('Change accidental'))


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
        super(MeterChangeAction, self).__init__('change_meter', MeterChangeAction.values, use_inner_match=True, display_name=_('Change meter'))


class UnitNoteLengthChangeAction(ValueChangeAction):
    values = [
        CodeDescription('1/2',  _('half note')),
        CodeDescription('1/4',  _('quarter note')),
        CodeDescription('1/8',  _('eighth note')),
        CodeDescription('1/16', _('sixteenth note'))
    ]
    def __init__(self):
        super(UnitNoteLengthChangeAction, self).__init__('change_unit_note_length', UnitNoteLengthChangeAction.values, use_inner_match=True, display_name=_('Change note length'))


class TempoNoteLengthChangeAction(ValueChangeAction):
    values = [
        CodeDescription('3/4',  _('three quarter note'), common=False),
        CodeDescription('1/2',  _('half note')),
        CodeDescription('3/8',  _('three eighth note'), common=False),
        CodeDescription('1/4',  _('quarter note')),
        CodeDescription('1/8',  _('eighth note')),
        CodeDescription('1/16', _('sixteenth note'))
    ]
    def __init__(self):
        super(TempoNoteLengthChangeAction, self).__init__('change_tempo_note1_length', TempoNoteLengthChangeAction.values, matchgroup='note1', use_inner_match=True, display_name=_('Change note length'))


class TempoNote2LengthChangeAction(ValueChangeAction):
    def __init__(self):
        super(TempoNote2LengthChangeAction, self).__init__('change_tempo_note2_length', TempoNoteLengthChangeAction.values, matchgroup='note2', use_inner_match=True, display_name=_('Change second note length'))


class TempoNotationChangeAction(ValueChangeAction):
    values = [
        ValueDescription('name', _('Only name')),
        ValueDescription('speed', _('Only speed')),
        ValueDescription('name+speed', _('Name & speed')),
    ]
    def __init__(self):
        super(TempoNotationChangeAction, self).__init__('change_tempo_notation', TempoNotationChangeAction.values, display_name=_('Change tempo notation'))

    def execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            super(TempoNotationChangeAction, self).execute(context, params)
        else:
            replacements = []
            if value in ['name', 'name+speed']:
                if not context.get_matchgroup('pre_text'):
                    replacements.append(('pre_text', '"Allegro"'))
            else:
                replacements.append(('pre_text', ''))

            if value in ['speed', 'name+speed']:
                if not context.get_matchgroup('metronome'):
                    replacements.append(('metronome', ' 1/4=120'))
            else:
                replacements.append(('metronome', ''))

            context.replace_matchgroups(replacements)

    def is_current_value(self, context, value):
        has_name = context.get_matchgroup('pre_text')
        has_speed = context.get_matchgroup('metronome')
        current_value = None
        if has_name:
            if has_speed:
                current_value = 'name+speed'
            else:
                current_value = 'name'
        elif has_speed:
            current_value = 'speed'
        return value == current_value


class TempoNameChangeAction(ValueChangeAction):
    values = [
        ValueDescription('Larghissimo'     , _('Larghissimo'), common=False),
        ValueDescription('Grave'           , _('Grave'), common=False),
        ValueDescription('Lento'           , _('Lento')),
        ValueDescription('Largo'           , _('Largo')),
        ValueDescription('Adagio'          , _('Adagio')),
        ValueDescription('Adagietto'       , _('Adagietto'), common=False),
        ValueDescription('Andante'         , _('Andante')),
        ValueDescription('Andantino'       , _('Andantino'), common=False),
        ValueDescription('Moderato'        , _('Moderato')),
        ValueDescription('Allegretto'      , _('Allegretto'), common=False),
        ValueDescription('Allegro'         , _('Allegro')),
        ValueDescription('Vivace'          , _('Vivace')),
        ValueDescription('Presto'          , _('Presto')),
        ValueDescription('Prestissimo'     , _('Prestissimo'), common=False),
    ]
    def __init__(self):
        super(TempoNameChangeAction, self).__init__('change_tempo_name', TempoNameChangeAction.values, matchgroup='pre_name', use_inner_match=True, display_name=_('Change tempo name'))


class PitchAction(ValueChangeAction):
    pitch_values = [
        ValueDescription('noteup', _('Note up')),
        ValueDescription('notedown', _('Note down')),
        ValueDescription("'", _('Octave up')),
        ValueDescription(",", _('Octave down'))
    ]
    all_notes = 'CDEFGABcdefgab'
    def __init__(self):
        super(PitchAction, self).__init__('change_pitch', PitchAction.pitch_values, display_name=_('Change pitch'))

    def can_execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            return super(PitchAction, self).can_execute(context, params)
        else:
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
        if value is None:
            super(PitchAction, self).execute(context, params)
        else:
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
    def __init__(self, name, values):
        super(DurationAction, self).__init__(name, values, display_name=_('Change duration'))
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
        return result

    @staticmethod
    def is_power2(num):
        return ((num & (num - 1)) == 0) and num != 0

    def can_execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            return super(DurationAction, self).can_execute(context, params)
        elif not value:
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
        if value is None:
            super(DurationAction, self).execute(context, params)
        elif not value:
            context.replace_matchgroups([('length', ''), ('pair', '')])
        elif value == 'Z':
            match = context.get_matchgroup('rest')
            new_value = None
            if match == 'z':
                new_value = 'Z'
            elif match == 'x':
                new_value = 'X'
            if new_value:
                context.replace_matchgroups([('rest', new_value), ('length', ''), ('pair', '')])
        elif value == 'z':
            match = context.get_matchgroup('rest')
            new_value = None
            if match == 'Z':
                new_value = 'z'
            elif match == 'X':
                new_value = 'x'
            if new_value:
                context.replace_matchgroups([('rest', new_value), ('length', '')])
        elif value == '1':
            context.replace_matchgroups([('length', '')])
        elif value in '/23+=':
            frac = self.length_to_fraction(context.get_matchgroup('length'))
            if value == '/':
                frac *= Fraction(1, 2)
            elif value == '2':
                frac *= Fraction(2, 1)
            elif value == '3':
                frac *= Fraction(3, 2)
            elif value == '+':
                frac += 1
            elif value == '=':
                frac -= 1

            if frac.numerator == 1:
                text = ''
            else:
                text = str(frac.numerator)

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
        super(MeasureRestDurationAction, self).__init__('change_measurerest_duration', MeasureRestDurationAction.values)
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
        super(NoteDurationAction, self).__init__('change_note_duration', NoteDurationAction.values)


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
        super(RestDurationAction, self).__init__('change_rest_duration', RestDurationAction.values)


class ChangeAnnotationAction(ValueChangeAction):
    values = [
        ValueDescription('"<(\u266f)"', _('Optional sharp')),
        ValueDescription('"<(\u266e)"', _('Optional natural')),
        ValueDescription('"<(\u266d)"', _('Optional flat')),
        ValueDescription('"^rit."', _('Ritenuto')),
    ]
    def __init__(self):
        super(ChangeAnnotationAction, self).__init__('change_annotation', ChangeAnnotationAction.values, matchgroup='annotation', display_name=_('Change annotation'))
        self.caret_after_matchgroup = True


class AnnotationPositionAction(ValueChangeAction):
    values = [
        CodeDescription('^', _('Above')),
        CodeDescription('_', _('Below')),
        CodeDescription('<', _('Left')),
        CodeDescription('>', _('Right')),
        CodeDescription('@', _('Auto'))
    ]
    def __init__(self):
        super(AnnotationPositionAction, self).__init__('change_annotation_position', AnnotationPositionAction.values, 'pos', display_name=_('Position'))


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
        CodeDescription('::', _('Both end and start of repetition'), common=False),
        CodeDescription('&',  _('Voice overlay'), common=False),
        CodeDescription('[|]', _('Invisible bar'), common=False)
    ]
    def __init__(self):
        super(BarChangeAction, self).__init__('change_bar', BarChangeAction.values, display_name=_('Change bar'))


class RestVisibilityChangeAction(ValueChangeAction):
    values = [
        CodeDescription('z',  _('Visible')),
        CodeDescription('x',  _('Hidden')),
    ]
    def __init__(self):
        super(RestVisibilityChangeAction, self).__init__('change_rest_visibility', RestVisibilityChangeAction.values, 'rest', display_name=_('Visibility'))


class MeasureRestVisibilityChangeAction(ValueChangeAction):
    values = [
        CodeDescription('Z',  _('Visible')),
        CodeDescription('X',  _('Hidden')),
    ]
    def __init__(self):
        super(MeasureRestVisibilityChangeAction, self).__init__('change_measurerest_visibility', MeasureRestVisibilityChangeAction.values, 'rest', display_name=_('Visibility'))


class AppoggiaturaOrAcciaccaturaChangeAction(ValueChangeAction):
    values = [
        CodeDescription('',   _('Appoggiatura')),
        CodeDescription('/',  _('Acciaccatura')),
    ]
    def __init__(self):
        super(AppoggiaturaOrAcciaccaturaChangeAction, self).__init__('change_appoggiatura_acciaccatura', AppoggiaturaOrAcciaccaturaChangeAction.values, 'acciaccatura', display_name=_('Appoggiatura/acciaccatura'))


class KeyChangeAction(ValueChangeAction):
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
        super(KeySignatureChangeAction, self).__init__('change_key_signature', KeySignatureChangeAction.values, matchgroup='tonic', use_inner_match=True, display_name=_('Key signature'))

    def is_action_allowed(self, context):
        return True

    def can_execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            return super(KeySignatureChangeAction, self).can_execute(context, params)

        if context.inner_match is None:
            return True
        tonic = context.get_matchgroup('tonic')

        value = params.get('value')
        if value == 'none':
            return tonic != value
        else:
            value = int(value)
            middle_idx = len(key_ladder) // 2
            try:
                tonic_idx = key_ladder.index(tonic)
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
        if value is None:
            super(KeySignatureChangeAction, self).execute(context, params)
        elif value == 'none':
            context.replace_match_text(value, tune_scope=TuneScope.InnerText)
        else:
            value = int(value)
            middle_idx = len(key_ladder) // 2
            new_value = middle_idx + value

            mode = context.get_matchgroup('mode')
            mode_idx = self.abc_mode_to_number(mode)
            if mode_idx is None:
                new_value -= 2 # assume major scale
                tonic = key_ladder[new_value]
                context.replace_match_text(tonic, tune_scope=TuneScope.InnerText)
            else:
                new_value += mode_idx
                tonic = key_ladder[new_value]
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
        super(KeyModeChangeAction, self).__init__('change_key_mode', KeyModeChangeAction.values, 'mode', use_inner_match=True, display_name=_('Mode'))

    def is_action_allowed(self, context):
        if context.inner_match is None:
            return False
        tonic = context.get_matchgroup('tonic')
        return tonic in key_ladder

    def can_execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            return super(KeyModeChangeAction, self).can_execute(context, params)
        else:
            tonic = context.get_matchgroup('tonic')
            if tonic in key_ladder:
                value = int(params.get('value'))
                mode = context.get_matchgroup(self.matchgroup)
                current_value = self.abc_mode_to_number(mode)
                return value != current_value
            else:
                return False

    def execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            super(KeyModeChangeAction, self).execute(context, params)
        else:
            value = int(value)
            tonic = context.get_matchgroup('tonic')
            mode = context.get_matchgroup(self.matchgroup)
            current_mode = self.abc_mode_to_number(mode)
            tonic = key_ladder[key_ladder.index(tonic) - current_mode + value]
            d = KeyChangeAction._mode_to_num
            [context.replace_matchgroups([('tonic', tonic), ('mode', mode)]) for mode in list(d) if d[mode] == value]


class ClefChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Default'), common=False),
        ValueDescription('treble', _('Treble clef')),
        ValueDescription('bass', _('Bass clef')),
        ValueDescription('tenor', _('Tenor clef'), common=False),
        ValueDescription('alto', _('Alto clef'), common=False),
        ValueDescription('C1', _('Soprano clef'), common=False),
        ValueDescription('C2', _('Mezzo-soprano clef'), common=False),
        ValueDescription('F3', _('Baritone clef'), common=False),
        ValueDescription('perc', _('Percussion clef'), common=False),
        ValueDescription('none', _('None'), common=False)
    ]
    def __init__(self):
        super(ClefChangeAction, self).__init__('change_clef', ClefChangeAction.values, 'clef', use_inner_match=True, display_name=_('Clef'))

    def can_execute(self, context, params=None):
        if super(ClefChangeAction, self).can_execute(context, params):
            value = params.get('value')
            if value is None:
                return True
            match = self.get_match(context)
            return match is None or value != match.group('clefname')
        return False

    def execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            super(ClefChangeAction, self).execute(context, params)
        else:
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
        super(StaffTransposeChangeAction, self).__init__('staff_transpose', StaffTransposeChangeAction.values, 'stafftranspose', use_inner_match=True, display_name=_('Staff transpose'))


class PlaybackTransposeChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Default')),
        ValueDescription(' transpose=12', _('Octave up')),
        ValueDescription(' transpose=-12', _('Octave down')),
    ]
    def __init__(self):
        super(PlaybackTransposeChangeAction, self).__init__('playback_transpose', PlaybackTransposeChangeAction.values, 'playtranspose', use_inner_match=True, valid_sections=AbcSection.TuneHeader, display_name=_('Playback transpose'))


class AbcOctaveChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Default')),
        ValueDescription(' octave=1', _('Octave up')),
        ValueDescription(' octave=-1', _('Octave down')),
    ]
    def __init__(self):
        super(AbcOctaveChangeAction, self).__init__('octave_shift', AbcOctaveChangeAction.values, 'octave', use_inner_match=True, display_name=_('Octave shift'))


class BaseDecorationChangeAction(ValueChangeAction):
    def __init__(self, name, decoration_values, display_name=None):
        values = []
        for mark in decoration_values:
            value = ValueImageDescription(mark, self.get_image_name(mark), decoration_to_description[mark])
            values.append(value)
        super(BaseDecorationChangeAction, self).__init__(name, values, 'decoration', display_name=display_name)


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
        super(DynamicsDecorationChangeAction, self).__init__('change_dynamics', AbcDynamicsDecoration.values, display_name=_('Change dynamics mark'))


class FingeringDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(FingeringDecorationChangeAction, self).__init__('change_fingering', AbcFingeringDecoration.values, display_name=_('Change fingering'))


class OrnamentDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(OrnamentDecorationChangeAction, self).__init__('change_ornament', AbcOrnamentDecoration.values, display_name=_('Change ornament'))


class DirectionDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(DirectionDecorationChangeAction, self).__init__('change_direction', AbcDirectionDecoration.values, display_name=_('Change direction marker'))


class ArticulationDecorationChangeAction(BaseDecorationChangeAction):
    def __init__(self):
        super(ArticulationDecorationChangeAction, self).__init__('change_articulation', AbcArticulationDecoration.values, display_name=_('Change articulation marker'))


class ChordNoteChangeAction(ValueChangeAction):
    def __init__(self):
        super(ChordNoteChangeAction, self).__init__('change_chord_note', [], 'chordnote', display_name=_('Change chord'))

    def get_values(self, context):
        i = key_ladder.index('C') # todo: retrieve from K:
        values = [
            self.get_value_for_chord(i),
            self.get_value_for_chord(i-1),
            self.get_value_for_chord(i+1),
            self.get_value_for_chord(i+3),
            self.get_value_for_chord(i+2),
            self.get_value_for_chord(i+4),
            self.get_value_for_chord(i+5),
        ]
        return values

    @staticmethod
    def get_value_for_chord(index):
        chord = key_ladder[index]
        return ValueDescription(chord, chord.replace('#', u'\u266F').replace('b', u'\u266D'))


class ChordNameChangeAction(ValueChangeAction):
    values = [
        CodeDescription('',      _('Major')),                                          # { 0, 4, 7 }
        CodeDescription('m',     _('Minor')),                                          # { 0, 3, 7 }
        CodeDescription('dim',   _('Diminished')),                                     # { 0, 3, 6 }
        CodeDescription('+',     _('Augmented'), alternate_values=['aug']),            # { 0, 4, 8 }
        CodeDescription('sus',   _('Suspended'), alternate_values=['sus4']),           # { 0, 5, 7 }
        CodeDescription('sus2',  _('Suspended (2nd)'), common=False),                  # { 0, 2, 7 }
        CodeDescription('7',     _('Seventh')),                                        # { 0, 4, 7, 10 }
        CodeDescription('M7',    _('Major seventh'), alternate_values=['maj7']),       # { 0, 4, 7, 11 }
        #CodeDescription('mM7',  _('Minor-major seventh')),                            # { 0, 3, 7, 11 }
        CodeDescription('m7',    _('Minor seventh')),                                  # { 0, 3, 7, 10 }
        #CodeDescription('augM7',_('Augmented-major seventh')),                        # { 0, 4, 8, 11 }
        CodeDescription('aug7',  _('Augmented seventh'), common=False),                # { 0, 4, 8, 10 }
        CodeDescription('dim7',  _('Diminished seventh'), common=False),               # { 0, 3, 6, 9 }
        CodeDescription('6',     _('Major sixth')),                                    # { 0, 4, 7, 9  }
        CodeDescription('m6',    _('Minor sixth')),                                    # { 0, 3, 7, 9  }
        CodeDescription('m7b5',  _('Half-diminished seventh'), common=False),          # { 0, 3, 6, 10 }
        #CodeDescription('7b5',  _('Seventh flat five')),                              # { 0, 4, 6, 10 }
        CodeDescription('5',     _('Power-chord (no third)')),                         # { 0, 7 }
        CodeDescription('7sus',  _('Seventh suspended'), alternate_values=['7sus4'], common=False),  # { 0, 5, 7, 10 }
        CodeDescription('7sus2', _('Seventh suspended (2nd)'), common=False),          # { 0, 2, 7, 10 }
        CodeDescription('9',     _('Dominant 9th')),                                   # { 0, 4, 7, 10, 14 }
        #CodeDescription('',     _('Minor Major 9th')),                                # { 0, 3, 7, 11, 14 }
        CodeDescription('M9',    _('Major 9th'), common=False),                        # { 0, 4, 7, 11, 14 }
        CodeDescription('m9',    _('Minor Dominant 9th'), common=False),               # { 0, 3, 7, 10, 14 }
        #CodeDescription('+M9',  _('Augmented Major 9th')),                            # { 0, 4, 8, 11, 14 }
        #CodeDescription('+9',   _('Augmented Dominant 9th')),                         # { 0, 4, 8, 10, 14 }
        #CodeDescription('o/9',  _('Half-Diminished 9th')),                            # { 0, 3, 6, 10, 14 }
        #CodeDescription('o/9b', _('Half-Diminished Minor 9th')),                      # { 0, 3, 6, 10, 13 }
        #CodeDescription('dim9', _('Diminished 9th')),                                 # { 0, 3, 6, 9, 14 }
        #CodeDescription('dim9b',_('Diminished Minor 9th')),                           # { 0, 3, 6, 9, 13 }
        CodeDescription('11',    _('Dominant 11th'), common=False),                    # { 0, 4, 7, 10, 14, 17 }
    ]
    def __init__(self):
        super(ChordNameChangeAction, self).__init__('change_chord_name', ChordNameChangeAction.values, matchgroup='chordname', display_name=_('Change chord name'))

    def is_action_allowed(self, context):
        return super(ChordNameChangeAction, self).is_action_allowed(context) and context.get_matchgroup('chordnote')


class ChordBaseNoteChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Root position')),
        ValueDescription('1', _('First inversion')),
        ValueDescription('2', _('Second inversion')),
    ]
    def __init__(self):
        super(ChordBaseNoteChangeAction, self).__init__('change_chord_bass_note', ChordBaseNoteChangeAction.values, matchgroup='bassnote', display_name=_('Change bass note'))

    def is_action_allowed(self, context):
        return False # super(ChordBaseNoteChangeAction, self).is_action_allowed(context) and context.get_matchgroup('chordnote')


class SlurChangeAction(ValueChangeAction):
    values = [
        ValueDescription('', _('Normal')),
        ValueDescription('.', _('Dashed')),
    ]
    def __init__(self):
        super(SlurChangeAction, self).__init__('change_slur', SlurChangeAction.values, matchgroup='dash', display_name=_('Change slur'))


class RedefinableSymbolChangeAction(ValueChangeAction):
    def __init__(self):
        super(RedefinableSymbolChangeAction, self).__init__('change_redefinable_symbol', [], display_name=_('Change redefinable symbol'))

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
    def __init__(self, name, url=None):
        super(UrlAction, self).__init__(name)
        self.url = url

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        url = self.get_url(context)
        webbrowser.open(url)

    def get_url(self, context):
        return self.url

    def get_outer_text(self, context):
        return _('Learn {0}...')

    def get_link_text(self, context):
        return _('more')

    @staticmethod
    def get_href(url, display_text):
        return u'<a href="{0}">{1}</a>'.format(url, escape(display_text))

    def get_action_html(self, context):
        if not self.can_execute(context):
            return ''
        outer_text = self.get_outer_text(context) or u'{0}'
        html = outer_text.format(self.get_href(self.get_url(context), self.get_link_text(context)))
        return html


class Abcm2psUrlAction(UrlAction):
    def __init__(self, keyword):
        url = 'http://moinejf.free.fr/abcm2ps-doc/{0}.xhtml'.format(urllib.parse.quote(keyword))
        super(UrlAction, self).__init__('lookup_abcm2ps', url)


class Abc2MidiUrlAction(UrlAction):
    def __init__(self, keyword):
        url = 'http://ifdo.pugmarks.com/~seymour/runabc/abcguide/abc2midi_body.html#{0}'.format(urllib.parse.quote(keyword))
        super(UrlAction, self).__init__('lookup_abc2midi', url)

class AbcStandardUrlAction(UrlAction):
    def __init__(self):
        super(AbcStandardUrlAction, self).__init__('lookup_abc_standard')

    def get_url(self, context):
        version = context.get_matchgroup('version', '2.1')
        return 'http://abcnotation.com/wiki/abc:standard:v{0}'.format(version)

    def can_execute(self, context, params=None):
        version = context.get_matchgroup('version', '2.1')
        return version.startswith('2.')

    def get_outer_text(self, context):
        return None

    def get_link_text(self, context):
        return _('Full ABC specification')


##################################################################################################
#  INSERT ACTIONS
##################################################################################################


class NewTuneAction(AbcAction):
    tune_re = re.compile(r'(?m)^X:\s*(\d+)')

    def __init__(self):
        super(NewTuneAction, self).__init__('new_tune', display_name=_('New tune'))

    def can_execute(self, context, params=None):
        return context.abc_section in [AbcSection.FileHeader, AbcSection.OutsideTune]

    def execute(self, context, params=None):
        last_tune_id = context.get_last_tune_id()
        new_tune_id = last_tune_id + 1
        text = u'X:%d' % new_tune_id
        text += os.linesep + 'T:' + _('Untitled') + '%d' % new_tune_id
        text += os.linesep + 'C:' + _('Unknown composer')
        text += os.linesep + 'M:4/4'
        text += os.linesep + 'L:1/4'
        text += os.linesep + 'K:C' + os.linesep

        if not context.contains_text:
            text = '%abc-2.1' + os.linesep + os.linesep + text
        elif context.previous_line and not context.previous_line.isspace():
            text = os.linesep + text
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
        context.replace_selection(new_text, scope_info.start, scope_info.stop)


class NewLineAction(AbcAction):
    def __init__(self):
        super(NewLineAction, self).__init__('new_line', display_name=_('New line'))

    def can_execute(self, context, params=None):
        can = context.abc_section in [AbcSection.TuneBody] and context.lines != ''
        return can

    def execute(self, context, params=None):
        value = os.linesep
        if AddBarAction.is_bar_expected(context):
            value = AddBarAction.get_bar_value(context) + value
        context.insert_text(value)


class NewSpaceAction(AbcAction):
    def __init__(self):
        super(NewSpaceAction, self).__init__('new_space', display_name=_('Space'))

    def can_execute(self, context, params=None):
        can = context.abc_section in [AbcSection.TuneBody] and context.previous_character != ' '
        return can

    def execute(self, context, params=None):
        value = ' '
        if AddBarAction.is_bar_expected(context):
            value = AddBarAction.get_bar_value(context) + value
        context.insert_text(value)


class NewNoteOrRestAction(InsertValueAction):
    values = ['C D E F G A B c d e f g a b'.split(' ')]
    def __init__(self):
        super(NewNoteOrRestAction, self).__init__('new_note', supported_values=NewNoteOrRestAction.values, valid_sections=AbcSection.TuneBody, display_name=_('New note/rest'))

    def execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            super(NewNoteOrRestAction, self).execute(context, params)
        else:
            if self.is_outside_chord(context):
                if AddBarAction.is_bar_expected(context):
                    value = AddBarAction.get_bar_value(context) + u' ' + value
                elif not context.previous_character in '` \t\r\n':
                    value = u' ' + value
            context.insert_text(value)

    def get_values(self, context):
        values = super(NewNoteOrRestAction, self).get_values(context)
        if self.is_outside_chord(context):
            values = [values[0] + ['z']]
            if not isinstance(context.current_element, AbcEmptyLineWithinTune):
                values = [values[0] + [ValueImageDescription(os.linesep, 'enter', description='')]]
        return values

    @staticmethod
    def is_outside_chord(context):
        return not isinstance(context.current_element, AbcChord)


class InsertAnnotationAction(InsertValueAction):
    values = [
        ValueDescription('""', _('Chord symbol')),
        ValueDescription('"<("">)"', _('Between parenthesis')),
        ValueDescription('"<(\u266f)"', _('Optional sharp'), common=False),
        ValueDescription('"<(\u266e)"', _('Optional natural'), common=False),
        ValueDescription('"<(\u266d)"', _('Optional flat'), common=False)
    ]
    def __init__(self, name='insert_annotation_or_chord', matchgroup=None):
        super(InsertAnnotationAction, self).__init__(name, InsertAnnotationAction.values, matchgroup=matchgroup, display_name=_('Insert annotation or chord'))
        self.caret_after_matchgroup = True


class AddAnnotationOrChordToNoteAction(InsertAnnotationAction):
    def __init__(self):
        super(AddAnnotationOrChordToNoteAction, self).__init__(name='add_annotation_or_chord_to_note', matchgroup='decoanno')


class InsertDecorationAction(InsertValueAction):
    values = [
        ValueImageDescription('!mf!', 'mf', _('Dynamics')),
        ValueImageDescription('!trill!', 'trill', _('Ornament')),
        ValueImageDescription('!fermata!', 'fermata', _('Articulation')),
        ValueImageDescription('!segno!', 'segno', _('Direction')),
        ValueImageDescription('!5!', '5', _('Fingering'), common=False)
    ]
    def __init__(self, name='insert_decoration', matchgroup=None):
        super(InsertDecorationAction, self).__init__(name, InsertDecorationAction.values, matchgroup=matchgroup, display_name=_('Insert decoration'))
        self.caret_after_matchgroup = True


class AddDecorationToNoteAction(InsertDecorationAction):
    def __init__(self):
        super(AddDecorationToNoteAction, self).__init__(name='add_decoration_to_note', matchgroup='decoanno')


class AddSlurAction(AbcAction):
    def __init__(self):
        super(AddSlurAction, self).__init__('add_slur', display_name=_('Add slur'))

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('({0})'.format(context.match_text))


class AddBarAction(AbcAction):
    def __init__(self):
        super(AddBarAction, self).__init__('add_bar', display_name=_('Add bar'))

    def can_execute(self, context, params=None):
        return self.is_action_allowed(context)

    def execute(self, context, params=None):
        text = self.get_bar_value(context)
        context.insert_text(text)

    @staticmethod
    def get_bar_value(context):
        prev_char = context.get_scope_info(TuneScope.PreviousCharacter).text
        pre_space = ''
        if prev_char not in ' \r\n:':
            pre_space = ' '
        return '{0}|'.format(pre_space)

    @staticmethod
    def is_action_allowed(context):
        if not context.abc_section in [AbcSection.TuneBody]:
            return False

    @staticmethod
    def is_bar_expected(context):
        text = context.get_scope_info(TuneScope.LineUpToSelection).text
        bar_re = re.compile(AbcBar.pattern)
        last_bar_offset = max([0] + [m.end(0) for m in bar_re.finditer(text)])  # offset of last bar symbol
        text = text[last_bar_offset:]  # the text from the last bar symbol up to the selection point
        tune_upto_selection = context.get_scope_info(TuneScope.TuneUpToSelection).text
        metre, default_len = AbcTune(tune_upto_selection).get_metre_and_default_length()

        if re.match(r"^[XZ]\d*$", text):
            duration = metre
        else:
            duration = get_bar_length(text, default_len, metre)

        result = duration >= metre
        return result


class CombineUsingBeamAction(AbcAction):
    def __init__(self):
        super(CombineUsingBeamAction, self).__init__('beam_notes', display_name=_('Combine using beam'))

    def can_execute(self, context, params=None):
        return True # check if all notes are shorter than a quarter note

    def execute(self, context, params=None):
        text = re.sub(r'\s+', '`', context.match_text)
        context.replace_match_text(text)


class CombineToChordAction(AbcAction):
    def __init__(self):
        super(CombineToChordAction, self).__init__('combine_to_chord', display_name=_('Combine to chord'))

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('[{0}]'.format(context.match_text.replace(' ', '')))


class MakeTripletsAction(AbcAction):
    notes_re = re.compile(AbcNoteGroup.note_or_chord_pattern)
    def __init__(self):
        super(MakeTripletsAction, self).__init__('make_triplets', display_name=_('Make triplets'))

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
        ValueDescription('landscape', _('Page orientation'))
    ]
    def __init__(self):
        super(PageFormatDirectiveChangeAction, self).__init__('change_page_format', PageFormatDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('Change page format'))


class MeasureNumberingChangeAction(DirectiveChangeAction):
    values = [
        ValueDescription('-1', _('None')),
        ValueDescription('0', _('Start of every line')),
        ValueDescription('1', _('Every measure')),
        ValueDescription('2', _('Every 2 measures')),
        ValueDescription('4', _('Every 4 measures')),
        ValueDescription('5', _('Every 5 measures')),
        ValueDescription('8', _('Every 8 measures')),
        ValueDescription('10', _('Every 10 measures'))
    ]
    def __init__(self):
        super(MeasureNumberingChangeAction, self).__init__('measurenb', 'change_measurenb', MeasureNumberingChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('Show measure numbers'))


class MeasureBoxChangeAction(DirectiveChangeAction):
    values = [
        ValueDescription('0', _('Normal')),
        ValueDescription('1', _('Boxed'))
    ]
    def __init__(self):
        super(MeasureBoxChangeAction, self).__init__('measurebox', 'change_measurebox', MeasureBoxChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('Show measure box'))


class FirstMeasureNumberChangeAction(DirectiveChangeAction):
    values = [
        ValueDescription('0', _('Zero')),
        ValueDescription('1', _('One'))
    ]
    def __init__(self):
        super(FirstMeasureNumberChangeAction, self).__init__('setbarnb', 'change_setbarnb', MeasureNumberingChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('First measure number'))


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
        super(FontDirectiveChangeAction, self).__init__('change_font_directive', FontDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('Change font directive'))


class ScaleDirectiveChangeAction(ValueChangeAction):
    values = [
        ValueDescription('scale', _('Page scale factor')),
        ValueDescription('staffscale', _('Staff scale factor'))
    ]
    def __init__(self):
        super(ScaleDirectiveChangeAction, self).__init__('change_scale_directive', ScaleDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('Change scale directive'))


class InsertDirectiveAction(InsertValueAction):
    values = [
        ValueDescription('MIDI', _('MIDI')),
        ValueDescription('pagewidth', _('Page layout')),
        ValueDescription('scale', _('Scale')),
        ValueDescription('titlefont', _('Font'))
    ]
    def __init__(self):
        super(InsertDirectiveAction, self).__init__('insert_directive', InsertDirectiveAction.values, display_name=_('Insert directive'))


class InsertTextAlignSymbolAction(InsertValueAction):
    values = [
        CodeDescription('-', _('break between syllables within a word')),
        CodeDescription('_', _('previous syllable is to be held for an extra note')),
        CodeDescription('*', _('one note is skipped (* is equivalent to a blank syllable)')),
        CodeDescription('~', _('appears as a space; aligns multiple words under one note')),
        CodeDescription(r'\-', _('appears as hyphen; aligns multiple syllables under one note')),
        CodeDescription('|', _('advances to the next bar'))
    ]
    def __init__(self):
        super(InsertTextAlignSymbolAction, self).__init__('insert_text_align_symbol', InsertTextAlignSymbolAction.values, display_name=_('Insert align symbol'))


class InsertAlignSymbolAction(InsertValueAction):
    values = [
        CodeDescription('*', _('one note is skipped')),
        CodeDescription('|', _('advances to the next bar'))
    ]
    def __init__(self):
        super(InsertAlignSymbolAction, self).__init__('insert_align_symbol', InsertAlignSymbolAction.values, display_name=_('Insert align symbol'))


class InsertFieldAction(InsertValueAction):
    values = [
        ValueDescription('K:', _('Key / clef')),
        ValueDescription('M:', name_to_display_text['meter']),
        ValueDescription('Q:', name_to_display_text['tempo']),
    ]
    def __init__(self):
        super(InsertFieldAction, self).__init__('insert_field', InsertFieldAction.values, display_name=_('Change...'))

    def execute(self, context, params=None):
        value = params.get('value')
        if value is None:
            super(InsertValueAction, self).execute(context, params)
        else:
            if not context.previous_character in '\r\n':
                context.insert_text('[{0}]'.format(value))
            else:
                context.insert_text(value)


class InsertFieldActionEmptyLineAction(InsertFieldAction):
    values = [
        ValueDescription('K:', _('Key / clef')),
        ValueDescription('M:', name_to_display_text['meter']),
        ValueDescription('Q:', name_to_display_text['tempo']),
        ValueDescription('L:', name_to_display_text['unit note length'], common=False),
        ValueDescription('V:', name_to_display_text['voice'], common=False),
        ValueDescription('w:', name_to_display_text['words (note aligned)'], common=False),
        ValueDescription('W:', name_to_display_text['words (at the end)'], common=False),
    ]
    def __init__(self):
        super(InsertFieldAction, self).__init__('insert_field_on_empty_line', InsertFieldActionEmptyLineAction.values, display_name=_('Change...'))

    def is_action_allowed(self, context):
        return super(InsertFieldActionEmptyLineAction, self).is_action_allowed(context) and context.tune_body != ''


class ActionSeparator(AbcAction):
    def __init__(self):
        super(ActionSeparator, self).__init__('separator')

    def get_action_html(self, context):
        #return '<BR>'
        return '<HR WIDTH="90%" NOSHADE>'


##################################################################################################
#  REMOVE ACTIONS
##################################################################################################

class RemoveAction(AbcAction):
    def __init__(self):
        super(RemoveAction, self).__init__('remove', display_name=_('Remove'))

    def get_action_html(self, context):
        desc = escape(self.display_name)
        params = {}
        action_url = self.get_action_url(params)
        image_html = html_image('remove-black', desc)
        columns = []
        columns += [UrlTuple(action_url, image_html)]
        columns += [UrlTuple(action_url, desc)]
        return ActionSeparator().get_action_html(context) + html_table([tuple(columns)], cellpadding=2)

    def execute(self, context, params=None):
        context.replace_match_text('')



##################################################################################################
#  ACTION HANDLERS
##################################################################################################


class AbcActionHandler(object):
    def __init__(self, actions = None, parent=None):
        self._actions_by_name = {}
        self._actions_ordered = []
        self.parent = parent
        if actions is not None:
            for action in actions:
                self.add_action(action)

    def add_action(self, action):
        self._actions_ordered.append(action)
        self._actions_by_name[action.name] = action

    def get_action(self, name):
        result = self._actions_by_name.get(name)
        if result is None and self.parent:
            result = self.parent.action_by_name(name)
        return result

    def get_action_html(self, context):
        rows = []
        for action in self._actions_ordered:
            rows.append(action.get_action_html(context))
        return html_table(rows)


class AbcActionHandlers(object):
    def __init__(self, elements):
        self.default_action_handler = AbcActionHandler()
        self.registered_actions = {}
        self.register_actions([
            NewTuneAction(),
            NewNoteOrRestAction(),
            NewLineAction(),
            RemoveAction(),
            NoteDurationAction(),
            AddSlurAction(),
            MakeTripletsAction(),
            CombineUsingBeamAction(),
            InsertFieldAction(),
            InsertFieldActionEmptyLineAction(),
            AbcStandardUrlAction(),
            AccidentalChangeAction(),
            PitchAction(),
            BarChangeAction(),
            RedefinableSymbolChangeAction(),
            RestDurationAction(),
            MeasureRestDurationAction(),
            SlurChangeAction(),
            CombineToChordAction(),
            DynamicsDecorationChangeAction(),
            ArticulationDecorationChangeAction(),
            OrnamentDecorationChangeAction(),
            DirectionDecorationChangeAction(),
            FingeringDecorationChangeAction(),
            RestVisibilityChangeAction(),
            MeasureRestVisibilityChangeAction(),
            AppoggiaturaOrAcciaccaturaChangeAction(),
            InsertAnnotationAction(),
            AddAnnotationOrChordToNoteAction(),
            InsertDecorationAction(),
            AddDecorationToNoteAction(),
            ChangeAnnotationAction(),
            AnnotationPositionAction(),
            ConvertToAnnotationAction(),
            InsertAlignSymbolAction(),
            InsertTextAlignSymbolAction(),
            KeySignatureChangeAction(),
            KeyModeChangeAction(),
            UnitNoteLengthChangeAction(),
            MeterChangeAction(),
            FixCharactersAction(),
            ClefChangeAction(),
            StaffTransposeChangeAction(),
            AbcOctaveChangeAction(),
            PlaybackTransposeChangeAction(),
            TempoNotationChangeAction(),
            TempoNameChangeAction(),
            TempoNoteLengthChangeAction(),
            TempoNote2LengthChangeAction(),
            ChordNoteChangeAction(),
            ChordNameChangeAction(),
            ChordBaseNoteChangeAction(),
            ActionSeparator(),
        ])

        self.action_handlers = {
            'empty_document'         : self.create_handler(['new_tune']),
            'abcversion'             : self.create_handler(['lookup_abc_standard']),
            'empty_line'             : self.create_handler(['new_tune']),
            'empty_line_file_header' : self.create_handler(['new_tune']),
            'empty_line_tune'        : self.create_handler(['new_tune', 'new_note', 'insert_field_on_empty_line']),
            'Whitespace'             : self.create_handler(['new_note', 'insert_field', 'remove']),
            'Note'                   : self.create_handler(['new_note', 'change_accidental', 'change_note_duration', 'change_pitch', 'add_decoration_to_note', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Rest'                   : self.create_handler(['new_note', 'change_rest_duration', 'change_rest_visibility', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Measure rest'           : self.create_handler(['new_note', 'change_measurerest_duration', 'change_rest_visibility', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Bar'                    : self.create_handler(['change_bar', 'remove']),
            'Annotation'             : self.create_handler(['change_annotation', 'change_annotation_position', 'remove']),
            'Chord'                  : self.create_handler(['new_note', 'change_note_duration', 'add_decoration_to_note', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Chord symbol'           : self.create_handler(['change_chord_note', 'change_chord_name', 'change_chord_bass_note', 'remove']),
            'Grace notes'            : self.create_handler(['change_appoggiatura_acciaccatura', 'remove']),
            'Multiple notes'         : self.create_handler(['add_slur', 'make_triplets', 'beam_notes', 'combine_to_chord', 'remove']),
            'Multiple notes/chords'  : self.create_handler(['add_slur', 'make_triplets', 'beam_notes', 'remove']),
            'Dynamics'               : self.create_handler(['change_dynamics', 'remove']),
            'Articulation'           : self.create_handler(['change_articulation', 'remove']),
            'Ornament'               : self.create_handler(['change_ornament', 'remove']),
            'Direction'              : self.create_handler(['change_direction', 'remove']),
            'Fingering'              : self.create_handler(['change_fingering', 'remove']),
            'Redefinable symbol'     : self.create_handler(['change_redefinable_symbol']),
            'Chord or annotation'    : self.create_handler(['change_chord_note', 'convert_to_annotation', 'remove']),
            'Slur'                   : self.create_handler(['change_slur']),
            #'Stylesheet directive'  self.create_handler: self.create_handler([InsertDirectiveAction()]),
            'w:'                     : self.create_handler(['insert_text_align_symbol']),
            's:'                     : self.create_handler(['insert_decoration', 'insert_annotation_or_chord', 'insert_align_symbol']),
            'K:'                     : self.create_handler(['change_key_signature', 'change_key_mode']),
            'L:'                     : self.create_handler(['change_unit_note_length']),
            'M:'                     : self.create_handler(['change_meter']),
            'Q:'                     : self.create_handler(['change_tempo_notation', 'change_tempo_name', 'change_tempo_note1_length', 'change_tempo_note2_length']),
            '%'                      : self.create_handler(['fix_characters'])
        }

        for key in ['V:', 'K:']:
            self.add_actions(key, ['change_clef', 'staff_transpose', 'octave_shift', 'playback_transpose'])

        #for key in ['X:', 'T:']:
        #    self.add_actions(key, [NewVoiceAction()])

        for element in elements:
            if type(element) == AbcStringField:
                key = element.keyword or element.name
                self.add_actions(key, ['fix_characters'])

    def get_action_handler(self, element):
        if element:
            key = element.keyword or element.name
            return self.action_handlers.get(key, self.default_action_handler)
        return self.default_action_handler

    def add_actions(self, key, action_names):
        action_handler = self.action_handlers.get(key)
        if action_handler is None:
            self.action_handlers[key] = self.create_handler(action_names)
        else:
            for action_name in action_names:
                action_handler.add_action(self.action_by_name(action_name))

    def register_actions(self, actions):
        for action in actions:
            self.registered_actions[action.name] = action

    def create_handler(self, action_names):
        actions = []
        for action_name in action_names:
            actions.append(self.action_by_name(action_name))
        return AbcActionHandler(actions, parent=self)

    def action_by_name(self, action_name):
        action = self.registered_actions.get(action_name)
        if action is None:
            print('action {0} not registered'.format(action_name))
        else:
            return action
