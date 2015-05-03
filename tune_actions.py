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

    def get_action_html(self, context, params=None):
        if self.can_execute(context, params):
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
        if self.matchgroup:
            value = params.get('value', '')
            if context.current_match:
                current_value = context.current_match.group(self.matchgroup)
                return value != current_value
        return True

    def execute(self, context, params=None):
        if self.matchgroup:
            value = params.get('value', '')
            context.replace_match_text(value, self.matchgroup)
        pass

    def get_action_html(self, context):
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
        return self.valid_sections is None or context.abc_section in self.valid_sections

    def execute(self, context, params=None):
        context.insert_text(params['value'])


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

    def can_execute(self, context, params=None):
        if not isinstance(context.current_element, AbcNote):
            return False
        return True

    def replace_regex_group(self, match, group, replace_value):
        #g = match.group(group)
        #r'\g<{0}>'.format(group)
        #return self._search_re[context.abc_section].sub(replace_value, context.match_text)
        return False


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
        super(MeterChangeAction, self).__init__('Meter', MeterChangeAction.values, matchgroup=1)


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


class DurationAction(ValueChangeAction):
    duration_values = [
        CodeDescription('/', _('Halve')),
        CodeDescription('2', _('Double')),
        CodeDescription('3', _('Dotted')),
        CodeDescription('>', _('This note dotted, next note halved')),
        CodeDescription('<', _('This note halved, next note dotted')),
        CodeDescription('-', _('Tie to next note')),
    ]
    def __init__(self):
        super(DurationAction, self).__init__('Duration', DurationAction.duration_values)

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('test')


class TempoChangeAction(ValueChangeAction):
    tempo_names = {
        'Larghissimo ' :  40,
        'Adagissimo  ' :  44,
        'Lentissimo  ' :  48,
        'Largo       ' :  56,
        'Adagio      ' :  59,
        'Lento       ' :  62,
        'Larghetto   ' :  66,
        'Adagietto   ' :  76,
        'Andante     ' :  88,
        'Andantino   ' :  96,
        'Moderato    ' : 104,
        'Allegretto  ' : 112,
        'Allegro     ' : 120,
        'Vivace      ' : 168,
        'Vivo        ' : 180,
        'Presto      ' : 192,
        'Allegrissimo' : 208,
        'Vivacissimo ' : 220,
        'Prestissimo ' : 240,
    }
    def __init__(self):
        super(TempoChangeAction, self).__init__('Change tempo', TempoChangeAction.tempo_names)

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        context.replace_match_text('test')


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


##################################################################################################
#  INSERT ACTIONS
##################################################################################################



class UrlAction(AbcAction):
    def __init__(self, url):
        super(AbcAction, self).__init__('link')
        self.url = url

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        webbrowser.open(href)

    def get_action_html(self, context, params=None):
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


class NewNoteAction(AbcAction):
    tune_re = re.compile(r'(?m)^X:\s*(\d+)')

    def __init__(self):
        super(NewNoteAction, self).__init__('abc_new_note', display_name=_('Add note or rest'))

    def can_execute(self, context, params=None):
        return context.previous_line is None or context.current_element.matches_text(context, context.previous_line) is not None

    def execute(self, context, params=None):
        text = params
        context.insert_text(text)


class InsertOptionalAccidental(InsertValueAction):
    values = [
        CodeDescription('"<(\u266f)"', _('Optional sharp')),
        CodeDescription('"<(\u266e)"', _('Optional natural')),
        CodeDescription('"<(\u266d)"', _('Optional flat'))
    ]
    def __init__(self):
        super(InsertOptionalAccidental, self).__init__('Insert annotation', InsertOptionalAccidental.values)


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
            'Empty line' : AbcActionHandler([NewTuneAction()]),
            'Note'       : AbcActionHandler([AccidentalChangeAction(), DurationAction(), PitchAction(),
                                             InsertOptionalAccidental()]),
            'Rest'       : AbcActionHandler([DurationAction()]),
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

