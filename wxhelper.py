import wx

WX4 = wx.version().startswith('4')


def wx_cursor(c):
    if WX4:
        return wx.Cursor(c)
    else:
        return wx.StockCursor(c)


def wx_colour(c):
    if WX4:
        return wx.Colour(c)
    else:
        return wx.NamedColour(c)


def delete_menuitem(menu, item):
    if WX4:
        menu.Delete(item)
    else:
        menu.DeleteItem(item)


def append_submenu(menu, label, submenu):
    if WX4:
        return menu.AppendSubMenu(submenu, label)
    else:
        return menu.AppendMenu(-1, label, submenu)


def append_menu_item(menu, label, description, handler, kind=wx.ITEM_NORMAL, id=-1, bitmap=None):
    menu_item = wx.MenuItem(menu, -1, label, description, kind)
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
        elif len(item) == 2:
            label = item[0]
            sub_menu = item[1]
            if not isinstance(sub_menu, wx.Menu):
                sub_menu = create_menu(sub_menu, menu.InvokingWindow)
            append_submenu(menu, label, sub_menu)
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
