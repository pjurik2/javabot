import wx
import wx.aui
from time import localtime, strftime, clock
import webbrowser
from styles import out_colors as styles


def safe_unicode(string):
    try:
        return unicode(string)
    except UnicodeDecodeError:
        return '<Decode error.>'

class Book():
    def __init__(self, name, bot, parent, panel, styles):
        self.name = name
        self.bot = bot
        self.parent = parent
        self.panel = panel
        self.styles = styles

        self.tab = {}
        self.order = []

        self.book = wx.aui.AuiNotebook(panel, style=styles)
        self.book.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.page_selected)

        self.parent.frame.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSED,
                               self.page_closed,
                               self.book)

        self.bot.events.add(self.parent, 'ui', self.name, 0, 0,
                            'add', self.page_add,
                            'remove', self.page_remove)

    def page_current(self):
        idx = self.book.GetSelection()
        name = self.order[idx]
        kind = self.tab[name].kind

        return idx, name, kind

    def page_add(self, kind, name, caption, *args, **kwargs):
        self.tab[name] = types[kind](self.bot, self.parent, self, name,
                                     caption)
        
        wx.CallAfter(self.do_page_add, kind, name, caption, *args, **kwargs)
    def do_page_add(self, kind, name, caption, *args, **kwargs):
        if 'select' in kwargs:
            select = kwargs['select']
            del kwargs['select']
        else:
            select = False
        self.tab[name].ui_start(*args, **kwargs)
        
        if 'ui_order' in kwargs:
            self.order.insert(kwargs['ui_order'], name)
            self.book.InsertPage(kwargs['ui_order'], self.tab[name].panel,
                                 caption, select=select)

            del kwargs['ui_order']
        else:
            self.order.append(name)
            self.book.AddPage(self.tab[name].panel, caption, select=select)

    def page_remove(self, name):
        try:
            idx = self.order.index(name)
        except:
            return

        try:
            func = self.tab[name].__del__
        except:
            pass
        else:
            func()

        try:
            self.book.DeletePage(idx)
        except:
            pass

        del self.order[idx]
        try:
            del self.tab[name]
        except KeyError:
            pass

    def page_selected(self, *evt):
        try:
            page_name = self.order[self.book.GetSelection()]
        except:
            return

        self.bot.events.call('ui', self.name, page_name, 'selected')

    def page_closed(self, evt):
        idx = evt.selection
        name = self.order[idx]
        
        try:
            func = self.tab[name].__del__
        except:
            pass
        else:
            func()
            
        del self.order[idx]
        del self.tab[name]

        self.bot.events.call('ui', self.name, 'closed', name, [name])

class List():
    kind = 'list'
    def __init__(self, bot, parent, nb, name, caption):
        self.bot = bot
        self.parent = parent
        self.nb = nb

        self.name = name
        self.caption = caption

        self.draw = []
        self.type = []
        self.menu = None

        self.bot.events.add(self.parent, 'ui', 'list', self.name, 0, 0,
                            'add_entry', self.add_entry,
                            'remove_entry', self.remove_entry,
                            'clear', self.clear,
                            'header', self.upd_header,
                            'upd_entry', self.upd_entry,
                            'menu', self.menu_add)
                            #'remove', self.remove)

    def ui_start(self, width, height, *args, **kwargs):
        self.panel = wx.Panel(self.nb.book)
        self.header = wx.TextCtrl(self.panel,
                                  style=(wx.TE_READONLY | wx.TE_CENTER | wx.TE_RICH | wx.TE_MULTILINE),
                                  size=(1,1))
        self.header.SetBackgroundColour('#000000')
        self.header.SetForegroundColour('#FFFFFF')
        self.header.Clear()
        self.header.AppendText(self.caption)
        
        self.lc = wx.ListCtrl(self.panel, style=wx.LC_REPORT |\
                              wx.LC_ALIGN_LEFT |\
                              wx.LC_ALIGN_TOP)
                              #size=(296, 1))
        self.lc.SetBackgroundColour('#000000')

        self.lc.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.popup_list)
        self.lc.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.insert_user)

        for x in range(0, len(args), 3):
            self.type.append(args[x+1])
            self.lc.InsertColumn((x / 3), args[x], width=args[x+2])

        self.icons, self.il, self.count = self.parent.load_icons(width,
                                                                 height,
                                                                 **kwargs)
        self.lc.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.gbs = wx.GridBagSizer(0, 0)
        self.gbs.Add(self.header, wx.GBPosition(0, 0), flag=wx.EXPAND)
        self.gbs.Add(self.lc, wx.GBPosition(1, 0), flag=wx.EXPAND)
        self.gbs.AddGrowableRow(1, 1)
        self.gbs.AddGrowableCol(0, 1)
        self.gbs.SetFlexibleDirection(wx.BOTH)
        
        self.panel.SetBackgroundColour('#000000')
        self.panel.SetSizerAndFit(self.gbs, True)

    def insert_user(self, evt_list):
        #Prepare yourself.
        list_col = self.type.index(0x00)
        list_item = self.lc.GetItem(evt_list.GetIndex(), list_col)
        list_text = list_item.GetText()
        self.parent.cb_send.SetValue(self.parent.cb_send.GetValue() +\
                                     list_text)

        evt_list.Skip(True)

    def popup_list(self, evt_list):
        if self.menu != None:
            sel_count = self.lc.GetSelectedItemCount()
            self.bot.status['selected'] = []
            last = -1
            
            for x in range(sel_count):
                last = self.lc.GetNextItem(last, wx.LIST_NEXT_ALL,
                                           wx.LIST_STATE_SELECTED)
                self.bot.status['selected'].append(last)
            
            self.lc.PopupMenu(self.menu)

        evt_list.Skip(True)

    def get_icon_idx(self, icon):
        fgsfds = type(icon)
        if fgsfds == tuple:
            return self.parent.get_lag_idx(icon)
        elif fgsfds == dict:
            return self.parent.get_bni_idx(icon, self.draw)
        else:
            return self.icons[icon]

    def upd_header(self, *rest):
        wx.CallAfter(self.do_upd_header, *rest)
    def do_upd_header(self, text):
        self.header.Clear()
        self.header.AppendText(text)

    def add_entry(self, *args, **kwargs):
        wx.CallAfter(self.do_add_entry, *args, **kwargs)
    def do_add_entry(self, *args, **kwargs):
        if ('idx' in kwargs) == False:
            kwargs['idx'] = self.lc.GetItemCount()

        idx = self.lc.InsertImageStringItem(kwargs['idx'],
                                            '',
                                            -1)
        if 'bold' in kwargs:
            if kwargs['bold']:
                font = wx.Font(10, wx.FONTFAMILY_DEFAULT,
                               wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_BOLD)
                self.lc.SetItemFont(idx, font)
        if 'color' in kwargs:
            self.lc.SetItemTextColour(idx, kwargs['color'])
        if 'bgcolor' in kwargs:
            self.lc.SetItemBackGroundColour(idx, kwargs['bgcolor'])

        x = 0
        for arg in args:
            if self.type[x] == 0x02:
                img_idx = self.get_icon_idx(arg)
                self.lc.SetItemColumnImage(idx, x, img_idx)
            else:
                self.lc.SetStringItem(idx, x, safe_unicode(arg))
            x += 1

    def upd_entry(self, *args, **kwargs):
        wx.CallAfter(self.do_upd_entry, *args, **kwargs)
    def do_upd_entry(self, idx, *args, **kwargs):
        if 'newidx' in kwargs:
            self.do_remove_entry(idx)
            kwargs['idx'] = kwargs['newidx']
            self.do_add_entry(*args, **kwargs)
        else:
            if 'color' in kwargs:
                self.lc.SetItemTextColour(idx, kwargs['color'])
            if 'bgcolor' in kwargs:
                self.lc.SetItemBackgroundColour(idx, kwargs['bgcolor'])
            for x in range(0, len(args), 2):
                if self.type[args[x]] == 0x02:
                    icon = self.get_icon_idx(args[x+1])
                    self.lc.SetItemColumnImage(idx, args[x], icon)
                else:
                    self.lc.SetStringItem(idx, args[x], safe_unicode(args[x+1]))

    def remove_entry(self, idx):
        wx.CallAfter(self.do_remove_entry, idx)
    def do_remove_entry(self, idx):
        col = 0
        for kind in self.type:
            if kind == 0x02:
                list_item = self.lc.GetItem(idx, col)
                img_idx = list_item.GetImage()

                if img_idx in self.draw:
                    self.parent.bni.remove(img_idx)
                    self.draw.remove(img_idx)
            col += 1

        self.lc.DeleteItem(idx)

    def clear(self):
        wx.CallAfter(self.do_clear)
    def do_clear(self):
        self.header.Clear()
        for x in self.draw:
            self.parent.bni.remove(x)
        self.draw = []
        self.lc.DeleteAllItems()

    def menu_add(self, *rest):
        wx.CallAfter(self.do_menu_add, *rest)
    def do_menu_add(self, *rest):
        self.menu = wx.Menu()

        for x in range(0, len(rest), 2):
            self.menu.Append(self.parent.menu_count, rest[x], '')
            wx.EVT_MENU(self.parent.frame, self.parent.menu_count, rest[x+1])
            self.parent.menu_count += 1
        
    def __del__(self):
        for x in self.draw:
            self.parent.bni.remove(x)

        self.bot.events.remove('ui', 'list', self.name)


class Disp():
    kind = 'disp'
    def __init__(self, bot, parent, nb, name, caption):
        self.bot = bot
        self.parent = parent
        self.nb = nb
        
        self.name = name
        self.caption = caption

        self.bot.events.add(self.parent, 'ui', 'disp', self.name, 0, 0,
                            'append', self.append,
                            'clear', self.clear)

    def ui_start(self):
        self.text = wx.TextCtrl(self.nb.book, style=wx.TE_MULTILINE |\
                           wx.TE_READONLY | wx.TE_RICH2 | wx.TE_NOHIDESEL |\
                           wx.TE_AUTO_URL)
        self.text.SetBackgroundColour('#000000')
        self.text.SetForegroundColour('#FFFFFF')
        self.parent.frame.Bind(wx.EVT_TEXT_URL, self.txt_url,
                               self.text)
        self.panel = self.text

    def txt_url (self, tue):
        if tue.GetMouseEvent().LeftDown():
            webbrowser.open(tue.EventObject.GetRange(tue.GetURLStart(),
                                                     tue.GetURLEnd()))

    def clear(self):
        self.text.Clear()

    def append (self, *args):
        wx.CallAfter(self.do_addchat, *args)
        
    def do_addchat(self, *args):
        if self.text.GetNumberOfLines() >= 250:
            length = self.text.GetLineLength(0) + 1
            self.text.Remove(0, length)

        self._indivchat('time', strftime('[%I:%M:%S %p] ', localtime()))
            
        if len(args) > 1:
            for x in range(0, len(args), 2):
                self._indivchat(args[x], args[x+1])
        else:
            self._indivchat('info', args[0])

        self.text.AppendText('\n')

    def _indivchat(self, style, text):  
        if style in styles:
            style = wx.TextAttr(styles[style])
        elif style[:4] == 'user':
            style = wx.TextAttr(style[4:])
        else:
            style = wx.TextAttr(style)

        self.text.SetDefaultStyle(style)
        try:
            self.text.AppendText(text)
        except UnicodeDecodeError:
            self.text.SetDefaultStyle(wx.TextAttr('error'))
            self.text.AppendText('<Unicode decode error>')

    def __del__(self):
        self.bot.events.remove('ui', 'disp', self.name)

class Profile ():
    kind = 'profile'
    def __init__ (self, bot, parent, nb, name, caption):
        self.ctrls = {'label': self.label,
                      'big_text': self.big_text,
                      'text': self.text}
        self.bot = bot
        self.parent = parent
        self.nb = nb
        self.name = name
        self.caption = caption
        self.write = {}

    def ui_start(self, name, keys):
        self.writable = (name.lower() == self.bot.status['username'].lower())
        self.username = name
            
        self.panel = wx.Panel(self.nb.book)
        self.grid = wx.GridBagSizer(0, 0)

        self.x = 0
        for key in keys:
            self.grid.Add(self.label(key[0]), wx.GBPosition(self.x, 0),
                          flag=wx.EXPAND)

            self.grid.Add(self.ctrls[key[1]](key),
                          wx.GBPosition(self.x, 1), flag=wx.EXPAND)
            self.x += 1

        if self.writable:
            self.cmd_cancel = wx.Button(self.panel, label='Cancel')
            self.cmd_save = wx.Button(self.panel, label='Save Profile')
            self.cmd_save.SetDefault()

            self.cmd_save.Bind(wx.EVT_BUTTON, self.save)
            self.cmd_cancel.Bind(wx.EVT_BUTTON, self.cancel)
            
            self.grid.Add(self.cmd_cancel, wx.GBPosition(self.x, 0),
                          flag=wx.EXPAND)
            self.grid.Add(self.cmd_save, wx.GBPosition(self.x, 1),
                          flag=wx.EXPAND)

        self.grid.AddGrowableCol(1, 1)
        self.grid.SetFlexibleDirection(wx.BOTH)

        self.panel.SetSizer(self.grid, True) 
        #self.Show(True)

    def save(self, evt):
        key = []
        value = []
        for k,v in self.write.iteritems():
            key.append(k)
            value.append(str(v.GetValue()))
            
        self.bot.events.call('profile', 'write', [self.username, key, value])
        self.nb.page_remove(self.name)

    def cancel(self, evt):
        self.nb.page_remove(self.name)

    def label(self, caption):
        ctrl = wx.StaticText(self.panel, -1, caption + ':',
                             style=wx.ALIGN_RIGHT)
        ctrl.SetBackgroundColour('#000000')
        ctrl.SetForegroundColour('#FFFFFF')
        return ctrl

    def big_text(self, key):
        self.grid.AddGrowableRow(self.x, 1)
        return self.text(key, style=wx.TE_MULTILINE)

    def text(self, key, style=0, **kwargs):
        try:
            if self.writable == False or key[3] == False:
                style |= wx.TE_READONLY
                ctrl = wx.TextCtrl(self.panel, -1, key[2], style=style,
                                   **kwargs)
            else:
                ctrl = wx.TextCtrl(self.panel, -1, key[2], style=style,
                                   **kwargs)
                self.write[key[3]] = ctrl
        except UnicodeDecodeError:
            ctrl = wx.TextCtrl(self.panel, -1,
                               '<There was an error decoding this entry.>',
                               **kwargs)
        ctrl.SetBackgroundColour('#000000')
        ctrl.SetForegroundColour('#FFFFFF')
        return ctrl

types = {'list': List,
         'disp': Disp,
         'profile': Profile}
