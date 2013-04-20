from hashlib import sha1
from struct import pack, unpack
import os.path

req1 = 0x497FB0
req2 = 0x49C33D
req3 = 0x4A2FF7

def warden_sha1(string):
    return unpack('<5L',
                  sha1(string).digest())
def str_warden_sha1(string):
    return pack('<5L', *warden_sha1(string))
def list_warden_sha1(string):
    return unpack('20B', pack('<5L', *warden_sha1(string)))

def list_to_str(ls):
    ret = ''
    for char in ls:
        ret += str(char)
    return ret

def int_to_str(ls):
    ret = ''
    for char in ls:
        ret += chr(char)
    return ret

class __init__():
    def __init__(self, bot):
        self.bot = bot
        self.key_out = None
        self.key_in = None

        self.bot.events.add(self, 'hashing', 'recv', -1, 0,
                            'cdkey', self.key_hashed)
        self.bot.events.add(self, 'BNCSRecv', 0, 0,
                            0x5E, self.BNCS_0x5E)

    def key_hashed(self):
        if not (self.bot.connfig['login']['product'] in ['SEXP', 'STAR']):
            return
        
        self.seed = self.bot.status['keyhash'][0x10:0x14]
        self.gen = keys(self.seed)
        self.key_out = simple_crypt(self.gen.get_bytes(0x10))
        self.key_in = simple_crypt(self.gen.get_bytes(0x10))

    def BNCS_0x5E(self, packet):
        data = packet['data']
        ret = do_crypt(self.key_in, data)
        pid = ord(ret[0])

        if pid == 0x00:
            data = chr(0x01)
            ret = do_crypt(self.key_out, data)
            self.bot.BNCS.insert_raw(ret)
            self.bot.BNCS.BNCSsend(0x5E)
        elif pid == 0x02:
            if os.path.isfile('StarCraft.exe'):
                evt = ord(ret[1])
                loops = (len(data) - 3) / 7

                f = open('StarCraft.exe', 'rb')
                pos = 2

                addr = []
                vals = []
                for i in range(loops):
                    pos += 2
                    addr.append(unpack('<L', ret[pos:pos+4])[0])
                    pos += 4
                    readlen = ord(ret[pos])
                    pos += 1

                    f.seek(addr[i] - 0x400000)
                    vals.append(f.read(readlen).ljust(readlen, '\0'))

                f.close()

                if addr[0] == req1 and addr[1] == req2 and addr[2] == req3:
                    checksum = 0x193E73E8
                elif addr[0] == req2 and addr[1] == req1 and addr[2] == req3:
                    checksum = 0xD6557DEF
                elif addr[0] == req1 and addr[1] == req3 and addr[2] == req2:
                    checksum = 0x2183172A
                elif addr[0] == req2 and addr[1] == req3 and addr[2] == req1:
                    checksum = 0xCA841860
                elif addr[0] == req3 and addr[1] == req2 and addr[2] == req1:
                    checksum = 0x9F2AD2C3
                elif addr[0] == req3 and addr[1] == req1 and addr[2] == req2:
                    checksum = 0xC04CF757
                else:
                    self.bot.addchat('error', 'Unknown Warden request.')
                    return
                for i in range(loops):
                    self.bot.BNCS.insert_byte(0x00)
                    self.bot.BNCS.insert_raw(vals[i])

                send = self.bot.BNCS.data
                self.bot.BNCS.clear()
                send = chr(0x02) + pack('<HL', len(send), checksum) + send
                self.bot.BNCS.insert_raw(do_crypt(self.key_out, send))
                self.bot.BNCS.BNCSsend(0x5E)
            else:
                self.bot.addchat('error', 'StarCraft.exe is missing. Bot will disconnect in two minutes.')
        else:
            self.bot.addchat('error', 'Unhandled Warden packet.')
            self.bot.addchat('error', ret.encode('hex'))
            self.bot.addchat('error', data.encode('hex'))

class keys():
    def __init__(self, seed):
        self.position = 0
        self.random_data = [0] * 0x14
        self.random_source1 = ''
        self.random_source2 = ''

        length1 = len(seed) >> 1

        seed1 = seed[:length1]
        seed2 = seed[length1:]

        self.random_source1 = str_warden_sha1(seed1)
        self.random_source2 = str_warden_sha1(seed2)

        self.update()
        self.position = 0

    def update(self):
        self.random_data = list_warden_sha1(self.random_source1 +\
                                            int_to_str(self.random_data) +\
                                            self.random_source2)
    def get_byte(self):
        val = self.random_data[self.position]

        self.position += 1
        if self.position >= 0x14:
            self.position = 0
            self.update()

        return val

    def get_bytes(self, num):
        buf = []
        for i in range(num):
            buf.append(self.get_byte())

        return int_to_str(buf)
            

def simple_crypt(base):
    val = 0
    position = 0
    key = range(0x100) + [0, 0]
    base = map(ord, list(base))
    base_len = len(base)

    for i in range(0x00, 0xFF, 0x04):
        for x in range(0, 4):
            val += key[i + x] + base[position % base_len]
            key[i+x], key[val&0xFF] = key[val&0xFF], key[i+x]
            position += 1
    return key

def do_crypt(key, data):
    i = 0
    temp = 0
    data = list(data)

    for i in range(len(data)):
        key[0x100] += 1
        key[0x101] += key[key[0x100] & 0xFF]

        key[key[0x101]&0xFF], key[key[0x100] & 0xFF] = key[key[0x100] & 0xFF], key[key[0x101] & 0xFF]

        data[i] = chr(ord(data[i]) ^ key[(key[key[0x101] & 0xFF] + key[key[0x100] & 0xFF]) & 0xFF])

    return list_to_str(data)
