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


#import xml.etree.ElementTree
import xml.etree.cElementTree as ET
from collections import defaultdict, deque, namedtuple
import re
import wx
from math import hypot, radians, sqrt, pi
import traceback
from datetime import datetime
from wxhelper import wx_colour, wx_bitmap
import sys
PY3 = sys.version_info.major > 2
WX4 = wx.version().startswith('4')
WX41 = WX4 and not wx.version().startswith('4.0')

# 1.3.6.2 [JWdJ] 2015-02-12 tags evaluated only once
svg_namespace = 'http://www.w3.org/2000/svg'
svg_ns = '{%s}' % svg_namespace
#use_tag = '{%s}use' % svg_namespace
#abc_tag = '{%s}abc' % svg_namespace
#path_tag = '{%s}path' % svg_namespace
#tspan_tag = '{%s}tspan' % svg_namespace
#group_tag = '{%s}g' % svg_namespace
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
    return [list_obj.popleft() for _ in range(n)]

def flatten(value):
    if isinstance(value, list):
        return sum(map(flatten, value))
    return value

def parse_css_props(props):
    attributes = {}
    for prop_match in css_prop_re.finditer(props):
        prop_name = prop_match.group('name')
        prop_value = prop_match.group('value')
        attributes[prop_name] = prop_value
    return attributes


class SvgElement(object):
    def __init__(self, name, attributes, children):
        self.name = name              # the name of the svg element (excluding the namespace), eg. 'g', 'circle', 'ellipse'
        self.attributes = attributes
        self.children = children

    # 1.3.7.2 [JWDJ] not used
    # def tree_iter(self):
    #     yield self
    #     for child in self.children:
    #         for c in child.tree_iter():
    #             yield c

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
        self.notes_row_col = []
        self.notes_in_row = None
        self.selected_indices = set()
        self.scale = 1.0
        self.index = -1
        children = []
        if svg is not None:
            # 1.3.6.2 [JWdJ] 2015-02-14 width and height in inches is useless, use viewbox instead
            viewbox = svg.get('viewBox')
            if viewbox:
                m = self.renderer.viewbox_re.match(viewbox)
                if m:
                    self.svg_width, self.svg_height = float(m.group(1)), float(m.group(2))
            else:
                # 1.3.6.5 [JWdJ] 2015-11-05 newer versions abcm2ps no longer have viewBox but do specify width and height in pixels
                width_in_pixels = svg.get('width')
                m = self.renderer.float_px_re.match(width_in_pixels)
                if m:
                    self.svg_width = float(m.group(1))

                height_in_pixels = svg.get('height')
                m = self.renderer.float_px_re.match(height_in_pixels)
                if m:
                    self.svg_height = float(m.group(1))

            # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
            self.base_color = svg.attrib.get('color', self.base_color)
            self.id_to_element = {}
            self.class_attributes = {}
            self.notes_in_row = defaultdict(list) # 1.3.6.3 [JWDJ] contains for each row of abctext note information
            children = [c for c in self.parse_elements(svg, {}) if c.name not in ['defs', 'style']]

        self.indices_per_row_col = self.group_note_indices(self.notes_row_col)
        self.root_group = SvgElement('g', {}, children)

    def clear_notes(self):
        self.notes = []

    def group_note_indices(self, notes_row_col):
        indices_per_row_col = defaultdict(lambda: defaultdict(set))
        for i, (abc_row, abc_col) in enumerate(notes_row_col):
            indices_per_row_col[abc_row][abc_col].add(i)
        return indices_per_row_col

    def parse_attributes(self, element, parent_attributes):
        attributes = parent_attributes.copy()
        if 'transform' in attributes:  # don't inherit transform
            transform = attributes.get('transform')
            m = self.renderer.scale_re.match(transform)
            if m:
                try:
                    scale = float(m.group(1))
                    attributes['parent_scale'] = scale
                except ValueError:
                    pass
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
            attributes.update(parse_css_props(style))
        attributes.update(element.attrib)
        return attributes

    def parse_css(self, css):
        # css = css_comment_re.sub(css, '') # remove comments
        for match in css_class_re.finditer(css):
            class_name = match.group('class')
            props = match.group('props')
            self.class_attributes[class_name] = parse_css_props(props)

    def parse_elements(self, elements, parent_attributes):
        result = []
        last_e_use = []
        elementnames_with_children = ['g', 'defs']
        no_children = ()
        notes_row_col_append = self.notes_row_col.append
        for element in elements:
            name = element.tag.replace(svg_ns, '')
            attributes = self.parse_attributes(element, parent_attributes)
            if name in elementnames_with_children:
                # 1.3.6.3 [JWDJ] 2015-3 use list(element) because getchildren is deprecated
                children = self.parse_elements(list(element), attributes)
            else:
                children = no_children

            if name == 'style' and attributes.get('type') == 'text/css':
                self.parse_css(element.text)
            elif name == 'abc':
                note_type = element.get('type')
                row, col = int(element.get('row')), int(element.get('col'))
                scale = attributes.get('parent_scale', 1.0)
                if scale:
                    self.scale = scale # JWDJ: older version of abcm2ps use page scaling of 0.75

                x, y, width, height = [float(element.get(x)) for x in ('x', 'y', 'width', 'height')]

                note_data = NoteData(note_type, row, col, x, y, width, height)
                self.notes_in_row[row].append(note_data)
                # each time a <desc> element is seen, find its next sibling (which is not a defs element) and set the description text as a 'desc' attribute
                if note_type in ['N', 'R']: #, 'B']:  # if note/rest meta-data
                    last_row_col = (row, col)
                    desc = (note_type, row, col, x, y, width, height)
                    for e_use in last_e_use:
                        e_use.attributes['desc'] = desc
                        notes_row_col_append(last_row_col)
                last_e_use = []
            else:
                svg_element = SvgElement(name, attributes, children)
                element_id = element.attrib.get('id')
                if element_id:
                    self.id_to_element[element_id] = svg_element
                if name == 'text':
                    # 1.3.6.3 [JWDJ] 2015-3 fixes !sfz! (z in sfz was missing)
                    text = u''.join(element.itertext())
                    text = text.replace('\n', '')
                    svg_element.attributes['text'] = text
                elif name == 'use': # 1.3.7.0 [JWDJ] 2016-01-05 all use-elements without id attribute belong to abc-note
                    href = element.get(href_tag)
                    if href not in ['#hl', '#hl1', '#mrest']: # leave out horizontal lines through notes above and below the stafflines (and measure rest too since abcm2ps does not add abc tag for measure rest)
                        last_e_use.append(svg_element)
                result.append(svg_element)
        return result

    def hit_test(self, x, y, return_closest_hit=False):
        calc_dist = hypot
        hit_distance = 9 * self.scale
        if return_closest_hit:
            if not self.notes:
                return None
            def calc_dist_key(k):
                return calc_dist(x - k[1][0], y - k[1][1])
            index, note = min(enumerate(self.notes), key=calc_dist_key)
            return index
            #return min(enumerate(self.notes), key=lambda k: calc_dist(x - k[1][0], y - k[1][1]))[0]  # [0] is the index generated by enumerate()
        else:
            return next((i for i, (xpos, ypos, abc_row, abc_col, desc) in enumerate(self.notes) if calc_dist(x - xpos, y - ypos) < hit_distance), None)
        # min_dist = 9999999
        # closest_i = None
        # for i, (xpos, ypos, abc_row, abc_col, desc) in enumerate(self.notes):
        #     dist = calc_dist(x - xpos, y - ypos)
        #     #dist = math.sqrt((x - xpos)**2 + (y - ypos)**2)
        #     if dist < min_dist and xpos >= x:
        #         min_dist = dist
        #         closest_i = i
        #     if dist < hit_distance:
        #         return i
        # if return_closest_hit:
        #     return closest_i
        # return None

    def select_notes(self, selection_rect):
        in_selection = selection_rect.Contains
        #FAU wx.Rect Contains needs integer as coordinates
        #selected_offsets = set((abc_row, abc_col) for (x, y, abc_row, abc_col, desc) in self.notes if in_selection((x, y)))
        selected_offsets = set((abc_row, abc_col) for (x, y, abc_row, abc_col, desc) in self.notes if in_selection((int(x), int(y))))
        list_of_sets = [self.indices_per_row_col[row][col] for row, col in selected_offsets]
        selected_indices = set().union(*list_of_sets)
        if selected_indices:
            selected_indices = set(range(min(selected_indices), max(selected_indices) + 1))
        self.selected_indices = selected_indices
        return selected_indices

    def clear_note_selection(self):
        self.selected_indices.clear()

    def add_note_to_selection(self, index):
        x, y, selected_abc_row, selected_abc_col, desc = self.notes[index]
        # if one note in a chord has been selected, then select all of them (all notes with the identical ABC offset data)
        selected = self.indices_per_row_col[selected_abc_row][selected_abc_col]
        self.selected_indices = selected.union(self.selected_indices)

    def get_indices_for_row_col(self, row, col):
        return self.indices_per_row_col[row][col]

    def draw(self, clear_background=True, dc=None):
        self.renderer.draw(self, clear_background, dc)


class SvgRenderer(object):
    def __init__(self, can_draw_sharps_and_flats, highlight_color, highlight_follow_color = None):
        self.can_draw_sharps_and_flats = can_draw_sharps_and_flats
        self.path_cache = {}
        self.fill_cache = {}
        self.stroke_cache = {}
        self.transform_cache = {}
        self.renderer = wx.GraphicsRenderer.GetDefaultRenderer()
        self.path_part_re = re.compile(r'([-+]?\d+(\.\d+)?|\w|\s)')
        self.transform_re = re.compile(r'(\w+)\((.+?)\)')
        self.transform_split_re = re.compile(r',\s*|\s+')
        self.color_re = re.compile(r'color:(#[0-9a-f]{6})')
        self.style_re = re.compile(r'^(?P<key>[a-z-]+):(?P<value>.*)$')
        self.scale_re = re.compile(r'scale\((.+?)\)')
        self.viewbox_re = re.compile(r'0 0 (\d+) (\d+)')
        self.float_px_re = re.compile(r'^(\d*(?:\.\d+))?px$')
        self.font_re = re.compile(r'\bfont:(?:(?P<typeface>[a-z-]+) )?(?P<size>-?\d+(?:\.\d+)?(?:px|pt|em|ex|in|cm|mm|pc|%)?) (?P<family>[-\w]+)')
        self.zoom = 1.0
        self.min_width = 1
        self.min_height = 1
        self.empty_page = SvgPage(self, None)
        self.buffer = None
        # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
        self.highlight_color = highlight_color
        if highlight_follow_color:
            self.highlight_follow_color = highlight_follow_color
        else:
            self.highlight_follow_color = highlight_color
        self.highlight_follow = False
        self.default_transform = None
        #self.update_buffer(self.empty_page)
        if wx.Platform == "__WXMAC__":
            self.transform_point = self.transform_point_osx
        else:
            self.transform_point = self.transform_point_normal

    def destroy(self):
        if self.renderer:
            self.renderer = None # do not destroy!
            self.path_cache = None
            self.fill_cache = None
            self.stroke_cache = None
            self.transform_cache = None
        if self.buffer:
            self.buffer.Destroy()
            self.buffer = None
        self.default_transform = None

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
            self.buffer = wx_bitmap(width, height, 32)

    def svg_to_page(self, svg):
        try:
            svg_xml = ET.fromstring(svg) # parse xml
            page = SvgPage(self, svg_xml)
            return page
        except:
            # print('warning: %s' % traceback.print_exc())
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
            # print('warning: %s' % traceback.print_exc())
            self.clear()
            raise

    def clear(self):
        if self.buffer:
            dc = wx.MemoryDC(self.buffer)
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()

    def draw_notes(self, page, note_indices, highlight, dc=None, highlight_follow=False ):
        if not page.note_draw_info or not note_indices:
            return
        dc = dc or wx.MemoryDC(self.buffer)
        gc = wx.GraphicsContext.Create(dc)
        transform = gc.SetTransform
        if wx.Platform == "__WXGTK__":
            transform = gc.ConcatTransform
        gc.PushState()
        for element_id, current_color, matrix in [page.note_draw_info[i] for i in note_indices]:
            gc.PushState()
            transform(gc.CreateMatrix(*matrix))
            self.draw_svg_element(page, gc, page.id_to_element[element_id], highlight, current_color, {}, highlight_follow)
            gc.PopState()
        gc.PopState()

    def draw(self, page, clear_background=True, dc=None):
        dc = dc or wx.MemoryDC(self.buffer)
        ##print 'draw', self.buffer.GetWidth(), self.buffer.GetHeight()
        if clear_background:
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()
        #h = dc.Size[1] # for simulating OSX
        gc = wx.GraphicsContext.Create(dc)
        #gc.Translate(0, h) # for simulating OSX
        #gc.Scale(1, -1) # for simulating OSX

        self.default_transform = gc.GetTransform()
        page.clear_notes()
        page.note_draw_info = []
        gc.PushState()
        gc.Scale(self.zoom, self.zoom)
        self.draw_svg_element(page, gc, page.root_group, False, page.base_color, {})
        gc.PopState()

        # in order to reveal all the sensitive areas in the music pane,
        # change False to True in the next line.
        if False:
            gc.PushState()
            gc.Scale(self.zoom, self.zoom)
            for x, y, abc_row, abc_col, desc in page.notes:
                x /= self.zoom
                y /= self.zoom
                self.set_fill(gc, 'none')
                self.set_stroke(gc, 'red')
                gc.DrawRoundedRectangle(x-6, y-6, 12, 12, 4)
            gc.PopState()

    def parse_path(self, svg_path_str):
        ''' Translates the path data in the svg file to instructions for drawing
            on the music pane.
        '''
        # 1.3.6.3 [JWDJ] 2015-3 search cache once instead of twice
        path = self.path_cache.get(svg_path_str)
        if path is None:
            svg_path = deque(try_convert_to_float(m[0]) for m in
                             self.path_part_re.findall(svg_path_str) if m[0].strip())
            path = self.renderer.CreatePath()
            last_cmd = None
            while svg_path:
                if type(svg_path[0]) is float:
                    cmd = last_cmd
                else:
                    cmd = svg_path.popleft()
                if cmd.islower():
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
                    rx, ry, xrot, large_arg_flag, sweep_flag, x, y = pop_many(svg_path, 7)
                    next_cmd = svg_path[0] if svg_path else None
                    if next_cmd == 'a' and (rx, ry, xrot, large_arg_flag, sweep_flag) == tuple([svg_path[i] for i in range(1, 6)]) and tuple([svg_path[i] for i in range(6, 8)]) in [(x, -y), (-x, y)]:
                        # two arcs make an ellipse
                        xcenter = curx + x / 2
                        ycenter = cury + y / 2
                        path.AddEllipse(xcenter-rx, ycenter-ry, rx+rx, ry+ry)
                        path.AddLineToPoint(curx, cury)
                        pop_many(svg_path, 8)
                    elif rx == ry and xrot == 0 and (x == curx or y == cury):
                        x += curx
                        y += cury
                        xcenter = (x + curx) / 2
                        ycenter = (y + cury) / 2
                        if x == curx:
                            startAngle = pi * 3/2
                            endAngle = pi / 2
                        else: # if y == cury:
                            startAngle = 0
                            endAngle = pi
                        if large_arg_flag:
                            startAngle += pi
                            endAngle += pi
                        clockwise = sweep_flag

                        path.AddArc(xcenter, ycenter, rx, startAngle, endAngle, clockwise)
                    else:
                        # https://www.w3.org/TR/SVG/paths.html#PathDataEllipticalArcCommands
                        x += curx
                        y += cury
                        path.AddLineToPoint(x, y)
                elif cmd == 'z':
                    path.CloseSubpath()
                else:
                    raise Exception('unknown svg command "%s" in path: %s' % (cmd, svg_path_str))
                last_cmd = cmd
            self.path_cache[svg_path_str] = path
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
    #                     angle = radians(args[0])
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
        split_transform = self.transform_split_re.split
        for t, args in self.transform_re.findall(svg_transform or ''):
            args = list(map(float, split_transform(args)))
            if t == 'translate':
                dc.Translate(*args)
            elif t == 'rotate':
                dc.Rotate(radians(args[0]))
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
                brush = self.renderer.CreateBrush(wx.Brush(wx_colour(svg_fill), wx.SOLID))
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
        key = (svg_stroke, line_width, dasharray)
        pen = self.stroke_cache.get(key)
        if pen is None:
            if svg_stroke == 'none':
                if WX41:
                    pen = self.renderer.CreatePen(wx.GraphicsPenInfo(style=wx.PENSTYLE_TRANSPARENT))
                else:
                    pen = self.renderer.CreatePen(wx.NullPen)
            else:
                if WX41:
                    wxpen = wx.GraphicsPenInfo(wx_colour(svg_stroke)).Width(line_width)
                    if linecap == 'butt':
                        wxpen.Cap(wx.CAP_BUTT)
                    elif linecap == 'round':
                        wxpen.Cap(wx.CAP_ROUND)
                    else:
                        raise Exception('linecap %s not supported yet' % linecap)
                    # if dasharray:
                    #     # 1.3.6.3 [JWDJ] 2015-3 dasharray is always a tuple, never a str or unicode
                    #     #if type(dasharray) in (str, unicode):
                    #     #    dasharray = [int(x.strip()) for x in dasharray.split(',')]
                    #     wxpen.Dashes(list(dasharray))
                    #     wxpen.Style(wx.USER_DASH)
                    wxpen.Join(wx.JOIN_MITER)
                else:
                    wxpen = wx.Pen(wx_colour(svg_stroke), int(line_width))
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
            self.stroke_cache[key] = pen
        dc.SetPen(pen)

    # 1.3.7.2 [JWdJ] not used
    # def zoom_matrix(self, matrix):
    #     sm = self.renderer.CreateMatrix()
    #     sm.Scale(self.zoom, self.zoom)
    #     sm.Concat(matrix)
    #     # on Mac OSX the default matrix is not equal to the identity matrix so we need to apply it too:
    #     om = self.renderer.CreateMatrix(*self.default_matrix.Get())
    #     om.Concat(sm)
    #     return om

    def draw_svg_element(self, page, dc, svg_element, highlight, current_color, current_style, highlight_follow=False):
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
        transform = attr.get('transform')
        if transform:
            dc.PushState()
            self.do_transform(dc, transform)

        # 1.3.6.2 [JWdJ] 2015-02-12 Added voicecolor
        if name == 'g':
            style = attr.get('style')
            if style:
                parts = style.split(";")
                for part in parts:
                    part = part.strip()
                    m = self.font_re.match(part)
                    if m:
                        size = m.group('size')
                        if size and size != 'inherit':
                            current_style['font-size'] = size[:-2]  # remove px

                        typeface = m.group('typeface')
                        if typeface and typeface != 'inherit':
                            current_style['font-typeface'] = typeface

                        family = m.group('family')
                        if family and family != 'inherit':
                            current_style['font-family'] = family
                    else:
                        m = self.color_re.match(part)
                        if m:
                            current_color = m.group(1).upper()
                        key = part[:part.index(':')]
                        value = part[part.index(':')+1:].strip()
                        if (value != 'inherit'):
                            current_style[key] = value

            # 1.3.6.2 [JWdJ] 2015-02-14 Only 'g' and 'defs' have children
            for child in svg_element.children:
                self.draw_svg_element(page, dc, child, highlight, current_color, current_style.copy(), highlight_follow)

        # if something is going to be drawn, prepare
        else:
            # 1.3.6.3 [JWDJ] 2015-3 Only set fill if fill is specified (where 'none' is not the same as None)
            fill = attr.get('fill')
            if fill is None and name == 'circle':
                fill = current_color # 1.3.6.4 To draw the two dots in !segno!
            if fill is not None:
                if fill == 'currentColor':
                    fill = current_color

                if highlight and fill != 'none':
                    if highlight_follow:
                        fill = self.highlight_follow_color
                    else:
                        fill = self.highlight_color    

                self.set_fill(dc, fill)

            stroke = attr.get('stroke', 'none')
            if stroke == 'currentColor':
                stroke = current_color

            if highlight and stroke != 'none':
                if highlight_follow:
                    stroke = self.highlight_follow_color
                else:
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

        elif name == 'use':
            x, y = float(attr.get('x', 0)), float(attr.get('y', 0))
            element_id = attr[href_tag][1:]
            # abcm2ps specific:
            desc = attr.get('desc')
            if desc:
                user_x, user_y = self.transform_point(dc, x, y)
                abc_row, abc_col = desc[1], desc[2]
                page.notes.append((user_x, user_y, abc_row, abc_col, desc))
                note_index = len(page.notes)-1
                if note_index in page.selected_indices:
                    highlight = True

            dc.PushState()
            dc.Translate(x, y)
            self.draw_svg_element(page, dc, page.id_to_element[element_id], highlight, current_color, current_style.copy(), highlight_follow)
            if desc:
                page.note_draw_info.append((element_id, current_color, dc.GetTransform().Get()))
            dc.PopState()

        #FAU: Attribut ellipse is used for note heads
        elif name == 'ellipse':
            cx, cy, rx, ry = attr.get('cx', 0), attr.get('cy', 0), attr['rx'], attr['ry']
            cx, cy, rx, ry = map(float, (cx, cy, rx, ry))
            path = dc.CreatePath()
            #FAU: Add +0.5 to better align note heads. %%TODO%% verify how to link it to score position
            path.AddEllipse(cx-rx, cy-ry+0.5, rx+rx, ry+ry)
            dc.DrawPath(path)

        elif name == 'circle':
            cx, cy, r = map(float, (attr.get('cx', 0), attr.get('cy', 0), attr['r']))
            path = dc.CreatePath()
            path.AddCircle(cx, cy, r)
            dc.DrawPath(path)

        #FAU: Attribut text in the svg is used for title, lyrics and also meter
        elif name == 'text':
            text = attr['text']
            if not self.can_draw_sharps_and_flats:
                text = text.replace(u'\u266d', 'b').replace(u'\u266f', '#').replace(u'\u266e', '=')
            x, y = float(attr.get('x', 0)), float(attr.get('y', 0))

            if attr.get('font-style') or current_style.get('font-typeface') == 'italic':
                font_style = wx.FONTSTYLE_ITALIC
            else:
                font_style = wx.FONTSTYLE_NORMAL

            if attr.get('font-weight') or current_style.get('font-typeface') == 'bold':
                weight = wx.FONTWEIGHT_BOLD
            else:
                weight = wx.FONTWEIGHT_NORMAL

            font_size = int(round(float(attr.get('font-size') or current_style.get('font-size', 12))))
            # 1.3.6.3 [JWDJ] 2015-3 bugfix: use correct font family
            font_face = ''
            svg_to_wx_font_family = {
                'serif': wx.FONTFAMILY_ROMAN,
                'sans-serif': wx.FONTFAMILY_SWISS,
                'monospace': wx.FONTFAMILY_MODERN,
                'bookman': wx.FONTFAMILY_ROMAN,
                'sans': wx.FONTFAMILY_SWISS, # should be 'sans-serif' (abcm2ps bug?)
            }

            svg_font_family = (attr.get('font-family') or current_style.get('font-family', 'serif')).lower()

            style = attr.get('style')
            if style:
                style_info = parse_css_props(style)
                font_info = style_info.get('font', '')
                for fi in font_info.split(' '):
                    if fi == 'bold':
                        weight = wx.FONTWEIGHT_BOLD
                    elif fi == 'italic':
                        font_style = wx.FONTSTYLE_ITALIC
                    elif fi.endswith('px'):
                        #FAU: font_size at least for the meter is drawn a bit too small. Add a +2
                        font_size = int(float(fi[0:-2])+2)
                    elif fi in ['serif','sans-serif','monospace','bookman']:
                        svg_font_family = fi

            font_family = svg_to_wx_font_family.get(svg_font_family)
            if font_family is None:
                font_family = wx.FONTFAMILY_DEFAULT
                font_face = svg_font_family # 1.3.6.4 [JWDJ] if font family is not known then assume it is a font face

            ##print repr(text), font_face, attr.get('font-size'), attr.get('font-weight')
            wxfont = wx.Font(font_size, font_family, font_style, weight, False, font_face, wx.FONTENCODING_DEFAULT)
            if wx.VERSION >= (3, 0) or '__WXMSW__' in wx.PlatformInfo:
                wxfont.SetPixelSize(wx.Size(0, font_size))
                y += 0.5
            else:
                wxfont.SetPointSize(font_size)

            font = dc.CreateFont(wxfont, wx_colour(attr.get('fill', 'black')))
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

        elif name == 'line':
            x1, y1, x2, y2 = map(float, (attr['x1'], attr['y1'], attr['x2'], attr['y2']))
            # 1.3.6.3 [JWDJ] 2015-3 Fill and stroke already have been set
            # self.set_fill(dc, 'none')
            # self.set_stroke(dc, stroke, float(attr.get('stroke-width', 1.0)), attr.get('stroke-linecap', 'butt'), attr.get('stroke-dasharray', None))
            # 1.3.6.3 [JWDJ] 2015-3 Fixes line in !segno!
            dc.DrawLines([(x1, y1), (x2, y2)])

        if transform:
            dc.PopState()

    def transform_point_normal(self, dc, x, y):
        matrix = self.renderer.CreateMatrix(*dc.GetTransform().Get())
        return matrix.TransformPoint(x, y)

    def transform_point_osx(self, dc, x, y):
        a, b, c, d, tx, ty = dc.GetTransform().Get()
        _, _, _, def_d, _, def_ty = self.default_transform.Get()
        matrix = self.renderer.CreateMatrix(a, b, c, d * def_d, tx, def_ty - ty) # last param could also be: def_ty + ty * def_d
        new_xy = matrix.TransformPoint(x, y)
        return new_xy

class MyApp(wx.App):
    def OnInit(self):
        self.SetAppName('EasyABC')
        return True

def matrix_to_str(m):
    return '(%s)' % ', '.join(['%.3f' % f for f in m.Get()])

if __name__ == "__main__":
    import os.path
    app = MyApp(0)

    buffer = wx_bitmap(200, 200, 32)
    dc = wx.MemoryDC(buffer)
    dc.SetBackground(wx.WHITE_BRUSH)
    dc.Clear()
    dc = wx.GraphicsContext.Create(dc)
    dc.SetBrush(dc.CreateBrush(wx.BLACK_BRUSH))
    print('default matrix %s' % dc.GetTransform().Get())
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
        a = radians(45)

    original = dc.CreateMatrix(*original_matrix.Get())
    om = dc.CreateMatrix(*original_matrix.Get())
    m0 = dc.CreateMatrix(); m0.Scale(0.5, 0.5)
    m1 = dc.CreateMatrix(); m1.Translate(150, 150)
    m2 = dc.CreateMatrix(); m2.Rotate(a)
    om.Concat(m0)
    om.Concat(m2)
    dc.SetTransform(om)
    dc.DrawPath(path)
    print('new matrix %s' % matrix_to_str(dc.GetTransform()))
    om.Concat(m1)
    om.Concat(m0)
    dc.SetTransform(om)
    dc.DrawPath(path)
    print('new matrix', matrix_to_str(dc.GetTransform()))

    print('----')
    dc.SetTransform(original)
    dc.Scale(0.5, 0.5)
    dc.Translate(150, 150)
    dc.Rotate(radians(25))
    dc.Scale(0.5, 0.5)
    print('new matrix %s' % matrix_to_str(dc.GetTransform()))

    buffer.SaveFile('dc_test_linux.png', wx.BITMAP_TYPE_PNG)
    if True:
        r = wx.GraphicsRenderer.GetDefaultRenderer()
        m1 = r.CreateMatrix(); m1.Scale(1.0, -1.0)
        m2 = r.CreateMatrix(); m2.Translate(50, 60)
        m1.Concat(m2)
        print(m1.TransformPoint(100, 100))

        m1 = r.CreateMatrix(); m1.Scale(1.0, -1.0)
        m2 = r.CreateMatrix(); m2.Translate(50, 60)
        m2.Concat(m1)
        print(m1.TransformPoint(100, 100))

        renderer = SvgRenderer(True)
        #renderer.set_svg(open(os.path.join('abc', 'cache', 'temp_02e3f5d62f001.svg'), 'rb').read())
        renderer.buffer.SaveFile('test_output.png', wx.BITMAP_TYPE_PNG)

