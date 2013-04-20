import pbuffer

from struct import pack, unpack
import socket
import time
from threading import Timer

logon_type = {0x00: 'Broken SHA-1 (STAR/SEXP/D2DV/D2XP)',
              0x01: 'NLS version 1 (War3Beta)',
              0x02: 'NLS Version 2 (WAR3/W3XP)'}
vc_results = {0x100: 'Old game version, need patch %r%',
              0x101: 'Invalid version',
              0x102: 'Game version must be downgraded to %r%',
              0x200: 'Invalid CD key',
              0x201: 'CD key in use by %r%',
              0x202: 'CD key is banned',
              0x203: 'Wrong product for this CD key',
              0x210: 'Invalid expansion CD key',
              0x211: 'Expansion CD key in use by %r%',
              0x212: 'Expansion CD key is banned',
              0x213: 'Wrong product for this expansion CD key'}
reg_error = {0x02: 'Name contained invalid characters',
             0x03: 'Name contained a banned word',
             0x04: 'Account already exists',
             0x06: 'Name did not contain enough alphanumeric characters',
             0x07: 'Name is too short/blank.',
             0x08: 'Name contains an illegal character.',
             0x09: 'Name contains an illegal word.',
             0x0a: 'Name contains too few alphanumeric characters.',
             0x0b: 'Name contains adjacent punctuation characters.',
             0x0c: 'Name contains too many punctuation characters.'}

class __init__ (pbuffer.conn):
    def __init__(self, bot):
        self.data = ''
        self.connected = False
        
        self.bot = bot
        self.bot.BNCS = self

        self.conn_attempts = 0
        self.conn_timer = None
        self.conn_idle = None
        self.conn_tick = 0

        self.bot.events.add(self, 'BNCSRecv', -1, 0,
                            0x0A, self.recv_0x0A,
                            0x0F, self.recv_0x0F,
                            0x29, self.recv_0x29,
                            0x3D, self.recv_0x3D,
                            0x50, self.recv_0x50,
                            0x51, self.recv_0x51,
                            0x52, self.recv_0x52,
                            0x53, self.recv_0x53,
                            0x54, self.recv_0x54)

        #Send after handling
        self.bot.events.add(self, 'BNCSRecv', 1000, 0,
                            0x25, self.send_0x25,
                            0x29, self.enter_chat,
                            0x3D, self.send_0x29,
                            0x51, self.send_0x14,
                            0x54, self.enter_chat)

        self.bot.events.add(self, 'BNLSRecv', 1000, 0,
                            0x0C, self.send_0x51,
                            0x10, self.BNCSconnect)

        self.bot.events.add(self, 'hashing', 'recv', 0, 0,
                            'pwhash', self.send_0x29,
                            'new_pwhash', self.send_0x3D,
                            'cdkey', self.send_0x51,
                            'game', self.send_0x51,
                            'nls_logon', self.send_0x53,
                            'nls_logon_proof', self.send_0x54,
                            'nls_create', self.send_0x52)

        self.bot.events.add(self, 'IO', 249, 0,
                            'send', self.send_split)

        self.bot.events.add(self, 'IO', 500, 0,
                            'send', self.send_chat)

        self.bot.events.add(self, 'bot', 0, 0,
                            'disc', self.BNCSclose,
                            'idle', self.send_0x00)
    def send_split(self, text):
        if len(text['text']) > 224: #IF message is too long
            txt = text['text']
            del text['text']
            while txt != '':
                start = txt[:224]
                if len(start) >= 224:
                    idx = start.rfind(' ')
                    if idx == -1:
                        idx = len(start)
                        stidx = idx
                    else:
                        stidx = idx + 1
                    txt = txt[stidx:]

                    self.bot.send(start[:idx], **text)
                else:
                    self.bot.send(start, **text)
                    txt = ''
                
                    
            return False

    def send_chat(self, text):
        try:    
            self.insert_string(text['text'])
            self.BNCSsend(0x0E)
            
        except socket.error, (errno, descr):
            self.clear()
            #self.bot.addchat('error', 'Cannot send message. Error #'+str(errno)+': '+descr)
        except AttributeError:
            self.clear() #Not yet connected

    def BNCSconnect(self, *args, **kwargs):
        if 'server' in kwargs:
            server = kwargs['server']
        else:
            server = self.bot.config['login']['server']

        try:        
            self.connect(server, 6112)
            self.bot.add_socket(self.socket, self.BNCSrecv)
        except socket.error, (errno, descr):
            self.bot.addchat('error', 'Error #'+str(errno)+': '+descr)
        except socket.herror, (errno, descr):
            self.bot.addchat('error', 'Address-related error #'+str(errno)+': '+descr)
        except socket.gaierror, (errno, descr):
            self.bot.addchat('error', 'Failed to get address, got error #'+\
                             str(errno)+': '+descr)
        except KeyError, missing:
            self.bot.need_setting(missing, self.BNCSconnect)
        except:
            self.bot.addchat('error', 'Connection attempt failed for an unknown reason')
        else:
            self.bot.addchat('success', 'Connected to Battle.net')
            self.send_0x50()
            return

        self.reconnect()


    def reconnect(self):
        conn_time = (30 * self.conn_attempts)
        self.bot.addchat('Reconnecting in ' + str(conn_time) + ' seconds.')
        self.conn_timer = Timer(30 * self.conn_attempts, self.bot.connect)
        self.conn_timer.start()
        self.conn_attempts += 1

    def BNCSclose(self):
        if self.conn_timer != None:
            self.conn_timer.cancel()
            self.conn_attempts = 0

        if self.conn_idle != None:
            self.conn_idle.cancel()

        self.close()

    def idle_func(self):
        if self.bot.status['connected']:
            self.conn_tick += 1
            self.bot.events.call('bot', 'idle', [self.conn_tick])
            self.conn_idle = Timer(60, self.idle_func)
            self.conn_idle.start()
        else:
            self.conn_idle = None
            self.conn_tick = 0

    def send_0x00(self, tick):
        if tick % 7 == 0:
            self.BNCSsend(0x00)

    def send_0x14(self, packet=None):
        if self.bot.config['login']['product'] in\
           ['STAR', 'SEXP', 'DSHR', 'W2BN', 'SSHR', 'JSTR', 'DRTL']:
            self.insert_raw('tenb')
            self.BNCSsend(0x14)

    def send_0x25(self, packet):
        self.insert_raw(packet['data'])
        self.BNCSsend(0x25)
		
    def send_0x29(self, packet=None):
        self.bot.addchat('Sending login information...')
        self.insert_long(self.bot.status['ctoken'])
        self.insert_long(self.bot.status['stoken'])
        self.insert_raw(self.bot.status['pwhash'])
        self.insert_string(self.bot.config['login']['username'])
        self.BNCSsend(0x29)

    def send_0x3D(self, packet=None):
        self.insert_raw(self.bot.status['new_pwhash'])
        self.insert_string(self.bot.config['login']['username'])
        self.BNCSsend(0x3D)
        
    def send_0x50(self, packet=None):
        try:
            self.bot.status['product'] = unpack('>L', self.bot.config['login']['product'])[0]
        except KeyError, missing:
            self.need_setting(missing, self.send_0x50)
            return
        
        self.insert_byte(0x01)
        self.send()
        self.insert_long(0x00)
        self.insert_raw('68XI')
        self.insert_long(self.bot.status['product'])
        self.insert_long(self.bot.status['verbyte'])
        self.insert_long(0x00)
        self.insert_long(0x00)
        self.insert_long(0x00)
        self.insert_long(0x00)
        self.insert_long(0x00)
        self.insert_string('USA')
        self.insert_string('United States')

        self.BNCSsend(0x50)

    def send_0x51(self, packet=None):
        if ('keyhash' in self.bot.status) == False or\
           ('version' in self.bot.status) == False:
            return #Not ready
        
        self.insert_long(self.bot.status['ctoken'])
        self.insert_long(self.bot.status['version'])
        self.insert_long(self.bot.status['checksum'])
        if self.bot.connfig['login']['product'] in ['D2XP', 'W3XP']:
            self.insert_long(2)
        else:
            self.insert_long(1)
        self.insert_long(0) #Spawn?

        self.insert_raw(self.bot.status['keyhash'])
        if self.bot.config['login']['product'] in ['D2XP', 'W3XP']:
            self.insert_raw(self.bot.status['expkeyhash'])

        self.insert_string(self.bot.status['vcstatstring'])

        try:
            self.insert_string(self.bot.config['login']['username'])
        except KeyError, missing:
            self.need_setting(missing, self.send_0x51)
            return
            
        self.BNCSsend(0x51)

    def send_0x52(self, packet=None):
        self.insert_raw(self.bot.status['new_wc3_account'])
        self.insert_string(self.bot.config['login']['username'])

        self.BNCSsend(0x52)

    def send_0x53(self, packet=None):
        self.bot.addchat('Sending login information...')
        self.insert_raw(self.bot.status['ckA'])
        self.insert_string(self.bot.config['login']['username'])

        self.BNCSsend(0x53)

    def send_0x54(self, packet=None):
        self.insert_raw(self.bot.status['M1'])
        self.BNCSsend(0x54)

    def enter_chat(self, packet=None):
        if self.bot.config['login']['product'] in ['WAR3', 'W3XP']:
            self.insert_byte(0x00)
        else:
            self.insert_string(self.bot.config['login']['username'])
        self.insert_byte(0x00)
        self.BNCSsend(0x0A)

        if self.bot.config['login']['home'] == '':
            self.insert_long(0x03)
            self.insert_string('wrd1730')
        else:
            self.insert_long(0x02)
            self.insert_string(self.bot.config['login']['home'])

        self.BNCSsend(0x0C)

    def recv_0x0A(self, packet):
        sl1 = packet['data'].find('\0', 0)
        sl2 = packet['data'].find('\0', 1+sl1) - (1+sl1)
        sl3 = packet['data'].find('\0', 2+sl1+sl2) - (2+sl1+sl2)

        results = unpack('<'+str(sl1)+'sx'+str(sl2)+'sx'+str(sl3)+'sx', packet['data'])
        
        self.bot.addchat('success', 'You are now logged in as '+results[0]+'.')

        self.bot.events.call('bot', 'connected', [results[0]])
        self.bot.status['username'] = results[0]

        self.conn_idle = Timer(60, self.idle_func)
        self.conn_idle.start()
        self.conn_attempts = 0
        self.conn_tick = 0
        
    def recv_0x0F(self, packet):
        if len(packet['data']) < 26:
            self.bot.addchat('error', 'Malformed chat packet')
            self.bot.addchat('error', 'Length: ' + str(len(packet['data'])) +\
                             '///' + str(packet['length']))
            try:
                self.bot.addchat('error', packet['data'])
            except UnicodeDecodeError:
                self.bot.addchat('error', '<Can\'t output raw data')

            self.bot.addchat('error', pbuffer.debug_output(packet['data']))
            return
        username, text = packet['data'][24:-1].split('\0', 1)
        
        results = unpack('<6l', packet['data'][:24])

        ref = {'id': results[0],
               'flags': results[1],
               'ping': results[2],
               'username': username,
               'text': text}

        if results[0] < 0x03 or results[0] == 0x09 and len(text) >= 4:
            ref['product'] = text[3] + text[2] + text[1] + text[0]
        else:
            ref['product'] = 'NULL'

        d2format = ref['username'].find('*')

        if d2format != -1:
            ref['username'] = ref['username'][d2format+1:]

        self.bot.events.call('BNCSChat', results[0], [ref])

    def recv_0x29(self, packet):
        results = unpack('<L', packet['data'])
        
        if results[0] == 0x00:
            self.bot.addchat('Login failed')
            self.bot.events.call('hashing', 'get', 'new_pwhash')
            return False
        else:
            self.bot.addchat('Login successful')

    def recv_0x3D(self, packet):
        if len(packet['data']) == 4:
            results = unpack('<L', packet['data'])
        else:
            sl1 = len(packet['data']) - 5
            
            results = unpack('<L'+str(sl1)+'sx', packet['data'])

        if results[0] == 0x00:
            self.bot.addchat('success', 'Account "'+self.bot.config['login']['username']+'" created')
            
        else:
            self.bot.addchat('error', 'Account "'+self.bot.config['login']['username']+'" creation failed. '+reg_error[results[0]])
            return False

    def recv_0x50(self, packet):
        sl1 = packet['data'].find('\0', 20) - 20
        sl2 = packet['data'].find('\0', 21+sl1) - (21+sl1)
        
        fmt = '<3L8s'+str(sl1)+'sx'+str(sl2)+'sx'
        if self.bot.config['login']['product'] in ['WAR3', 'W3XP']:
            fmt=fmt+'128s'

        results = unpack(fmt, packet['data'])

        try:
            self.bot.addchat('Logon type '+logon_type[results[0]]+' recognized')
        except:
            self.bot.addchat('error', 'Logon type not recognized.')
            return False
            
        self.bot.status['logontype'] = results[0]
        self.bot.status['stoken'] = results[1]
        self.bot.status['udpval'] = results[2]
        self.bot.status['mpqtime'] = results[3]
        self.bot.status['verfile'] = results[4]
        self.bot.status['valstring'] = results[5]

##        print self.bot.status['verfile']
##        print self.bot.status['verfile'].encode('hex')
##        print self.bot.status['valstring']
##        print self.bot.status['valstring'].encode('hex')

        self.bot.events.call('hashing', 'get', 'cdkey')
        self.bot.events.call('hashing', 'get', 'game')
        
    def recv_0x51(self, packet):
        sl1 = packet['length'] - 5

        results = unpack('<L'+str(sl1)+'sx', packet['data'])

        if results[0] == 0x000:
            self.bot.addchat('success', 'Version check passed. CD key is valid.')
            if (self.bot.connfig['login']['product'] in ['WAR3', 'W3XP']):
                self.bot.events.call('hashing', 'get', 'nls_logon')
            else:
                self.bot.events.call('hashing', 'get', 'pwhash')
            return True
        elif results[0] in vc_results:
            try:
                extra = unicode(results[1])
            except UnicodeDecodeError:
                self.bot.addchat('error', vc_results[results[0]])
                print vc_results[results[0]].replace('%r%', results[1])
            else:
                self.bot.addchat('error', vc_results[results[0]].replace('%r%', results[1]))
            
        else:
            self.bot.addchat('error', 'Invalid version code. (' + hex(results[0]) + ':' + results[1] + ')')

        return False

    def recv_0x52(self, packet):
        results = unpack('<L', packet['data'])

        if results[0] == 0x00:
            self.bot.addchat('success', 'Account "'+self.bot.config['login']['username']+'" created')
            self.bot.events.call('hashing', 'get', 'nls_logon_from_create')
        else:
            try:
                self.bot.addchat('error', 'Account "'+self.bot.config['login']['username']+'" creation failed. '+reg_error[results[0]])
            except KeyError:
                self.bot.addchat('error', 'Account "'+self.bot.config['login']['username']+'" creation failed. Account already exists.')
            return False

    def recv_0x53(self, packet):
        results = unpack('<L32s32s', packet['data'])
        self.bot.status['salt'] = results[1]
        self.bot.status['ckB'] = results[2]

        if results[0] == 0x00:
            self.bot.events.call('hashing', 'get', 'nls_logon_proof')
        elif results[0] == 0x01:
            self.bot.addchat('error', 'Account does not exist')
            self.bot.events.call('hashing', 'get', 'nls_create')
            return False
        else:
            self.bot.addchat('error', 'Login failed.')
            return False

    def recv_0x54(self, packet):
        if packet['length'] > 24:
            sl1 = packet['length'] - 25
            results = unpack('<L20s'+str(sl1)+'sx', packet['data'])
        else:
            results = unpack('<L20s', packet['data'])

        if results[0] in [0x00, 0x0E]:
            self.bot.addchat('success', 'Login successful.')
        else:
            self.bot.addchat('error', 'Login failed.')
            return False

        self.bot.status['M2'] = results[1]

        
    def BNCSsend(self, packet):
        self.data = chr(0xFF) + chr(packet) + pbuffer.make_word(len(self.data) + 4) + self.data
        self.send()

    def BNCSrecv(self):
        try:
            h1 = self.recv(4)
            header = unpack('<2BH', h1)
            
            if header[0] != chr(0xFF): #Validate packet, if invalid, attempt fix
                offset = h1.find(chr(0xFF))
                if offset == -1:
                    return

                h1 = h1[offset:]
                h1 += self.recv(4 - len(h1))
                header = unpack('<2BH', h1)
        except: #socket died
            self.bot.addchat('error', 'BNCS disconnected')
            if self.bot.want_connected:
                self.bot.disc()
                self.reconnect()
            return

        length = (header[2] - 4)
        data = ''

        while len(data) < length:
            to_go = length - len(data)
            data += self.recv(length)

        self.bot.events.call('BNCSRecv', header[1],
                             [{'id': header[1],
                               'length': length,
                               'data': data}])
