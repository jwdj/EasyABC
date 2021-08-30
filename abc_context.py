from tune_elements import *
from abc_character_encoding import ensure_unicode, unicode_text_to_abc
import wx
import sys
PY3 = sys.version_info.major > 2
if PY3:
    xrange = range


class AbcContext(object):
    def __init__(self, editor, settings, on_invalidate=None):
        self._editor = editor
        self.on_invalidate = on_invalidate
        self.settings = settings
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
            TuneScope.Tune: self.get_scope_tune,
            TuneScope.FileHeader: self.get_scope_file_header,
            TuneScope.BodyUpToSelection: self.get_scope_body_up_to_selection,
            TuneScope.BodyAfterSelection: self.get_scope_body_after_selection,
            TuneScope.TuneUpToSelection: self.get_scope_tune_up_to_selection,
            TuneScope.LineUpToSelection: self.get_scope_line_up_to_selection,
            TuneScope.PreviousLine: self.get_scope_previous_line,
            TuneScope.MatchText: self.get_empty_scope_info,  # is determined elsewhere
            TuneScope.InnerText: self.get_empty_scope_info,  # is determined elsewhere
            TuneScope.PreviousCharacter: self.get_scope_previous_character,
            TuneScope.NextCharacter: self.get_scope_next_character,
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
                end_found = not line.strip()  # last empty line is also part of the body
                end_line_no += 1
        return end_line_no

    @property
    def current_match(self):
        return self._current_match

    def create_scope_info_from_match(self, match, offset, match_group=0):
        start = match.start(match_group)
        stop = match.end(match_group)
        text = match.string[start:stop]
        encoded_text = text.encode('utf-8')
        start = len(match.string[:start].encode('utf-8'))
        stop = start + len(encoded_text)
        return TuneScopeInfo(ensure_unicode(text), start+offset, stop+offset, encoded_text)

    def set_current_match(self, match, tune_scope):
        offset = self.get_scope_info(tune_scope).start
        inner_match = None
        if isinstance(match, tuple):
            if len(match) > 1:
                inner_match = match[len(match)-1]
            match = match[0]

        self._current_match = match
        if match:
            scope_info = self.create_scope_info_from_match(match, offset)
        else:
            scope_info = self.get_empty_scope_info()
        self._tune_scope_info[TuneScope.MatchText] = scope_info

        inner_scope_info = None
        if inner_match:
            match = inner_match.match
            self.inner_match = match
            offset += inner_match.offset
            inner_scope_info = self.create_scope_info_from_match(match, offset)
        elif match:
            try:
                if match.start('inner') >= 0:
                    inner_scope_info = self.create_scope_info_from_match(match, offset, 'inner')
            except IndexError:
                pass  # no group named inner present
        self._tune_scope_info[TuneScope.InnerText] = inner_scope_info

    @property
    def match_text(self):
        return self.get_scope_info(TuneScope.MatchText).text

    @property
    def inner_text(self):
        return self.get_scope_info(TuneScope.InnerText).text

    @property
    def lines(self):
        return self.get_scope_info(TuneScope.SelectedLines).text

    @property
    def selected_text(self):
        return self.get_scope_info(TuneScope.SelectedText).text

    @property
    def previous_line(self):
        return self.get_scope_info(TuneScope.PreviousLine).text

    @property
    def previous_character(self):
        return self.get_scope_info(TuneScope.PreviousCharacter).text

    @property
    def tune_header(self):
        return self.get_scope_info(TuneScope.TuneHeader).text

    @property
    def tune_body(self):
        return self.get_scope_info(TuneScope.TuneBody).text

    @property
    def tune(self):
        return self.get_scope_info(TuneScope.Tune).text

    @property
    def contains_text(self):
        return self._editor.GetTextLength() != 0

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
        return self.create_scope(0, self._editor.GetTextLength())

    def get_scope_selected_text(self):
        start, stop = self._editor.GetSelection()
        return self.create_scope(start, stop)

    def get_scope_selected_lines(self):
        sel_start, sel_stop = self._editor.GetSelection()
        first_line_no = self._editor.LineFromPosition(sel_start)
        last_line_no = self._editor.LineFromPosition(sel_stop)
        editor_lines_start = self._editor.PositionFromLine(first_line_no)
        editor_lines_end = self._editor.GetLineEndPosition(last_line_no)
        return self.create_scope(editor_lines_start, editor_lines_end)

    def get_scope_previous_line(self):
        line_no = self._editor.GetCurrentLine()
        if line_no == 0:
            return self.get_empty_scope_info()
        else:
            line_no -= 1
            start_pos = self._editor.PositionFromLine(line_no)
            end_pos = self._editor.GetLineEndPosition(line_no)
            return self.create_scope(start_pos, end_pos)

    def get_scope_file_header(self):
        start_line = 0
        line_count = self._editor.GetLineCount()
        while start_line < line_count and not self._editor.GetLine(start_line).startswith('X:'):
            start_line += 1
        tune_start_pos = self._editor.PositionFromLine(start_line)
        return self.create_scope(0, tune_start_pos)

    def get_scope_tune_header(self):
        if self.tune_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.PositionFromLine(self.tune_start_line)
            if self.body_start_line is not None:
                end_pos = self._editor.PositionFromLine(self.body_start_line)
            else:
                end_pos = self._editor.GetTextLength()
            return self.create_scope(start_pos, end_pos)

    def get_scope_tune_body(self):
        if self.body_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.PositionFromLine(self.body_start_line)
            end_pos = self._editor.PositionFromLine(self.body_end_line)
            return self.create_scope(start_pos, end_pos)

    def get_scope_tune(self):
        if self.tune_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.PositionFromLine(self.tune_start_line)
            if self.body_end_line is not None:
                end_pos = self._editor.PositionFromLine(self.body_end_line)
            else:
                end_pos = self._editor.GetTextLength()
            return self.create_scope(start_pos, end_pos)

    def get_scope_tune_up_to_selection(self):
        if self.tune_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.PositionFromLine(self.tune_start_line)
            end_pos = self._editor.GetCurrentPos()
            return self.create_scope(start_pos, end_pos)

    def get_scope_line_up_to_selection(self):
        if self.tune_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos, end_pos = self._editor.GetSelection()
            line_no = self._editor.GetCurrentLine()
            start_pos = self._editor.PositionFromLine(line_no)
            return self.create_scope(start_pos, end_pos)

    def get_scope_previous_character(self):
        start_pos, end_pos = self._editor.GetSelection()
        if start_pos == 0:
            return self.get_empty_scope_info()
        else:
            start_pos, end_pos = start_pos - 1, start_pos
            return self.create_scope(start_pos, end_pos)

    def get_scope_next_character(self):
        start_pos, end_pos = self._editor.GetSelection()
        if end_pos >= self._editor.GetTextLength():
            return self.get_empty_scope_info()
        else:
            start_pos, end_pos = end_pos, end_pos + 1
            return self.create_scope(start_pos, end_pos)

    def get_scope_body_up_to_selection(self):
        if self.body_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.PositionFromLine(self.body_start_line)
            end_pos = self._editor.GetCurrentPos()
            return self.create_scope(start_pos, end_pos)

    def get_scope_body_after_selection(self):
        if self.body_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.GetCurrentPos()
            end_pos = self._editor.PositionFromLine(self.body_end_line)
            return self.create_scope(start_pos, end_pos)

    def get_scope_measure_up_to_selection(self):
        if self.body_start_line is None:
            return self.get_empty_scope_info()
        else:
            start_pos = self._editor.PositionFromLine(self.body_start_line)
            end_pos = self._editor.PositionFromLine(self.body_end_line)
            return self.create_scope(start_pos, end_pos)

    @staticmethod
    def get_empty_scope_info():
        return TuneScopeInfo(None, None, None, None)

    def create_scope(self, start_pos, end_pos):
        text = self._editor.GetTextRange(start_pos, end_pos)
        return TuneScopeInfo(text, start_pos, end_pos, text.encode('utf-8'))

    def insert_text(self, text):
        self._editor.BeginUndoAction()
        self._editor.AddText(text)
        self._editor.EndUndoAction()
        self.invalidate()

    def set_relative_selection(self, relative_selection):
        if relative_selection:
            selection_start, selection_end = self._editor.GetSelection()
            selection_end += relative_selection
            if selection_start > selection_end:
                selection_start = selection_end
            self._editor.SetSelection(selection_start, selection_end)

    def replace_selection(self, text, selection_start=None, selection_end=None):
        text = unicode_text_to_abc(text)
        self._editor.BeginUndoAction()
        try:
            if selection_start is not None:
                if selection_end is None:
                    self._editor.SetSelection(selection_start, selection_start)
                else:
                    self._editor.SetSelection(selection_start, selection_end)
            elif selection_end is not None:
                self._editor.SetSelectionEnd(selection_end)

            selection_start, selection_end = self._editor.GetSelection()
            # selected_text = self._editor.GetTextRange(selection_start, selection_end)
            i = 0
            # while i < len(selected_text) and i < len(text) and selected_text[-(1 + i)] == text[-(1 + i)]:
            #     i += 1

            if i > 0:
                selection_end -= i
                self._editor.SetSelectionEnd(selection_end)
                text = text[:-i]

            self._editor.ReplaceSelection(text)
        finally:
            self._editor.EndUndoAction()
            self.invalidate()

    def ensure_tune_scope(self, tune_scope):
        if tune_scope is None:
            tune_scope = TuneScope.MatchText
            if self.inner_match:
                tune_scope = TuneScope.InnerText
        return tune_scope

    def replace_match_text(self, new_text, matchgroup=None, tune_scope=None, caret_after_matchgroup=False):
        tune_scope = self.ensure_tune_scope(tune_scope)
        m = self.current_match
        if tune_scope == TuneScope.InnerText and self.inner_match:
            m = self.inner_match

        if matchgroup:
            s = m.string
            new_text = s[m.start():m.start(matchgroup)] + new_text + s[m.end(matchgroup):m.end()]

        self.replace_in_editor(new_text, tune_scope)
        if matchgroup and caret_after_matchgroup:
            self.set_relative_selection(m.end(matchgroup) - m.end())

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
        if scope_info != self.get_empty_scope_info():
            self.replace_selection(new_text, scope_info.start, scope_info.stop)
            wx.CallAfter(self.invalidate)
        # else:
        #     print('Failed to find scope')

    def get_matchgroup(self, matchgroup, default=None):
        match = self.inner_match or self.current_match
        try:
            result = match.group(matchgroup)
        except IndexError:
            result = None

        if result is None:
            result = default
        return result

    def invalidate(self):  # context has changed so is not valid anymore
        self._tune_scope_info = {}
        self.current_element = None
        self._current_match = None
        if self.on_invalidate is not None:
            self.on_invalidate()

    def get_last_tune_id(self):
        tune_index_re = re.compile(r'(?m)^X:\s*(\d+)')
        tune_match = tune_index_re.match
        editor = self._editor
        get_line = editor.GetLine
        last_index = 0
        for line_no in xrange(editor.GetLineCount()):
            m = tune_match(get_line(line_no))
            if m:
                last_index = max(last_index, int(m.group(1)))
        return last_index