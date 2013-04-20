import wx
from struct import unpack, pack
from os import sep, unlink

bni_pre = ['legacy_icons.bni',
           '0.gif',
           '1.gif',
           '2.gif',
           '3.gif',
           '4.gif',
           '5.gif',
           '6.gif',
           'plug.gif',
           'icons.bni',
           'icons_STAR.bni',
           'w3xp_icons.bni',
           'war3_icons.bni',
           'd2_icons.bni']

class bni():
    def __init__(self, bnis=bni_pre):
        wx.InitAllImageHandlers()
        self.max_height = 18
        self.max_width = 34
        self.count = 0
        self.icon = []
        self.legacy = []
        self.removed = []

        if type(bnis) == list:
            for x in bnis:
                if x[-4:] != '.bni':
                    img = wx.Bitmap('icons' + sep + x, wx.BITMAP_TYPE_GIF)
                    self.legacy.append({'flags': 0,
                                        'width': img.GetWidth(),
                                        'height': img.GetHeight(),
                                        'products': '',
                                        'img': img,
                                        'img_fil': True})
                else:
                    self.load_bni(x)

                    if x == 'legacy_icons.bni':
                        self.legacy = [] + self.icon
                        self.icon = []
        else:
            self.load_bni(bnis)

        self.prod = {}
        self.flag = []
        
        for x in self.icon:
            if x['flags'] != 0:
                self.flag.append(x)
            elif x['products'] != 0:
                for y in x['products']:
                    self.prod[y] = x
                    del self.prod[y]['products']

        self.load_icon_list()

        del self.icon 

    def load_bni(self, fname):
        fname = 'icons' + sep + fname
        f = open(fname, 'rb')
        bni = f.read()
        f.close()

        header = bni[:0x10]
        bni = bni[0x10:]
        length, ver, unused, num_icons, data_start = unpack('<L2H2L', header)

        start = len(self.icon)

        for x in range(num_icons):
            flags, width, height = unpack('<3L', bni[:0x0C])
            bni = bni[0x0C:]

            softwares = []
            end = False
            while end == False:
                new = unpack('<L', bni[:4])[0]
                bni = bni[4:]

                if new == 0x00000000:
                    end = True
                else:
                    softwares.append(pack('>L', new))

            self.icon.append({'flags': flags,
                              'width': width,
                              'height': height,
                              'products': softwares,
                              'img_fil': False})

            self.max_width = max(width, self.max_width)
            self.max_height = max(height, self.max_height)

        f = open('temp.tga', 'wb') #ugh
        f.write(bni)
        f.close()
        img = wx.Bitmap('temp.tga', wx.BITMAP_TYPE_TGA)
        unlink('temp.tga')
        
        self.get_subs(img, start)

    def load_icon_list(self):
        il = wx.ImageList(self.max_width, self.max_height)
        icons = None

        self.pt = wx.Point(0, 0)
        self.sz = wx.Size(self.max_width, self.max_height)

        for v in self.legacy:
            self.resize(v)
            if v['img_fil']:
                v['idx'] = il.Add(v['img'])
                #v['idx'] = il.AddWithColourMask(v['img'], '#000000')
            else:
                v['idx'] = il.Add(v['img'])
                #v['idx'] = il.AddWithColourMask(v['img'], '#000000')

        for v in self.flag:
            self.resize(v)
            v['idx'] = il.Add(v['img'])
            #v['idx'] = il.AddWithColourMask(v['img'], '#000000')
            
        for k, v in self.prod.iteritems():
            self.resize(v)
            self.prod[k]['idx'] = il.Add(v['img'])
            #self.prod[k]['idx'] = il.AddWithColourMask(v['img'], '#000000')

        self.il = il
        del self.pt
        del self.sz

    def resize(self, v):
        if v['height'] != self.max_height or\
           v['width'] != self.max_width:
            img = v['img'].ConvertToImage()
            img.Resize(self.sz, self.pt, 0, 0, 0)
            v['img'] = wx.BitmapFromImage(img)

        self.count += 1

    def remove(self, idx):
        self.removed.append(idx)
        self.il.Replace(idx, wx.EmptyBitmap(self.max_width, self.max_height))

    def add(self, bitm):
        if len(self.removed) != 0:
            idx = self.removed.pop(0)
            self.il.Replace(idx, bitm)
        else:
            idx = self.il.Add(bitm)

        return idx

    def get_subs(self, img, start):
        y = 0

        for k in range(start, len(self.icon)):
            self.icon[k]['img'] = img.GetSubBitmap(wx.Rect(0, y,
                                                   self.icon[k]['width'],
                                                   self.icon[k]['height']))
            y += self.icon[k]['height']
