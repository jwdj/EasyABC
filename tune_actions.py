from __future__ import unicode_literals
import re
import os
import sys
import traceback

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
from abc_tune import AbcTune, note_to_number, number_to_note
from abc_character_encoding import unicode_text_to_abc

if PY3:
    basestring = str
    def unicode(value):
        return value


UrlTuple = namedtuple('UrlTuple', 'url content')

from utils import get_application_path
application_path = get_application_path()

word_re = re.compile(r'\b(\w+)\b')

def get_words(text):
    return [m.group(1) for m in word_re.finditer(text)]

def path2url(path):
    # url_path = urlparse.urljoin('file:', urllib.pathname2url(path))
    # url_path = re.sub(r'(/[A-Z]:/)/', r'\1', url_path) # replace double slash after drive letter with single slash
    # return url_path
    return path  # wx.HtmlWindow can only handle regular path-name and not file:// notation

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
        self.show_current_value = False
        self.multiple_items_can_apply = False

    def can_execute(self, context, params=None):
        show_non_common = params.get('show_non_common')
        if show_non_common is not None:
            return True
        value = params.get('value', '')
        return not self.is_current_value(context, value)

    def get_current_value(self, context):
        current_value = None
        if self.matchgroup:
            match = self.get_match(context)
            if match:
                current_value = match.group(self.matchgroup)
        elif self.use_inner_match:
            current_value = context.inner_text
        else:
            current_value = context.match_text
        return current_value

    def is_current_value(self, context, value):
        current_value = self.get_current_value(context)
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
            value = value.encode('latin-1').decode('utf-8')
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

    def append_current_value_to_rows(self, context, rows):
        if self.show_current_value:
            current_value = self.get_current_value(context)
            if current_value and current_value.strip():
                descriptions = [v.description for v in self.get_values(context) if v.value == current_value]
                if descriptions:
                    text = descriptions[0]
                else:
                    text = current_value

                row = u'\u25BA ' + escape(text)
                rows.append(row)
                rows.append('<br>')
        return rows

    def get_action_html(self, context):
        result = u''
        if not self.is_action_allowed(context):
            return result
        rows = []
        rows = self.append_current_value_to_rows(context, rows)

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
                        if self.multiple_items_can_apply:
                            html = url_tuple_to_href(self.enclose_action_url(action_url, desc))
                            html = self.html_selected_item(context, value.value, html)
                            columns.append(html)
                        else:
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
                columns.append(self.html_selected_item(context, value, desc))

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

    def html_selected_item(self, context, value, description):
        if self.is_current_value(context, value):
            return description + ' \u25C4'
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
        self.matchgroup = 'text'

    def can_execute(self, context, params=None):
        chord = context.get_matchgroup('chordnote')
        return chord is None or chord[0].lower() not in 'abcdefg'

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
        ValueDescription('thirdup', _('Third up'), common=False),
        ValueDescription('thirddown', _('Third down'), common=False),
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
            if value == "'" or value == 'noteup' or value == 'thirdup':
                return note_no < 4*7
            elif value == ',' or value == 'notedown' or value == 'thirddown':
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
            elif value == 'thirdup':
                note_no += 2
            elif value == 'thirddown':
                note_no -= 2
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
    denominator_re = re.compile(r'/(\d*)')
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
        return ((num & (num - 1)) == 0) and num > 0

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
        ValueDescription('"<(\\u266f)"', _('Optional sharp')),
        ValueDescription('"<(\\u266e)"', _('Optional natural')),
        ValueDescription('"<(\\u266d)"', _('Optional flat')),
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

    def is_current_value(self, context, value):
        return True

    @staticmethod
    def abc_key_to_number(tonic, mode):
        middle_idx = len(key_ladder) // 2
        try:
            tonic_idx = key_ladder.index(tonic)
        except ValueError:
            return None

        mode_idx = KeyChangeAction.abc_mode_to_number(mode)

        if tonic_idx >= 0 and mode_idx is not None:
            return tonic_idx - middle_idx - mode_idx


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
            mode = context.get_matchgroup('mode')
            current_value = self.abc_key_to_number(tonic, mode)
            return current_value != value

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
            return not self.is_current_value(context, value)
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

    def is_current_value(self, context, value):
        match = self.get_match(context)
        return value == (match.group('clefname') or '')


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
        values = [ValueImageDescription(mark, self.get_image_name(mark), decoration_to_description[mark]) for mark in decoration_values]
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
            '!^!': 'marcato',
            '!upbow!': 'u',
            '!downbow!': 'v',
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
        super(ChordNoteChangeAction, self).__init__('change_chord_note', [], 'chordsymbol', display_name=_('Change chord'))
        self.show_current_value = True

    def contains_only_common(self, values):
        return False

    def get_values(self, context):
        try:
            (tonic, mode) = AbcTune(context.tune).initial_tonic_and_mode
            i = KeyChangeAction.abc_key_to_number(tonic, mode) - 2 + len(key_ladder) // 2
        except:
            i = key_ladder.index('C')

        return [
            self.get_value_for_chord(i),
            self.get_value_for_chord(i-1),
            self.get_value_for_chord(i+1),
            self.get_value_for_chord(i+1, '7', common=False),
            self.get_value_for_chord(i+3, 'm'),
            self.get_value_for_chord(i+2, 'm'),
            self.get_value_for_chord(i+4, 'm'),
            self.get_value_for_chord(i+4, '7', common=False),
            self.get_value_for_chord(i+5, 'dim', common=False),
        ]

    @staticmethod
    def get_value_for_chord(index, suffix = '', common=True):
        chord = key_ladder[index] + suffix
        return ValueDescription(chord, chord.replace('#', u'\u266F').replace('b', u'\u266D'), common=common)


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


class MidiInstrumentChangeAction(ValueChangeAction):
    def __init__(self):
        super(MidiInstrumentChangeAction, self).__init__('change_midi_instrument', self.get_instrument_values(), matchgroup='instrument', display_name=_('Change instrument'), use_inner_match=False)
        self.show_current_value = True

    @staticmethod
    def get_instrument_values():
        from generalmidi import general_midi_instruments
        return [ValueDescription(u' ' + str(index), value) for index, value in enumerate(general_midi_instruments)]


class MidiChannelChangeAction(ValueChangeAction):
    def __init__(self):
        super(MidiChannelChangeAction, self).__init__('change_midi_channel', self.get_channel_values(), matchgroup='channel', display_name=_('Change channel'), use_inner_match=False)

    @staticmethod
    def get_channel_values():
        return [ValueDescription(' ' + str(channel), str(channel)) for channel in range(1, 16 + 1)]


class MidiDrumInstrumentChangeAction(ValueChangeAction):
    values = [
        ValueDescription('27', _('High Q'), common=False),
        ValueDescription('28', _('Slap'), common=False),
        ValueDescription('29', _('Scratch Push'), common=False),
        ValueDescription('30', _('Scratch Pull'), common=False),
        ValueDescription('31', _('Sticks'), common=False),
        ValueDescription('32', _('Square Click'), common=False),
        ValueDescription('33', _('Metronome Click'), common=False),
        ValueDescription('34', _('Metronome Bell'), common=False),
        ValueDescription('35', _('Acoustic Bass Drum')),
        ValueDescription('36', _('Bass Drum 1')),
        ValueDescription('37', _('Side Stick')),
        ValueDescription('38', _('Acoustic Snare')),
        ValueDescription('39', _('Hand Clap')),
        ValueDescription('40', _('Electric Snare')),
        ValueDescription('41', _('Low Floor Tom')),
        ValueDescription('42', _('Closed Hi Hat')),
        ValueDescription('43', _('High Floor Tom')),
        ValueDescription('44', _('Pedal Hi-Hat')),
        ValueDescription('45', _('Low Tom')),
        ValueDescription('46', _('Open Hi-Hat')),
        ValueDescription('47', _('Low-Mid Tom')),
        ValueDescription('48', _('Hi Mid Tom')),
        ValueDescription('49', _('Crash Cymbal 1')),
        ValueDescription('50', _('High Tom')),
        ValueDescription('51', _('Ride Cymbal 1')),
        ValueDescription('52', _('Chinese Cymbal')),
        ValueDescription('53', _('Ride Bell')),
        ValueDescription('54', _('Tambourine')),
        ValueDescription('55', _('Splash Cymbal')),
        ValueDescription('56', _('Cowbell')),
        ValueDescription('57', _('Crash Cymbal 2')),
        ValueDescription('58', _('Vibraslap')),
        ValueDescription('59', _('Ride Cymbal 2')),
        ValueDescription('60', _('Hi Bongo')),
        ValueDescription('61', _('Low Bongo')),
        ValueDescription('62', _('Mute Hi Conga')),
        ValueDescription('63', _('Open Hi Conga')),
        ValueDescription('64', _('Low Conga')),
        ValueDescription('65', _('High Timbale')),
        ValueDescription('66', _('Low Timbale')),
        ValueDescription('67', _('High Agogo')),
        ValueDescription('68', _('Low Agogo')),
        ValueDescription('69', _('Cabasa')),
        ValueDescription('70', _('Maracas')),
        ValueDescription('71', _('Short Whistle')),
        ValueDescription('72', _('Long Whistle')),
        ValueDescription('73', _('Short Guiro')),
        ValueDescription('74', _('Long Guiro')),
        ValueDescription('75', _('Claves')),
        ValueDescription('76', _('Hi Wood Block')),
        ValueDescription('77', _('Low Wood Block')),
        ValueDescription('78', _('Mute Cuica')),
        ValueDescription('79', _('Open Cuica')),
        ValueDescription('80', _('Mute Triangle')),
        ValueDescription('81', _('Open Triangle')),
        ValueDescription('82', _('Shaker'), common=False),
        ValueDescription('83', _('Jingle Bell'), common=False),
        ValueDescription('84', _('Belltree'), common=False),
        ValueDescription('85', _('Castanets'), common=False),
        ValueDescription('86', _('Closed Surdo'), common=False),
        ValueDescription('87', _('Open Surdo'), common=False),
    ]
    def __init__(self):
        super(MidiDrumInstrumentChangeAction, self).__init__('change_midi_drum_instrument', MidiDrumInstrumentChangeAction.values, matchgroup='druminstrument', display_name=_('Change percussion instrument'))
        self.show_current_value = True


class MidiVolumeChangeAction(ValueChangeAction):
    values = [
        ValueDescription('0', _('Muted')),
        ValueDescription('13', '10 %'),
        ValueDescription('26', '20 %'),
        ValueDescription('39', '30 %'),
        ValueDescription('51', '40 %'),
        ValueDescription('64', '50 %'),
        ValueDescription('77', '60 %'),
        ValueDescription('89', '70 %'),
        ValueDescription('102', '80 %'),
        ValueDescription('115', '90 %'),
        ValueDescription('127', '100 %'),
    ]
    def __init__(self):
        super(MidiVolumeChangeAction, self).__init__('change_midi_volume', MidiVolumeChangeAction.values, matchgroup='volume', display_name=_('Change volume'))

    def append_current_value_to_rows(self, context, rows):
        current_value = self.get_current_value(context)

        if current_value and current_value.strip():
            row = u'{0} %'.format(int(current_value) * 100 // 127)
            rows.append(row)
            volume_bars = 50
            volume_bar = int(current_value) * volume_bars // 127
            rows.append('[{0}{1}]'.format('|' * volume_bar, u'&#x2005;' * (volume_bars - volume_bar)))
            rows.append('<br>')
        return rows


class MidiGuitarChordChangeAction(ValueChangeAction):
    values_even = [
        ValueDescription('fcfc', _('Preset') + ' 1'),
        ValueDescription('c',   _('Preset') + ' 2'),
        ValueDescription('fc', _('Preset') + ' 3'),
        ValueDescription('f3c3c2', _('Preset') + ' 4'),
        ValueDescription('GIHI', _('Preset') + ' 5'),
        ValueDescription('', _('Custom')),
    ]
    values_odd = [
        ValueDescription('fccfcc', _('Preset') + ' 1'),
        ValueDescription('c',   _('Preset') + ' 2'),
        ValueDescription('fcc', _('Preset') + ' 3'),
        ValueDescription('fc', _('Preset') + ' 4'),
        ValueDescription('GIIHII', _('Preset') + ' 5'),
        ValueDescription('', _('Custom')),
    ]
    def __init__(self):
        super(MidiGuitarChordChangeAction, self).__init__('change_gchord', [], matchgroup='pattern', display_name=_('Change guitar pattern'))
        self.show_current_value = True

    def get_values(self, context):
        try:
            metre, default_len = AbcTune(context.tune_header).get_metre_and_default_length()
            if metre.numerator % 3 == 0:
                return MidiGuitarChordChangeAction.values_odd
        except:
            pass
        return MidiGuitarChordChangeAction.values_even


class MidiGuitarChordInsertAction(InsertValueAction):
    values = [
        CodeDescription('f', _('Fundamental')),
        CodeDescription('c', _('Chord')),
        CodeDescription('z', _('Rest')),
        CodeDescription('2', _('Double duration')),
        CodeDescription('b', _('Fundamental plus chord'), common=False),
        CodeDescription('G', _('Lowest note'), common=False),
        CodeDescription('H', _('Second note'), common=False),
        CodeDescription('I', _('Third note'), common=False),
        CodeDescription('J', _('Fourth note'), common=False),
        CodeDescription('g', _('Lowest note') + ' ' + _('an octave higher'), common=False),
        CodeDescription('h', _('Second note') + ' ' + _('an octave higher'), common=False),
        CodeDescription('i', _('Third note') + ' ' + _('an octave higher'), common=False),
        CodeDescription('j', _('Fourth note') + ' ' + _('an octave higher'), common=False),
    ]
    def __init__(self):
        super(MidiGuitarChordInsertAction, self).__init__('insert_gchord', MidiGuitarChordInsertAction.values, matchgroup='pattern', display_name=_('Insert pattern'))


class MidiGuitarChordTimeAction(ValueChangeAction):
    def __init__(self):
        super(MidiGuitarChordTimeAction, self).__init__('time_gchord', [], matchgroup='pattern', display_name=_('Change time'))

    def get_values(self, context):
        values = []
        current_value = self.get_current_value(context)
        values.append(ValueDescription('/', _('Double time')))
        l = len(current_value)
        if l >= 2 and current_value[:l // 2] == current_value[l // 2:]:
            values.append(ValueDescription('2', _('Half time')))
        return values

    def execute(self, context, params=None):
        value = params.get('value', '')
        current_value = self.get_current_value(context)
        if value == '/':
            new_text = current_value + current_value
        else:
            new_text = current_value[:len(current_value) // 2]
        context.replace_match_text(new_text, self.matchgroup) # , tune_scope=self.get_tune_scope())


##################################################################################################
#  COSMETIC ACTIONS
##################################################################################################


class Space(AbcAction):
    def __init__(self):
        super(Space, self).__init__('')

    def get_action_html(self, context):
        return u'<br>'


##################################################################################################
#  URL ACTIONS
##################################################################################################


class UrlAction(AbcAction):
    def __init__(self, name, url=None):
        super(UrlAction, self).__init__(name)
        self.url = url

    def can_execute(self, context, params=None):
        return self.get_url(context) is not None

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
    def __init__(self):
        super(UrlAction, self).__init__('lookup_abcm2ps')

    def get_url(self, context):
        keyword = self.get_keyword_from_context(context)
        if keyword:
            url = 'http://moinejf.free.fr/abcm2ps-doc/{0}.xhtml'.format(quote(keyword))
            return url
        return None

    def get_keyword_from_context(self, context):
        return context.inner_text.strip().split(' ', 1)[0]


class Abc2MidiUrlAction(UrlAction):
    def __init__(self):
        super(UrlAction, self).__init__('lookup_abc2midi')

    def get_url(self, context):
        keyword = self.get_keyword_from_context(context)
        if keyword:
            url = 'https://abcmidi.sourceforge.io/#{0}'.format(quote(keyword))
            return url
        return None

    def get_keyword_from_context(self, context):
        return context.inner_text[len('MIDI '):].strip().split(' ', 1)[0]

class AbcStandardUrlAction(UrlAction):
    def __init__(self):
        super(AbcStandardUrlAction, self).__init__('lookup_abc_standard')

    def get_url(self, context):
        version = self.get_version_from_context(context)
        return 'http://abcnotation.com/wiki/abc:standard:v{0}'.format(version)

    def can_execute(self, context, params=None):
        version = self.get_version_from_context(context)
        return version.startswith('2.')

    @staticmethod
    def get_version_from_context(context):
        return context.get_matchgroup('version', '2.1')

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
        text += os.linesep + 'T:' + _('Untitled') + ' %d' % new_tune_id
        text += os.linesep + 'C:' + _('Unknown composer')
        text += os.linesep + 'M:4/4'
        text += os.linesep + 'L:1/4'
        text += os.linesep + 'Q:1/4=120'
        text += os.linesep + self.key_and_body()

        if not context.contains_text:
            text = r'%abc-2.1' + os.linesep + os.linesep + text
        elif context.previous_line and not context.previous_line.isspace():
            text = os.linesep + text
        context.insert_text(text)

    def key_and_body(self):
        return 'K:C' + os.linesep


class NewMultiVoiceTuneAction(NewTuneAction):
    def __init__(self):
        super(NewTuneAction, self).__init__('new_multivoice_tune', display_name=_('New tune with multiple voices'))

    def key_and_body(self):
        return '''V:S clef=treble name=S
V:A clef=treble name=A
V:T clef=bass name=T
V:B clef=bass name=B
%%score [ (S A) (T B) ]
K:C
V:S
%%MIDI program 52
c
V:A
%%MIDI program 53
G
V:T
%%MIDI program 54
G,
V:B
%%MIDI program 35
C,
'''


class NewDrumTuneAction(NewTuneAction):
    def __init__(self):
        super(NewTuneAction, self).__init__('new_drum_tune', display_name=_('New drum score'))

    def key_and_body(self):
        return '''%%MIDI drummap ^a 49
%%MIDI drummap ^g 42
%%MIDI drummap _g 46
%%MIDI drummap c 38
%%MIDI drummap F 35
V:1
V:2
%%score ( 1 2 )
K:C clef=perc
V:1
%%MIDI channel 10
^a^g[c^g]^g | ^g^g[c^g]_g | ^g^g[c^g]^g | ^g/c/^g c/^a3/ ||
V:2
%%MIDI channel 10
FF/F/ z3/{/F}F/ | zF/F/ z/F3/ | FF/F/ z3/F/ | z3/F/ z/F3/ ||
'''


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

    def get_action_html(self, context):
        if self.can_execute(context):
            return ActionSeparator().get_action_html(context) + super(FixCharactersAction, self).get_action_html(context)
        else:
            return super(FixCharactersAction, self).get_action_html(context)


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
            if not isinstance(context.current_element, AbcEmptyLineWithinTuneBody):
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
        ValueImageDescription('P', 'pralltriller', _('Shortcut symbol'), common=False),
        ValueImageDescription('!5!', '5', _('Fingering'), common=False),
        ValueImageDescription('!editorial!', 'editorial', _('Accidental'), common=False),
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
        context.replace_match_text('(3' + context.match_text)


class ShowSingleVoiceAction(ValueChangeAction):
    def __init__(self):
        super(ShowSingleVoiceAction, self).__init__('show_single_voice', [], display_name=_('Show single voice'), use_inner_match=True)
        self.show_current_value = True

    def get_values(self, context):
        tune = AbcTune(context.tune)
        all_voices = tune.get_voice_ids()
        values = [ValueDescription(voice_id, voice_id) for voice_id in all_voices]
        return values

    def can_execute(self, context, params=None):
        tune = AbcTune(context.tune or '')
        voice = params.get('value', '')
        if len(tune.get_voice_ids()) > 1 and not self.is_current_value(context, voice):
            return True

    def execute(self, context, params=None):
        voice = params.get('value', '')
        new_text = ' ' + voice
        context.replace_match_text(new_text, tune_scope=TuneScope.InnerText)

    def is_action_allowed(self, context):
        if len(self.get_values(context)) > 1:
            return True

    def get_current_value(self, context):
        current_value = None
        shown_voices = get_words(context.inner_text)
        if shown_voices and len(shown_voices) == 1:
            current_value = shown_voices[0]
        return current_value


class ShowAllVoicesAction(AbcAction):
    def __init__(self):
        super(ShowAllVoicesAction, self).__init__('show_all_voices', display_name=_('Show all voices'))

    def can_execute(self, context, params=None):
        tune = AbcTune(context.tune or '')
        all_voices = tune.get_voice_ids()
        shown_voices = get_words(context.inner_text)
        hidden_voices = [v for v in all_voices if v not in shown_voices]
        if hidden_voices:
            return True

    def execute(self, context, params=None):
        tune = AbcTune(context.tune)
        all_voices = tune.get_voice_ids()
        new_text = ' ' + ' '.join(all_voices)
        context.replace_match_text(new_text, tune_scope=TuneScope.InnerText)


class ShowVoiceAction(ValueChangeAction):
    def __init__(self):
        super(ShowVoiceAction, self).__init__('show_voice', [], display_name=_('Show additional voice'), use_inner_match=True)

    def get_values(self, context):
        tune = AbcTune(context.tune)
        all_voices = tune.get_voice_ids()
        shown_voices = get_words(context.inner_text)
        hidden_voices = [v for v in all_voices if v not in shown_voices]
        values = [ValueDescription(voice_id, voice_id) for voice_id in hidden_voices]
        return values

    def can_execute(self, context, params=None):
        return context.tune is not None

    def execute(self, context, params=None):
        voice = params.get('value', '')
        text = context.inner_text
        insert_pos = None
        shown_voices = get_words(context.inner_text)
        if shown_voices:
            last_voice = shown_voices[-1]
            new_text = re.sub(r'\b' + last_voice + r'\b', last_voice + ' ' + voice, text)
        else:
            new_text = ' ' + voice
        context.replace_match_text(new_text, tune_scope=TuneScope.InnerText)

    def is_action_allowed(self, context):
        if self.get_values(context):
            return True


class HideVoiceAction(ValueChangeAction):
    def __init__(self):
        super(HideVoiceAction, self).__init__('hide_voice', [], display_name=_('Hide voice'), use_inner_match=True)

    def can_execute(self, context, params=None):
        return True

    def get_values(self, context):
        voices = get_words(context.inner_text)
        return [ValueDescription(voice, voice) for voice in voices]

    def execute(self, context, params=None):
        voice = params.get('value', '')
        new_text = re.sub(r'\b' + voice + r'\b', '', context.inner_text)
        new_text = re.sub(' +', ' ', new_text)
        context.replace_match_text(new_text, tune_scope=TuneScope.InnerText)

    def is_action_allowed(self, context):
        values = self.get_values(context)
        if len(values) > 1:
            return True


class JoinTogetherInScoreAction(AbcAction):
    def __init__(self, action_name, begin_char, end_char, display_name):
        super(JoinTogetherInScoreAction, self).__init__(action_name, display_name=display_name)
        self.begin_char = begin_char
        self.end_char = end_char

    def can_execute(self, context, params=None):
        text = context.inner_text
        return not self.begin_char in text and not self.end_char in text and len(get_words(text)) > 1

    def execute(self, context, params=None):
        new_text = ' {0} {1} {2}'.format(self.begin_char, context.inner_text.strip(), self.end_char)
        context.replace_match_text(new_text, tune_scope=TuneScope.InnerText)


class GroupTogetherAction(JoinTogetherInScoreAction):
    def __init__(self):
        super(GroupTogetherAction, self).__init__('group_together', '(', ')', display_name=_('Group together on same stave'))

    def can_execute(self, context, params=None):
        if super(GroupTogetherAction, self).can_execute(context, params):
            text = context.inner_text
            for c in r'[\{\}]':
                if c in text:
                    return False
                return True


class BraceTogetherAction(JoinTogetherInScoreAction):
    def __init__(self):
        super(BraceTogetherAction, self).__init__('brace_together', '{', '}', display_name=_('Brace together'))

    def can_execute(self, context, params=None):
        if super(BraceTogetherAction, self).can_execute(context, params):
            text = context.inner_text
            for c in r'[]':
                if c in text:
                    return False
                return True


class BracketTogetherAction(JoinTogetherInScoreAction):
    def __init__(self):
        super(BracketTogetherAction, self).__init__('bracket_together', '[', ']', display_name=_('Bracket together'))


class ToggleContinuedBarlinesAction(AbcAction):
    def __init__(self):
        super(ToggleContinuedBarlinesAction, self).__init__('toggle_continued_barlines', display_name=_('Toggle continued bar lines'))

    def can_execute(self, context, params=None):
        shown_voices = get_words(context.inner_text)
        return len(shown_voices) > 1

    def execute(self, context, params=None):
        text = context.inner_text
        replace_value = ' | '
        if '|' in text:
            replace_value = ' '
        new_text = re.sub(r'(?<=[\w\)])(?:\s*\|\s*|\s+)(?=[\w\(])', replace_value, text)
        context.replace_match_text(new_text, tune_scope=TuneScope.InnerText)


class SimplifyNoteAction(AbcAction):
    def __init__(self):
        super(SimplifyNoteAction, self).__init__('simplify_note', display_name=_('Simplify note'))

    def can_execute(self, context, params=None):
        note = self.current_note(context)
        new_note = self.simplified_note(context)
        return note != new_note

    def execute(self, context, params=None):
        new_note = self.simplified_note(context)
        context.replace_matchgroups([('note', new_note[0]), ('octave', new_note[1:])])

    def current_note(self, context):
        return context.get_matchgroup('note') + context.get_matchgroup('octave')

    def simplified_note(self, context):
        note = self.current_note(context)
        num = note_to_number(note)
        return number_to_note(num)


class PickFieldsAction(ValueChangeAction):
    values = [
        CodeDescription('B', _('Book'                ), common=False),
        CodeDescription('C', _('Composer'            )),
        CodeDescription('D', _('Discography'         ), common=False),
        CodeDescription('F', _('File url'            ), common=False),
        CodeDescription('G', _('Group'               ), common=False),
        CodeDescription('H', _('History'             ), common=False),
        CodeDescription('N', _('Notes'               ), common=False),
        CodeDescription('O', _('Origin'              )),
        CodeDescription('P', _('Parts'               )),
        CodeDescription('Q', _('Tempo'               )),
        CodeDescription('R', _('Rhythm'              )),
        CodeDescription('S', _('Source'              ), common=False),
        CodeDescription('T', _('Tune title'          )),
        CodeDescription('w', _('Words (note aligned)')),
        CodeDescription('W', _('Words (at the end)'  )),
        CodeDescription('X', _('Reference number'    ), common=False),
        CodeDescription('Z', _('Transcription'       ), common=False),
    ]
    def __init__(self):
        super(PickFieldsAction, self).__init__('pick_fields', PickFieldsAction.values, display_name=_('Fields'), matchgroup='fields')
        self.multiple_items_can_apply = True

    def is_current_value(self, context, value):
        current_value = self.get_current_value(context)
        return value in current_value

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        value = params.get('value')
        if value:
            current_value = (self.get_current_value(context) or '').replace('_', '')
            if value in current_value:
                new_text = current_value.replace(value, '')
            else:
                new_text = current_value + value
            if not new_text:
                new_text = '_'
            context.replace_matchgroups([('fields', new_text)])
        else:
            super(PickFieldsAction, self).execute(context, params)


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


class MeasureNumberingChangeAction(ValueChangeAction):
    values = [
        ValueDescription('-1', _('None')),
        ValueDescription('0', _('Start of every line')),
        ValueDescription('1', _('Every measure')),
        ValueDescription('4', _('Every 4 measures')),
        ValueDescription('5', _('Every 5 measures')),
    ]
    def __init__(self):
        super(MeasureNumberingChangeAction, self).__init__('change_measurenb', MeasureNumberingChangeAction.values, matchgroup='interval', display_name=_('Show measure numbers'))


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
        super(FirstMeasureNumberChangeAction, self).__init__('setbarnb', 'change_setbarnb', FirstMeasureNumberChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('First measure number'))


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
        ValueDescription('pagescale', _('Page scale factor')),
        ValueDescription('staffscale', _('Staff scale factor'))
    ]
    def __init__(self):
        super(ScaleDirectiveChangeAction, self).__init__('change_scale_directive', ScaleDirectiveChangeAction.values, valid_sections=AbcSection.TuneHeader, display_name=_('Change scale directive'))


class InsertDirectiveAction(InsertValueAction):
    values = [
        ValueDescription('score', _('Score layout')),
        ValueDescription('pagescale 1.0', _('Page scale factor')),
        ValueDescription('measurenb 0', _('Measure numbering')),
        ValueDescription('writefields PQ false', _('Hide fields')),
        ValueDescription('MIDI', _('Playback')),
    ]
    def __init__(self):
        super(InsertDirectiveAction, self).__init__('insert_directive', InsertDirectiveAction.values, display_name=_('Insert directive'))

    def is_action_allowed(self, context):
        return context.inner_text == ''


class InsertMidiDirectiveAction(InsertValueAction):
    play_chords_cmds = (
        r' chordprog 24    % ' + _('Chord instrument'),
        r'%%MIDI chordvol 64       % ' + _('Chord volume'),
        r'%%MIDI bassprog 24       % ' + _('Bass instrument'),
        r'%%MIDI bassvol 64        % ' + _('Bass volume'),
        r'%%MIDI gchordon',
        r'%%MIDI gchord c          % ' + _('Accompaniment pattern (optional). Place after line with M:')
    )
    values = [
        ValueDescription(' program 0       % ' + _('Instrument'), _('Set instrument')),
        ValueDescription(' control 7 127   % ' + _('Volume'), _('Set volume')),
        # ValueDescription(' drum dddd 34 33 33 33 100 100 100 100        % {0}\n%%MIDI drumon'.format(_('Metronome')), _('Turn on metronome')),
        ValueDescription(os.linesep.join(play_chords_cmds), _('Play chords')),
    ]
    def __init__(self):
        super(InsertMidiDirectiveAction, self).__init__('insert_midi_directive', InsertMidiDirectiveAction.values, display_name=_('Insert playback directive'))


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
        ValueDescription('M:4/4', name_to_display_text['meter']),
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


class InsertFieldInHeaderAction(InsertValueAction):
    values = [
        ValueDescription('T:' + _('Untitled'), name_to_display_text['tune title']),
        ValueDescription('C:', name_to_display_text['composer']),
        ValueDescription('M:4/4', name_to_display_text['meter']),
        ValueDescription('L:1/4', name_to_display_text['unit note length']),
        ValueDescription('Q:1/4=120', name_to_display_text['tempo']),
        ValueDescription('V:1', name_to_display_text['voice']),
        ValueDescription(r'%%', name_to_display_text['instruction']),
        ValueDescription('I:', name_to_display_text['instruction'], common=False),
        ValueDescription('O:', name_to_display_text['origin'], common=False),
        ValueDescription('R:', name_to_display_text['rhythm'], common=False),
        ValueDescription('r:', name_to_display_text['remark'], common=False),
        ValueDescription('U: T = !trill!', name_to_display_text['user defined'], common=False),
        ValueDescription('Z:', name_to_display_text['transcription'], common=False),
        ValueDescription('K:', _('Key / clef')),
    ]
    def __init__(self):
        super(InsertFieldInHeaderAction, self).__init__('insert_field_in_header', InsertFieldInHeaderAction.values, display_name=_('Add...'))

    def get_values(self, context):
        tune_header = context.tune_header
        return [vd for vd in self.supported_values if vd.value in [r'%%', 'V:1'] or vd.value not in tune_header]


    # def execute(self, context, params=None):
    #     value = params.get('value')
    #     # if value == 'V:':
    #     #     params['value'] = 'V:xxx'
    #     super(InsertFieldActionEmptyLineAction, self).execute(context, params)


class InsertChangeFieldActionEmptyLineAction(InsertValueAction):
    values = [
        ValueDescription('K:', _('Key / clef')),
        ValueDescription('M:4/4', name_to_display_text['meter']),
        ValueDescription('Q:', name_to_display_text['tempo']),
        ValueDescription('L:1/4', name_to_display_text['unit note length'], common=False),
        ValueDescription('V:', name_to_display_text['voice'], common=False),
    ]
    def __init__(self):
        super(InsertChangeFieldActionEmptyLineAction, self).__init__('insert_change_field_on_empty_line', InsertChangeFieldActionEmptyLineAction.values, display_name=_('Change...'))

    def is_action_allowed(self, context):
        return context.tune_body.strip() != '' and super(InsertChangeFieldActionEmptyLineAction, self).is_action_allowed(context)


class InsertAppendFieldActionEmptyLineAction(InsertValueAction):
    values = [
        ValueDescription('w:', name_to_display_text['words (note aligned)']),
        ValueDescription('W:', name_to_display_text['words (at the end)'], common=False),
        ValueDescription('s:', name_to_display_text['symbol line'], common=False),
        ValueDescription(r'%%', name_to_display_text['instruction']),
    ]
    def __init__(self):
        super(InsertAppendFieldActionEmptyLineAction, self).__init__('insert_append_field_on_empty_line', InsertAppendFieldActionEmptyLineAction.values, display_name=_('Add...'))

    def is_action_allowed(self, context):
        return context.tune_body.strip() != '' and super(InsertAppendFieldActionEmptyLineAction, self).is_action_allowed(context)


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
            Space(),
            NewTuneAction(),
            NewMultiVoiceTuneAction(),
            NewDrumTuneAction(),
            NewNoteOrRestAction(),
            NewLineAction(),
            RemoveAction(),
            NoteDurationAction(),
            AddSlurAction(),
            MakeTripletsAction(),
            CombineUsingBeamAction(),
            InsertFieldAction(),
            InsertFieldInHeaderAction(),
            InsertChangeFieldActionEmptyLineAction(),
            InsertAppendFieldActionEmptyLineAction(),
            AbcStandardUrlAction(),
            Abcm2psUrlAction(),
            Abc2MidiUrlAction(),
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
            MidiInstrumentChangeAction(),
            MidiChannelChangeAction(),
            MidiDrumInstrumentChangeAction(),
            MidiVolumeChangeAction(),
            MidiGuitarChordChangeAction(),
            MidiGuitarChordInsertAction(),
            MidiGuitarChordTimeAction(),
            InsertDirectiveAction(),
            InsertMidiDirectiveAction(),
            ShowVoiceAction(),
            HideVoiceAction(),
            ShowAllVoicesAction(),
            ShowSingleVoiceAction(),
            GroupTogetherAction(),
            BraceTogetherAction(),
            BracketTogetherAction(),
            ToggleContinuedBarlinesAction(),
            MeasureNumberingChangeAction(),
            SimplifyNoteAction(),
            PickFieldsAction(),
        ])

        new_tune_actions = ['new_tune', '', 'new_multivoice_tune', '', 'new_drum_tune']
        self.action_handlers = {
            'abcversion'             : self.create_handler(['lookup_abc_standard']),
            'empty_document'         : self.create_handler(new_tune_actions),
            'empty_line'             : self.create_handler(new_tune_actions),
            'empty_line_file_header' : self.create_handler(new_tune_actions),
            'empty_line_header'      : self.create_handler(['new_note', 'insert_field_in_header']),
            'empty_line_tune'        : self.create_handler(['new_note', 'insert_change_field_on_empty_line', 'insert_append_field_on_empty_line']),
            'Whitespace'             : self.create_handler(['new_note', 'insert_field', 'remove']),
            'Note'                   : self.create_handler(['simplify_note', 'new_note', 'change_accidental', 'change_note_duration', 'change_pitch', 'add_decoration_to_note', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Rest'                   : self.create_handler(['new_note', 'change_rest_duration', 'change_rest_visibility', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Measure rest'           : self.create_handler(['new_note', 'change_measurerest_duration', 'change_measurerest_visibility', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Bar'                    : self.create_handler(['change_bar', 'remove']),
            'Annotation'             : self.create_handler(['change_annotation', 'change_annotation_position', 'fix_characters', 'remove']),
            'Chord'                  : self.create_handler(['new_note', 'change_note_duration', 'add_decoration_to_note', 'add_annotation_or_chord_to_note', 'insert_field', 'remove']),
            'Chord symbol'           : self.create_handler(['change_chord_note', 'change_chord_name', 'change_chord_bass_note', 'fix_characters', 'remove']),
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
            'Stylesheet directive'   : self.create_handler(['insert_directive']),
            'w:'                     : self.create_handler(['insert_text_align_symbol']),
            's:'                     : self.create_handler(['insert_decoration', 'insert_annotation_or_chord', 'insert_align_symbol']),
            'K:'                     : self.create_handler(['change_key_signature', 'change_key_mode']),
            'L:'                     : self.create_handler(['change_unit_note_length']),
            'M:'                     : self.create_handler(['change_meter']),
            'Q:'                     : self.create_handler(['change_tempo_notation', 'change_tempo_name', 'change_tempo_note1_length', 'change_tempo_note2_length']),
            '%'                      : self.create_handler(['fix_characters']),
            'MIDI_program'           : self.create_handler(['change_midi_instrument', 'change_midi_channel']),
            'MIDI_chordprog'         : self.create_handler(['change_midi_instrument']),
            'MIDI_bassprog'          : self.create_handler(['change_midi_instrument']),
            'MIDI_channel'           : self.create_handler(['change_midi_channel']),
            'MIDI_drummap'           : self.create_handler(['change_midi_drum_instrument']),
            'MIDI_volume'            : self.create_handler(['change_midi_volume']),
            'MIDI_gchord'            : self.create_handler(['change_gchord', 'insert_gchord', 'time_gchord']),
            'MIDI'                   : self.create_handler(['insert_midi_directive']),
            'score'                  : self.create_handler(['show_single_voice', 'hide_voice', 'show_voice', 'show_all_voices', 'toggle_continued_barlines', 'group_together', 'brace_together', 'bracket_together']),
            'measurenb'              : self.create_handler(['change_measurenb']),
            'show_fields'            : self.create_handler(['pick_fields']),
            'hide_fields'            : self.create_handler(['pick_fields']),
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
