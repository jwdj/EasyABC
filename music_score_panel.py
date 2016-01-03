import wx
import traceback
import sys

class MusicScorePanel(wx.ScrolledWindow):
    def __init__(self, parent, renderer):
        wx.ScrolledWindow.__init__(self, parent, -1)#, style=wx.CLIP_CHILDREN )
        self.renderer = renderer
        self.draw_ops = []
        #self.SetVirtualSize(wx.Size(1450, 1001))
        self.svg = None
        self.fill_cache = {}
        self.stroke_cache = {}
        self.path_cache = {}
        self.note_paths = []
        self.current_page = renderer.empty_page
        ##self.selected_note_path_indices = set()
        ##self.selected_note_descriptions = set()
        if wx.Platform == "__WXMSW__":
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.buffer_width = 400
        self.buffer_height = 800
        for i in range(wx.Display.GetCount()):
            r = wx.Display(i).GetGeometry()
            self.buffer_width = max(self.buffer_width, r.GetWidth())
            self.buffer_height = max(self.buffer_height, r.GetHeight())        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)        
        self.OnNoteSelectionChangedDesc = None
        self.cross_cursor = wx.StockCursor(wx.CURSOR_CROSS)
        self.pointer_cursor = wx.StockCursor(wx.CURSOR_ARROW)
        self.drag_start_x = None
        self.drag_start_y = None
        self.drag_rect = None
        self.SetVirtualSize((self.buffer_width, self.buffer_height))
        self.SetScrollbars(20, 20, 50, 50)        
        # 1.3.6.2 [JWdJ] 2015-02-14 hook events after initializing to prevent unnecessary redraws
        self.need_redraw = True
        self.redrawing = False
        # self.redraw_counter = 0
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def reset_scrolling(self):
        self.SetVirtualSize((self.buffer_width, self.buffer_height))
        self.SetScrollbars(20, 20, 50, 50)

    def get_xy_of_mouse_event(self, event):
        z = self.renderer.zoom
        x, y = self.CalcUnscrolledPosition(event.GetX(), event.GetY())        
        return (x / z, y / z)

    def get_path_under_mouse(self, event):
        x, y = self.get_xy_of_mouse_event(event)
        pt = wx.Point2D(x, y)
        for i, path in enumerate(self.note_paths):
            path_box = path.GetBox()
            path_box.Inset(-2.0, -2.0)                
            if path_box.Contains(pt):
                self.SetCursor(self.pointer_cursor)
                return (i, path)
        return (-1, None)

    def get_note_desc_under_mouse(self, event):        
        pt = wx.Point2D(x, y)
        for i, path in enumerate(self.note_paths):
            path_box = path.GetBox()
            path_box.Inset(-2.0, -2.0)                
            if path_box.Contains(pt):
                self.SetCursor(self.pointer_cursor)
                return (i, path)
        return (-1, None)

    def move_selection(self, direction):        
        if not self.renderer.notes or not self.renderer.selected_indices:
            return
        index = min(self.renderer.selected_indices) + direction
        if index < 0:
            index = 0
        elif index >= len(self.renderer.notes):
            index = len(self.renderer.notes)-1
        self.renderer.clear_note_selection()
        self.renderer.add_note_to_selection(index)        
        self.redraw()
        if self.OnNoteSelectionChangedDesc:
            self.OnNoteSelectionChangedDesc(self.renderer.selected_indices)
    
    def OnLeftButtonDown(self, event):        
        if event.LeftDown():
            self.SetFocus()
            page = self.current_page
            old_selection = page.selected_indices.copy()
            page.clear_note_selection()
            x, y = self.get_xy_of_mouse_event(event)
            note_index = page.hit_test(x, y)
            if note_index is None:
                close_note_index = page.hit_test(x, y, return_closest_hit=True)
            else:
                close_note_index = None            
            signal_change = False
            if note_index is not None:
                page.add_note_to_selection(note_index)
            else:
                self.drag_start_x, self.drag_start_y = self.get_xy_of_mouse_event(event)
                self.CaptureMouse()
                self.OnMouseMotion(event)
            
            if old_selection != page.selected_indices:
                self.redraw()
            #if old_selection != self.renderer.selected_indices or note_index is not None:
            self.OnNoteSelectionChangedDesc(page.selected_indices, close_note_index=close_note_index)
                
##        if event.LeftDown():
##            self.SetFocus()
##            old_selection = self.selected_note_path_indices.copy()
##            self.selected_note_path_indices = set()
##            self.selected_note_descriptions = set()
##            i, path = self.get_path_under_mouse(event)
##            if path:            
##                self.selected_note_path_indices.add(i)
##            else:
##                self.drag_start_x, self.drag_start_y = self.get_xy_of_mouse_event(event)
##                self.CaptureMouse()
##                self.OnMouseMotion(event)
##            if old_selection != self.selected_note_path_indices:
##                self.redraw()
##                if self.OnNoteSelectionChanged:
##                    self.OnNoteSelectionChanged(sorted(self.selected_note_path_indices))                    

    def OnLeftButtonUp(self, event):
        if self.HasCapture():
            try:
                self.ReleaseMouse()
            except:
                pass
            self.drag_start_x = None
            self.drag_start_y = None
            self.drag_rect = None        
            self.OnMouseMotion(event)
            self.redraw()

    def OnMouseMotion(self, event):        
        page = self.current_page
        if self.HasCapture():
            if self.drag_start_x is not None and self.drag_start_y is not None:
                x, y = self.get_xy_of_mouse_event(event)
                self.drag_rect = (min(self.drag_start_x, x), min(self.drag_start_y, y), abs(self.drag_start_x-x), abs(self.drag_start_y-y))
                rect = wx.Rect(*map(lambda x: int(x), self.drag_rect))
                old_selection = page.selected_indices.copy()
                page.select_notes(rect)
                if old_selection != page.selected_indices and self.OnNoteSelectionChangedDesc:
                    self.OnNoteSelectionChangedDesc(page.selected_indices)
                self.redraw()
        else:
            x, y = self.get_xy_of_mouse_event(event)
            if page.hit_test(x, y) is not None:
                self.SetCursor(self.pointer_cursor)
            else:
                self.SetCursor(self.cross_cursor)                
##        if self.HasCapture():
##            x, y = self.get_xy_of_mouse_event(event)
##            self.drag_rect = (min(self.drag_start_x, x), min(self.drag_start_y, y), abs(self.drag_start_x-x), abs(self.drag_start_y-y))            
##            #rect = wx.Rect2D(*self.drag_rect)            
##            #rect = wx.Rect(*map(lambda x: int(x*self.renderer.zoom), self.drag_rect))
##            rect = wx.Rect(*map(lambda x: int(x), self.drag_rect))
##            self.renderer.select_notes(rect)
##            old_selection = self.selected_note_path_indices.copy()
##            self.selected_note_path_indices = set()
##            for i, path in enumerate(self.note_paths):
##                path_box = path.GetBox()
##                if rect.Intersects(path_box):
##                    self.selected_note_path_indices.add(i)            
##            self.redraw()
##            if old_selection != self.selected_note_path_indices and self.OnNoteSelectionChanged:                
##                self.OnNoteSelectionChanged(sorted(self.selected_note_path_indices))
##        else:
##            i, path = self.get_path_under_mouse(event)
##            if path:
##                self.SetCursor(self.pointer_cursor)
##            else:
##                self.SetCursor(self.cross_cursor)        

    def OnSize(self, evt):                
        w, h = self.GetClientSize()
        # 1.3.6.2 [JWdJ] 2015-02-14 prevent unneeded redraws
        if w != self.renderer.min_width or h != self.renderer.min_height:
            self.renderer.min_width = w
            self.renderer.min_height = h
            if self.current_page:
                self.renderer.update_buffer(self.current_page)
                self.redraw()
        
    def OnPaint(self, evt):
        # The buffer already contains our drawing, so no need to
        # do anything else but create the buffered DC.  When this
        # method exits and dc is collected then the buffer will be
        # blitted to the paint DC automagically
        ##if wx.Platform == "__WXMSW__":
        ##    dc = wx.BufferedPaintDC(self, self.renderer.buffer, wx.BUFFER_VIRTUAL_AREA)
        ##else:
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        if self.current_page:
            if self.need_redraw:
                self.Draw()
                self.need_redraw = False
            dc.DrawBitmap(self.renderer.buffer, 0, 0)
        else:
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()

    def set_page(self, page):
        self.current_page = page
        self.redraw()

    def clear(self):
        self.current_page = self.renderer.empty_page
        self.renderer.clear()
        self.Refresh()

    def redraw(self):
        if self.redrawing:
            return

        page = self.current_page
        if page is None:
            return

        z = self.renderer.zoom
        w, h = int(page.svg_width*z), int(page.svg_height*z)
        self.redrawing = True
        try:
            self.SetVirtualSize((w, h)) # triggers redraw again
            self.note_paths = []
            self.need_redraw = True
            self.renderer.update_buffer(page)
            # self.redraw_counter += 1
            # print 'need_redraw %d' % self.redraw_counter
        finally:
            self.redrawing = False

        self.Refresh()
        self.Update()

##    def set_fill(self, dc, svg_fill):
##        if svg_fill in self.fill_cache:
##            brush = self.fill_cache[svg_fill]
##        elif svg_fill == 'none':
##            brush = dc.CreateBrush(wx.NullBrush)
##        elif svg_fill == 'white':
##            brush = dc.CreateBrush(wx.WHITE_BRUSH)
##        elif svg_fill == 'black':
##            brush = dc.CreateBrush(wx.BLACK_BRUSH)        
##        else:
##            brush = dc.CreateBrush(wx.Brush(wx.NamedColour(svg_fill), wx.SOLID))
##        self.fill_cache[svg_fill] = brush
##        dc.SetBrush(brush)
##
##    def set_stroke(self, dc, svg_stroke, line_width):
##        if (svg_stroke, line_width) in self.stroke_cache:
##            pen = self.stroke_cache[(svg_stroke, line_width)]
##        elif svg_stroke == 'none':
##            pen = dc.CreatePen(wx.NullPen)
##        else:
##            pen = dc.CreatePen(wx.Pen(wx.NamedColour(svg_stroke), line_width))
##        self.stroke_cache[(svg_stroke, line_width)] = pen
##        dc.SetPen(pen)
##
##    def svg_path_to_dc_path(self, dc, svg_path):        
##        if svg_path in self.path_cache:
##            return self.path_cache[svg_path]
##        original_svg_path = svg_path
##        svg_path = deque(svg_path.split())
##        path = dc.CreatePath()
##        while svg_path:
##            cmd = svg_path.popleft()
##            if cmd == 'M':
##                x, y = float(svg_path.popleft()), float(svg_path.popleft())
##                path.MoveToPoint(x, y)
##            elif cmd == 'L':
##                x, y = float(svg_path.popleft()), float(svg_path.popleft())
##                path.AddLineToPoint(x, y)
##            elif cmd == 'C':
##                cx1, cy1, cx2, cy2, x, y = float(svg_path.popleft()), float(svg_path.popleft()), \
##                                           float(svg_path.popleft()), float(svg_path.popleft()), \
##                                           float(svg_path.popleft()), float(svg_path.popleft())
##                path.AddCurveToPoint(cx1, cy1, cx2, cy2, x, y)
##            elif cmd == 'A':
##                rx, ry, xrot, large_arg_flac, sweep_flag, x, y = (float(svg_path.popleft()), float(svg_path.popleft()), 
##                                                                  float(svg_path.popleft()),
##                                                                  float(svg_path.popleft()), float(svg_path.popleft()),
##                                                                  float(svg_path.popleft()), float(svg_path.popleft()))                
##                path.AddEllipse(x-rx*2, y-ry*2, rx*2, ry*2)
##            elif cmd == 'Z':
##                path.CloseSubpath()
##            else:
##                raise Exception('unkown svg command: %s' % cmd)
##        self.path_cache[original_svg_path] = path
##        return path
##
##    def draw_svg(self, dc):        
##        if wx.Platform != "__WXMSW__":
##            stroke_width_factor = 1.9
##        else:
##            stroke_width_factor = 1.0        
##        has_drawn_text = False
##        staff_element_seen = False
##        namespace = 'http://www.w3.org/2000/svg'
##        if not self.svg:
##            return        
##        for element in self.svg:
##            a = element.attrib
##            values = {}
##            for key, value in a.items() + [s.split(':') for s in a.get('style', '').split(';')]:            
##                key, value = key.strip(), value.strip()
##                if key == 'font-size' and value.endswith('px'):
##                    value = value.replace('px', '')
##                try:
##                    value = float(value)
##                except:
##                    pass
##                values[key] = value
##            if element.tag == '{%s}text' % namespace:
##                #if has_drawn_text:
##                #    continue
##                text = element.text or u''
##                has_drawn_text = True
##                x, y = values['x'], values['y']
##                if values['font-style'] == 'italic':
##                    style = wx.FONTSTYLE_ITALIC
##                else:
##                    style = wx.FONTSTYLE_NORMAL
##                if values['font-weight'] == 'bold':
##                    weight = wx.FONTWEIGHT_BOLD
##                else:
##                    weight = wx.FONTWEIGHT_NORMAL
##                #style = wx.FONTSTYLE_NORMAL
##                #weight = wx.FONTWEIGHT_NORMAL
##                if wx.Platform != "__WXMSW__":
##                    font_size = int(round(values['font-size']*1))
##                    y = y - font_size * 0.15
##                else:
##                    font_size = int(round(values['font-size']*0.85))
##                wxfont = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, style, weight, False, "Times New Roman", wx.FONTENCODING_SYSTEM)
##                font = dc.CreateFont(wxfont, wx.NamedColour(values['fill']))                
##                dc.SetFont(font)                                
##                (width, height, descent, externalLeading) = dc.GetFullTextExtent(text)                
##                dc.DrawText(text, x, y-(height*0.6666)) #*self.GetParent().zoom_factor)  #/self.GetParent().zoom_factor                
##            elif element.tag == '{%s}path' % namespace:
##                path = self.svg_path_to_dc_path(dc, a['d'])
##                staff_element_seen |= element.attrib.get('class', None) == 'staff'
##                if element.attrib.get('class', None) in ['HD', 'Hd', 'hd', 'ghd'] and staff_element_seen:  # only start collecting notes after staff element (so that we won't get Q: field note)
##                    self.note_paths.append(path)
##                if values['fill'] != 'none':
##                    if element.attrib.get('class', None) in ['HD', 'Hd', 'hd', 'ghd'] and len(self.note_paths)-1 in self.selected_note_path_indices:                        
##                        self.set_fill(dc, '#cc0000')
##                    else:
##                        self.set_fill(dc, values['fill'])
##                    dc.FillPath(path, wx.WINDING_RULE)
##                if values['stroke'] != 'none':                    
##                    self.set_stroke(dc, values['stroke'], values.get('stroke-width', 1.0)*stroke_width_factor)
##                    dc.StrokePath(path)
##            elif element.tag == '{%s}rect' % namespace:
##                x, y, width, height = values['x'], values['y'], values['width'], values['height']
##                #self.set_stroke(dc, values['stroke'], values.get('stroke-width', 1.0))
##                #self.set_fill(dc, values['fill'])
##                path = dc.CreatePath()
##                path.MoveToPoint(x, y)
##                path.AddLineToPoint(x+width, y)
##                path.AddLineToPoint(x+width, y+height)
##                path.AddLineToPoint(x, y+height)
##                path.AddLineToPoint(x, y)
##                if values['fill'] != 'none':
##                    self.set_fill(dc, values['fill'])
##                    dc.FillPath(path)
##                if values['stroke'] != 'none':
##                    self.set_stroke(dc, values['stroke'], values.get('stroke-width', 1.0)*stroke_width_factor)
##                    dc.StrokePath(path)
##                #dc.DrawRectangle(x, y, width, height)                
##            #elif element.tag == 'rect':

##    #def InitBuffer(self):
##        #sz = self.GetVirtualSize()        
##        #sz.width = max(1, sz.width)
##        #sz.height = max(1, sz.height)        
##        #self.SetVirtualSize((self.buffer_width, self.buffer_height))
##        #self._buffer = wx.EmptyBitmap(self.buffer_width, self.buffer_height, 32)
##        #self.Draw()

    def draw_drag_rect(self, dc):
        if self.drag_rect:
            x, y, width, height = self.drag_rect
            dc.SetPen( dc.CreatePen(wx.Pen(wx.NamedColour('black'), 1.0, style=wx.DOT )) )            
            dc.SetBrush(dc.CreateBrush(wx.Brush(wx.NamedColour('#fffbc6'), wx.SOLID)))            
            path = dc.CreatePath()
            path.MoveToPoint(x, y)
            path.AddLineToPoint(x+width, y)
            path.AddLineToPoint(x+width, y+height)
            path.AddLineToPoint(x, y+height)
            path.AddLineToPoint(x, y)            
            dc.DrawPath(path)

    def Draw(self):
        dc = wx.BufferedDC(None, self.renderer.buffer)
        dc.BeginDrawing()
        try:
            try:
                dc.SetBackground(wx.WHITE_BRUSH)
                dc.Clear()
                gc = wx.GraphicsContext.Create(dc)        
                z = self.renderer.zoom
                gc.Scale(z, z)
                self.draw_drag_rect(gc)
                self.renderer.zoom = z
                self.renderer.draw(page=self.current_page, clear_background=False)
                ##self.draw_svg(gc)
                ##td = datetime.now() - t
            finally:
                dc.EndDrawing()
        except Exception as e:
            error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
            print 'Warning: %s' % error_msg
        ##print 'draw time', td.seconds*1000000 + td.microseconds


