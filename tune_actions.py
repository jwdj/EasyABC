import re
import os
from collections import namedtuple
from wx import GetTranslation as _
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2
import urllib

meter_values = [
    'C',
    'C|',
    '4/4',
    '3/4',
    '2/4',
    '2/2',
    '6/8'
]

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

UrlTuple = namedtuple('UrlTuple', 'url content')

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

class ValueChangeAction(AbcAction):
    def __init__(self, name, supported_values, display_name=None, group=None):
        super(ValueChangeAction, self).__init__(name, display_name=display_name, group=group)
        self.supported_values = supported_values

    def can_execute(self, context, params=None):
        return True

    def execute(self, context, params=None):
        pass

    def get_action_html(self, context):
        result = html_enclose('h4', escape(self.display_name))
        html_values = []
        for value in self.supported_values:
            params = {'value': value}
            if self.can_execute(context, params):
                action_url = '%s?%s' % (self.name, urllib.urlencode(params))
                t = UrlTuple(action_url, escape(value))
                html_values.append(t)
            else:
                html_values.append(escape(value))
        result += html_table(html_values)
        return result

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


class MeterActionHandler(AbcActionHandler):
    def __init__(self):
        super(MeterActionHandler, self).__init__()
        action = ValueChangeAction('Change meter', meter_values)
        self.add_action(action)

class TempoActionHandler(AbcActionHandler):
    def __init__(self):
        super(TempoActionHandler, self).__init__()
        action = ValueChangeAction('Change tempo', tempo_names)
        self.add_action(action)

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


class NoteActionHandler(AbcActionHandler):
    def __init__(self):
        super(NoteActionHandler, self).__init__()


class AbcActionHandlers(object):
    def __init__(self):
        self.default_action_handler = AbcActionHandler()
        self.action_handlers = {
            'K:'         : KeyActionHandler(),
            'Empty line' : AbcActionHandler([NewTuneAction()]),
            'Note'       : NoteActionHandler(),
            'meter'      : MeterActionHandler(),
            'Q:'         : TempoActionHandler()
        }

    def get_action_handler(self, element):
        if element:
            return self.action_handlers.get(element.name, self.default_action_handler)
        return self.default_action_handler

