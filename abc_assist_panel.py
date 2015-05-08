from tune_elements import *
from tune_actions import *
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
    def __init__(self, abc_section, editor, on_invalidate=None):
        self._editor = editor
        self.abc_section = abc_section
        line_no = editor.GetCurrentLine()
        self.previous_line = None
        if line_no > 0:
            self.previous_line = editor.GetLine(line_no - 1)
        self.editor_sel_start, self.editor_sel_end = editor.GetSelection()
        self.selected_text = editor.GetTextRange(self.editor_sel_start, self.editor_sel_end)
        first_line_no = editor.LineFromPosition(self.editor_sel_start)
        last_line_no = editor.LineFromPosition(self.editor_sel_end)
        self.single_line_select = first_line_no == last_line_no
        self.editor_lines_start = editor.PositionFromLine(first_line_no)
        self.editor_lines_end = editor.GetLineEndPosition(last_line_no)
        self.lines = editor.GetTextRange(self.editor_lines_start, self.editor_lines_end)
        self.selection = (self.editor_sel_start - self.editor_lines_start, self.editor_sel_end - self.editor_lines_start)
        self.current_element = None
        self.current_match = None
        self.match_text = None
        self.match_text_start = None
        self.on_invalidate = on_invalidate

    @property
    def empty_selection(self):
        return self.selection[0] == self.selection[1]

    def get_full_text(self):
        return self._editor.GetText()

    def insert_text(self, text):
        self._editor.BeginUndoAction()
        self._editor.AddText(text)
        self._editor.EndUndoAction()

    def replace_selection(self, text, selection_start=None, selection_end=None):
        self._editor.BeginUndoAction()
        if selection_start is not None:
            if selection_end is None:
                self._editor.SetSelection(selection_start, selection_start)
            else:
                self._editor.SetSelection(selection_start, selection_end)
        elif selection_end is not None:
            self._editor.SetSelectionEnd(selection_end)

        self._editor.ReplaceSelection(text)
        self._editor.EndUndoAction()
        self.invalidate()

    def replace_match_text(self, new_text, matchgroup=None):
        m = self.current_match
        start = m.start()
        end = m.end()

        if matchgroup:
            s = m.string
            group_start = m.start(matchgroup)
            group_end = m.end(matchgroup)
            new_text = s[start:group_start] + new_text + s[group_end:end]

        self.replace_in_editor(new_text, start, end)

    def replace_matchgroups(self, values):
        m = self.current_match
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
        self.replace_in_editor(s, start, end)

    def replace_in_editor(self, new_text, start, end):
        if self.current_element.exact_match_required:
            start += self.editor_sel_start
            end += self.editor_sel_start
        else:
            start += self.editor_lines_start
            end += self.editor_lines_start

        self.replace_selection(new_text, start, end)
        self.invalidate()

    def get_matchgroup(self, matchgroup, default=None):
        result = self.current_match.group(matchgroup)
        if result is None:
            result = default
        return result

    def invalidate(self): # context has changed so is not valid anymore
        self.lines = None
        self.match_text = None
        self.selected_text = None
        self.current_element = None
        self.selection = None
        if self.on_invalidate is not None:
            self.on_invalidate()


class AbcAssistPanel(wx.Panel):
    html_header = """\
<!DOCTYPE html>
<meta charset="utf-8" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<html>
<head>
<style type="text/css">
a { text-decoration:none }
table, th, td {
    border: 0px solid black;
}
</style>
</head>
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
        self.current_element = None
        self.elements = AbcStructure.generate_abc_elements(cwd)
        self.actions_handlers = AbcActionHandlers()

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

        self.current_html = wx.html.HtmlWindow(panel, -1)
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

    def get_abc_section(self):
        line_no = self._editor.GetCurrentLine()
        start_line = self.get_tune_start_line(line_no)
        if self._editor.GetLine(start_line).startswith('X:'):
            body_start_line = self.get_body_start_line(start_line + 1)
            if line_no < body_start_line:
                return ABC_SECTION_TUNE_HEADER
            elif line_no < self.get_body_end_line(body_start_line):
                return ABC_SECTION_TUNE_BODY
            else:
                return ABC_SECTION_OUTSIDE_TUNE
        else:
            return ABC_SECTION_FILE_HEADER

    def update_assist(self):
        try:
            self.context = AbcContext(self.get_abc_section(), self._editor, on_invalidate=self.update_assist)
            element, match = self.get_current_element()
            self.context.current_element = element
            self.context.current_match = match
            if match:
                self.context.match_text = match.string[match.start():match.end()]
            else:
                self.context.match_text = None
            self.current_element = element

            html = self.html_header
            if element is not None:
                html += element.get_description_html(self.context)
                action_html = self.actions_handlers.get_action_handler(element).get_action_html(self.context)
                if action_html:
                    html += '<br>' + action_html
            html += self.html_footer
            self.set_html(html)
        except Exception as ex:
            print ex

    def set_html(self, html, save_scroll_pos=True):
        pos = self.current_html.GetViewStart()[1]
        self.current_html.Freeze()
        self.current_html.SetPage(html)
        if save_scroll_pos:
            self.current_html.Scroll(0, pos)
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
            action_handler = self.actions_handlers.get_action_handler(self.current_element)
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

    def get_tune_start_line(self, offset_line):
        start_line = offset_line
        while start_line > 0 and not self._editor.GetLine(start_line).startswith('X:'):
            start_line -= 1
        return start_line

    def get_body_start_line(self, offset_line):
        key_line = offset_line
        line_count = self._editor.GetLineCount()
        while key_line < line_count and not self._editor.GetLine(key_line).startswith('K:'):
            key_line += 1

        body_line = None
        if self._editor.GetLine(key_line).startswith('K:'):
            body_line = key_line + 1
        return body_line

    def get_body_end_line(self, offset_line):
        end_line_no = offset_line
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

    def get_tune_start(self, offset):
        start_line = self.get_tune_start_line(self._editor.LineFromPosition(offset))
        start_position = self._editor.PositionFromLine(start_line)
        return start_position

    def get_tune_end(self, offset):
        position = offset
        start_line = self._editor.LineFromPosition(position)
        end_line = start_line + 1
        line_count = self._editor.GetLineCount()
        while end_line < line_count and not self._editor.GetLine(end_line).startswith('X:'):
            end_line += 1
        end_position = self._editor.GetLineEndPosition(end_line - 1)
        return end_position
