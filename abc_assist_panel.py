from tune_actions import *
from abc_context import *
import logging
import wx
import wx.html
import webbrowser

try:
    from urllib.parse import parse_qsl  # py3
except ImportError:
    from urlparse import parse_qsl  # py2


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
                choices = list(choices)
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


class AbcAssistPanel(wx.Panel):
    html_header = """\
<!DOCTYPE html>
<meta charset="utf-8" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<html>
<body>
"""
    html_footer = "</body></html>"

    def __init__(self, parent, editor, cwd, settings):
        wx.Panel.__init__(self, parent, -1)
        if wx.Platform == "__WXMSW__":
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        self._editor = editor
        self.settings = settings
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

        if wx.Platform == "__WXMAC__":
            font_size = 14
        else:
            font_size = 10

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
            self.context = AbcContext(self._editor, self.settings, on_invalidate=self.update_assist)
            element, match = self.get_current_element()
            self.context.current_element = element
            if element is not None:
                self.context.set_current_match(match, element.tune_scope)
                element = element.get_inner_element(self.context)

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
                params = dict(parse_qsl(parts[1], keep_blank_values=True))
            else:
                params = None # {}
            action = action_handler.get_action(action_name)
            if action is not None:
                try:
                    action.execute(self.context, params)
                except Exception as e:
                    pass # print(e)

                self._editor.SetFocus()
        return wx.html.HTML_BLOCK

    def __on_editor_update_delayed(self, update_number):
        if self.queue_number_update_assist == update_number:
            self.update_assist()

    def __on_editor_update(self, event):
        event.Skip()
        self.queue_number_update_assist += 1
        wx.CallLater(250, self.__on_editor_update_delayed, self.queue_number_update_assist)
