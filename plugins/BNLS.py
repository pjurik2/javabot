import pbuffer
from struct import unpack
import socket

BNLSProtByte = {'STAR': 0x01,
                'SEXP': 0x02,
                'W2BN': 0x03,
                'D2DV': 0x04,
                'D2XP': 0x05,
                'JSTR': 0x06,
                'WAR3': 0x07,
                'W3XP': 0x08}

class __init__ (pbuffer.conn):
    def __init__(self, bot):
        self.data = ''
        self.connected = False
        
        self.bot = bot
        self.bot.BNLS = self
        
        self.bot.events.add(self, 'BNLSRecv', 0, 0,
                            0x02, self.recv_0x02,
                            0x03, self.recv_0x03,
                            0x04, self.recv_0x04,
                            0x10, self.recv_0x10,
                            0x1A, self.recv_0x1A,
                            0x0C, self.recv_0x0C,
                            0x0B, self.recv_0x0B)

        self.bot.events.add(self, 'BNCSRecv', 1000, 0,
                            0x0A, self.BNLSclose)

        self.bot.events.add(self, 'hashing', 'get', 0, 0,
                            'pwhash', self.send_0x0B,
                            'new_pwhash', self.create_account,
                            'cdkey', self.send_0x0C,
                            'game', self.send_0x1A,
                            'nls_logon', self.send_nls_start,
                            'nls_logon_from_create', self.send_0x02,
                            'nls_logon_proof', self.send_0x03,
                            'nls_create', self.send_0x04)
        
        self.bot.events.add(self, 'bot', 0, 0,
                            'connect', self.BNLSconnect,
                            'disc', self.close)

        if int(self.bot.config['plugins']['gui_wx']) == 0: #GUI disabled
            self.bot.connect()
        
    def BNLSconnect(self, *rest):
        self.bot.addchat('Connecting...')

        try:        
            self.connect(self.bot.config['login']['bnlsserver'], 9367)
            self.bot.add_socket(self.socket, self.BNLSrecv)
        except socket.error, (errno, descr):
            self.bot.addchat('error', 'Error #'+str(errno)+': '+descr)
        except socket.herror, (errno, descr):
            self.bot.addchat('error', 'Address-related error #'+str(errno)+': '+descr)
        except socket.gaierror, (errno, descr):
            self.bot.addchat('error', 'Failed to get address, got error #'+\
                             str(errno)+': '+descr)
        else:
            self.bot.addchat('success', 'Connected to BNLS')
            self.send_0x10()

    def send_nls_start(self, packet):
        self.bot.BNLS.send_0x0D()
        self.bot.BNLS.send_0x02()

    def send_0x02(self, packet=None):
        self.insert_string(self.bot.config['login']['username'])
        
        try:
            self.insert_string(self.bot.config['login']['password'].lower())
        except KeyError, missing:
            self.need_setting(missing, self.send_0x02)
            return
            
        self.BNLSsend(0x02)

    def send_0x03(self, packet=None):
        self.insert_raw(self.bot.status['salt'])
        self.insert_raw(self.bot.status['ckB'])
        self.BNLSsend(0x03)

    def send_0x04(self, packet=None):
        self.insert_string(self.bot.config['login']['username'])
        self.insert_string(self.bot.config['login']['password'].lower())

        self.BNLSsend(0x04)

    def send_0x0B(self, packet=None, flags=0x06):
        try:
            self.insert_long(len(self.bot.config['login']['password']))
        except KeyError, missing:
            self.need_setting(missing, self.send_0x0B)
            return
            
        self.insert_long(flags) #0x02: double hash, 0x04: cookie hash
        self.insert_raw(self.bot.config['login']['password'].lower())
        if (flags & 0x02) == 0x02:
            self.insert_long(self.bot.status['ctoken'])
            self.insert_long(self.bot.status['stoken'])
        self.insert_long(flags) #cookie
        self.BNLSsend(0x0B)

    def send_0x0C(self):
        self.insert_long(0x00)
        if self.bot.config['login']['product'] in ['D2XP', 'W3XP']:
            self.insert_byte(0x02)
        else:
            self.insert_byte(0x01)
        self.insert_long(0x01)
        self.insert_long(self.bot.status['stoken'])

        try:
            self.insert_string(self.bot.config['login']['cdkey'])
        except KeyError, missing:
            self.need_setting(missing, self.send_0x0C)
            return
            
        if self.bot.config['login']['product'] in ['D2XP', 'W3XP']:
            try:
                self.insert_string(self.bot.config['login']['expcdkey'])
            except KeyError, missing:
                self.need_setting(missing, self.send_0x0C)
                return
            
        self.BNLSsend(0x0C)

    def send_0x0D(self, packet=None):
        self.insert_long(self.bot.status['logontype'])
        self.BNLSsend(0x0D)

    def send_0x10(self, packet=None):
        try:
            self.insert_long(BNLSProtByte[self.bot.config['login']['product']])
        except KeyError, missing:
            self.need_setting(missing, self.send_0x10)
            return
            
        self.BNLSsend(0x10)

    def send_0x1A(self, packet=None):
        self.insert_long(BNLSProtByte[self.bot.config['login']['product']])
        self.insert_long(0x00000000)
        self.insert_long(0x00000000)
        self.insert_raw(self.bot.status['mpqtime'])
        self.insert_string(self.bot.status['verfile'])
        self.insert_string(self.bot.status['valstring'])
        
        self.BNLSsend(0x1A)

    def recv_0x02(self, packet):
        data = unpack('<32s', packet['data'])

        self.bot.status['ckA'] = data[0]
        self.bot.events.call('hashing', 'recv', 'nls_logon')

    def recv_0x03(self, packet):
        data = unpack('<20s', packet['data'])

        self.bot.status['M1'] = data[0]
        self.bot.events.call('hashing', 'recv', 'nls_logon_proof')

    def recv_0x04(self, packet):
        data = unpack('<64s', packet['data'])

        self.bot.status['new_wc3_account'] = data[0]
        self.bot.events.call('hashing', 'recv', 'nls_create')

    def recv_0x0B(self, packet):
        results = unpack('<20sl', packet['data'])
        if (results[1] & 0x02) == 0x02:
            self.bot.status['pwhash'] = results[0]
            self.bot.events.call('hashing', 'recv', 'pwhash')
        else:
            self.bot.status['new_pwhash'] = results[0]
            self.bot.events.call('hashing', 'recv', 'new_pwhash')
            return False

    def recv_0x0C(self, packet):
        fmt = '<L2B2L36s'
        if packet['length'] < 50:
            self.bot.addchat('CD-keys failed to hash.')
            return False
        
        if self.bot.config['login']['product'] in ['D2XP', 'W3XP']:
            fmt = fmt+'L36s'
            if packet['length'] < 90:
                self.bot.addchat('CD-keys failed to hash.')
                return False

        results = unpack(fmt, packet['data'])

        if results[1] != results[2]:
            self.bot.addchat('CD-keys failed to hash.')
            return False
        
        self.bot.status['ctoken'] = results[4]
        self.bot.status['keyhash'] = results[5]
        
        if results[1] == 2:
            self.bot.status['expkeyhash'] = results[7]

        self.bot.events.call('hashing', 'recv', 'keyhash')
        return False

    def recv_0x10(self, packet):
        data = unpack('<2L', packet['data'])

        self.bot.status['verbyte'] = data[1]
        
        self.bot.addchat('Verbyte received ('+hex(self.bot.status['verbyte'])+')')

    def recv_0x1A(self, packet):
        sl1 = packet['length'] - 21

        if sl1 < 0:
            self.bot.addchat('Version check failed.')
            return 0
        
        results = unpack('<3L'+str(sl1)+'sx2L', packet['data'])
        
        self.bot.status['version'] = results[1]
        self.bot.status['checksum'] = results[2]
        self.bot.status['vcstatstring'] = results[3]

        self.bot.events.call('hashing', 'recv', 'game')
        return False

    def create_account(self):
        self.send_0x0B(flags=0x04)
        
    def BNLSsend(self, packet):
        self.data = pbuffer.make_word(len(self.data) + 3) + chr(packet) + self.data
        self.send()

    def BNLSrecv(self):
        try:
            header = unpack('<HB', self.recv(3))
        except: #socket died
            self.close()
            return
        
        data = self.recv(header[0] - 3)

        self.bot.events.call('BNLSRecv', header[1],
                             [{'id': header[1],
                               'length': header[0] -3,
                               'data': data}])

    def BNLSclose(self, *rest):
        self.close()
