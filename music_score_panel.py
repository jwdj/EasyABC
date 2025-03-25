import wx
import traceback
import sys
from wxhelper import wx_cursor, wx_colour
PY3 = sys.version_info.major > 2
WX4 = wx.version().startswith('4')

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
        self.cross_cursor = wx_cursor(wx.CURSOR_CROSS)
        self.pointer_cursor = wx_cursor(wx.CURSOR_ARROW)
        self.drag_start_x = None
        self.drag_start_y = None
        self.drag_rect = None
        #FAU 20250120: mouse_select_ongoing positionned to avoid the race with event of selection change in TextCtrl
        self.mouse_select_ongoing = False
        self.SetVirtualSize((self.buffer_width, self.buffer_height))
        self.SetScrollbars(20, 20, 50, 50)
        # 1.3.6.2 [JWdJ] 2015-02-14 hook events after initializing to prevent unnecessary redraws
        self.need_redraw = True
        self.redrawing = False
        # self.redraw_counter = 0
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.highlighted_notes = None
        self.highlight_follow = False

    def reset_scrolling(self):
        self.SetVirtualSize((self.buffer_width, self.buffer_height))
        self.SetScrollbars(20, 20, 50, 50)

    def get_xy_of_mouse_event(self, event):
        x, y = self.CalcUnscrolledPosition(event.GetX(), event.GetY())
        return x, y

    # def get_path_under_mouse(self, event):
    #     x, y = self.get_xy_of_mouse_event(event)
    #     pt = wx.Point2D(x, y)
    #     for i, path in enumerate(self.note_paths):
    #         path_box = path.GetBox()
    #         path_box.Inset(-2.0, -2.0)
    #         if path_box.Contains(pt):
    #             self.SetCursor(self.pointer_cursor)
    #             return (i, path)
    #     return (-1, None)

    # def get_note_desc_under_mouse(self, event):
    #     x, y = self.get_xy_of_mouse_event(event)
    #     pt = wx.Point2D(x, y)
    #     for i, path in enumerate(self.note_paths):
    #         path_box = path.GetBox()
    #         path_box.Inset(-2.0, -2.0)
    #         if path_box.Contains(pt):
    #             self.SetCursor(self.pointer_cursor)
    #             return (i, path)
    #     return (-1, None)

    # def move_selection(self, direction):
    #     if not self.renderer.notes or not self.renderer.selected_indices:
    #         return
    #     index = min(self.renderer.selected_indices) + direction
    #     if index < 0:
    #         index = 0
    #     elif index >= len(self.renderer.notes):
    #         index = len(self.renderer.notes)-1
    #     self.renderer.clear_note_selection()
    #     self.renderer.add_note_to_selection(index)
    #     self.redraw()
    #     if self.OnNoteSelectionChangedDesc:
    #         self.OnNoteSelectionChangedDesc(self.renderer.selected_indices)

    def OnLeftButtonDown(self, event):
        if event.LeftDown():
            #FAU 20250126: mouse_select_ongoing positionned to avoid the race with event of selection change in TextCtrl
            self.mouse_select_ongoing = True
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
        #FAU 20250126: mouse_select_ongoing positionned to avoid the race with event of selection change in TextCtrl
        self.mouse_select_ongoing = False

    def OnMouseMotion(self, event):
        page = self.current_page
        if self.HasCapture():
            if self.drag_start_x is not None and self.drag_start_y is not None:
                x, y = self.get_xy_of_mouse_event(event)
                self.drag_rect = (min(self.drag_start_x, x), min(self.drag_start_y, y), abs(self.drag_start_x-x), abs(self.drag_start_y-y))
                rect = wx.Rect(*map(int, self.drag_rect))
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
            #FAU 20250126: mouse_select_ongoing positionned to avoid the race with event of selection change in TextCtrl
            self.mouse_select_ongoing = False
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
            if self.current_page != self.renderer.empty_page:
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
        if self.current_page != self.renderer.empty_page:
            if self.need_redraw:
                self.Draw()
                self.need_redraw = False
            dc.DrawBitmap(self.renderer.buffer, 0, 0)
            if self.highlighted_notes:
                self.renderer.draw_notes(page=self.current_page, note_indices=self.highlighted_notes, highlight=True, dc=dc, highlight_follow=self.highlight_follow)
        else:
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()

    def set_page(self, page):
        is_other_page = self.current_page and page and self.current_page.index != page.index
        self.current_page = page
        self.redraw()
        if is_other_page:
            self.Scroll(0, 0)

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
        w, h = int(page.svg_width * z), int(page.svg_height * z)
        self.redrawing = True
        try:
            self.SetVirtualSize((w, h)) # triggers redraw again
            self.note_paths = []
            self.need_redraw = True
            self.renderer.update_buffer(page)
            # self.redraw_counter += 1
            # print 'need_redraw %d' % self.redraw_counter
            self.Refresh()
            self.Update()
        finally:
            self.redrawing = False

    def draw_drag_rect(self, dc):
        if self.drag_rect:
            dc = wx.GraphicsContext.Create(dc)
            #z = self.renderer.zoom
            #dc.Scale(z, z)
            x, y, width, height = self.drag_rect
            #FAU Width argument for pen is an int not a float.
            #dc.SetPen( dc.CreatePen(wx.Pen(wx_colour('black'), 1.0, style=wx.DOT )) )
            dc.SetPen( dc.CreatePen(wx.Pen(wx_colour('black'), width=1, style=wx.DOT )) )
            dc.SetBrush(dc.CreateBrush(wx.Brush(wx_colour('#fffbc6'), wx.SOLID)))
            path = dc.CreatePath()
            path.MoveToPoint(x, y)
            path.AddLineToPoint(x+width, y)
            path.AddLineToPoint(x+width, y+height)
            path.AddLineToPoint(x, y+height)
            path.AddLineToPoint(x, y)
            dc.DrawPath(path)

    def draw_notes_highlighted(self, note_indices, highlight_follow=False):
        self.highlighted_notes = note_indices
        self.redrawing = True
        self.highlight_follow = highlight_follow
        try:
            self.Refresh()
            self.Update()
        finally:
            self.redrawing = False
            if not wx.Platform == "__WXMAC__":
                self.highlighted_notes = None

    def Draw(self):
        dc = wx.BufferedDC(None, self.renderer.buffer)
        if not WX4:
            dc.BeginDrawing()
        try:
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()
            self.draw_drag_rect(dc)
            if self.current_page != self.renderer.empty_page:
                self.renderer.draw(page=self.current_page, clear_background=False, dc=dc)
        except Exception as e:
            error_msg = traceback.format_exc()
            print('Warning: ' + error_msg)
        finally:
            if not WX4:
                dc.EndDrawing()



