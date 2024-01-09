import wx

WX4 = wx.version().startswith('4')

if WX4:
    wx_cursor = wx.Cursor
    wx_colour = wx.Colour
else:
    wx_cursor = wx.StockCursor
    wx_colour = wx.NamedColour

def delete_menuitem(menu, item):
    if WX4:
        menu.Delete(item)
    else:
        menu.DeleteItem(item)

def wx_set_size(frame, x, y, width, height):
    if WX4:
        frame.SetSize(x, y, width, height)
    else:
        frame.SetDimensions(x, y, width, height)

def append_submenu(menu, label, submenu):
    if WX4:
        return menu.AppendSubMenu(submenu, label)
    else:
        return menu.AppendMenu(-1, label, submenu)


def append_menu_item(menu, label, description, handler, kind=wx.ITEM_NORMAL, id=-1, bitmap=None):
    menu_item = wx.MenuItem(menu, id=wx.ID_ANY, text=label, helpString=description, kind=kind)
    if bitmap is not None:
        menu_item.SetBitmap(bitmap)
    if WX4:
        menu.Append(menu_item)
    else:
        menu.AppendItem(menu_item)

    if handler is not None:
        if menu.InvokingWindow is not None:
            menu.InvokingWindow.Bind(wx.EVT_MENU, handler, menu_item)
        else:
            menu.Bind(wx.EVT_MENU, handler, menu_item)
    return menu_item


def append_to_menu(menu, items):
    for item in items:
        if len(item) == 0:
            menu.AppendSeparator()
        elif len(item) >= 2:
            label = item[0]
            sub_menu = item[1]
            if isinstance(sub_menu, (wx.Menu, tuple, list)):
                if not isinstance(sub_menu, wx.Menu):
                    sub_menu = create_menu(sub_menu, menu.InvokingWindow)
                menu_item = append_submenu(menu, label, sub_menu)
                after_add = item[-1]
                if hasattr(after_add, '__call__'):
                    after_add(menu_item)
            else:
                id = None
                after_add = None
                if isinstance(item[0], int):
                    id = item[0]
                    item = tuple(list(item)[1:]) # strip id from tuple
                if len(item) > 3:
                    after_add = item[-1]
                    if hasattr(after_add, '__call__'):
                        item = tuple(list(item)[0:-1]) # strip after-add-function
                menu_item = append_menu_item(menu, *item, id=id)
                if after_add is not None:
                    after_add(menu_item)


def create_menu(items, parent=None):
    menu = wx.Menu()
    if parent is not None:
        menu.InvokingWindow = parent
    append_to_menu(menu, items)
    return menu


def create_menu_bar(items, parent=None):
    menuBar = wx.MenuBar()
    if parent is not None:
        menuBar.InvokingWindow = parent
    for item in items:
        label = item[0]
        items = item[1]
        if not isinstance(items, wx.Menu):
            items = create_menu(items, parent=parent)
        menuBar.Append(items, label)
    return menuBar


def wx_bitmap(width, height, depth=-1):
    if WX4:
        return wx.Bitmap(width, height, depth)
    else:
        return wx.EmptyBitmap(width, height, depth)

def wx_slider_set_tick_freq(slider, freq):
    if WX4:
        slider.SetTickFreq(freq)
    else:
        slider.SetTickFreq(freq, 0)

def wx_sound(path):
    if WX4:
        import wx.adv
        return wx.adv.Sound(path)
    else:
        return wx.Sound(path)

def wx_show_message(title, message):
    dlg = wx.MessageDialog(None, message, title, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

def wx_insert_dropdown_value(combobox, value, max=None):
    combobox.Insert(value, 0)
    if max:
        if combobox.Count > max:
            combobox.Delete(max)

def wx_dirdialog(parent, message, path):
    dlg = wx.DirDialog(parent, message, path, style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    try:
        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetPath()
    finally:
        dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
