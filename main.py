import time
start = time.clock()
from select import select
import sys
import ConfigParser
from os import sep

import extensions
from events import Events
from config_class import config_class
from time_format import time_diff

rep = {'sep': sep}

try:
    servers = open('profiles' + sep + 'global' + sep + 'servers.txt').readlines()
except IOError:
    servers = ['useast.battle.net',
               'uswest.battle.net',
               'europe.battle.net',
               'asia.battle.net']
for x in range(0, len(servers)):
    servers[x] = servers[x].strip(' \n\r')

product_aliases = {'starcraft': 'STAR',
                   'star': 'STAR',
                   'starcraft - broodwar': 'SEXP',
                   'sexp': 'SEXP',
                   'diablo ii': 'D2DV',
                   'd2dv': 'D2DV',
                   'diablo ii - lord of destruction': 'D2XP',
                   'd2xp': 'D2XP',
                   'warcraft ii battle.net edition': 'W2BN',
                   'w2bn': 'W2BN',
                   'warcraft iii': 'WAR3',
                   'war3': 'WAR3',
                   'warcraft iii - the frozen throne': 'W3XP',
                   'w3xp': 'W3XP',
                   '': 'D2DV'}
        
class Bot (config_class):
    name = 'login'
    def __init__(self, wrapper=None, config='config.ini', path=''):
        config_class.__init__(self)
        self.bot_start = time.time()
        self.bot_connected = -1
        self.want_connected = False
        self.ui_loaded = False
        
        self.def_config = config
        self.cfg_file = ['global.ini', config]
        self.path = path
        self.status = {'connected': False}
        
        self.wrapper = wrapper         
        
        self.events = Events()
        self.events.add('IO', 0, 0,
                        'addchat', self.print_text)

        self.events.add('IO', 1000, 0,
                        'send', self.display_send)

        self.events.add('bot', -1, 0,
                        'disc', self.disced,
                        'connect', self.conn_clock,
                        'connected', self.connected,
                        'configure', self.edit_config,
                        'load_config', self.load_spec_config)

        self.events.add('ui', 0, 0,
                        'start', self.add_menus)

        self.load_spec_config()
        self.reload_connfig()
        
        self.plugins = extensions.plugins(self)
        self.plugins.load_classes(order=self.config['plugins'])

        self.events.call('bot', 'start')

    def add_menus(self):
        self.events.call('ui', 'menu', 'add',
                         ['Bot Settings',
                          'Configure...\tCTRL+E', self.show_config,
                          'Reload settings\tCTRL+R', self.reload_config])
        self.events.call('ui', 'menu', 'add',
                         ['Connection',
                          'Connect\tCTRL+B', self.connect,
                          'Disconnect\tCTRL+D', self.disc])

    def show_config(self, *rest):
        self.events.call('ui', 'config')
    
    def reload_config(self, *rest):
        self.events.call('bot', 'load_config')
        self.addchat('Settings reloaded.')

    def add_socket(self, socket, func):
        self.wrapper.sockets[socket] = func

    def del_socket(self, socket):
        func = self.wrapper.sockets[socket]
        del self.warpper.sockets[socket]
        return func
    
    def set_socket_func(self, socket, new_func):
        func = self.wrapper.sockets[socket]
        self.wrapper.sockets[socket] = new_func
        return func

    def disc(self, *rest):
        self.want_connected = False
        self.events.call('bot', 'disc')

        self.addchat('Bot disconnected.')
        self.status['connected'] = False

    def connect(self, *rest):
        self.want_connected = True
        self.events.call('bot', 'connect')

    def conn_clock(self):
        self.reload_connfig()
        self.conn_start = time.time()

    def connected(self, username):
        self.status = {'connected': True}
        self.addchat('Bot connected in '+ \
                     time_diff(self.conn_start, time.time()))

        self.conn_start = -1
        self.bot_connected = time.time()

    def disced(self):
        self.reload_connfig()
        self.status = {}
        self.bot_connected = -1

    def addchat(self, *args, **kwargs):
        if ('loudness' in kwargs) == False:
            kwargs['loudness'] = 1

        if kwargs['loudness'] >= self.config['ui']['loudness']:
            self.events.call('IO', 'addchat', list(args))

    def print_text(self, *args):
        tf = time.strftime('[%I:%M:%S %p] ', time.localtime())
        if len(args) > 1:
            out = ''
            for x in range(0, len(args), 2):
                out=out+args[x+1]
        else:
            out = args[0]

        print tf+out

    def load_spec_config(self, *rest):
        self.load_config(self.cfg_file)

        default = {'bnlsserver': 'pyro.no-ip.biz',
                   'server_file': 'servers.txt',
                   'username': '',
                   'password': '',
                   'cdkey': '',
                   'expcdkey': '',
                   'product': 'D2DV',
                   'server': 'useast.battle.net',
                   'home': 'Clan BoT'}
        try:
            default.update(self.config['login'])
        except KeyError:
            pass
        finally:
            self.config['login'] = default
        default = {'loudness': 1}
        try:
            default.update(self.config['ui'])
        except KeyError:
            pass
        finally:
            self.config['ui'] = default

        self.config['login']['product'] = product_aliases[self.config['login']['product'].lower()]
        if ('plugins' in self.config) == False:
            self.config['plugins'] = {}

    def reload_connfig(self):
        self.connfig = {}
        self.connfig.update(self.config)

    def edit_config(self, settings):
        config = [{'key': 'username'},
                  {'key': 'password', 'type': ('text', 0x800)},
                  {'key': 'product', 'type': ('list', ['Starcraft',
                                                       'Starcraft - Broodwar',
                                                       'Diablo II',
                                                       'Diablo II - Lord of Destruction',
                                                       'Warcraft II Battle.net Edition',
                                                       'Warcraft III',
                                                       'Warcraft III - The Frozen Throne'])},
                  {'key': 'cdkey', 'caption': 'CD Key'},
                  {'key': 'expcdkey', 'caption': 'Exp. CD Key'},
                  {'key': 'server', 'type': ('list', servers)},
                  {'key': 'bnlsserver', 'caption': 'BNLS Server',
                   'type': ('list', ['pyro.no-ip.biz',
                                     'jbls.org',
                                     'bnls.valhallalegends.com',
                                     'jbls.idiat.com'])},
                  {'key': 'home'}]
        
        settings.insert(0, {'caption': 'Login',
                            'file': self.cfg_file[1],
                            'title': 'login',
                            'dict': self.config['login'],
                            'settings': config})
            
    def ver(self):
        return 'JavaBot, Release 4.1'

    def uptime(self):
        now = time.time()
        if self.bot_connected == -1:
            return 'Bot uptime: ' + time_diff(self.bot_start, now)
        else:
            return 'Bot uptime: ' + time_diff(self.bot_start, now) +\
                   '; connection uptime: ' + time_diff(self.bot_connected, now)
    
    def send (self, text='', **kwargs):
        if text == '':
            return
        ref = {'text': text}
        ref.update(kwargs)

        self.events.call('IO', 'send', [ref])

    def confirm(self, *args):
        self.events.call('ui', 'confirm', list(args))

    def respond(self, cmd, response, output='addchat'):
        cmd['text']['text'] = response
        
        if cmd['output'] == 'send' or output == 'send':
            self.send(**cmd['text'])
        elif cmd['output'] == 'whisper':
            cmd['text']['text'] = '/w ' + cmd['username'] + ' ' + cmd['text']['text']
            self.send(**cmd['text'])
        elif cmd['output'] == 'addchat':
            self.addchat(response)

    def display_send(self, msg):
        if msg['text'][0] != '/':
            try:
                self.addchat('me', '<'+self.status['username']+'> ',
                             'chat', msg['text'])
            except KeyError:
                self.addchat('chat', msg['text'])

class Raptor(config_class):
    def __init__(self):
        config_class.__init__(self)
        self.sockets = {} #Sockets that will be polled by an inter-bot select statement.
                          #Functions to be called when self.sockets has received data
        self.bots = [] #List of bot instances
        
        self.events = Events()

        self.def_config = 'profiles' + sep + 'global' + sep + 'config.ini'
        self.cfg_file = [self.def_config]
        self.load_config(self.cfg_file)

        if ('plugins' in self.config) == False:
            self.config['plugins'] = {}
        
        self.plugins = extensions.plugins(self)
        self.plugins.load_classes('wrap', order=self.config['plugins'])

        self.load_bots()
        self.events.call('wrap', 'start')

        print 'Bot(s) loaded in ' + str(time.clock() - start) + ' seconds'
        self.recv_all()

    def load_bots(self):
        del sys.argv[0] #sys.argv likes to include script name

        #If an argument is supplied that ends with .txt, use that as loadlist.txt instead
        if sys.argv != [] and sys.argv[0].endswith('.txt'):
            self.list_file = sys.argv.pop(0)
        else:
            #Default loadlist.txt file
            self.list_file = 'profiles' + sep + 'loadlist.txt'

        #Rest of arguments are bot profiles to be loaded
        self.load_files = sys.argv

        #Read loadlist.txt
        try:
            load_list = open(self.list_file, 'r')
        except IOError:
            pass
        else:
            new_files = load_list.readlines()

            for new in new_files:
                self.load_files.append(new.strip(sep+' \n\r'))

        #If there are no profiles, load a default config profile.
        if self.load_files == []:
            self.load_files.append('config.ini')

        for f in self.load_files:
            bot_path = 'profiles' + sep #Presently all profiles are in ./profiles
            f = f % rep #Replace cross-platform patterns with platform-dependent equivalents at run-time
            paths = f.rsplit(sep, 1) #To to separate a file name from path
            if len(paths) > 1:
                bot_path += paths[0]
                cfg_name = paths[1]
            else:
                cfg_name = f

            if cfg_name.find('.') == -1:
                bot_path += cfg_name
                cfg_name = 'config.ini'

            cfg_name = bot_path + sep + cfg_name
            self.bots.append(Bot(self, cfg_name, bot_path+sep))
        
    def recv_all(self):
        while True:
            if self.sockets == {}:
                time.sleep(0.01)
            else:
                avail = select(self.sockets.iterkeys(), [], [], 0.01)

                for recv in avail[0]:
                    try:
                        f = self.sockets[recv]
                    except KeyError:
                        pass
                    else:
                        f()

Raptor()
