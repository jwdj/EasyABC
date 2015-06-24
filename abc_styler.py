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
#Style ornament was defined twice: remove first definition
#        self.STYLE_ORNAMENT = 10
        self.STYLE_STRING = 11
        self.STYLE_ORNAMENT_EXCL = 12
        self.STYLE_ORNAMENT_PLUS = 13
        self.STYLE_ORNAMENT = 14
        self.STYLE_LYRICS = 15

    def ColorTo(self, pos, style):        
        num_chars = pos - self.styling_startpos + 1    
        if num_chars > 0:
            self.e.SetStyling(num_chars, style)
            self.styling_startpos = pos+1

    def OnStyleNeeded(self, event):        
        start = self.e.GetEndStyled()    # this is the first character that needs styling
        end = event.GetPosition()        # this is the last character that needs styling        
        start = self.e.PositionFromLine(self.e.LineFromPosition(start))
        state = self.e.GetStyleAt(start-1)  # init style
        if start >= 0:
            if chr(self.e.GetCharAt(start-1)) == '}':
                state = self.STYLE_DEFAULT
        lengthDoc = end + 1

        self.styling_startpos = start
        self.e.StartStyling(start, 31)   # only style the text style bits
        i = start
        ch = chr(self.e.GetCharAt(i))
        chNext = chr(self.e.GetCharAt(i+1))
        chPrev = chr(self.e.GetCharAt(i-1))
        while i <= lengthDoc:
            advance = True
            if state == self.STYLE_DEFAULT:
                if (ch == '|' or (ch == ':' and chNext in '|:')) or (ch == '[' and chNext in '1234'):
                    self.ColorTo(i-1, state)
                    state = self.STYLE_BAR
                elif chPrev in '\r\n[\x00' and ch in 'ABCDEFGHIJKLMNOPQRSTUVWwXYZ' and chNext == ':':
                    self.ColorTo(i-1, state)                    
                    if ch == 'X':
                        state = self.STYLE_FIELD_INDEX
                    elif chPrev in '\r\n' and ch in ('w', 'W'):
                        state = self.STYLE_LYRICS                        
                    elif chPrev in '\r\n':
                        state = self.STYLE_FIELD
                    elif chNext != '[':
                        state = self.STYLE_EMBEDDED_FIELD   # field on the [M:3/4] form                    
                    else:
                        state = self.STYLE_DEFAULT
                elif ch == '!':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_ORNAMENT_EXCL
                elif ch == '+':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_ORNAMENT_PLUS
                elif ord('h') <= ord(ch.lower()) <= ord('x'): ## ch in 'uvTHLMPSO':
                    self.ColorTo(i-1, state)
                    self.ColorTo(i, self.STYLE_ORNAMENT)
                    state = self.STYLE_DEFAULT
                elif ch == '%' and chNext != '%':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_COMMENT_NORMAL                    
                elif ch == '%' and chNext == '%':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_COMMENT_SPECIAL
                elif ch == '"':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_STRING
                elif ch == '{':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_GRACE
            elif state == self.STYLE_BAR:
                if ch not in '|[]:1234':
                    self.ColorTo(i-1, state)
                    state = self.STYLE_DEFAULT
                    advance = False
            elif state in [self.STYLE_FIELD, self.STYLE_EMBEDDED_FIELD, self.STYLE_FIELD_INDEX, self.STYLE_FIELD_VALUE, self.STYLE_EMBEDDED_FIELD_VALUE, self.STYLE_COMMENT_NORMAL, self.STYLE_COMMENT_SPECIAL]:
#Do not check for ] in other case thant STYLE EMBEDDED to avoid going in default style if used in comments or commands like %%staves/%%scores
#                if ch in '\r\n]' or (state == self.STYLE_EMBEDDED_FIELD_VALUE and ch == ']'):
                if ch in '\r\n' or (state == self.STYLE_EMBEDDED_FIELD_VALUE and ch == ']'):
                    self.ColorTo(i-1, state)
                    state = self.STYLE_DEFAULT
                    self.ColorTo(i, state)
                elif state == self.STYLE_FIELD and ch == ':':
                    self.ColorTo(i, state)
                    state = self.STYLE_FIELD_VALUE
                elif state == self.STYLE_EMBEDDED_FIELD and ch == ':':
                    self.ColorTo(i, state)
                    state = self.STYLE_EMBEDDED_FIELD_VALUE
                #elif state == self.STYLE_EMBEDDED_FIELD_VALUE and ch == ']':
                #    self.ColorTo(i, state)
                #    state = self.STYLE_DEFAULT
                    
            elif state == self.STYLE_STRING:
                if ch == '"' and chPrev != '\\' or ch in '\r\n':
                    self.ColorTo(i, state)
                    state = self.STYLE_DEFAULT
            elif state == self.STYLE_LYRICS:
                if ch in '\r\n':
                    self.ColorTo(i, state)
                    state = self.STYLE_DEFAULT
            elif state == self.STYLE_GRACE:
                if ch == '}':
                    self.ColorTo(i, state)
                    state = self.STYLE_DEFAULT
            elif state == self.STYLE_ORNAMENT_EXCL:
                if ch in '!\r\n':
                    self.ColorTo(i, state)
                    state = self.STYLE_DEFAULT                
            elif state == self.STYLE_ORNAMENT_PLUS:
                if ch in '+\r\n':
                    self.ColorTo(i, state)
                    state = self.STYLE_DEFAULT
#force to go back to STYLE_DEFAULT if in none of the previous case
            else:
                state = self.STYLE_DEFAULT

#go back to default style if next character is \r\n (to avoid some strange syntax highlighting whith lyrics at least on mac version)
            if chNext in '\r\n':
                self.ColorTo(i, state)
                state = self.STYLE_DEFAULT

            if advance:
                i += 1
                chPrev = ch
                ch = chNext
                chNext = chr(self.e.GetCharAt(i+1))

        self.ColorTo(end, state)
