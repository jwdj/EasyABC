from tune_elements import *
from tune_actions import *
import logging
import wx
import wx.html
import webbrowser
import urlparse
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2

class AbcAssistControl(object):
    def __init__(self, parent, element):
        self.element = element
        if isinstance(element.default, bool):
            ctrl = wx.CheckBox(parent, -1, '')
            ctrl.SetValue(element.default)
        elif isinstance(element.default, int):
            ctrl = wx.SpinCtrl(parent, -1, "", min=1, max=10, initial=element.default)
        elif element.supported_values is not None:
            choices = element.supported_values
            if isinstance(choices, dict):
                choices = choices.keys()
            ctrl = wx.ComboBox(parent, -1, choices=choices, style=wx.CB_DROPDOWN | wx.CB_READONLY)
            if element.default is not None:
                ctrl.SetSelection(element.default)
        else:
            value = element.default
            if value is None:
                value = ''
            if isinstance(element, AbcStringField):
                style = wx.TE_MULTILINE | wx.NO_BORDER
            else:
                style = wx.NO_BORDER # wx.SIMPLE_BORDER # wx.SUNKEN_BORDER
            ctrl = wx.TextCtrl(parent, -1, value, style=style)
        #if element.description is not None:
            #ctrl.SetHint(element.description.splitlines()[0])
        #    ctrl.SetHint(element.description.split('\n', 1)[0])
        self.control = ctrl

class AbcContext(object):
    def __init__(self, editor, on_invalidate=None):
        self._editor = editor
        self.on_invalidate = on_invalidate
        self.editor_sel_start, self.editor_sel_end = editor.GetSelection()
        self.current_element = None
        self._current_match = None
        self.inner_match = None
        self.match_text_start = None
        self._tune_scope_info_getter = {
            TuneScope.FullText: self.get_scope_full_text,
            TuneScope.SelectedText: self.get_scope_selected_text,
            TuneScope.SelectedLines: self.get_scope_selected_lines,
            TuneScope.TuneHeader: self.get_scope_tune_header,
            TuneScope.TuneBody: self.get_scope_tune_body,
            TuneScope.FileHeader: self.get_scope_file_header,
            TuneScope.PreviousLine: self.get_scope_previous_line,
            TuneScope.MatchText: self.get_empty_scope_info
        }
        self._tune_scope_info = {}

        line_no = self._editor.GetCurrentLine()
        self.tune_start_line = self.get_tune_start_line(line_no)
        self.body_start_line = None
        self.body_end_line = None

        if self.tune_start_line is None:
            self.abc_section = AbcSection.FileHeader
        else:
            self.body_start_line = self.get_body_start_line(self.tune_start_line + 1)
            if self.body_start_line is None:
                self.abc_section = AbcSection.TuneHeader
            else:
                self.body_end_line = self.get_body_end_line(self.body_start_line)
                if line_no < self.body_start_line:
                    self.abc_section = AbcSection.TuneHeader
                elif line_no < self.body_end_line:
                    self.abc_section = AbcSection.TuneBody
                else:
                    self.abc_section = AbcSection.OutsideTune

    def get_tune_start_line(self, current_line):
        start_line = current_line
        while not self._editor.GetLine(start_line).startswith('X:'):
            start_line -= 1
            if start_line < 0:
                return None
        return start_line

    def get_body_start_line(self, tune_start_line):
        key_line = tune_start_line
        line_count = self._editor.GetLineCount()
        while key_line < line_count and not self._editor.GetLine(key_line).startswith('K:'):
            key_line += 1

        body_line = None
        if self._editor.GetLine(key_line).startswith('K:'):
            body_line = key_line + 1
        return body_line

    def get_body_end_line(self, body_start_line):
        end_line_no = body_start_line
        line_count = self._editor.GetLineCount()
        end_found = False
        while not end_found and end_line_no < line_count:
            line = self._editor.GetLine(end_line_no)
            if line.startswith('X:'):
                end_found = True
            else:
                end_found = not line.strip() # last empty line is also part of the body
                end_line_no += 1
        return end_line_no

    @property
    def current_match(self):
        return self._current_match

    def set_current_match(self, match, tune_scope):
        offset = self.get_scope_info(tune_scope).start
        inner_match = None
        if isinstance(match, tuple):
            if len(match) > 1:
                inner_match = match[len(match)-1]
            match = match[0]

        self._current_match = match
        if match:
            start = match.start()
            stop = match.end()
            scope_info = TuneScopeInfo(match.string[start:stop], start+offset, stop+offset)
        else:
            scope_info = self.get_empty_scope_info()
        self._tune_scope_info[TuneScope.MatchText] = scope_info

        self.inner_match = None
        inner_scope_info = scope_info
        if match:
            try:
                start = match.start('inner')
                if start >= 0:
                    stop = match.end('inner')
                    inner_scope_info = TuneScopeInfo(match.string[start:stop], start+offset, stop+offset)
            except IndexError:
                pass # no group named inner present

        if inner_match:
            match = inner_match.match
            self.inner_match = match
            start = match.start()
            stop = match.end()
            offset += inner_match.offset
            inner_scope_info = TuneScopeInfo(match.string[start:stop], start+offset, stop+offset)
        self._tune_scope_info[TuneScope.InnerText] = inner_scope_info

    @property
    def match_text(self):
        return self.get_scope_info(TuneScope.MatchText).text

    @property
    def lines(self):
        return self.get_scope_info(TuneScope.SelectedLines).text

    @property
    def selected_text(self):
        return self.get_scope_info(TuneScope.SelectedText).text

    @property
    def previous_line(self):
        return self.get_scope_info(TuneScope.PreviousLine).text

    def get_scope_info(self, tune_scope):
        result = self._tune_scope_info.get(tune_scope)
        if result is None:
            result = self._tune_scope_info_getter[tune_scope]()
            self._tune_scope_info[tune_scope] = result
        return result

    def get_selection_within_scope(self, tune_scope):
        return self.translate_range_for_scope(TuneScope.SelectedText, tune_scope)

    def translate_range_for_scope(self, from_scope, to_scope):
        f = self.get_scope_info(from_scope)
        t = self.get_scope_info(to_scope)
        return f.start-t.start, f.stop-t.start

    def get_scope_full_text(self):
        return TuneScopeInfo(self._editor.GetText(), 0, self._editor.GetTextLength())

    def get_scope_selected_text(self):
        start, stop = self._editor.GetSelection()
        if start == stop:
            return TuneScopeInfo('', start, stop)
        else:
            return TuneScopeInfo(self._editor.GetTextRange(start, stop), start, stop)

    def get_scope_selected_lines(self):
        sel_start, sel_stop = self._editor.GetSelection()
        first_line_no = self._editor.LineFromPosition(sel_start)
        last_line_no = self._editor.LineFromPosition(sel_stop)
        editor_lines_start = self._editor.PositionFromLine(first_line_no)
        editor_lines_end = self._editor.GetLineEndPosition(last_line_no)
        return TuneScopeInfo(self._editor.GetTextRange(editor_lines_start, editor_lines_end), editor_lines_start, editor_lines_end)

    def get_scope_previous_line(self):
        line_no = self._editor.GetCurrentLine()
        if line_no == 0:
            return self.get_empty_scope_info()
        else:
            line_no -= 1
            return TuneScopeInfo(self._editor.GetLine(line_no), self._editor.PositionFromLine(line_no), self._editor.GetLineEndPosition(line_no))

    def get_scope_file_header(self):
        start_line = 0
        line_count = self._editor.GetLineCount()
        while start_line < line_count and not self._editor.GetLine(start_line).startswith('X:'):
            start_line += 1
        tune_start_pos = self._editor.PositionFromLine(start_line)
        return TuneScopeInfo(self._editor.GetTextRange(0, tune_start_pos), 0, tune_start_pos)

    def get_scope_tune_header(self):
        if self.tune_start_line is None:
            return self.get_empty_scope_info()
        start_pos = self._editor.PositionFromLine(self.tune_start_line)
        if self.body_start_line is not None:
            end_pos = self._editor.PositionFromLine(self.body_start_line)
        else:
            end_pos = self._editor.GetTextLength()
        return TuneScopeInfo(self._editor.GetTextRange(start_pos, end_pos), start_pos, end_pos)

    def get_scope_tune_body(self):
        if self.body_start_line is None:
            return self.get_empty_scope_info()
        else:
            tune_start_pos = self._editor.PositionFromLine(self.body_start_line)
            tune_end_pos = self._editor.PositionFromLine(self.body_end_line)
            return TuneScopeInfo(self._editor.GetTextRange(tune_start_pos, tune_end_pos), tune_start_pos, tune_end_pos)

    def get_empty_scope_info(self):
        return TuneScopeInfo(None, None, None)

    def insert_text(self, text):
        self._editor.BeginUndoAction()
        sel = self._editor
        self._editor.AddText(text)
        self._editor.EndUndoAction()

    def set_relative_selection(self, relative_selection):
        if relative_selection:
            selection_start, selection_end = self._editor.GetSelection()
            selection_end += relative_selection
            if selection_start > selection_end:
               selection_start = selection_end
            self._editor.SetSelection(selection_start, selection_end)

    def replace_selection(self, text, selection_start=None, selection_end=None):
        self._editor.BeginUndoAction()
        if selection_start is not None:
            if selection_end is None:
                self._editor.SetSelection(selection_start, selection_start)
            else:
                self._editor.SetSelection(selection_start, selection_end)
        elif selection_end is not None:
            self._editor.SetSelectionEnd(selection_end)

        selection_start, selection_end = self._editor.GetSelection()
        selected_text = self._editor.GetTextRange(selection_start, selection_end)
        i = 0
        while i < len(selected_text) and i < len(text) and selected_text[-(1 + i)] == text[-(1 + i)]:
            i += 1

        if i > 0:
            selection_end -= i
            self._editor.SetSelectionEnd(selection_end)
            text = text[:-i]

        self._editor.ReplaceSelection(text)
        self._editor.EndUndoAction()
        self.invalidate()

    def ensure_tune_scope(self, tune_scope):
        if tune_scope is None:
            tune_scope = TuneScope.MatchText
            if self.inner_match:
                tune_scope = TuneScope.InnerText
        return tune_scope

    def replace_match_text(self, new_text, matchgroup=None, tune_scope=None):
        tune_scope = self.ensure_tune_scope(tune_scope)
        m = self.current_match
        if tune_scope == TuneScope.InnerText and self.inner_match:
            m = self.inner_match

        if matchgroup:
            s = m.string
            new_text = s[m.start():m.start(matchgroup)] + new_text + s[m.end(matchgroup):m.end()]

        self.replace_in_editor(new_text, tune_scope)

    def replace_matchgroups(self, values, tune_scope=None):
        tune_scope = self.ensure_tune_scope(tune_scope)
        m = self.current_match
        if tune_scope == TuneScope.InnerText:
            m = self.inner_match

        start = m.start()
        end = m.end()
        s = m.string
        offset = 0
        for (matchgroup, value) in values:
            group_start = m.start(matchgroup)
            group_end = m.end(matchgroup)
            old_length = group_end-group_start
            length_diff = len(value) - old_length
            s = s[:group_start+offset] + value + s[group_end+offset:]
            offset += length_diff
        s = s[start:end+offset]
        self.replace_in_editor(s, tune_scope)

    def replace_in_editor(self, new_text, tune_scope):
        scope_info = self.get_scope_info(tune_scope)
        self.replace_selection(new_text, scope_info.start, scope_info.stop)
        wx.CallAfter(self.invalidate)

    def get_matchgroup(self, matchgroup, default=None):
        match = self.inner_match or self.current_match
        try:
            result = match.group(matchgroup)
        except IndexError:
            result = None

        if result is None:
            result = default
        return result

    def invalidate(self): # context has changed so is not valid anymore
        self._tune_scope_info = {}
        self.current_element = None
        self._current_match = None
        if self.on_invalidate is not None:
            self.on_invalidate()


class AbcAssistPanel(wx.Panel):
    html_header = """\
<!DOCTYPE html>
<meta charset="utf-8" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<html>
<body>
"""
    html_footer = "</body></html>"

    def __init__(self, parent, editor, cwd):
        wx.Panel.__init__(self, parent, -1)
        if wx.Platform == "__WXMSW__":
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        self._editor = editor
        self.context = None
        self.abc_section = None
        self.elements = AbcStructure.generate_abc_elements(cwd)
        self.actions_handlers = AbcActionHandlers(self.elements)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        panel = wx.Panel(self)
        self.sizer.Add(panel, 1, wx.ALL | wx.EXPAND)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panel_sizer)

        #element_types = []
        #for element in self.elementselements.itervalues():
        #    element_types.append(element.display_name)
        #self.cmb_element_type = wx.ComboBox(panel, -1, choices=element_types, size=(250, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)


        #self.current_text = wx.TextCtrl(self.current_element, -1, '', style=wx.TE_MULTILINE | wx.NO_BORDER)
        #current_element_sizer.Add(self.current_text, 1, wx.EXPAND)
        #self.current_text.Hide()

        #self.current_description = wx.TextCtrl(self.current_element, -1, '', style=wx.TE_MULTILINE | wx.NO_BORDER | wx.TE_READONLY)
        #self.current_description = wx.StaticText(self.current_element, -1, '', style=wx.TE_MULTILINE)
        #current_element_sizer.Add(self.current_description, 1, wx.ALL | wx.EXPAND)
        #self.current_description.Hide()

        if wx.Platform == "__WXMSW__":
            font_size = 10
        else:
            font_size = 14

        h1_size = font_size * 5 // 3
        h2_size = font_size * 3 // 2
        h3_h4_size = font_size * 5 // 4
        h5_h6_size = font_size * 5 // 4

        self.current_html = wx.html.HtmlWindow(panel, -1, style=wx.html.HW_SCROLLBAR_AUTO | wx.html.HW_NO_SELECTION)
        self.current_html.SetFonts('', '', sizes=[font_size, font_size, font_size, h5_h6_size, h3_h4_size, h2_size, h1_size])

        panel_sizer.Add(self.current_html, 1, wx.ALL | wx.EXPAND)
        self.current_html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.on_link_clicked)

        #self.change_element_box = wx.StaticBox(self, wx.ID_ANY, 'Change')
        #panel_sizer.Add(self.change_element_box, 0)


        # self.notebook.AddPage(self.current_element, _('Empty line'))

        # self.element_panel = ScrolledPanel(self.notebook)
        # self.notebook.AddPage(self.element_panel, "Elements")
        # sizer = rcsizer.RowColSizer()
        # self.element_panel.SetSizer(sizer)
        # border = 3
        # row = 0
        # for element in self.elements.itervalues():
        #     label = wx.StaticText(self.element_panel, -1, element.display_name + ":")
        #     ctrl = AbcAssistControl(self.element_panel, element).control
        #     sizer.Add(label, row=row, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        #     sizer.Add(ctrl, row=row, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        #     row += 1
        # self.element_panel.SetupScrolling()

    def update_assist(self):
        try:
            self.context = AbcContext(self._editor, on_invalidate=self.update_assist)
            element, match = self.get_current_element()
            self.context.current_element = element
            if element is not None:
                self.context.set_current_match(match, element.tune_scope)

            html = self.html_header
            if element is not None:
                html += element.get_description_html(self.context)
                action_html = self.actions_handlers.get_action_handler(element).get_action_html(self.context)
                if action_html:
                    html += '<br>' + action_html
            html += self.html_footer
            self.set_html(html)
        except Exception as ex:
            logging.exception(ex)

    def set_html(self, html):
        scrollpos = self.current_html.GetViewStart()[1]
        self.current_html.Freeze()
        self.current_html.SetPage(html)
        self.current_html.Scroll(0, scrollpos)
        self.current_html.Thaw()

    def get_current_element(self):
        for element in self.elements:
            m = element.matches(self.context)
            if m:
                return element, m
        return None, None

    def on_link_clicked(self, evt):
        href = evt.GetLinkInfo().GetHref()
        if href.startswith('http'):
            webbrowser.open(href)
        else:
            action_handler = self.actions_handlers.get_action_handler(self.context.current_element)
            parts = href.split('?', 1)
            action_name = parts[0]
            if len(parts) > 1:
                params = dict(urlparse.parse_qsl(parts[1]))
            else:
                params = None # {}
            action = action_handler.get_action(action_name)
            if action is not None:
                action.execute(self.context, params)
                self._editor.SetFocus()
        return wx.html.HTML_BLOCK

    def __on_editor_update_delayed(self, update_number):
        if self.queue_number_update_assist == update_number:
            self.update_assist()

    def __on_editor_update(self, event):
        event.Skip()
        self.queue_number_update_assist += 1
        wx.CallLater(250, self.__on_editor_update_delayed, self.queue_number_update_assist)
