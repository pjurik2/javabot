import pbuffer
import socket
from config_class import config_class
from struct import pack, unpack

socks4_fail_descr = {91: 'Request rejected or failed.',
                     92: 'Request rejected becuase SOCKS server cannot connect to identd on the client',
                     93: 'Request rejected because the client program and identd report different user-ids'}


socks5_fail_descr = {0x01: 'General failure',
                     0x02: 'Connection not allowed by ruleset',
                     0x03: 'Network unreachable',
                     0x04: 'Host unreachable',
                     0x05: 'Connection refused by destination host',
                     0x06: 'TTL expired',
                     0x07: 'Command not supported / protocol error',
                     0x08: 'Address type not supported'}


class __init__(pbuffer.conn, config_class):
    name = 'proxy'
    def __init__(self, bot):
        self.bot = bot
        self.cfg_file = self.bot.cfg_file
        
        self.load_spec_config()

    def main_events(self):
        self.bot.events.add(self, 'bot', 0, 1,
                            'disc', self.reset)
        self.bot.events.add(self, 'bot', 0, 0,
                            'configure', self.edit_config,
                            'load_config', self.load_spec_config)

    def load_spec_config(self):
        #We're going to want to remove old events regarldess of what happens
        #because if use_proxy is true we'll have duplicate entries
        self.bot.events.remove(self)
        self.main_events()

        default = {'protocol': 'socks4',
                   'use_proxy': False,
                   'proxy': ''}
        try:
            default.update(self.bot.config['proxy'])
        except KeyError:
            pass
        finally:
            self.bot.config['proxy'] = default
        self.config = self.bot.config['proxy']

        self.config['use_proxy'] = self.bot.get_bool(self.config['use_proxy'])

        if self.config['use_proxy'] == True:
            #Connect to proxy socket instead of BNCS socket
            self.bot.events.add('BNLSRecv', 500, -1,
                                0x10, self.connect_sock)

        #Server/Port setting business
        split = self.config['proxy'].split(':', 1)
        self.config['server'] = split[0]
        
        if len(split) > 1:
            self.config['port'] = int(split[1])
        elif ('port' in self.config):
            self.config['port'] = int(self.config['port'])
        else:
            self.config['port'] = 1080

    def edit_config(self, settings):
        config = [{'key': 'proxy', 'value': self.config['server']},
                  {'key': 'port', 'value': str(self.config['port'])},
                  {'key': 'protocol', 'type': ('list', ['socks4', 'socks5'])},
                  {'key': 'use_proxy', 'caption': 'Connect to Battle.net with this proxy',
                   'type': ('checkbox',)}]

        settings.append({'caption': 'Proxy',
                         'file': self.bot.cfg_file[1],
                         'title': self.name,
                         'dict': self.config,
                         'settings': config})

    def send_connect(self):
        self.insert_byte(0x04) #version
        self.insert_byte(0x01) #command id (CONNECT)
        self.insert_short(0xE017) #destination port (0x17E0/6112, bytes reversed)
        self.insert_string(socket.inet_aton(socket.gethostbyname(self.bot.connfig['login']['server']))) #destination IP
        self.send()

    def send_connect5(self):
        self.insert_byte(0x05) #version
        self.insert_byte(0x01) #connection type: TCP/IP stream connection
        self.insert_byte(0x00) #reserved

        server = self.get_dstip()
        self.insert_byte(0x01) #address type: IPv4

        self.insert_raw(socket.inet_aton(socket.gethostbyname(self.bot.connfig['login']['server'])))
        self.insert_short(0xE017) #destination port (0x17E0/6112, bytes reversed)

        self.send()

    def send_greet(self):
        self.insert_byte(0x05) #version
        self.insert_byte(0x01) #number of supported authentication methods
        self.insert_byte(0x00) #no authentication
        self.send()

    def recv_socks4(self):
        try:
            h1 = self.recv(8)
            result = ord(h1[1]) #second byte
        except: #socket died?
            self.reset()
            self.bot.addchat('error', 'Proxy disconnected')
            return
        
        if result == 90:
            self.bot.addchat('success', 'Request granted from SOCKS4 proxy')

            self.give_up()
        else:
            try:
                self.bot.addchat('error', socks4_fail_descr[result])
            except KeyError:
                self.bot.addchat('error', 'Invalid response code: '+result)

            self.bot.disc()

    def recv_socks5(self):
        try:
            h1 = self.recv(10)
            result = ord(h1[1]) #second byte
        except: #socket died?
            self.close()
            self.bot.addchat('error', 'Proxy disconnected')
            return

        if len(h1) <= 3:
            if result == 0xFF:
                self.bot.addchat('error', 'Proxy rejected listed authentication method')
                return

            self.send_connect5()
        else:
            if result == 0x00:
                self.bot.addchat('success', 'Request granted from SOCKS5 proxy')

                self.give_up()
            else:
                try:
                    self.bot.addchat('error', 'Request failed: '+socks4_fail_descr[result])
                except KeyError:
                    self.bot.addchat('error', 'Invalid response code: '+hex(result))

                self.bot.disc()
    def give_up(self): #Give control to BNCS plugin
        self.bot.BNCS.clear()
        self.bot.BNCS.socket = self.socket
        
        self.bot.set_socket_func(self.bot.BNCS.socket, self.bot.BNCS.BNCSrecv)
        self.bot.BNCS.send_0x50()
        
    def connect_sock(self, *rest):
        self.bot.addchat('Connecting to '+self.config['protocol'].upper()+' proxy...')

        try:        
            self.connect(self.config['server'], self.config['port'])

            if self.config['protocol'] == 'socks4':
                self.bot.add_socket(self.socket, [self.recv_socks4])
            else:
                self.bot.add_socket(self.socket, [self.recv_socks5])
                
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
            self.bot.addchat('success', 'Connected to proxy')
            if self.config['protocol'] == 'socks4':
                self.send_connect()
            else:
                self.send_greet()
