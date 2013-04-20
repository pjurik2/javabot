from struct import pack

icons = ['D2AM',
'D2SO',
'D2NE',
'D2PA',
'D2BA',
'D2DR',
'D2AS',
         'DXAM',
'DXSO',
'DXNE',
'DXPA',
'DXBA',
'DXDR',
'DXAS']


def str_reverse(string):
    build = ''
    for char in reversed(string):
        build += char

    return build

class builder():
    def __init__(self):
        self.build = ''
        
        f = open('file.tga', 'rb')
        tgaf = f.read()
        f.close()

        self.new_icon(0x00, 28, 14, icons)
        self.make_header()

        f = open('file.bni', 'wb')
        f.write(self.build + tgaf)
        f.close()


    def make_header(self):
        self.build = pack('<L2H2L', len(self.build) + 0x10,
                          0x01,
                          0x00,
                          len(icons),
                          len(self.build) + 0x10) + self.build


    def new_icon(self, flags, width, height, products):
        for x in products:
            self.build += pack('<3L', flags, width, height)
            self.build += str_reverse(x)
            self.build += pack('<L', 0x00000000)
            

        



lol = builder()
