import wx
import threading
import time
import extensions

config = {'type': 'wrap',
          'order': 1}

class __init__(threading.Thread):
    """A wrapper plugin, loads all wx plugins after bots have started up"""
    def __init__(self, parent):
        self.library = {}
        self.parent = parent
        self.parent.wx = self
        parent.events.add('wrap', 0, 0,
                          'start', self.start)

        threading.Thread.__init__(self)

    def run (self):
        self.app = wx.PySimpleApp()
        self.parent.wx_app = self.app

        for bot in self.parent.bots:
            bot.ui_loaded = bot.events.call('ui', 'load')

        #self.ui = WrapperUI(self.parent.bots)
            
        self.app.MainLoop()

    def load_library(self, name, cl, *args, **kwargs):
        try:
            return self.library[name]
        except KeyError:
            self.library[name] = cl(*args, **kwargs)
            return self.library[name]


class WrapperUI():
    def __init__(self, bots):
        self.frame = wx.Frame(None, wx.ID_ANY, 'JavaBot Manager',
                              size=(400, 400))

        self.list = wx.ListCtrl(self.frame, style=wx.LC_REPORT |\
                                wx.LC_ALIGN_LEFT | wx.LC_ALIGN_TOP)
        self.list.InsertColumn(0, 'Path')
        self.list.InsertColumn(1, 'Username')
        self.list.InsertColumn(2, 'Status')

        for x in range(len(bots)):
            idx = self.list.InsertStringItem(0, bots[x].cfg_file[1])
            self.list.SetItemTextColour(idx, '#FFFFFF')
            self.list.SetStringItem(idx, 1, bots[x].config['username'])
            self.list.SetStringItem(idx, 2, 'Offline')
            

        self.list.SetBackgroundColour('#000000')

        self.frame.Show(True)

        
