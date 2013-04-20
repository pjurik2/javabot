import wx
import wx.aui
from os import sep
import datetime
import ConfigParser

from books import Book
from bni import bni

class __init__():
    def __init__(self, bot):
        
        self.icons = {}
        
        self.queue = []
        self.delay = 0

        self.menu = {}
        self.menu_count = 1
        
        self.req = {'enabled': False}
        self.bot = bot

        self.bot.events.add('ui', 0, 0,
                            'load', self.load_gui)

        if self.bot.ui_loaded:
            wx.CallAfter(self.load_gui)

    def load_gui(self):
        self.wrapper = self.bot.wrapper.wx
        self.bni = self.wrapper.load_library('bni', bni)
        
        #GUI - START
        self.frame = wx.Frame(None, wx.ID_ANY, self.bot.ver(), size=(800, 450))
        self.panel = wx.Panel(self.frame)

        #TASK BAR ICON
        self.tray_icon = wx.Icon('icons' + sep + 'tray_icon.gif', wx.BITMAP_TYPE_GIF)
        self.tb_icon = wx.TaskBarIcon()

        self.frame.Bind(wx.EVT_ICONIZE, self.create_icon)
        self.tb_icon.Bind(wx.EVT_TASKBAR_LEFT_UP, self.remove_icon)

        self.frame.SetIcon(self.tray_icon)

        #MENU BAR
        self.menu_bar = wx.MenuBar()
        self.frame.SetMenuBar(self.menu_bar)

        #CHAT BOX, SEND BOX, CHANNEL HEADER
        self.nb_disp = Book('disp', self.bot, self, self.panel,
                            wx.aui.AUI_NB_WINDOWLIST_BUTTON |\
                            wx.aui.AUI_NB_CLOSE_BUTTON |\
                            wx.aui.AUI_NB_CLOSE_ON_ALL_TABS |\
                            wx.aui.AUI_NB_SCROLL_BUTTONS)

        self.txt_chat()
        self.bot.events.add(self, 'ui', 'disp', 'closed', 0, 0,
                            'main', self.txt_chat)
        
        self.cb_send = wx.ComboBox(self.panel, style=wx.CB_DROPDOWN |\
                                   wx.TE_PROCESS_ENTER)
        self.frame.Bind(wx.EVT_TEXT_ENTER, self.send_text, self.cb_send)
        self.frame.Bind(wx.EVT_TEXT_PASTE, self.text_pasted, self.cb_send)

        #CHANNEL LIST
        self.nb_list = Book('list', self.bot, self, self.panel,
                            wx.aui.AUI_NB_WINDOWLIST_BUTTON |\
                            wx.aui.AUI_NB_BOTTOM |\
                            wx.aui.AUI_NB_SCROLL_BUTTONS)

        #COLOURS - Inherit doesn't work for me ;(
        self.cb_send.SetBackgroundColour('#000000')
        self.cb_send.SetForegroundColour('#FFFFFF') 

        #SIZING / POSITIONING
        self.grid = wx.GridBagSizer()
        self.grid.Add(self.cb_send, wx.GBPosition(1, 0), flag=wx.EXPAND)
        self.grid.Add(self.nb_list.book, wx.GBPosition(0, 1),
                      flag=wx.EXPAND,
                      span=wx.GBSpan(2, 1))
        self.grid.Add(self.nb_disp.book, wx.GBPosition(0, 0), flag=wx.EXPAND)

        #SIZING - RESIZING
        self.grid.AddGrowableCol(0, 1)
        self.grid.AddGrowableRow(0, 1)
        self.grid.SetFlexibleDirection(wx.BOTH)

        #SIZING - MINIMUMS
        self.nb_disp.book.SetSizeHints(1, 1)
        self.nb_list.book.SetSizeHints(300, 1)
 
        #GET READY
        self.panel.SetSizerAndFit(self.grid, True)
        self.frame.Show(True)

        self.add_events()

        #ADDCHAT READY
        self.bot.addchat(self.bot.ver())

        self.bot.events.call('ui', 'start')
        self.menu_add('Window',
                      'Clear current display(s)\tCTRL-S', self.clear_chat)

        if self.bot.ui_loaded:
            self.bot.events.call('ui', 'reload')
        
        self.cb_send.SetFocus()

    def txt_chat(self, name=''):
        self.nb_disp.page_add('disp', 'main', 'Main')

    def text_pasted(self, event):
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                wx.TheClipboard.GetData(data)
                msg = str(data.GetText())

                if msg.find('\n') == -1:
                    event.Skip(True)
                else:
                    for line in msg.split('\n'):
                        line = line.strip('\n\r')
                        if line != '':
                            self.bot.send(line)
                            self.cb_send.Insert(line, 0)

            wx.TheClipboard.Close()

    def menu_add(self, *rest):
        wx.CallAfter(self.do_menu_add, *rest)

    def do_menu_add(self, menu, *rest):
        key = menu.lower()
        if (key in self.menu) == False:
            self.menu[key] = (wx.Menu(), self.menu_bar.GetMenuCount())
            self.menu_bar.Append(self.menu[key][0], menu)

        for x in range(0, len(rest), 2):
            mi = wx.MenuItem(self.menu[key][0], self.menu_count,
                             rest[x])
            self.menu[key][0].AppendItem(mi)
            wx.EVT_MENU(self.frame, self.menu_count, rest[x+1])
            self.menu_count += 1

    def menu_remove(self, menu):
        try:
            self.menu_bar.Remove(self.menu[menu][1])
            self.menu[menu][0].Destroy()
            del self.menu[menu]
        except KeyError:
            pass
        
    def add_events(self):
        self.bot.events.add(self, 'IO', -1, -1,
                            'addchat', self.main_addchat,
                            'input', self.req_input)

        self.bot.events.add(self, 'ui', 'menu', 0, 0,
                            'add', self.menu_add,
                            'remove', self.menu_remove)

        self.bot.events.add(self, 'ui', 0, 0,
                            'config', self.show_config,
                            'confirm', self.confirm,
                            'get_profile', self.request_profile)

        self.bot.events.add(self, 'ui', 'send', 0, 0,
                            'send', self.send_send,
                            'clear', self.clear_send)

        self.bot.events.add(self, 'profile', 0, 0,
                            'received', self.got_profile)

    def load_icons(self, x=28, y=14, **kwargs):
        if kwargs == {}:
            il = self.bni.il
            icons = None
            count = self.bni.count
            
        else:        
            il = wx.ImageList(x, y)
            icons = {}
            count = 0
            for k, v in kwargs.iteritems():
                icons[k] = il.Add(wx.Bitmap(v))
                count += 1
                
        return icons, il, count

    def get_lag_idx(self, arg):
        ping, flags = arg
        if (flags & 0x10) == 0x10:
            return self.bni.legacy[49]['idx']
        elif ping <= 0:
            return self.bni.legacy[42]['idx']
        elif ping < 200:
            return self.bni.legacy[43]['idx']
        elif ping > 700:
            return self.bni.legacy[48]['idx']
        else:
            return self.bni.legacy[ping / 100 + 42]['idx']

    def get_bni_idx(self, user, draw):
        il = self.bni.il
        try:
            icon = user['icon'][-4:] or user['product'][-4:]
        except KeyError:
            icon = user['product'][-4:]
        flags = user['flags']

        idx = -1
        for x in self.bni.flag:
            if (flags & x['flags']) == x['flags']:
                idx = x['idx']
                return idx

        if (icon in ['STAR', 'SEXP', 'SSHR', 'JSTR']):
            try:
                if user['ladder_rank'] != 0:
                    if user['ladder_rank'] == 1:
                        idx = self.bni.legacy[13]['idx']
                    else:
                        idx = self.bni.legacy[12]['idx']
                elif user['ladder_rating'] != 0:
                    idx = self.bni.legacy[11]['idx']
                elif user['wins'] > 0:
                    idx = ((user['wins'] > 10) and 10) or\
                            user['wins']
                    idx = self.bni.legacy[idx]['idx']
                    return idx
            except KeyError:
                pass

        elif icon == 'W2BN':
            try:
                if user['ladder_rank'] != 0:
                    if user['ladder_rank'] == 1:
                        idx = self.bni.legacy[28]['idx']
                    else:
                        idx = self.bni.legacy[26]['idx']
                elif user['ladder_rating'] != 0:
                    idx = self.bni.legacy[25]['idx']
                elif user['wins'] > 0:
                    idx = (((user['wins'] > 10) and 10) or\
                            user['wins']) + 14
                    return idx
            except KeyError:
                pass
                
        elif icon in ['DRTL', 'DSHR']:
            try:
                if user['class_num'] != -1:
                    idx = 30 + user['class_num'] + 3 * user['dots']
            except KeyError:
                pass
        elif user['product'] in ['WAR3', 'W3XP']:
            try:
                if user['level'] == 0:
                        icon = user['product'] #Override to more specific icon
            except KeyError:
                icon = user['product']
        if idx == -1:
            try:
                idx = self.bni.prod[icon]['idx']
            except KeyError:
                return -1

        if 'level' in user:
            if user['level'] == 0:
                return idx
            bitm = il.GetBitmap(idx)
            mdc = wx.MemoryDC(bitm)
            mdc.SetTextForeground('#3399FF')
            font = wx.Font(6, wx.FONTFAMILY_ROMAN,
                           wx.FONTSTYLE_NORMAL,
                           wx.FONTWEIGHT_NORMAL)
            mdc.SetFont(font)
            if user['product'] in ['WAR3', 'W3XP']:
                mdc.DrawText(str(user['level']), 22, 3)
            elif user['product'] in ['DRTL', 'DSHR']:
                mdc.DrawText(str(user['level']), 16, 3)
            elif user['product'] in ['D2DV', 'D2XP']:
                mdc.DrawText(str(user['level']), 16, 3)

            mdc.SelectObjectAsSource(wx.NullBitmap)
            idx = self.bni.add(bitm)
            draw.append(idx)
            return idx

        if 'ladder_rating' in user:
            if user['ladder_rating'] == 0:
                return idx

            bitm = il.GetBitmap(idx)
            mdc = wx.MemoryDC(bitm)
            font = wx.Font(6, wx.FONTFAMILY_ROMAN,
                               wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_NORMAL)
            mdc.SetFont(font)
            mdc.SetTextForeground('#FFFFFF')
            mdc.DrawText(str(user['ladder_rating']), 5, 3)
            #if user['ladder_rank'] != 0:
            #    mdc.SetTextForeground('#3399FF')
            #    mdc.DrawText(str(user['ladder_rank']), 26, 10)
            #Not enough space anymore
            mdc.SelectObjectAsSource(wx.NullBitmap)
                
            idx = self.bni.add(bitm)
            draw.append(idx)
            return idx

        return idx

    def notify_tab(self, msg):
        idx, name, kind = self.nb_disp.page_current()
        keep = [name, msg]
        self.bot.events.call('ui', kind, name, 'send', [keep])
        msg = keep[1]

        idx, name, kind = self.nb_list.page_current()
        keep = [name, msg]
        self.bot.events.call('ui', kind, name, 'send', [keep])

        return keep[1]

    def confirm(self, title, msg, func_yes, func_no=None):
        md = wx.MessageDialog(self.panel, msg, title, wx.YES_NO | wx.ICON_QUESTION)
        if md.ShowModal() == wx.ID_YES:
            func_yes()
        else:
            if func_no != None:
                func_no()

    def create_icon(self, evt_icon):
        if evt_icon.Iconized():
            self.tb_icon.SetIcon(self.tray_icon)
            self.frame.Lower()
            self.frame.Show(False)
        
    def remove_icon(self, *rest):
        self.tb_icon.RemoveIcon()
        self.frame.Restore()
        self.frame.Raise()
        self.frame.Show(True)

    def send_send(self, pre='', post='', clear=True):
        self.cb_send.SetValue(str(self.cb_send.GetValue()))
        self.send_text(clear=clear, pre=pre, post=post)

    def request_profile(self, names):
        self.bot.events.call('profile', 'request', name)
        
    def got_profile(self, names, results):
        wx.CallAfter(self.got_profile2,
                     names,
                     results)

    def got_profile2(self, name, keys):
        self.nb_disp.page_add('profile', 'prof_'+name, 'Profile: ' + name,
                              name, keys, select=True)
            
    def req_input(self, req):
        self.bot.addchat('info', req['query'])
        self.req = req
        self.req['enabled'] = True

    def show_config(self, *rest):
        self.config = Config(self.bot)

    def clear_chat(self, cmd=None):
        idx, name, kind = self.nb_disp.page_current()
        if kind == 'disp':
            self.bot.events.call('ui', kind, name, 'clear')

        idx, name, kind = self.nb_list.page_current()
        if kind == 'disp':
            self.bot.events.call('ui', kind, name, 'clear')
        
    def send_text(self, wtf=0, clear=True, pre='', post=''):
        msg = pre+str(self.cb_send.GetValue())+post
        if msg == '':
            return

        if self.req['enabled'] == False:
            msg = self.notify_tab(msg)
            self.bot.send(msg)
        else:
            self.req['enabled'] = False #Can't delete req dict. ret_func disappears
            self.req['ret_func'](msg)

        if clear == True:
            self.clear_send()
        self.cb_send.Insert(msg, 0)

    def clear_send(self):
        self.cb_send.SetValue('')

    def main_addchat(self, *args):
        self.bot.events.call('ui', 'disp', 'main', 'append', list(args))

    def __del__(self, *rest):
        self.frame.Destroy()

class Config (wx.Frame):
    def __init__(self, bot):

        self.obj_types = {'text': self.text,
                          'list': self.combo,
                          'checkbox': self.check_box}

        self.bot = bot
        
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          'Settings: ' + self.bot.cfg_file[1], size=(350, 325))
        self.panel = wx.Panel(self)

        self.grid = wx.GridBagSizer(4, 4)
        self.notebook = wx.Notebook(self.panel)

        self.cmd_save =  wx.Button(self.panel, label='Apply and Close')
        self.cmd_cancel = wx.Button(self.panel, label='Cancel')

        self.cmd_save.SetDefault()

        self.Bind(wx.EVT_BUTTON, self.save_settings, self.cmd_save)
        self.Bind(wx.EVT_BUTTON, self.cancel, self.cmd_cancel)

        self.grid.Add(self.notebook, wx.GBPosition(0, 0), span=wx.GBSpan(1, 2), flag=wx.EXPAND)
        self.grid.Add(self.cmd_cancel, wx.GBPosition(1, 0), flag=wx.EXPAND)
        self.grid.Add(self.cmd_save, wx.GBPosition(1, 1), flag=wx.EXPAND)

        self.grid.AddGrowableRow(0, 1)
        self.grid.AddGrowableCol(1, 1)
        self.grid.SetFlexibleDirection(wx.BOTH)

        self.panel.SetSizer(self.grid, True) 
        self.Show(True)

        self.load_notebook()

    def load_notebook(self):
        self.settings = []

        self.bot.events.call('bot', 'configure', [self.settings])

        for sect in self.settings:
            sect['panel'] = wx.Panel(self.notebook)
            sect['grid'] = wx.GridBagSizer(4, 4)

            if ('file' in sect) == False:
                sect['file'] = self.bot.cfg_file[1]

            self.x = 0
            
            for x in range(0, len(sect['settings'])):
                sect['settings'][x] = self.get_keys(sect['settings'][x])
                setting = sect['settings'][x]
                
                if setting['value'] == '' and setting['key'] in sect['dict']:
                    setting['value'] = sect['dict'][setting['key']]

                setting['obj'] = self.obj_types[setting['type'][0]](sect, setting, *setting['type'][1:])

                self.x += 1

            sect['grid'].AddGrowableCol(1, 1)
                

            sect['panel'].SetSizerAndFit(sect['grid'], True)
            self.notebook.AddPage(sect['panel'], sect['caption'])

    def get_keys(self, setting):
        wtf = {'caption': setting['key'].capitalize(),
               'value': '',
               'type': ('text',)}
        wtf.update(setting)
        return wtf
        
    def label(self, parent, caption):
        return wx.StaticText(parent, -1, caption + ':', style=wx.ALIGN_RIGHT)
    
    def text(self, sect, setting, styl=0):
        tc = wx.TextCtrl(sect['panel'], -1, str(setting['value']), style=styl)
        st = self.label(sect['panel'], setting['caption'])
        self.place_default(sect['grid'], st, tc)

        return tc

    def combo(self, sect, setting, opts=[], styl=wx.CB_DROPDOWN):
        cb = wx.ComboBox(sect['panel'], value=setting['value'], choices=opts, style=styl)
        st = self.label(sect['panel'], setting['caption'])
        self.place_default(sect['grid'], st, cb)

        return cb

    def check_box(self, sect, setting, styl=0):
        cb = wx.CheckBox(sect['panel'], -1, setting['caption'], style=styl)
        cb.SetValue(setting['value'])
        self.place_alone(sect['grid'], cb)

        return cb

    def place_default(self, grid, st, ctrl):
        grid.Add(st, wx.GBPosition(self.x, 0), flag=wx.EXPAND)
        grid.Add(ctrl, wx.GBPosition(self.x, 1), flag=wx.EXPAND)

    def place_alone(self, grid, ctrl):
        grid.Add(ctrl, wx.GBPosition(self.x, 1), flag=wx.EXPAND)

    def save_settings(self, *rest):
        for sect in self.settings:
            cp_config = ConfigParser.ConfigParser()

            try:
                cp_config.readfp(open(sect['file']))
            except:
                pass
            if cp_config.has_section(sect['title']) == False:
                cp_config.add_section(sect['title'])

            for setting in sect['settings']:
                if 'section' in setting:
                    if setting['section'] != sect['title']:
                        if cp_config.has_section(setting['section']) == False:
                            cp_config.add_section(setting['section'])
                else:
                    setting['section'] = sect['title']

                cp_config.set(setting['section'], setting['key'],
                              setting['obj'].GetValue())

            cp_config.write(open(sect['file'], 'w'))
                
        self.Destroy()
        self.bot.events.call('bot', 'load_config')
        del self

    def cancel(self, *rest):
        self.Destroy()
        del self
