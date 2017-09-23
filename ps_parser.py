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

import re
import os
import sys
import traceback
from math import sin, cos
import codecs
from datetime import datetime
from collections import deque
import cPickle as pickle
import locale
import weakref

num_re = re.compile(r'([-+]?(\d+(\.\d+)?|\.\d+))$')
num_with_base_re = re.compile(r'[0-9a-fA-F]+#[0-9a-fA-F]+$')
token_split_pattern_re = re.compile(r'(?s)(\s+|[{}\]\[]|/[-A-Za-z0-9_$@]+|\(.*?\)|<.*?>)')

def toint(i, bits=32):
    ' converts to a signed integer with bits bits '
    i &= (1 << bits) - 1  # get last "bits" bits, as unsigned
    if i & (1 << (bits - 1)):  # is negative in N-bit 2's comp
        i -= 1 << bits         # ... so make it negative
    return int(i)

class UndefinedNameException(Exception):
    def __init__(self, message):
        super(UndefinedNameException, self).__init__(message)

class PSObject(object):
    def __repr__(self):
        return repr(self.value)
    def __str__(self):
        return repr(self.value)
    def copy_from(self, other):
        self.value = other.value

class PSLiteralName(PSObject):
    def __init__(self, name):
        super(PSLiteralName, self).__init__()
        self.value = name

class PSName(PSObject):
    def __init__(self, name):
        super(PSName, self).__init__()
        self.value = name

class PSString(PSObject):
    def __init__(self, value):
        super(PSString, self).__init__()
        self.value = value

class PSNumber(PSObject):
    def __init__(self, value):
        super(PSNumber, self).__init__()
        self.value = value

class PSBoolean(PSObject):
    def __init__(self, value):
        super(PSBoolean, self).__init__()
        self.value = value

class PSArray(PSObject):
    def __init__(self, value=None, executable=True):
        super(PSArray, self).__init__()
        if value is None:
            value = []
        assert(type(value) is list)
        self.value = value
        self.first = 0
        self.last = len(value)-1
        self.executable = executable
    def copy_from(self, other):
        self.value = other.value[:]
    def __getitem__(self, index):
        assert(self.first <= index <= self.last)
        return self.value[index + self.first]
    def __setitem__(self, index, value):
        assert(self.first <= index <= self.last)
        self.value[index + self.first] = value
    def __iter__(self):
        return iter(self.value[self.first:self.last+1])
    def as_list(self):
        return self.value[self.first:self.last+1]

class PSGraphicsState(PSObject):
    def __init__(self, interpreter):
        super(PSGraphicsState, self).__init__()
        self.interpreter = interpreter
        self.x = 0.0
        self.y = 0.0
        self.linewidth = 1.0
        self.currentgray = 0.0
        self.path = []
        self.path_is_terminated = False
        self.font_name = 'Times'
        self.font_size = 12
        self.final_scaling = 1.0
        self.x_scale = 1.0
        self.y_scale = 1.0
        self.x_offset = 0.0
        self.y_offset = 0.0
        self.scale(4.0/3.0, 4.0/3.0)

    def copy(self):
        gstate = PSGraphicsState(self.interpreter)
        gstate.x = self.x
        gstate.y = self.y
        gstate.linewidth = self.linewidth
        gstate.currentgray = self.currentgray
        gstate.path = self.path[:]
        gstate.path_is_terminated = False  # when True the next path segment that is added will start a new curve
        gstate.font_name = self.font_name
        gstate.font_size = self.font_size
        gstate.final_scaling = self.final_scaling
        gstate.x_scale = self.x_scale
        gstate.y_scale = self.y_scale
        gstate.x_offset = self.x_offset
        gstate.y_offset = self.y_offset
        return gstate

    def get_transformed_cur_pos(self):
        return self.get_device_coordinate(self.x, self.y)

    def move_to(self, x, y, relative=False):
        if relative:
            self.x += x
            self.y += y
        else:
            self.x = x
            self.y = y

    def get_effective_line_width(self):
        lw = (self.x_scale + self.y_scale) / 2.0 * self.linewidth
        return lw

    def transform(self, x, y):
        return (self.x_offset + self.x_scale * x, self.y_offset + self.y_scale * y)

    def translate(self, x, y):
        self.x_offset += x * self.x_scale
        self.y_offset += y * self.y_scale
        return

    def scale(self, x, y):
        self.x_scale *= x
        self.y_scale *= y
        self.x /= x
        self.y /= y
        return

    def get_device_coordinate(self, x, y):
        x, y = self.transform(x, y)
        y = 850*4/3.0 - y
        x *= self.final_scaling
        y *= self.final_scaling
        if abs(round(x) - x) < 0.01:
            x = float(int(round(x)))
        if abs(round(y) - y) < 0.01:
            y = float(int(round(y)))
        return (x, y)

    def __repr__(self):
        return '<gstate>'

    def copy_from(self, other):
        raise Exception('not yet implemented')

##    def get_wx_font(self):
##        if 'Italic' in self.font_name:
##            style = wx.FONTSTYLE_ITALIC
##        else:
##            style = wx.FONTSTYLE_NORMAL
##        if 'Bold' in self.font_name:
##            weight = wx.FONTWEIGHT_BOLD
##        else:
##            weight = wx.FONTWEIGHT_NORMAL
##        font = wx.Font(int(self.font_size*self.final_scaling*self.y_scale*0.93), wx.FONTFAMILY_DEFAULT, style, weight, False, "Times New Roman", wx.FONTENCODING_SYSTEM)
##        return font

    def get_svg_fill(self):
        if self.currentgray == 0.0:
            return 'black'
        elif self.currentgray == 1.0:
            return 'white'
        else:
            s = '%.2x' % int(255 * self.currentgray)
            return '#' + s + s + s

    def get_path(self):
        cmds = []
        for cmd in self.path:
            for x in cmd:
                if type(x) is float:
                    x = ('%.2f' % x).rstrip('0')
                cmds.append(x)
        svg_command = ' '.join(cmds)
        return svg_command

class PSBuiltinOperator(PSObject):
    def __init__(self, interpreter, func_name):
        super(PSBuiltinOperator, self).__init__()
        self.interpreter = interpreter
        self.func_name = func_name
        if self.func_name == '[':
            self.internal_func_name = 'PS_start_array'
        elif self.func_name == ']':
            self.internal_func_name = 'PS_end_array'
        elif self.func_name in ['=', '==']:
            self.internal_func_name = 'PS_print_operator'
        else:
            self.internal_func_name = 'ps_' + func_name
    def __repr__(self):
        return self.func_name
    def __str__(self):
        return repr(self.func_name)
    def __call__(self, *args, **kwargs):
        func = getattr(self.interpreter, self.internal_func_name)
        func(*args, **kwargs)
    def __hash__(self):
        return hash(self.func_name)
    def __cmp__(self, other):
        return cmp(self.func_name, other.func_name)
    def __eq__(self, other):
        return isinstance(other, PSBuiltinOperator) and self.func_name == other.func_name
    def copy_from(self, other):
        self.interpreter = other.interpreter
        self.func = other.func
        self.func_name = other.func_name
        self.internal_func_name = other.internal_func_name

class PSInterpreter(object):
    def __init__(self, final_scaling=1.0):
        self.userdict = {}
        self.dict_stack = [self.userdict]
        self.operand_stack = [] # deque()
        self.gstate = PSGraphicsState(self)
        self.gstate_stack = [self.gstate]
        self.gstate.final_scaling = final_scaling
        self.trace_on = False
        self.StandardEncoding = self.get_standard_encoding_names()
        self.ISOLatin1Encoding = self.get_ISO_latin1_encoding_names()
        self.time_stats = {}
        self.count_stats = {}
        self.num_pages = 0
        self.svg = []
        self.executed_name_stack = []

    def get_svg_class(self):
        if self.executed_name_stack:
            return ' class="%s"' % self.executed_name_stack[-1]
        else:
            return ''

    def get_text_extent(self, text):
        # just a rough estimation
        font_width = self.gstate.font_size * 0.48 * self.gstate.x_scale
        return (len(text) * font_width, 0)
##        dc = wx.MemoryDC()
##        dc.SetFont(self.gstate.get_wx_font())
##        (width, height, descent, externalLeading) = dc.GetTextExtent(text)
##        return (width, height)

    def before_path_drawing(self):
        if self.gstate.path_is_terminated:
            self.gstate.path = []
            self.gstate.path_is_terminated = False

    def parse_hex_string_token(self, s):
        s = str(s).translate(None, ' \t\r\n') # delete white space
        bytes = [int(x+y, 16) for (x,y) in zip(s[0::2], s[1:-1:2])]
        if not bytes:
            return PSString('')

        homogenous_number_array_type = 149
        if bytes[0] == homogenous_number_array_type:
            array_type, representation, len1, len0 = bytes[:4]
            array_len = (len1 << 8) + len0
            numbers = []
            if 0 <= representation <= 31:  # fixed point 32-bit
                scale = 2**representation
                for i in range(0, array_len, 4):
                    n = toint((bytes[i] << 24) + (bytes[i+1] << 16) + (bytes[i+2] << 8) + bytes[i+3]) / float(scale)
                    numbers.append(PSNumber(n))
            elif 32 <= representation <= 47: # fixed point 16-bit
                scale = 2**(representation-32)
                for i in range(0, array_len, 2):
                    n = toint((bytes[i] << 8) + bytes[i+1], 16) / float(scale)
                    numbers.append(PSNumber(n))
                ##print numbers
            else:
                raise Exception("Number format in homogenous postscript number array not supported: %s" % representation)
            return PSArray(numbers)

        else:
            return PSString(''.join(chr(i) for i in bytes))

    def tokenize(self, ps_code):
        ps_code = re.sub(r'(?m)%.*$', '', ps_code)
        ps_code = ps_code.replace(r'\(', unicode(0x300A)).replace(r'\)', unicode(0x300B))
        tokens = []
        for t in token_split_pattern_re.split(ps_code):
            # skip empty space
            if not t.strip():
                continue
            # start of end of array
            elif t == '{' or t == '}':
                tokens.append(t)
            # string token
            elif t[0] == '(':
                t = t.replace(unicode(0x300A), '(').replace(unicode(0x300B), ')')
                tokens.append(PSString(t[1:-1]))
            # hexadecimal string token
            elif t[0] == '<':
                tokens.append(self.parse_hex_string_token(t[1:-1]))
            # literal name
            elif t[0] == '/':
                tokens.append(PSLiteralName(t[1:]))
            # number in 10 base (int or float)
            elif num_re.match(t):
                try:
                    t = int(t)
                except:
                    t = float(t)
                tokens.append(PSNumber(t))
            # integer in some other base than 10
            elif num_with_base_re.match(t):
                base, num = t.split('#')
                tokens.append(PSNumber( int(num, int(base)) ))
            # name token
            else:
                tokens.append(PSName(t))
        tokens.reverse()  # the last element represents the top of the stack, so reverse the elements to get right order
        return tokens

    def interpret(self, ps_code):
        self.num_pages = 0
        tokens = self.tokenize(ps_code)
        self.execute_tokens(tokens)

    def execute_single(self, t, dont_execute_array=False):
        if self.trace_on:
            print 'token:', t, 'stack:', self.operand_stack[-5:]
        if isinstance(t, (PSLiteralName, PSNumber, PSString)):
            self.push_operand(t)
        elif isinstance(t, PSName):
            start_time = datetime.now()
            ps_operator = t.value
            self.executed_name_stack.append(ps_operator)
            #print 'execute', t
            #if 'hyph' in str(t):
            #    self.trace_on = True
            try:
                self.execute_single(self.lookup(t))
            except Exception as e:
                print 'execute', t
                print 'stack:', list(reversed(self.operand_stack))
                raise
            self.executed_name_stack.pop()
            self.time_stats[t.value] = self.time_stats.get(t.value, 0) + (datetime.now() - start_time).seconds*1000000 + (datetime.now() - start_time).microseconds
            self.count_stats[t.value] = self.count_stats.get(t.value, 0) + 1
        elif isinstance(t, PSArray):
            if t.executable and not dont_execute_array:
                self.execute_tokens(list(reversed(t.value)))
            else:
                self.push_operand(t)
        elif hasattr(t, '__call__'):
            start_time = datetime.now()
            t()
            self.time_stats[t.func_name] = self.time_stats.get(t.func_name, 0) + (datetime.now() - start_time).seconds*1000000 + (datetime.now() - start_time).microseconds
            self.count_stats[t.func_name] = self.count_stats.get(t.func_name, 0) + 1
        else:
            raise Exception('Unknown operand type - cannot execute it: %s' % t)

    def read_array(self, tokens):
        elements = []
        tokens.pop() # first '{' character
        while tokens[-1] != '}':
            if tokens[-1] == '{':
                elements.append(self.read_array(tokens)) # recursive array
            else:
                elements.append(tokens.pop())
        tokens.pop() # last '{' character
        return PSArray(elements)

    def execute_tokens(self, tokens):
        while tokens:
            if tokens[-1] == '{':
                self.push_operand(self.read_array(tokens))
            else:
                t = tokens.pop()
                dont_execute_array = \
                     len(tokens) >= 1 and isinstance(tokens[-1], PSBuiltinOperator) and tokens[-1].func_name in ['repeat', 'if', 'ifelse', 'for'] or \
                     len(tokens) >= 2 and isinstance(tokens[-2], PSBuiltinOperator) and tokens[-2].func_name in ['ifelse']
                self.execute_single(t, dont_execute_array)

    def lookup(self, ps_name):
        # if not found - try to see if we can find a built-in function among the methods of this class
        if ps_name.value in ['=', '==']:
            builtin_func_name = 'PS_print_operator'
        else:
            builtin_func_name = 'ps_' + ps_name.value
        if hasattr(self, builtin_func_name) or ps_name.value in ('[', ']'):
            return PSBuiltinOperator(self, ps_name.value)

        for name_dict in reversed(self.dict_stack):
            if ps_name.value in name_dict:
                return name_dict[ps_name.value]

        if ps_name.value == 'StandardEncoding':
            return self.StandardEncoding
        elif ps_name.value == 'ISOLatin1Encoding':
            return self.ISOLatin1Encoding
        elif ps_name.value == 'languagelevel':
            return PSNumber(2)

        raise UndefinedNameException('name not found: %s' % ps_name.value)

    def pop_operand(self):
        return self.operand_stack.pop()

    def push_operand(self, operand):
        return self.operand_stack.append(operand)

    def pop_operands(self, n=1):
        result = []
        for i in range(n):
            result.append(self.operand_stack.pop())
        result.reverse()
        return result

    def push_operands(self, *operands):
        self.operand_stack.extend(operands)

    def bind_helper(self, obj):
        # apply bind recursively
        if isinstance(obj, PSArray):
            return PSArray([self.bind_helper(x) for x in obj], obj.executable)

        # bind if the name can be found, otherwise leave it unchanged without any error
        elif isinstance(obj, PSName):
            try:
                return self.lookup(obj)
            except UndefinedNameException:
                return obj
        else:
            return obj

    def PS_start_array(self):  # [ operator
        self.push_operand(PSName('['))

    def PS_end_array(self):  # [ operator
        elements = []
        while self.operand_stack[-1].value != '[':
            elements.append(self.pop_operand())
        self.pop_operand() # pop the [
        elements.reverse()
        self.push_operand(PSArray(elements, executable=False))

    def PS_print_operator(self):
        print self.pop_operand().value

    def ps_load(self):
        self.push_operand(self.lookup(self.pop_operand()))

    def ps_def(self):
        name, value = self.pop_operands(2)
        self.dict_stack[-1][name.value] = value

    def ps_cvlit(self):
        obj = self.pop_operand()
        if isinstance(obj, PSArray):
            obj.executable = False
        elif isinstance(obj, PSName):
            obj = PSLiteralName(obj.value)
        self.push_operand(obj)

    def ps_where(self):
        key = self.pop_operand()
        try:
            value = self.lookup(key)
            self.push_operands(None, PSBoolean(True))  # TODO: instead of None the dict is supposed to be passed
        except UndefinedNameException:
            self.push_operand(PSBoolean(False))

    def ps_eq(self):
        a, b = self.pop_operands(2)
        self.push_operand(PSBoolean(a.value == b.value))
        # TODO: handle also composite objects

    def ps_ne(self):
        self.ps_eq()
        self.operand_stack[-1].value = not self.operand_stack[-1].value # perform 'eq' and then negate result

    def ps_and(self):
        ' If the operands are booleans, and returns their logical conjunction. If the operands are integers, and returns the bitwise and of their binary representations. '
        a, b = self.pop_operands(2)
        if isinstance(a, PSBoolean) and isinstance(b, PSBoolean):
            self.push_operand(PSBoolean(a.value and b.value))
        elif isinstance(a, PSNumber) and isinstance(b, PSNumber):
            a, b = int(a.value), int(b.value)
            self.push_operand(PSNumber(a & b))

    def ps_if(self):
        condition, proc = self.pop_operands(2)
        if condition.value is True:
            self.execute_tokens(list(reversed(proc.as_list())))

    def ps_ifelse(self):
        condition, proc1, proc2 = self.pop_operands(3)
        if condition.value is True:
            self.execute_tokens(list(reversed(proc1.as_list())))
        elif condition.value is False:
            self.execute_tokens(list(reversed(proc2.as_list())))
        else:
            raise Exception('incorrect boolean value')

    def ps_repeat(self):
        times, proc = self.pop_operands(2)
        for i in range(times.value):
            self.execute_tokens(list(reversed(proc.as_list())))

    def ps_for(self):
        initial, increment, limit, proc = self.pop_operands(4)
        tokens = list(reversed(proc.as_list()))
        x = initial.value
        if increment.value > 0:
            while x < limit.value:
                self.push_operand(PSNumber(x))
                self.execute_tokens(tokens)
                x += increment.value
        else:
            while x > limit.value:
                self.push_operand(PSNumber(x))
                self.execute_tokens(tokens)
                x -= increment.value

    def ps_translate(self):
        x, y = self.pop_operands(2)
        self.gstate.translate(x.value, y.value)

    def ps_rotate(self):
        angle = self.pop_operand()
        assert(isinstance(angle, PSNumber))
        print 'warning: rotation not supported. Operation ignored.'
        #self.gstate.rotate(angle)

    def ps_scale(self):
        x, y = self.pop_operands(2)
        self.gstate.scale(x.value, y.value)

    def ps_transform(self):
        x, y = self.pop_operands(2)
        x, y = self.gstate.transform(x.value, y.value)
        self.push_operands(PSNumber(x), PSNumber(y))
        # TODO: handle other types of operands

    def ps_matrix(self):
        self.push_operand(PSArray([1.0, 0.0, 0.0, 1.0, 0.0, 0.0]))

    def ps_currentmatrix(self):
        matrix = self.pop_operand()
        assert(isinstance(matrix, PSArray) and len(matrix.value) == 6)
        a, b, c, d, e, f = [self.gstate.matrix[i] for i in [(0, 0), (0, 1), (0, 1), (1, 1), (0, 2), (1, 2)]]
        self.push_operand(PSArray([a, b, c, d, e, f], executable=False))

    def ps_moveto(self):
        self.before_path_drawing()
        x, y = self.pop_operands(2)
        self.gstate.move_to(x.value, y.value, relative=False)
        x, y = self.gstate.get_device_coordinate(self.gstate.x, self.gstate.y)
        if self.gstate.path and self.gstate.path[-1][0] == 'M':
            self.gstate.path.pop()
        self.gstate.path.append(('M', x, y))

    def ps_rmoveto(self):
        self.before_path_drawing()
        x, y = self.pop_operands(2)
        self.gstate.move_to(x.value, y.value, relative=True)
        x, y = self.gstate.get_device_coordinate(self.gstate.x, self.gstate.y)
        if self.gstate.path and self.gstate.path[-1][0] == 'M':
            self.gstate.path.pop()
        self.gstate.path.append(('M', x, y))

    def ps_lineto(self):
        self.before_path_drawing()
        x, y = self.pop_operands(2)
        self.gstate.move_to(x.value, y.value, relative=False)
        x, y = self.gstate.get_device_coordinate(self.gstate.x, self.gstate.y)
        self.gstate.path.append(('L', x, y))

    def ps_rlineto(self):
        self.before_path_drawing()
        x, y = self.pop_operands(2)
        x1, y1 = self.gstate.get_device_coordinate(self.gstate.x, self.gstate.y)
        x2, y2 = self.gstate.get_device_coordinate(self.gstate.x + x.value, self.gstate.y + y.value)
        self.gstate.move_to(x.value, y.value, relative=True)
        self.gstate.path.append(('L', x2, y2))

    def ps_curveto(self):
        self.before_path_drawing()
        x1, y1, x2, y2, x3, y3 = [v.value for v in self.pop_operands(6)]
        self.gstate.move_to(x3, y3)
        x1, y1 = self.gstate.get_device_coordinate(x1, y1)
        x2, y2 = self.gstate.get_device_coordinate(x2, y2)
        x3, y3 = self.gstate.get_device_coordinate(x3, y3)
        self.gstate.path.append(('C', x1, y1, x2, y2, x3, y3))

    def ps_rcurveto(self):
        self.before_path_drawing()
        dx1, dy1, dx2, dy2, dx3, dy3 = [v.value for v in self.pop_operands(6)]
        x1, y1 = self.gstate.get_device_coordinate(self.gstate.x + dx1, self.gstate.y + dy1)
        x2, y2 = self.gstate.get_device_coordinate(self.gstate.x + dx2, self.gstate.y + dy2)
        x3, y3 = self.gstate.get_device_coordinate(self.gstate.x + dx3, self.gstate.y + dy3)
        self.gstate.path.append(('C', x1, y1, x2, y2, x3, y3))
        self.gstate.move_to(dx3, dy3, relative=True)

    def ps_arc(self):
        self.before_path_drawing()
        x, y, r, ang1, ang2 = [x.value for x in self.pop_operands(5)]
        x1, y1 = self.gstate.get_device_coordinate(x-r, y+r)
        x2, y2 = self.gstate.get_device_coordinate(x+r, y-r)
        x, y = self.gstate.get_device_coordinate(x, y)
        rx = (x2-x1)/2
        ry = (y2-y1)/2
        self.gstate.path.append(('A', rx, ry, 0.0, 1.0, 0.0, x2, y2))
        self.gstate.move_to(x2, y2)
        # TODO: handle arcs in a correct way

    def ps_setlinewidth(self):
        w = self.pop_operand()
        self.gstate.linewidth = w.value

    def ps_setdash(self):
        array, offset = self.pop_operands(2)
        print 'warning: postscript setdash operand ignored (not yet supported)'
        # TODO: add support for this

    def ps_rectfill(self):
        x, y, width, height = [v.value for v in self.pop_operands(4)]
        x1, y1 = self.gstate.get_device_coordinate(x, y)
        x2, y2 = self.gstate.get_device_coordinate(x + width, y + height)
        #self.svg.append('<rect x="%f" y="%f" width="%f" height="%f" style="fill:%s; stroke:none"/>' %
        #                (x1, y1, x2-x1, y2-y1, self.gstate.get_svg_fill()))
        path = ' '.join('%s %.2f %.2f' % c for c in [('M', x1, y1), ('L', x2, y1), ('L', x2, y2), ('L', x1, y2)]) + ' Z'
        self.svg.append('<path%s d="%s" style="fill:%s; stroke:none"/>' % (self.get_svg_class(), path, self.gstate.get_svg_fill()))

    def ps_ufill(self):
        userpath = self.pop_operand()
        # map from op-code (index into the array) to operator name:
        #code2operator = ['setbbox', 'moveto', 'rmoveto', 'lineto', 'rlineto', 'curveto', 'rcurveto', 'arc', 'arcn', 'arct', 'closepath', 'ucache']
        code2operator = [('setbbox', 4),
                         ('moveto', 2),
                         ('rmoveto', 2),
                         ('lineto', 2),
                         ('rlineto', 2),
                         ('curveto', 6),
                         ('rcurveto', 6),
                         ('arc', 5),
                         ('arcn', 5),
                         ('arct', 5),
                         ('closepath', 0),
                         ('ucache', 0)]
        values, operators = userpath.value
        values = values.value
        #values.reverse()
        #self.operand_stack.extend(values)
        operand_offset = 0
        repeat_count = 1
        for opcode in operators.value:
            opcode = ord(opcode)
            if 32 < opcode <= 255:
                repeat_count = opcode - 32
            else:
                op_name, operand_count = code2operator[opcode]
                operands = values[operand_offset : operand_offset+operand_count]
                operator = PSName(op_name)
                for i in range(repeat_count):
                    print operator, operands
                    self.push_operands(*operands)
                    self.execute_single(operator)
                repeat_count = 1
        print userpath

    def ps_ucache(self):
        pass

    def ps_setbbox(self):
        self.pop_operands(4)

    def ps_fill(self):
        ' paints the area enclosed by the current path with the current color. '
        self.svg.append('<path%s d="%s" style="fill:%s; stroke:none"/>' %
                        (self.get_svg_class(), self.gstate.get_path(), self.gstate.get_svg_fill()))
        self.gstate.path = []
        self.gstate.path_is_terminated = False

    def ps_stroke(self):
        ' paints a line following the current path and using the current color.  '
        if self.gstate.get_path():
            self.svg.append('<path%s d="%s" style="fill:none; stroke:%s; stroke-width:%f"/>' %
                            (self.get_svg_class(), self.gstate.get_path(), self.gstate.get_svg_fill(), self.gstate.get_effective_line_width()))
        self.gstate.path = []
        self.gstate.path_is_terminated = False

    def ps_closepath(self):
        self.gstate.path.append(('Z', ))
        self.gstate.path_is_terminated = True

    def ps_showpage(self):
        self.num_pages += 1
        self.gstate = PSGraphicsState(self)
        self.gstate.x_scale = (4/3.0)**2
        self.gstate.y_scale = (4/3.0)**2
        self.gstate_stack = [self.gstate]
        self.gstate.translate(0, -1030.7 * self.num_pages)  # TODO: check what number we need to use here

    def ps_selectfont(self):
        ' obtains a font whose name is key, transforms it according to scale or matrix, and establishes it as the current font dictionary in the graphics state.  '
        key, scale_or_matrix = self.pop_operands(2)
        test = int(scale_or_matrix.value)
        self.gstate.font_size = scale_or_matrix.value
        self.gstate.font_name = key.value

    def ps_stringwidth(self):
        text = self.pop_operand().value
        width, height = self.get_text_extent(text)
        self.push_operands(PSNumber(width), PSNumber(0))

    def ps_show(self):
        text = self.pop_operand().value
        x, y = self.gstate.get_device_coordinate(self.gstate.x, self.gstate.y)
        width, height = self.get_text_extent(text)
        height = height / (self.gstate.final_scaling)

        font_family = 'Helvetica'
        if 'italic' in self.gstate.font_name.lower():
            font_style = 'italic'
        else:
            font_style = 'normal'
        if 'bold' in self.gstate.font_name.lower():
            font_weight = 'bold'
        else:
            font_weight = 'normal'

        svg_text = text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')   # xml escape text
        self.svg.append('<text%s x="%f" y="%f" style="font-family:%s; font-style:%s; font-weight:%s; font-size:%fpx; fill: %s">%s</text>' %
                        (self.get_svg_class(), x, y, font_family, font_style, font_weight,
                         self.gstate.font_size * self.gstate.y_scale * self.gstate.final_scaling, self.gstate.get_svg_fill(), svg_text))

        # move current position to the right side of the text
        self.gstate.move_to(width, 0, relative=True)

    def ps_setlinecap(self):
        linecap = self.pop_operand().value
        # TODO: handle

    def ps_setlinejoin(self):
        linejoin = self.pop_operand().value
        # TODO: handle

    def ps_currentpoint(self):
        self.push_operands(PSNumber(self.gstate.x), PSNumber(self.gstate.y))

    def ps_currentgray(self):
        self.push_operand(PSNumber(self.gstate.currentgray))

    def ps_setgray(self):
        self.gstate.currentgray = self.pop_operand().value

    def ps_index(self):
        ' removes the non-negative integer n from the operand stack, counts down to the nth element from the top of the stack, and pushes a copy of that element on the stack.  '
        n = self.pop_operand()
        self.push_operand(self.operand_stack[-1 - n.value])

    def ps_dup(self):
        ' duplicates the top element on the operand stack. Note that dup copies only the object. The value of a composite object is not copied but is shared.  '
        self.push_operand(self.operand_stack[-1])

    def ps_copy(self):
        x = self.operand_stack[-1]
        # if top element on stack is non-negative integer
        if isinstance(x, PSNumber) and type(x.value) in [int, long] and x.value >= 0:
            n = int(self.pop_operand().value)
            if n > 0:
                elements = self.pop_operands(n)
                self.push_operands(*(elements + elements))
        else:
            # shallow-copy obj1 into obj2
            obj1, obj2 = self.pop_operands(2)
            obj2.copy_from(obj1)
            self.push_operand(obj2)

    def ps_pop(self):
        self.pop_operand()

    def ps_roll(self):
        ' performs a circular shift of the objects anyn-1 through any0 on the operand stack by the amount j. Positive j indicates upward motion on the stack, whereas negative j indicates downward motion. '
        j = self.pop_operand().value
        n = self.pop_operand().value
        objects = self.pop_operands(n)
        objects = [objects[(i - j + n) % n] for i in range(n)]  # roll j steps
        self.push_operands(*objects)

    def ps_exch(self):
        ' exchanges the top two elements on the operand stack. '
        a, b = self.pop_operands(2)
        self.push_operands(b, a)

    def ps_gsave(self):
        self.gstate_stack.append(self.gstate.copy())
        self.gstate = self.gstate_stack[-1]

    def ps_grestore(self):
        self.gstate_stack.pop()
        self.gstate = self.gstate_stack[-1]

    def ps_getinterval(self):
        array, index, count = self.pop_operands(3)
        new_array = PSArray(array.as_list(), array.executable)
        new_array.first = index.value
        new_array.last = index.value + count.value - 1
        self.push_operand(new_array)

    def ps_array(self):
        length = self.pop_operand().value
        self.push_operand(PSArray([None]*length, executable=False))

    def ps_length(self):
        x = self.pop_operand()
        self.push_operand(PSNumber(len(x.value)))

    def ps_put(self):
        array, index, value = self.pop_operands(3)
        array[index.value] = value

    def ps_aload(self):
        ' successively pushes all n elements of array or packedarray on the operand stack (where n is the length of the operand), and finally pushes the operand itself.  '
        array = self.pop_operand()
        assert(isinstance(array, PSArray))
        self.push_operands(*(array.as_list() + [array]))

    def ps_cvi(self):
        ' convert to integer) takes an integer, real, or string object from the stack and produces an integer result. '
        value = int(self.pop_operand().value)
        self.push_operand(PSNumber(value))

    def ps_idiv(self):
        ' divides int1 by int2 and returns the integer part of the quotient, with any fractional part discarded. Both operands of idiv must be integers and the result is an integer. '
        a, b = [int(x.value) for x in self.pop_operands(2)]
        self.push_operand(PSNumber(a / b))

    def ps_div(self):
        ' divides num1 by num2, producing a result that is always a real even if both operands are integers. '
        a, b = [float(x.value) for x in self.pop_operands(2)]
        self.push_operand(PSNumber(a / b))

    def ps_add(self):
        ' returns the sum of num1 and num2.  '
        num1, num2 = self.pop_operands(2)
        self.push_operand(PSNumber(num1.value + num2.value))

    def ps_sub(self):
        ' difference returns the result of subtracting num2 from num1. If both operands are integers and the result is within integer range, the result is an integer. Otherwise, the result is a real. '
        num1, num2 = self.pop_operands(2)
        self.push_operand(PSNumber(num1.value - num2.value))

    def ps_mul(self):
        num1, num2 = self.pop_operands(2)
        self.push_operand(PSNumber(num1.value * num2.value))

    def ps_neg(self):
        self.push_operand(PSNumber(-self.pop_operand().value))

    def ps_bind(self):
        ##x = self.operand_stack[-1]
        ##print 'before:', x, 'after:', self.bind_helper(x)
        self.push_operand(self.bind_helper(self.pop_operand()))


    def get_standard_encoding_names(self):
        standard_encoding = '''/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /space /exclam /quotedbl /numbersign
         /dollar /percent /ampersand /quoteright /parenleft /parenright /asterisk /plus
         /comma /hyphen /period /slash /zero /one /two /three /four /five /six /seven
         /eight /nine /colon /semicolon /less /equal /greater /question /at /A /B /C /D
         /E /F /G /H /I /J /K /L /M /N /O /P /Q /R /S /T /U /V /W /X /Y /Z /bracketleft
         /backslash /bracketright /asciicircum /underscore /quoteleft /a /b /c /d /e /f
         /g /h /i /j /k /l /m /n /o /p /q /r /s /t /u /v /w /x /y /z /braceleft /bar
         /braceright /asciitilde /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /exclamdown /cent /sterling /fraction /yen /florin /section /currency
         /quotesingle /quotedblleft /guillemotleft /guilsinglleft /guilsinglright /fi /fl
         /.notdef /endash /dagger /daggerdbl /periodcentered /.notdef /paragraph /bullet
         /quotesinglbase /quotedblbase /quotedblright /guillemotright /ellipsis /perthousand
         /.notdef /questiondown /.notdef /grave /acute /circumflex /tilde /macron /breve
         /dotaccent /dieresis /.notdef /ring /cedilla /.notdef /hungarumlaut /ogonek /caron
          /emdash /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
         /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /AE /.notdef
         /ordfeminine /.notdef /.notdef /.notdef /.notdef /Lslash /Oslash /OE /ordmasculine
         /.notdef /.notdef /.notdef /.notdef /.notdef /ae /.notdef /.notdef /.notdef
         /dotlessi /.notdef /.notdef /lslash /oslash /oe /germandbls /.notdef /.notdef
         /.notdef /.notdef'''
        return PSArray([PSLiteralName(x[1:]) for x in standard_encoding.split()],
                       executable=False)

    def get_ISO_latin1_encoding_names(self):
        encoding = '''/.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
            /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
            /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
            /.notdef /.notdef /.notdef /.notdef /.notdef /space /exclam /quotedbl /numbersign
            /dollar /percent /ampersand /quoteright /parenleft /parenright /asterisk /plus
            /comma /minus /period /slash /zero /one /two /three /four /five /six /seven
             /eight /nine /colon /semicolon /less /equal /greater /question /at /A /B /C /D
            /E /F /G /H /I /J /K /L /M /N /O /P /Q /R /S /T /U /V /W /X /Y /Z /bracketleft
            /backslash /bracketright /asciicircum /underscore /quoteleft /a /b /c /d /e /f /g
            /h /i /j /k /l /m /n /o /p /q /r /s /t /u /v /w /x /y /z /braceleft /bar /braceright
            /asciitilde /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
            /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef /.notdef
            /dotlessi /grave /acute /circumflex /tilde /macron /breve /dotaccent /dieresis
            /.notdef /ring /cedilla /.notdef /hungarumlaut /ogonek /caron /space /exclamdown
            /cent /sterling /currency /yen /brokenbar /section /dieresis /copyright /ordfeminine
            /guillemotleft /logicalnot /hyphen /registered /macron /degree /plusminus
            /twosuperior /threesuperior /acute /mu /paragraph /periodcentered /cedilla
            /onesuperior /ordmasculine /guillemotright /onequarter /onehalf /threequarters
            /questiondown /Agrave /Aacute /Acircumflex /Atilde /Adieresis /Aring /AE /Ccedilla
            /Egrave /Eacute /Ecircumflex /Edieresis /Igrave /Iacute /Icircumflex /Idieresis
            /Eth /Ntilde /Ograve /Oacute /Ocircumflex /Otilde /Odieresis /multiply /Oslash
            /Ugrave /Uacute /Ucircumflex /Udieresis /Yacute /Thorn /germandbls /agrave
            /aacute /acircumflex /atilde /adieresis /aring /ae /ccedilla /egrave /eacute /ecircumflex
            /edieresis /igrave /iacute /icircumflex /idieresis /eth /ntilde /ograve /oacute
            /ocircumflex /otilde /odieresis /divide /oslash /ugrave /uacute /ucircumflex /udieresis /yacute /thorn /ydieresis'''
        return PSArray([PSLiteralName(x[1:]) for x in encoding.split()],
                       executable=False)


class PSFromAbcInterpreter(PSInterpreter):
    pass
##    def __init__(self, final_scaling=1.0):
##        super(PSFromAbcInterpreter, self).__init__(final_scaling)
##        self.names = set()
##
##    def lookup(self, ps_name):
##        self.names.add(str(ps_name))
##        result = super(PSFromAbcInterpreter, self).lookup(ps_name)
##        return result
##
##    def ps_hd(self):
##        x, y = self.pop_operands(2)
##        self.dict_stack[-1]['x'] = x
##        self.dict_stack[-1]['y'] = y
##
##    def ps_sd(self):
##        height = self.pop_operand()
##
##    def ps_su(self):
##        height = self.pop_operand()
##
##    def ps_bm(self):
##        a, b, c, d, e = self.pop_operands(5)

##    def ps_hl(self):
##        x, y = self.pop_operands(2)
##
##    def ps_staff(self):
##        _ = self.pop_operands(4)
##
##    def ps_bar(self):
##        _ = self.pop_operands(3)
##
##    def ps_tclef(self):
##        _ = self.pop_operands(2)
##
##    def ps_dt(self):
##        pass

# ---------------------- code specific to parsing of abcm2ps output: --------------------------------

class Abcm2psOutputParser(object):
    def __init__(self):
        super(Abcm2psOutputParser, self).__init__()
        self.currently_processing = False

    def _simplify_postscript(self, text):
        # make a few changes so that the postscript interpreter will be able to interpret the PS code
        text = re.sub(r'(?s)/Error<<.*?>>definefont pop', '', text)
        text = re.sub(r'(?s)/mkfont-utf8.*?definefont pop}bind def', '', text)
        text = re.sub(r'(?s)/ExtraFont 10 dict begin.*?definefont pop', '', text)
        #i = text.index('FontMatrix')
        #print text[i-100:i+100]
        #a=b

        text = re.sub(r'(?s)(/mkfont(ext)?([01]|-utf8).*?!)', '', text)
        text = re.sub('(mkfont(ext)?([01]|-utf8))', 'def', text)
        text = re.sub('Times-Roman([01]|-utf8)',  'Times', text)
        text = re.sub('Times-Bold([01]|-utf8)',   'Times-Bold', text)
        text = re.sub('Times-Italic([01]|-utf8)', 'Times-Italic', text)
        # change the font scaling in the time signature from 1.2 x 1 to 1x1
        s1 = '/tsig{\tM gsave/Times-Bold 16 selectfont 1.2 1 scale\r\n\t0 1 RM currentpoint 3 -1 roll showc\r\n\t12 add M showc grestore}!'
        s2 = '/tsig{\tM /Times-Bold 16 selectfont 1.0 1 scale\r\n\t0 1 RM currentpoint 3 -1 roll showc\r\n\t12 add M showc }!'
        text = text.replace(s1, s2)
        return text

    def ps_file_to_svg(self, ps_filepath, interpreter_filepath, scale_factor=1.0, force_interpret_all_ps_code=False):
        #print self.currently_processing
        #print encoding, ps_filepath
        self.currently_processing = True
        start_time = datetime.now()

        try:
            scale_factor = 4/3.0
            encoding = 'latin-1'
            text = codecs.open(ps_filepath, 'r', encoding).read()
            text = self._simplify_postscript(text)

            preamble_ps, song_ps = text.split('%%EndSetup')

            full_run = False or not interpreter_filepath or not os.path.exists(interpreter_filepath)
            if full_run or force_interpret_all_ps_code:
                interpreter = PSFromAbcInterpreter()
                interpreter.gstate.final_scaling = scale_factor
                interpreter.interpret(preamble_ps)
                if full_run and interpreter_filepath:
                    pickle.dump(interpreter, open(interpreter_filepath, 'wb'), pickle.HIGHEST_PROTOCOL)
            else:
                interpreter = pickle.load(open(interpreter_filepath, 'rb'))
                #print 'read-time', (datetime.now() - start_time).microseconds/1000
                interpreter.gstate.final_scaling = scale_factor
            t = datetime.now()
            interpreter.interpret(song_ps)
            print 'interpret time: ', (datetime.now() - t).microseconds/1000

            ##l = [(v, k) for (k, v) in interpreter.time_stats.items()]
            ##for v, k in sorted(l):
            ##    print '%s (%s): \t%s' % (k, interpreter.count_stats[k], v/1000)
        finally:
            self.currently_processing = False

        svg = ('<?xml version="1.0" standalone="no"?>\n' +
             '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n' +
             '<svg width="1060px" height="1500px" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n%s\n</svg>\n') % '\n'.join(interpreter.svg)
        return svg

def profile_func():
    for i in range(6):
        ps_file_to_image(r'cache\temp2.ps')

if __name__ == "__main__":
    p = Abcm2psOutputParser()
    svg = p.ps_file_to_svg(r'Out.ps', '', scale_factor=1.5)
    #svg = ps_file_to_image(r'cache\temp.ps', scale_factor=1.5)
    codecs.open('output.html', 'w', 'latin-1').write(svg)
    ##import cProfile
    ##cProfile.run('profile_func()', 'profilerdata.dat')

