#    Copyright (C) 2011 Nils Liberg (mail: kotorinl at yahoo.co.uk)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
PY3 = sys.version_info.major > 2
if PY3:
    xrange = range


class ABCStyler:
    def __init__(self, styled_text_ctrl):
        self.e = styled_text_ctrl
        self.STYLE_DEFAULT = 0
        self.STYLE_COMMENT_NORMAL = 1
        self.STYLE_COMMENT_SPECIAL = 2
        self.STYLE_GRACE = 3
        self.STYLE_FIELD = 4
        self.STYLE_FIELD_VALUE = 5
        self.STYLE_FIELD_INDEX = 6
        self.STYLE_EMBEDDED_FIELD = 7
        self.STYLE_EMBEDDED_FIELD_VALUE = 8
        self.STYLE_BAR = 9
        self.STYLE_CHORD = 10
        self.STYLE_STRING = 11
        self.STYLE_ORNAMENT_EXCL = 12
        self.STYLE_ORNAMENT_PLUS = 13
        self.STYLE_ORNAMENT = 14
        self.STYLE_LYRICS = 15

        self.fields = 'ABCDEFGHIJKLMmNOPQRrSsTUVWwXYZ'
        self.ornaments = 'HIJKLMNOPQRSTUVWhijklmnopqrstuvw~'
        self.bar_chars = '|:[.'
        # go back to default style if next character is \r\n (to avoid some strange syntax highlighting with lyrics at least on mac version)
        new_line_style_changers = self.bar_chars + '!%"{+' + self.fields + self.ornaments
        self.style_changers = {
            '\r': new_line_style_changers,
            '\n': new_line_style_changers,
            ':': '\n%',
            '%': '\n',
            '%%': '\n%',
            '!': '!\n%',
            '+': '+\n%',
            '{': '}\n%',
            '[': ']\n%',
            '"': '"\n%',
        }
        self.non_style_changers = {
            self.STYLE_BAR: '|[]:1234',
            self.STYLE_ORNAMENT: self.ornaments,
            self.STYLE_COMMENT_SPECIAL: '%'
        }
        self.style_per_char = {
            '!': self.STYLE_ORNAMENT_EXCL,
            '+': self.STYLE_ORNAMENT_PLUS,
            '{': self.STYLE_GRACE,
        }

    def OnStyleNeeded(self, event):
        STYLE_DEFAULT = self.STYLE_DEFAULT
        STYLE_COMMENT_NORMAL = self.STYLE_COMMENT_NORMAL
        STYLE_COMMENT_SPECIAL = self.STYLE_COMMENT_SPECIAL
        STYLE_GRACE = self.STYLE_GRACE
        STYLE_FIELD = self.STYLE_FIELD
        STYLE_FIELD_VALUE = self.STYLE_FIELD_VALUE
        STYLE_FIELD_INDEX = self.STYLE_FIELD_INDEX
        STYLE_EMBEDDED_FIELD = self.STYLE_EMBEDDED_FIELD
        STYLE_EMBEDDED_FIELD_VALUE = self.STYLE_EMBEDDED_FIELD_VALUE
        STYLE_BAR = self.STYLE_BAR
        STYLE_CHORD = self.STYLE_CHORD
        STYLE_STRING = self.STYLE_STRING
        STYLE_ORNAMENT_EXCL = self.STYLE_ORNAMENT_EXCL
        STYLE_ORNAMENT_PLUS = self.STYLE_ORNAMENT_PLUS
        STYLE_ORNAMENT = self.STYLE_ORNAMENT
        STYLE_LYRICS = self.STYLE_LYRICS
        STYLE_CHORD = self.STYLE_CHORD
        style_changers = self.style_changers
        style_per_char = self.style_per_char
        non_style_changers = self.non_style_changers
        fields = self.fields
        ornaments = self.ornaments
        editor = self.e
        get_char_at = editor.GetCharAt
        get_text_range = editor.GetTextRangeRaw
        set_styling = editor.SetStyling
        start = editor.GetEndStyled()    # this is the first character that needs styling
        end = event.GetPosition()        # this is the last character that needs styling
        line_start = editor.LineFromPosition(start)
        start = editor.PositionFromLine(line_start)
        state = next_state = STYLE_DEFAULT  #  editor.GetStyleAt(start-1)  # init style
        text_length = editor.GetTextLength()
        old_state = state
        try:
            editor.StartStyling(start, 31)   # only style the text style bits
        except:
            editor.StartStyling(start)
        i = start
        chPrev = chr(get_char_at(i-1))
        ch = chr(get_char_at(i))

        buffer_pos = start + 1
        buffer_size = min(65536, end-start)
        next_buffer = get_text_range(buffer_pos, min(buffer_pos + buffer_size, text_length))
        next_buffer = list(map(chr, next_buffer))
        buffer_pos += len(next_buffer)

        char_count = 0
        style_changer = None
        non_style_changer = None
        while True:
            for chNext in next_buffer:
                if (not style_changer or ch in style_changer) or (non_style_changer and not ch in non_style_changer):
                    style_changer = None
                    if non_style_changer:
                        non_style_changer = None
                        state = STYLE_DEFAULT

                    if ch in '\r\n':
                        state = STYLE_DEFAULT
                        style_changer = style_changers[ch]
                    elif state == STYLE_DEFAULT:
                        if chPrev in '\n[\x00' and ch in fields and chNext == ':':
                            if chPrev == '[':
                                state = STYLE_EMBEDDED_FIELD   # field on the [M:3/4] form
                            elif ch in 'wW':
                                state = STYLE_LYRICS
                                style_changer = style_changers[':']
                            elif ch == 'X':
                                state = STYLE_FIELD_INDEX
                                style_changer = style_changers[':']
                            else:
                                state = STYLE_FIELD
                        elif ch == '|' or (ch in ':.' and chNext in '|:') or (ch == '[' and chNext in '1234'):
                            state = STYLE_BAR
                            non_style_changer = non_style_changers[state]
                        elif ch in '!+{':
                            state = style_per_char[ch]
                            style_changer = style_changers[ch]
                        elif ch == '%':
                            if chNext == '%' and chPrev in '\n\x00':
                                state = STYLE_COMMENT_SPECIAL
                            else:
                                state = STYLE_COMMENT_NORMAL
                                style_changer = style_changers[ch]
                        elif ch == '"':
                            state = STYLE_STRING
                            style_changer = style_changers[ch]
                        elif ch in ornaments:
                            state = STYLE_ORNAMENT
                            non_style_changer = non_style_changers[state]
                        elif chPrev == '[':
                            state = STYLE_CHORD
                            style_changer = style_changers[chPrev]
                    elif state in (STYLE_ORNAMENT_EXCL, STYLE_ORNAMENT_PLUS, STYLE_GRACE):
                        if style_per_char.get(ch) == state:
                            next_state = STYLE_DEFAULT
                    elif state in (STYLE_FIELD_VALUE, STYLE_LYRICS, STYLE_COMMENT_SPECIAL):
                        if ch == '%' and chPrev != '\\':
                            state = STYLE_COMMENT_NORMAL
                            style_changer = style_changers[ch]
                    elif state in (STYLE_CHORD, STYLE_EMBEDDED_FIELD_VALUE):
                        if ch == ']':
                            state = STYLE_DEFAULT
                    elif state == STYLE_FIELD:
                        if ch == ':':
                            next_state = STYLE_FIELD_VALUE
                            style_changer = style_changers[ch]
                    elif state == STYLE_EMBEDDED_FIELD:
                        if ch == ':':
                            next_state = STYLE_EMBEDDED_FIELD_VALUE
                            style_changer = style_changers['[']
                    elif state == STYLE_STRING:
                        if ch == '"':
                            if chPrev != '\\':
                                next_state = STYLE_DEFAULT
                            else:
                                style_changer = style_changers[ch]  # when " is escaped with \ then look for next ""
                    elif state == STYLE_COMMENT_SPECIAL and chPrev == '%':
                        style_changer = style_changers['%%']
                    else:
                        state == STYLE_DEFAULT

                if old_state != state:
                    set_styling(char_count, old_state)
                    char_count = 0
                    old_state = next_state = state

                state = next_state

                char_count += 1
                chPrev, ch = ch, chNext

            if buffer_pos >= end:
                break

            next_buffer = get_text_range(buffer_pos, min(buffer_pos + buffer_size, text_length))
            next_buffer = list(map(chr, next_buffer))
            buffer_pos += len(next_buffer)

        # final style
        set_styling(char_count, old_state)
