# Svgrenderer.py contains the code to display a abc svg file produced by
# abcm2ps onto the musicscorepanel window.

# There are two main classes: SvgPage and SvgRenderer.
# The object for SvgRenderer self.renderer  is created in the MainFrame class
# of easy_abc.py # during initialization. The object for SvgPage, called page,
# is created inside SvgRenderer.
#
# There are two indirect calls to SvgRenderer from easy_abc.py. The function
# svg_to_page is called from render_page in UpdateMusicPane in easy_abc.py
# This puts the contents of the svg files into a python dictionary called
# self.page[page_index] and returns it to the variable page in UpdateMusicPane
# in easy_abc.py. The second call to render.draw() is called indirectly from
# MusicScorePanel when an EVT_PAINT event is processed.
#
# page.notes[] (also called self.notes[] in  SvgPage) is used to match
# the notes in the music pane with the text in the abc file. The
# contents of page.notes[] are filled while the module is drawing
# each element on the bitmap using the method draw_svg_element.

# 1.3.6.3 [JWDJ] Fixed drawing problems with abcm2ps version 8.7.6


import xml.etree.ElementTree
import xml.etree.cElementTree as ET
from collections import defaultdict, deque, namedtuple
import re
import wx
import math
import traceback
from datetime import datetime

# 1.3.6.2 [JWdJ] 2015-02-12 tags evaluated only once
svg_namespace = 'http://www.w3.org/2000/svg'
use_tag = '{%s}use' % svg_namespace
abc_tag = '{%s}abc' % svg_namespace
path_tag = '{%s}path' % svg_namespace
tspan_tag = '{%s}tspan' % svg_namespace
group_tag = '{%s}g' % svg_namespace
xlink_namespace = 'http://www.w3.org/1999/xlink'
href_tag = '{%s}href' % xlink_namespace

css_comment_re = re.compile(r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)')
css_class_re = re.compile(r'(?m)^\s*\.(?P<class>\w*)\s*\{(?P<props>[^}]*)}')
css_prop_re = re.compile(r'(?P<name>[\w\-]*)\s*:\s*(?P<value>[^;}]*)')

def try_convert_to_float(v):
    try:
        return float(v)
    except ValueError:
        return v

def pop_many(list_obj, n):
    return [list_obj.popleft() for i in range(n)]

def flatten(L):
    if isinstance(L,list):
        return sum(map(flatten,L))
    else:
        return L

class SvgElement(object):
    def __init__(self, name, attributes, children):
        self.name = name              # the name of the svg element (excluding the namespace), eg. 'g', 'circle', 'ellipse'
        self.attributes = attributes  
        self.children = children

    def tree_iter(self):
        yield self
        for child in self.children:
            for c in child.tree_iter():
                yield c

# 1.3.6.2 [JWdJ] 2015-02-22 introduced SvgPage for better handling of multiple pages.
 
# An abc tune may convert into several svg files in order to display all the pages.
# The class contains the function parse_element which performs an initial pass through
# the svg files creating a dictionary for all the <def> and <g> 's that occur in the
# files and storing them in id_to_element. This will be used by draw_svg_element in
# SvgRenderer when it performs a second pass through the files and draws the graphics
# into a bitmap. The <defs> include instructions on how to draw notes, rests, clefs,
# etc. The <g>'s group graphical objects which share the same fill, colour and other
# options. These groups and defs are accessed through the <use> tag in the svg file.

NoteData = namedtuple('NoteData', 'note_type row col x y width height')

class SvgPage(object):
    def __init__(self, renderer, svg):
        self.renderer = renderer
        self.svg = svg
        self.svg_width, self.svg_height = 0.0, 0.0
        self.id_to_element = {}
        self.base_color = 'black'
        self.notes = []
        self.notes_in_row = None
        self.selected_indices = set()
        self.scale = 1.0
        self.index = -1
        if svg is None:
            self.root_group = SvgElement('g', {}, [])
        else:
            # 1.3.6.2 [JWdJ] 2015-02-14 width and height in inches is useless, use viewbox instead
            viewbox = self.svg.get('viewBox')
            if viewbox:
                m = self.renderer.viewbox_re.match(viewbox)
                if m:
                    self.svg_width, self.svg_height = float(m.group(1)), float(m.group(2))
            else:
                # 1.3.6.5 [JWdJ] 2015-11-05 newer versions abcm2ps no longer have viewBox but do specify width and height in pixels
                width_in_pixels = self.svg.get('width')
                m = self.renderer.float_px_re.match(width_in_pixels)
                if m:
                    self.svg_width = float(m.group(1))

                height_in_pixels = self.svg.get('height')
                m = self.renderer.float_px_re.match(height_in_pixels)
                if m:
                    self.svg_height = float(m.group(1))

            self.process_xml_tree()
            self.id_to_element = {}
            self.class_attributes = {}
            self.notes_in_row = {} # 1.3.6.3 [JWDJ] contains for each row of abctext note information
            children = [c for c in self.parse_elements(self.svg, {}) if c.name not in ['defs','style']]
            self.root_group = SvgElement('g', {}, children)

    def parse_attributes(self, element, parent_attributes):
        attributes = parent_attributes.copy()
        if 'transform' in attributes:  # don't inherit transform
            del attributes['transform']
        if 'desc' in attributes:  # don't inherit desc
            del attributes['desc']
        class_name = element.attrib.get('class')
        if class_name:
            class_attr = self.class_attributes.get(class_name, {})
            attributes.update(class_attr)
        # 1.3.6.5 [JWdJ] 2015-11-05 added parsing style property
        style = element.attrib.get('style')
        if style:
            attributes.update(self.parse_css_props(style))
        attributes.update(element.attrib)
        return attributes

    def parse_css_props(self, props):
        attributes = {}
        for prop_match in css_prop_re.finditer(props):
            prop_name = prop_match.group('name')
            prop_value = prop_match.group('value')
            attributes[prop_name] = prop_value
        return attributes

    def parse_css(self, css):
        # css = css_comment_re.sub(css, '') # remove comments
        for match in css_class_re.finditer(css):
            class_name = match.group('class')
            props = match.group('props')
            self.class_attributes[class_name] = self.parse_css_props(props)

    def parse_elements(self, elements, parent_attributes):
        result = []
        for element in elements:
            name = element.tag.replace('{%s}' % svg_namespace, '')
            attributes = self.parse_attributes(element, parent_attributes)
            if name in ['g', 'defs']:
                # 1.3.6.3 [JWDJ] 2015-3 use list(element) because getchildren is deprecated
                children = self.parse_elements(list(element), attributes)
            else:
                children = []

            if name == 'style' and attributes.get('type') == 'text/css':
                self.parse_css(element.text)
            else:
                svg_element = SvgElement(name, attributes, children)
                #if name == 'path':
                #    svg_element.path = self.parse_path(element.attrib['d'])
                if name == 'abc':
                    note_type = element.get('type')
                    row, col = int(element.get('row')), int(element.get('col'))
                    x, y, width, height = [float(element.get(x)) for x in ('x', 'y', 'width', 'height')]
                    note_data = NoteData(note_type, row, col, x, y, width, height)
                    notes_in_row = self.notes_in_row.get(row, None)
                    if notes_in_row is None:
                        self.notes_in_row[row] = [note_data]
                    else:
                        notes_in_row.append(note_data)

                if name == 'text':
                    text = u''
                    # 1.3.6.3 [JWDJ] 2015-3 fixes !sfz! (z in sfz was missing)
                    #for e in element.iter():
                    #    print e.text
                    #    if e.tag == tspan_tag:
                    #        text = text + (e.text or '')
                    for t in element.itertext():
                        text += t

                    text = text.replace('\n', '')
                    ##text = text.replace('(= )show ', ' = ')  # Temporary work-around for abcm2ps6.3.3 bug
                    svg_element.attributes['text'] = text
                element_id = element.attrib.get('id')
                if element_id:
                    self.id_to_element[element_id] = svg_element
                result.append(svg_element)
        return result

    def process_xml_tree(self):
        self.scale = 1.0
        scale_found = False

        # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
        self.base_color = self.svg.attrib.get('color', self.base_color)

        # each time a <desc> element is seen, find its next sibling (which is not a defs element) and set the description text as a 'desc' attribute
        for element in self.svg.getiterator():
            if not scale_found:
                transform = element.get('transform')
                if transform and element.tag == group_tag:
                    m = self.renderer.scale_re.match(transform)
                    if m:
                        try:
                            s = float(m.group(1))
                            scale_found = True
                            if 0.2 < s <= 3.0:
                                self.scale = s
                        except ValueError:
                            pass

            desc = None
            # last_desc = None
            #Not selection does not work properly as structure of svg file as changed.
            last_e_use = []
            # 1.3.6.3 [JWDJ] 2015-3 use iter() because getchildren is deprecated
            for e in element.iter():
                href = e.get(href_tag)
                if e.tag == abc_tag and e.get('type') in ['N', 'R']: #, 'B']:  # if note/rest meta-data
                    atype = e.get('type')
                    row, col = int(e.get('row')), int(e.get('col'))
                    x, y, width, height = [float(e.get(x)) for x in ('x', 'y', 'width', 'height')]
                    desc = (atype, row, col, x, y, width, height)
                    last_desc = desc
                    for e_use in last_e_use:
                        e_use.set('desc', desc)
                    last_e_use = []
#                elif desc and (e.tag == use_tag and href != '#hl' or
#                               e.tag == path_tag and desc[0] == 'B'):
#                    e.set('desc', desc)
#                    desc = None
#                elif href and e.tag == use_tag and href in ('#hl','#hl1','#hl2','#hd','#Hd','#HD','#HDD','#breve','#longa'):
#                    e.set('desc', last_desc)
                elif desc and (e.tag == use_tag and href != '#hl'):
                    desc = None
                    last_e_use.append(e)
                elif href and e.tag == use_tag and href in ('#hl','#hl1','#hl2','#hd','#Hd','#HD','#HDD','#breve','#longa'):
                    last_e_use.append(e)
            # 1.3.6.2 [JWdJ] 2015-02-14 width and height already known through viewbox attribute
            #max_x = max(max_x, float(element.get('x', 0.0)))
            #max_y = max(max_y, float(element.get('y', 0.0)))
        #print 'max_y=', max_y, 'zoom=', self.zoom

        #self.svg_height = (max_y + 25) * self.scale    # the 25 is just some extra margin in case there is some line that goes beyond its starting position
        #self.svg_width  = (max_x + 25) * self.scale    # same thing here

    def hit_test(self, x, y, return_closest_hit=False):
        min_dist = 9999999
        closest_i = None
        for i, (xpos, ypos, abc_row, abc_col, desc) in enumerate(self.notes):
            dist = math.sqrt((x - xpos)**2 + (y - ypos)**2)
            if dist < min_dist and xpos >= x:
                min_dist = dist
                closest_i = i
            if dist < 9 * self.scale:
                return i
        if return_closest_hit:
            return closest_i
        return None

    def select_notes(self, selection_rect):
        self.selected_indices.clear()
        for i, (x, y, abc_row, abc_col, desc) in enumerate(self.notes):
            if selection_rect.Contains((x, y)):
                self.add_note_to_selection(i)
        if self.selected_indices:
            for i in range(min(self.selected_indices), max(self.selected_indices)):
                self.selected_indices.add(i)
        return self.selected_indices.copy()

    def clear_note_selection(self):
        self.selected_indices.clear()

    def add_note_to_selection(self, index):
        self.selected_indices.add(index)
        self.finalize_selection()

    def finalize_selection(self):
        # if one note in a chord has been selected, then select all of them (all notes with the identical ABC offset data)
        selected_offsets = set([self.notes[i][2:4] for i in self.selected_indices]) # [(row, col), ...]
        for i, (xpos, ypos, abc_row, abc_col, desc) in enumerate(self.notes):
            if (abc_row, abc_col) in selected_offsets:
                self.selected_indices.add(i)

    def draw(self, clear_background=True, dc=None):
        self.renderer.draw(self, clear_background, dc)


class SvgRenderer(object):
    def __init__(self, can_draw_sharps_and_flats):
        self.can_draw_sharps_and_flats = can_draw_sharps_and_flats
        self.path_cache = {}
        self.fill_cache = {}
        self.stroke_cache = {}
        self.transform_cache = {}
        self.renderer = wx.GraphicsRenderer.GetDefaultRenderer()
        self.path_part_re = re.compile(r'([-+]?\d+(\.\d+)?|\w|\s)')
        self.transform_re = re.compile(r'(\w+)\((.+?)\)')
        self.color_re = re.compile(r'color:(#[0-9a-f]{6})')
        self.scale_re = re.compile(r'scale\((.+?)\)')
        self.viewbox_re = re.compile(r'0 0 (\d+) (\d+)')
        self.float_px_re = re.compile(r'^(\d*(?:\.\d+))?px$')
        self.zoom = 2.0
        self.min_width = 1
        self.min_height = 1
        self.empty_page = SvgPage(self, None)
        self.buffer = None
        # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
        self.highlight_color = '#cc0000'
        self.default_transform = None
        self.update_buffer(self.empty_page)

    def update_buffer(self, page):
        width, height = max(self.min_width, page.svg_width * self.zoom), \
                        max(self.min_height, page.svg_height * self.zoom + 100)
        width, height = int(width), int(height)
        #if self.buffer:
        #    print (self.buffer.GetWidth(), self.buffer.GetHeight()), '->'
        #print (width, height), '->'
        if self.buffer:
            # if size has decreased by less than 250 pixels, then don't change size
            if 0 <= self.buffer.GetWidth() - width < 250:
                width = self.buffer.GetWidth()        
            if 0 <= self.buffer.GetHeight() - height < 250:
                height = self.buffer.GetHeight()
            # if size has increased, then resize and add some extra pixels so that we won't
            # have to resize quickly again if the note image grows just slightly
            if self.buffer.GetWidth() < width:
                width += 250
            if self.buffer.GetHeight() < height:
                height += 250
        
        if self.buffer is None or width != self.buffer.GetWidth() or height != self.buffer.GetHeight():            
            #print 'create new buffer!!!!!!!!', (width, height)
            self.buffer = wx.EmptyBitmap(width, height, 32)    

    def svg_to_page(self, svg):
        try:
            svg_xml = ET.fromstring(svg) # parse xml
            page = SvgPage(self, svg_xml)
            return page
        except:
            print 'warning:',
            traceback.print_exc()
            self.clear()
            raise

    def set_svg(self, svg, dc=None):
        try:
            page = self.svg_to_page(svg)

            self.start_time = datetime.now()
            self.update_buffer(page)
            self.draw(page, dc=dc)
            #t = datetime.now() - self.start_time
            ##if wx.Platform != "__WXGTK__":
            ##    print 'draw_time    \t', t.seconds*1000 + t.microseconds/1000
        except:
            print 'warning:',
            traceback.print_exc()
            self.clear()
            raise

    def clear(self):
        dc = wx.MemoryDC(self.buffer)        
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()

    def draw(self, page, clear_background=True, dc=None):
        dc = dc or wx.MemoryDC(self.buffer)
        ##print 'draw', self.buffer.GetWidth(), self.buffer.GetHeight()
        if clear_background:            
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()
        dc = wx.GraphicsContext.Create(dc)
        self.default_transform = dc.GetTransform()
        #self.set_fill(dc, 'white')
        #dc.DrawRectangle(0, 0, 1000, 1000)
        #self.default_matrix = dc.GetTransform()
        page.notes = []
        dc.PushState()
        dc.Scale(self.zoom, self.zoom)
        self.draw_svg_element(page, dc, page.root_group, False, page.base_color)
        #matrix = dc.CreateMatrix()
        #matrix.Scale(self.zoom, self.zoom)
        #matrix.Invert()
        #print self.zoom
        #dc.SetTransform(self.default_matrix)
        #dc.Scale(1, -1)
        dc.PopState()        

        # in order to reveal all the sensitive areas in the music pane,
        # change False to True in the next line.
        if False:
            dc.PushState()
            dc.Scale(self.zoom, self.zoom)
            print dc.GetTransform().Get()
            #dc.SetTransform(self.default_transform)
            for x, y, abc_row, abc_col, desc in page.notes:
                self.set_fill(dc, 'none')
                self.set_stroke(dc, 'red')            
                dc.DrawRoundedRectangle(x-6, y-6, 12, 12, 4)
            dc.PopState()     
            #print (x, y)
            
        #self.buffer.SaveFile('DC.png', wx.BITMAP_TYPE_PNG)

    def parse_path(self, svg_path):
        ''' Translates the path data in the svg file to instructions for drawing
            on the music pane.  
        '''
        # 1.3.6.3 [JWDJ] 2015-3 search cache once instead of twice
        path = self.path_cache.get(svg_path)
        if path is None:
            original_svg_path = svg_path
            svg_path = deque(try_convert_to_float(m[0]) for m in
                             self.path_part_re.findall(svg_path) if m[0].strip())
            path = self.renderer.CreatePath()
            last_cmd = None
            while svg_path:
                if type(svg_path[0]) is float:
                    cmd = last_cmd
                else:
                    cmd = svg_path.popleft()
                if cmd == cmd.lower():
                    curx, cury = path.GetCurrentPoint()

                if cmd == 'M':
                    x, y = pop_many(svg_path, 2)
                    path.MoveToPoint(x, y)
                elif cmd == 'm':
                    x, y = pop_many(svg_path, 2)
                    path.MoveToPoint(curx+x, cury+y)
                elif cmd == 'L':
                    x, y = pop_many(svg_path, 2)
                    path.AddLineToPoint(x, y)
                elif cmd == 'l':
                    x, y = pop_many(svg_path, 2)
                    path.AddLineToPoint(curx+x, cury+y)
                elif cmd == 'h':
                    x, = pop_many(svg_path, 1)
                    path.AddLineToPoint(curx+x, cury)
                elif cmd == 'H':
                    x, = pop_many(svg_path, 1)
                    path.AddLineToPoint(x, cury)
                elif cmd == 'v':
                    y, = pop_many(svg_path, 1)
                    path.AddLineToPoint(curx, cury+y)
                elif cmd == 'V':
                    y, = pop_many(svg_path, 1)
                    path.AddLineToPoint(curx, y)
                elif cmd == 'c':
                    cx1, cy1, cx2, cy2, x, y = pop_many(svg_path, 6)
                    path.AddCurveToPoint(curx+cx1, cury+cy1, curx+cx2, cury+cy2, curx+x, cury+y)
                elif cmd == 'C':
                    cx1, cy1, cx2, cy2, x, y = pop_many(svg_path, 6)
                    path.AddCurveToPoint(cx1, cy1, cx2, cy2, x, y)
                elif cmd == 'a':
                    rx, ry, xrot, large_arg_flac, sweep_flag, x, y = pop_many(svg_path, 7)
                    x += curx
                    y += cury
                    # if sweep_flag and rx == ry:
                    #    path.AddArc(x, y, rx, startAngle, endAngle, clockwise)
                    # else:
                    path.AddEllipse(x-rx*2, y-ry*2, rx*2, ry*2)
                elif cmd == 'z':
                    path.CloseSubpath()
                else:
                    raise Exception('unknown svg command "%s" in path: %s' % (cmd, original_svg_path))
                last_cmd = cmd
            self.path_cache[original_svg_path] = path
        return path

    # 1.3.6.2 [JWdJ] not used 
    # def get_transform(self, svg_transform):
    #     if svg_transform in self.transform_cache:
    #         matrix = self.transform_cache[svg_transform]
    #     else:
    #         matrix = self.renderer.CreateMatrix()
    #         for t, args in reversed(self.transform_re.findall(svg_transform or '')):
    #             args = map(float, re.split(',\s*|\s+', args))
    #             old_matrix = matrix
    #             matrix = self.renderer.CreateMatrix()
    #             if t == 'translate':
    #                 matrix.Translate(*args)
    #             elif t == 'rotate':
    #                 if wx.Platform == "__WXMSW__":
    #                     angle = args[0]
    #                 else:
    #                     angle = math.radians(args[0])
    #                 #matrix.Translate(-4,  0)
    #                 #matrix.Rotate(angle)
    #             elif t == 'scale':
    #                 if len(args) == 1:
    #                     args *= 2
    #                 matrix.Scale(*args)
    #             elif t == 'matrix':
    #                 matrix.Set(*args)
    #             matrix.Concat(old_matrix)
    #         self.transform_cache[svg_transform] = matrix
    #
    #     return matrix

    def do_transform(self, dc, svg_transform):                
        for t, args in self.transform_re.findall(svg_transform or ''):
            args = map(float, re.split(',\s*|\s+', args))            
            if t == 'translate':
                dc.Translate(*args)                    
            elif t == 'rotate':                
                dc.Rotate(math.radians(args[0]))
            elif t == 'scale':
                if len(args) == 1:
                    args *= 2
                dc.Scale(*args)                
            elif t == 'matrix':                
                dc.ConcatTransform(dc.CreateMatrix(*args))            
        
    def set_fill(self, dc, svg_fill):
        # 1.3.6.3 [JWDJ] 2015-3 search cache once instead of twice
        brush = self.fill_cache.get(svg_fill)
        if brush is None:
            if svg_fill == 'none':
                brush = self.renderer.CreateBrush(wx.NullBrush)
            elif svg_fill == 'white':
                brush = self.renderer.CreateBrush(wx.WHITE_BRUSH)
            elif svg_fill == 'black':
                brush = self.renderer.CreateBrush(wx.BLACK_BRUSH)
            elif svg_fill.startswith('#'): # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
                brush = self.renderer.CreateBrush(wx.Brush(svg_fill, wx.SOLID))
            else:
                brush = self.renderer.CreateBrush(wx.Brush(wx.NamedColour(svg_fill), wx.SOLID))
            self.fill_cache[svg_fill] = brush
        dc.SetBrush(brush)

    def set_stroke(self, dc, svg_stroke, line_width=1.0, linecap='butt', dasharray=None):
        #Patch to avoid to have too dim lines for staff, bar, note stems
        if line_width < 1:
            line_width = 1.0
        #End Patch
        if dasharray:
            # convert from something like "5,5" to (5,5)
            dasharray = tuple([int(x.strip()) for x in dasharray.split(',')])
        # 1.3.6.3 [JWDJ] 2015-3 search cache once instead of twice
        pen = self.stroke_cache.get((svg_stroke, line_width, dasharray))
        if pen is None:
            if svg_stroke == 'none':
                pen = self.renderer.CreatePen(wx.NullPen)
            else:                
                wxpen = wx.Pen(wx.NamedColour(svg_stroke), line_width)                
                if linecap == 'butt':
                    wxpen.SetCap(wx.CAP_BUTT)
                elif linecap == 'round':
                    wxpen.SetCap(wx.CAP_ROUND)
                else:
                    raise Exception('linecap %s not supported yet' % linecap)
                if dasharray:
                    # 1.3.6.3 [JWDJ] 2015-3 dasharray is always a tuple, never a str or unicode
                    #if type(dasharray) in (str, unicode):
                    #    dasharray = [int(x.strip()) for x in dasharray.split(',')]
                    wxpen.SetDashes(list(dasharray))
                    wxpen.SetStyle(wx.USER_DASH)
                wxpen.SetJoin(wx.JOIN_MITER)
                pen = self.renderer.CreatePen(wxpen)
            self.stroke_cache[(svg_stroke, line_width, dasharray)] = pen
        dc.SetPen(pen)

    def zoom_matrix(self, matrix):
        sm = self.renderer.CreateMatrix()
        sm.Scale(self.zoom, self.zoom)
        sm.Concat(matrix)
        # on Mac OSX the default matrix is not equal to the identity matrix so we need to apply it too:
        om = self.renderer.CreateMatrix(*self.default_matrix.Get())
        om.Concat(sm)
        return om


    def draw_svg_element(self, page, dc, svg_element, highlight, current_color):
        ''' This is the main engine for converting the svg items in the svg file into graphics
        displayed in the music pane. The book SVG Essentials by J. David
        Eisenberg describes all the elements used (eg. g, use, ellipse, ...)
        In addition there is an item <abc> which contains annotation and
        information for matching the graphics element with the note in the
        abc file. The <abc> element id indicates the type of object.
        (N - notes, R - rest, B - bar line, b - beam joining notes, e - note flag,
         M - time signature, K - key signature, 'c' octave shift in clef)
        '''

        name = svg_element.name
        if name == 'defs':
            return

        attr = svg_element.attributes
        transform = svg_element.attributes.get('transform')

        if transform:
            dc.PushState()
            self.do_transform(dc, transform)

        # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
        if name == 'g':
            style = attr.get('style')
            if style:
                m = self.color_re.match(style)
                if m:
                    current_color = m.group(1).upper()

            # 1.3.6.2 [JWdJ] 2015-02-14 Only 'g' and 'defs' have children
            for child in svg_element.children:
                self.draw_svg_element(page, dc, child, highlight, current_color)

        # if something is going to be drawn, prepare
        else:
            # 1.3.6.3 [JWDJ] 2015-3 Only set fill if fill is specified (where 'none' is not the same as None)
            fill = attr.get('fill')
            if fill is None and name=='circle':
                fill = current_color # 1.3.6.4 To draw the two dots in !segno!
            if fill is not None:
                if fill == 'currentColor':
                    fill = current_color

                if highlight and fill != 'none':
                    fill = self.highlight_color

                self.set_fill(dc, fill)

            stroke = attr.get('stroke', 'none')
            if stroke == 'currentColor':
                stroke = current_color

            if highlight and stroke != 'none':
                stroke = self.highlight_color

            self.set_stroke(dc, stroke, float(attr.get('stroke-width', 1.0)), attr.get('stroke-linecap', 'butt'), attr.get('stroke-dasharray', None))
            
        #print 'setmatrix', matrix.Get(), '[%s]' % attr.get('transform', '')
                
        # 1.3.6.2 [JWdJ] 2015-02-14 Process most common names first (path, ellipse, use)
        if name == 'path':
            path = self.parse_path(attr['d'])
            #Patch from Seymour regarding Debian 7.0 to be tested on other platform
            #if wx.Platform != "__WXMAC__": #At least the SetPen has some side effect on Mac didn't tried on other. So do not apply Seymour Patch if under Mac
            #    dc.SetPen(wx.Pen('#000000', 1, wx.SOLID))
            #End of patch
            dc.DrawPath(path, wx.WINDING_RULE)
        elif name == 'ellipse':
            cx, cy, rx, ry = attr.get('cx', 0), attr.get('cy', 0), attr['rx'], attr['ry']
            cx, cy, rx, ry = map(float, (cx, cy, rx, ry))
            path = dc.CreatePath()
            path.AddEllipse(cx-rx, cy-ry, rx*2, ry*2)
            dc.DrawPath(path)
        elif name == 'use':
            x, y = float(attr.get('x', 0)), float(attr.get('y', 0))
            element_id = attr[href_tag][1:]
            # abcm2ps specific:
            if 'desc' in svg_element.attributes and svg_element.attributes['desc']: ## and ('note' in svg_element.attributes['desc'] or
                                                 ##    'grace' in svg_element.attributes['desc']):
                desc = svg_element.attributes['desc']

                matrix_inv = self.renderer.CreateMatrix(*dc.GetTransform().Get())  #*self.get_transform(transform).Get())
                matrix_inv.Invert()
                matrix_inv.Concat(self.default_transform)   # the default transform on mac is not the identity matrix - the y-coordinates goes the other direction
                user_x, user_y = matrix_inv.TransformPoint(x, y)

                user_x *= self.zoom * page.scale**2 #0.75
                user_y *= self.zoom * page.scale**2 #0.75
                #print (user_x, user_y), ((desc[3] + desc[5] / 2) * self.scale, (desc[4] + desc[6] / 2) * self.scale)
                #user_x = (desc[3] + desc[5] / 2) * self.scale
                #user_y = (desc[4] + desc[6] / 2) * self.scale

                abc_row, abc_col = desc[1], desc[2]
                page.notes.append((user_x, user_y, abc_row, abc_col, desc))
                note_index = len(page.notes)-1
                if note_index in page.selected_indices:
                    highlight = True

            dc.PushState()
            dc.Translate(x, y)

            #if 'desc' in svg_element.attributes:
            #    print svg_element, svg_element.attributes['desc']
            self.draw_svg_element(page, dc, page.id_to_element[element_id], highlight, current_color)
            dc.PopState()

        elif name == 'text':
            text = attr['text']
            if not self.can_draw_sharps_and_flats:
                text = text.replace(u'\u266d', 'b').replace(u'\u266f', '#').replace(u'\u266e', '=')
            x, y = float(attr.get('x', 0)), float(attr.get('y', 0))            
            if attr.get('font-style') == 'italic':
                style = wx.FONTSTYLE_ITALIC
            else:
                style = wx.FONTSTYLE_NORMAL
            if attr.get('font-weight') == 'bold':                
                weight = wx.FONTWEIGHT_BOLD
            else:
                weight = wx.FONTWEIGHT_NORMAL
            font_size = int(round(float(attr.get('font-size', 12))*1))
            # 1.3.6.3 [JWDJ] 2015-3 bugfix: use correct font family
            font_face = ''
            svg_to_wx_font_family = {
                'serif': wx.FONTFAMILY_ROMAN,
                'sans-serif': wx.FONTFAMILY_SWISS,
                'monospace': wx.FONTFAMILY_MODERN,
                'bookman': wx.FONTFAMILY_ROMAN,
                'sans': wx.FONTFAMILY_SWISS, # should be 'sans-serif' (abcm2ps bug?)
            }

            svg_font_family = attr.get('font-family', 'serif').lower()
            font_family = svg_to_wx_font_family.get(svg_font_family)
            if font_family is None:
                font_family = wx.FONTFAMILY_DEFAULT
                font_face = svg_font_family # 1.3.6.4 [JWDJ] if font family is not known then assume it is a font face

            ##print repr(text), font_face, attr.get('font-size'), attr.get('font-weight')
            wxfont = wx.Font(font_size, font_family, style, weight, False, font_face, wx.FONTENCODING_DEFAULT)
            if '__WXMSW__' in wx.PlatformInfo:                
                wxfont.SetPixelSize((font_size, font_size))
                y += 1
            else:
                wxfont.SetPointSize(font_size)
            font = dc.CreateFont(wxfont, wx.NamedColour(attr.get('fill', 'black')))                
            dc.SetFont(font)
            (width, height, descent, externalLeading) = dc.GetFullTextExtent(text)                
            if attr.get('text-anchor') == 'middle':
                x -= width / 2                
            elif attr.get('text-anchor') == 'end':
                x -= width
            try:
                dc.DrawText(text, x, y-height+descent)                
            except wx.PyAssertionError:
                raise Exception(u'Could not draw text, text=%s, font=%s (%s / %s), size=%s, fill=%s, weight=%s, style=%s, x=%s, y=%s, height=%s, descent=%s, transform=%s' %
                                (repr(text), font_face, wxfont.GetFaceName(), wxfont.GetDefaultEncoding(), font_size,
                                attr.get('fill', 'black'),
                                attr.get('font-weight', '<none>'),
                                attr.get('font-style', '<none>'),
                                x, y, height, descent, dc.GetTransform().Get()))
                                
        elif name == 'rect':
            x, y, width, height = attr.get('x', 0), attr.get('y', 0), attr['width'], attr['height']
            if '%' in width:
                # 1.3.6.2 [JWdJ] 2015-02-12 Added for %%bgcolor
                if width == height == '100%':
                    x, y, width, height = map(float, (0, 0, self.buffer.GetWidth(), self.buffer.GetHeight()))
                else:
                    return
            else:
                x, y, width, height = map(float, (x, y, width, height))
            path = dc.CreatePath()
            path.MoveToPoint(x, y)
            path.AddLineToPoint(x+width, y)
            path.AddLineToPoint(x+width, y+height)
            path.AddLineToPoint(x, y+height)
            path.AddLineToPoint(x, y)
            dc.DrawPath(path)                     
        elif name == 'circle':
            cx, cy, r = map(float, (attr.get('cx', 0), attr.get('cy', 0), attr['r']))            
            path = dc.CreatePath()
            path.AddCircle(cx, cy, r)
            dc.DrawPath(path)     
        elif name == 'line':            
            x1, y1, x2, y2 = map(float, (attr['x1'], attr['y1'], attr['x2'], attr['y2']))            
            # 1.3.6.3 [JWDJ] 2015-3 Fill and stroke already have been set
            # self.set_fill(dc, 'none')
            # self.set_stroke(dc, stroke, float(attr.get('stroke-width', 1.0)), attr.get('stroke-linecap', 'butt'), attr.get('stroke-dasharray', None))
            # 1.3.6.3 [JWDJ] 2015-3 Fixes line in !segno!
            dc.DrawLines([(x1, y1), (x2, y2)])

        if transform:
            dc.PopState()

class MyApp(wx.App):
    def OnInit(self):
        self.SetAppName('EasyABC')
        return True

def matrix_to_str(m):
    return '(%s)' % ', '.join(['%.3f' % f for f in m.Get()])

if __name__ == "__main__":
    import os.path
    app = MyApp(0)

    buffer = wx.EmptyBitmap(200, 200, 32)
    dc = wx.MemoryDC(buffer)
    dc.SetBackground(wx.WHITE_BRUSH)
    dc.Clear()
    dc = wx.GraphicsContext.Create(dc)
    dc.SetBrush(dc.CreateBrush(wx.BLACK_BRUSH))
    print 'default matrix', dc.GetTransform().Get()
    import math
    original_matrix = dc.GetTransform()
    path = dc.CreatePath()
    path.AddEllipse(0, 20, 40, 20)
    path.MoveToPoint(0, 0)
    path.AddLineToPoint(10, 10)
    path.AddLineToPoint(20, 0)
    path.CloseSubpath()

    if wx.Platform == "__WXMSW__":
        a = 45
    else:
        a = math.radians(45)

    original = dc.CreateMatrix(*original_matrix.Get())
    om = dc.CreateMatrix(*original_matrix.Get())
    m0 = dc.CreateMatrix(); m0.Scale(0.5, 0.5)
    m1 = dc.CreateMatrix(); m1.Translate(150, 150)
    m2 = dc.CreateMatrix(); m2.Rotate(a)
    om.Concat(m0)
    om.Concat(m2)
    dc.SetTransform(om)
    dc.DrawPath(path)
    print 'new matrix', matrix_to_str(dc.GetTransform())
    om.Concat(m1)
    om.Concat(m0)
    dc.SetTransform(om)
    dc.DrawPath(path)
    print 'new matrix', matrix_to_str(dc.GetTransform())

    print '----'
    dc.SetTransform(original)    
    dc.Scale(0.5, 0.5)    
    dc.Translate(150, 150)
    dc.Rotate(math.radians(25))
    dc.Scale(0.5, 0.5)
    print 'new matrix', matrix_to_str(dc.GetTransform())
    
    buffer.SaveFile('dc_test_linux.png', wx.BITMAP_TYPE_PNG)
    if True:
        r = wx.GraphicsRenderer.GetDefaultRenderer()
        m1 = r.CreateMatrix(); m1.Scale(1.0, -1.0)
        m2 = r.CreateMatrix(); m2.Translate(50, 60)
        m1.Concat(m2)
        print m1.TransformPoint(100, 100)
        
        m1 = r.CreateMatrix(); m1.Scale(1.0, -1.0)
        m2 = r.CreateMatrix(); m2.Translate(50, 60)
        m2.Concat(m1)
        print m1.TransformPoint(100, 100) 
        
        renderer = SvgRenderer(True)
        #renderer.set_svg(open(os.path.join('abc', 'cache', 'temp_02e3f5d62f001.svg'), 'rb').read())
        renderer.buffer.SaveFile('test_output.png', wx.BITMAP_TYPE_PNG)    
        
