# easyabc_dialogs.py

# Dedicated file to centralize the dialogs of EasyABC
# At first only include the new ones
# Todo migrate dialogs from easy_abc.py to easyabc_dialogs.py

import os
import wx
from wx import GetTranslation as _
from utils import get_application_path
from easyabc_version import program_name 

import re

def _absolutize_html_paths(htmlpage, application_path):
    """convert relative paths (src/href) in absolute on (file://) absolus,
    other links not modified (http(s), mailto:, file://, anchors (#))."""
    pattern = re.compile(
        r'(src|href)="(?!https?://|file://|mailto:|#)([^"]+)"'
    )
    base = application_path.replace('\\', '/')
    return pattern.sub(r'\1="file://%s/\2"' % base, htmlpage)

class AboutFrame(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, _('About EasyABC'), size=(900, 600) )
        application_path = get_application_path()
        docs_path = os.path.join(application_path,"docs")
        language = "en"
        lang = wx.GetApp().locale.GetCanonicalName()
        if lang and len(lang) >= 2:
            language = lang[:2].lower()

        language = lang[:2].lower()
        about_file = os.path.join(
            docs_path,
            language,
            f"about_{language}.html"
        )

        if not os.path.exists(about_file):
            about_file = os.path.join(
                docs_path,
                "en",
                "about_en.html")
        with open(about_file, encoding="utf-8") as f:
            htmlpage = f.read()
        htmlpage = htmlpage.format(program_name)
        htmlpage = _absolutize_html_paths(htmlpage, application_path)
        about_html = wx.html.HtmlWindow(self)
        about_html.SetPage(htmlpage)
        button = wx.Button(self, wx.ID_OK, _('&Ok'))
        button.SetDefault()

        # Definition of the padding of the window
        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(button, wx.Top, 5)
        lc.right.SameAs(self, wx.Right, 5)
        about_html.SetConstraints(lc)

        # Definition of the position of the OK button
        lc = wx.LayoutConstraints()
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.centreX.SameAs(self, wx.CentreX)
        lc.width.AsIs()
        lc.height.AsIs()
        button.SetConstraints(lc)

        about_html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked)

        self.SetAutoLayout(True)
        self.Layout()
        self.CentreOnParent(wx.BOTH)

    def OnLinkClicked(self, evt):
        webbrowser.open(evt.GetLinkInfo().GetHref())
        return wx.html.HTML_BLOCK


class WelcomeFrame(wx.Dialog):

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, _('Welcome to EasyABC 1.4'), size=(700, 550))

        application_path = get_application_path()
        docs_path = os.path.join(application_path,"docs")
        language = "en"
        lang = wx.GetApp().locale.GetCanonicalName()
        if lang and len(lang) >= 2:
            language = lang[:2].lower()

        language = lang[:2].lower()
        welcome_file = os.path.join(
            docs_path,
            language,
            f"welcome_{language}.html"
        )

        if not os.path.exists(welcome_file):
            welcome_file = os.path.join(
                docs_path,
                "en",
                "welcome_en.html")
        with open(welcome_file, encoding="utf-8") as f:
            htmlpage = f.read()
        htmlpage = _absolutize_html_paths(htmlpage, application_path)
        html = wx.html.HtmlWindow(self)
        html.SetPage(htmlpage)

        self.show_on_startup = wx.CheckBox(
            self,
            label=_('Show this welcome page at startup')
        )
        self.show_on_startup.SetValue(True)

        doc_button = wx.Button(
            self,
            label=_('Open Documentation')
        )

        ok_button = wx.Button(
            self,
            wx.ID_OK,
            _('OK')
        )
        ok_button.SetDefault()

        html.Bind(
            wx.html.EVT_HTML_LINK_CLICKED,
            self.OnLinkClicked
        )

        doc_button.Bind(
            wx.EVT_BUTTON,
            self.OnOpenDocumentation
        )

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_sizer.Add(
            self.show_on_startup,
            0,
            wx.ALIGN_CENTER_VERTICAL
        )

        button_sizer.AddStretchSpacer()

        button_sizer.Add(
            doc_button,
            0,
            wx.RIGHT,
            5
        )

        button_sizer.Add(
            ok_button,
            0
        )

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(
            html,
            1,
            wx.EXPAND | wx.ALL,
            5
        )

        main_sizer.Add(
            button_sizer,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            10
        )

        self.SetSizer(main_sizer)

        self.CentreOnParent()

    def OnLinkClicked(self, evt):
        webbrowser.open(evt.GetLinkInfo().GetHref())

    def OnOpenDocumentation(self, evt):
        webbrowser.open(
            'https://easyabc.sourceforge.net/'
        )


class EasyAbcDocFrame(wx.Dialog):

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY, _('EasyABC 1.4 help page'), size=(700, 550))

        application_path = get_application_path()
        docs_path = os.path.join(application_path,"docs")
        language = "en"
        lang = wx.GetApp().locale.GetCanonicalName()
        if lang and len(lang) >= 2:
            language = lang[:2].lower()

        language = lang[:2].lower()
        welcome_file = os.path.join(
            docs_path,
            language,
            f"easyabc-doc_{language}.html"
        )

        if not os.path.exists(welcome_file):
            welcome_file = os.path.join(
                docs_path,
                "en",
                "easyabc-doc_en.html")
        with open(welcome_file, encoding="utf-8") as f:
            htmlpage = f.read()
        htmlpage = _absolutize_html_paths(htmlpage, application_path)
        html = wx.html.HtmlWindow(self)
        html.SetPage(htmlpage)

        doc_button = wx.Button(
            self,
            label=_('Open Documentation on Sourceforge')
        )

        ok_button = wx.Button(
            self,
            wx.ID_OK,
            _('OK')
        )
        ok_button.SetDefault()

        html.Bind(
            wx.html.EVT_HTML_LINK_CLICKED,
            self.OnLinkClicked
        )

        doc_button.Bind(
            wx.EVT_BUTTON,
            self.OnOpenDocumentation
        )

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_sizer.AddStretchSpacer()

        button_sizer.Add(
            doc_button,
            0,
            wx.RIGHT,
            5
        )

        button_sizer.Add(
            ok_button,
            0
        )

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(
            html,
            1,
            wx.EXPAND | wx.ALL,
            5
        )

        main_sizer.Add(
            button_sizer,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            10
        )

        self.SetSizer(main_sizer)

        self.CentreOnParent()

    def OnLinkClicked(self, evt):
        webbrowser.open(evt.GetLinkInfo().GetHref())

    def OnOpenDocumentation(self, evt):
        webbrowser.open(
            'https://easyabc.sourceforge.net/'
        )