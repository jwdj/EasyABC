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
        self.STYLE_STRING = 11
        self.STYLE_ORNAMENT_EXCL = 12
        self.STYLE_ORNAMENT_PLUS = 13
        self.STYLE_ORNAMENT = 14
        self.STYLE_LYRICS = 15

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
        STYLE_STRING = self.STYLE_STRING
        STYLE_ORNAMENT_EXCL = self.STYLE_ORNAMENT_EXCL
        STYLE_ORNAMENT_PLUS = self.STYLE_ORNAMENT_PLUS
        STYLE_ORNAMENT = self.STYLE_ORNAMENT
        STYLE_LYRICS = self.STYLE_LYRICS
        editor = self.e
        get_char_at = editor.GetCharAt
        set_styling = editor.SetStyling
        start = editor.GetEndStyled()    # this is the first character that needs styling
        end = event.GetPosition()        # this is the last character that needs styling        
        line_start = editor.LineFromPosition(start)
        start = editor.PositionFromLine(line_start)
        state = editor.GetStyleAt(start-1)  # init style
        lengthDoc = end + 1
        editor.StartStyling(start, 31)   # only style the text style bits
        i = start
        ch = chr(get_char_at(i))
        chNext = chr(get_char_at(i+1))
        chPrev = chr(get_char_at(i-1))
        char_count = 0
        if chPrev == '}':
            state = STYLE_DEFAULT  # why?
        while i <= lengthDoc:
            old_state = state

            if state == STYLE_BAR:
                if ch not in '|[]:1234':
                    state = STYLE_DEFAULT

            if ch in '\r\n':  # go back to default style if next character is \r\n (to avoid some strange syntax highlighting whith lyrics at least on mac version)
                state = STYLE_DEFAULT
            elif state == STYLE_DEFAULT:
                if (ch == '|' or (ch == ':' and chNext in '|:')) or (ch == '[' and chNext in '1234'):
                    state = STYLE_BAR
                elif chPrev in '\r\n[\x00' and ch in 'ABCDEFGHIJKLMmNOPQRrSsTUVWwXYZ' and chNext == ':':
                    if ch == 'X':
                        state = STYLE_FIELD_INDEX
                    elif chPrev in '\r\n':
                        if ch in ('w', 'W'):
                            state = STYLE_LYRICS
                        else:
                            state = STYLE_FIELD
                    elif chNext != '[':
                        state = STYLE_EMBEDDED_FIELD   # field on the [M:3/4] form
                    else:
                        state = STYLE_DEFAULT
                elif ch == '!':
                    state = STYLE_ORNAMENT_EXCL
                elif ch == '+':
                    state = STYLE_ORNAMENT_PLUS
                elif ch == '%' and chNext != '%':
                    state = STYLE_COMMENT_NORMAL
                elif ch == '%' and chNext == '%':
                    state = STYLE_COMMENT_SPECIAL
                elif ch == '"':
                    state = STYLE_STRING
                elif ch == '{':
                    state = STYLE_GRACE
                elif ch in 'HIJKLMNOPQRSTUVWhijklmnopqrstuvw~':
                    state = STYLE_ORNAMENT
            elif state == STYLE_ORNAMENT:
                state = STYLE_DEFAULT
            elif state == STYLE_FIELD_VALUE:
                if ch == '%' and chPrev != '\\':
                    state = STYLE_COMMENT_NORMAL
            elif state == STYLE_EMBEDDED_FIELD_VALUE:
                if ch == ']':
                    state = STYLE_DEFAULT
            elif state == STYLE_FIELD:
                if ch == ':':
                    state = STYLE_FIELD_VALUE
            elif state == STYLE_EMBEDDED_FIELD:
                if ch == ':':
                    state = STYLE_EMBEDDED_FIELD_VALUE
            elif state == STYLE_STRING:
                if ch == '"' and chPrev != '\\':
                    state = STYLE_DEFAULT
            elif state == STYLE_GRACE:
                if ch == '}':
                    state = STYLE_DEFAULT
            elif state == STYLE_ORNAMENT_EXCL:
                if ch == '!':
                    state = STYLE_DEFAULT
            elif state == STYLE_ORNAMENT_PLUS:
                if ch == '+':
                    state = STYLE_DEFAULT
            #elif state not in [STYLE_LYRICS, STYLE_BAR, STYLE_COMMENT_NORMAL, STYLE_COMMENT_SPECIAL, STYLE_FIELD_INDEX]:
            #    state = STYLE_DEFAULT  # force to go back to STYLE_DEFAULT if in none of the previous case

            if old_state != state: # and char_count > 0:
                set_styling(char_count, old_state)
                char_count = 0

            char_count += 1
            i += 1
            chPrev = ch
            ch = chNext
            chNext = chr(get_char_at(i+1))

        if char_count > 0:
            set_styling(char_count, old_state)
