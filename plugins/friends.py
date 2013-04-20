from struct import unpack

from status_list import status_list

def get_status(status):
    build = ''
    if (status & 0x01) == 0x01:
        build += '/Mutual'
    if (status & 0x02) == 0x02:
        build += '/DND'
    if (status & 0x04) == 0x04:
        build += '/Away'

    return build[1:]

def get_loc(loc, loc_name):
    if loc == 0x00:
        return 'Offline'
    elif loc == 0x01:
        return 'Not in chat'
    elif loc == 0x02:
        if loc_name == '':
            return 'In chat'
        else:
            return loc_name + ' (Channel)'
    elif loc == 0x03:
        if loc_name == '':
            return 'In public game'
        else:
            return loc_name + ' (Game)'
    elif loc == 0x04:
        return 'Priv. game'
    elif loc == 0x05:
        return loc_name + ' (Private game)'
        

def get_prod(prod):
    build = ''
    prod = reversed(prod)
    for n in prod:
        build += n

    return build
    

class __init__():
    def __init__(self, bot):
        self.bot = bot
        
        self.friends = status_list(self.bot, 'friends')
        self.bot.friends = self.friends
        self.friends.updating = []
        self.friends.online = 0

        self.bot.events.add(self, 'bot', 2, 0,
                            'connected', self.in_friends,
                            'disc', self.out_friends,
                            'idle', self.get_friends)

        self.bot.events.add(self, 'BNCSRecv', -1, 0,
                            0x65, self.recv_friends,
                            0x66, self.recv_update,
                            0x67, self.recv_new,
                            0x68, self.recv_remove,
                            0x69, self.recv_move)

        self.bot.events.add(self, 'ui', 0, 0,
                            'reload', self.ui_reload)

        self.has_ui = False

    def clear(self):
        self.friends.online = 0
        self.friends.clear()
        self.bot.events.call('ui', 'list', 'friends', 'clear')

    def out_friends(self):
        self.friends.clear()
        self.bot.events.call('ui', 'list', 'remove', ['friends'])
        self.has_ui = False

    def ui_reload(self):
        self.has_ui = False
        self.ui_start()
        self.get_friends()

    def in_friends(self, un=''):
        self.ui_start()
        self.get_friends()
                            
    def ui_start(self):
        if self.has_ui == True:
            return
        self.bot.events.call('ui', 'list', 'add',
                             ['list', 'friends', 'Friends', 0, 0,
                              'Pic', 2, 39,
                              'User', 0, 120,
                              'Status', 0, 45,
                              'Location', 0, 70], {})

        self.bot.events.call('ui', 'list', 'friends', 'menu',
                             ['Promote', self.user_promote,
                              'Demote', self.user_demote,
                              'Remove', self.user_remove,
                              'Whisper', self.user_whisper,
                              'Squelch', self.user_squelch,
                              'Profile', self.user_profile])

        self.has_ui = True

    def user_promote(self, *rest):
        for x in self.bot.status['selected']:
            self.bot.send('/f p ' + self.friends.name_from_idx(x))

    def user_demote(self, *rest):
        for x in self.bot.status['selected']:
            self.bot.send('/f d ' + self.friends.name_from_idx(x))

    def user_remove(self, *rest):
        for x in self.bot.status['selected']:
            self.bot.send('/f r ' + self.friends.name_from_idx(x))

    def user_whisper(self, *rest):
        for x in self.bot.status['selected']:
            self.bot.events.call('ui', 'send', 'send',
                                 {'pre': '/w ' + self.friends.name_from_idx(x) +\
                                  ' ', 'clear': False})
        self.bot.events.call('ui', 'send', 'clear')

    def user_squelch(self, *rest):
        for x in self.bot.status['selected']:
            self.bot.send('/squelch ' + self.friends.name_from_idx(x))
            #un = self.friends.name_from_idx(x)
            #if self.friends.user[un.lower()]['squelched']:
            #    self.bot.send('/unsquelch ' + un)
            #else:
            #    self.bot.send('/squelch ' + un)

    def user_profile(self, *rest):
        for x in self.bot.status['selected']:
            self.bot.events.call('profile', 'request',
                                 [self.friends.name_from_idx(x)])

    def get_friends(self, tick=0):
        if tick % 10 == 0:
            self.friends.online = 0
            self.friends.clear()
            self.bot.BNCS.BNCSsend(0x65)

    def pick_color(self, loc):
        if loc == 0x00: #offline
            return '#FF0000' #red
        else: #online somewhere
            return '#00FF00' #green

    def update_header(self):
        self.bot.events.call('ui', 'list', 'friends', 'header',
                             ['Friends (' +\
                              str(self.friends.online) + '/' +\
                              str(self.friends.count) + ')'])

    def reset_list(self):
        self.bot.events.call('ui', 'list', 'friends', 'clear')
        for x in self.friends.order:
            self.bot.events.call('ui', 'list', 'friends', 'add_entry',
                                 [self.friends.user[x],
                                  self.friends.user[x]['username'],
                                  get_status(self.friends.user[x]['status']),
                                  get_loc(self.friends.user[x]['loc'],
                                          self.friends.user[x]['loc_name'])],
                                  {'color':
                                   self.pick_color(self.friends.user[x]['loc'])})


        self.update_header()

    def recv_move(self, packet):
        old = ord(packet['data'][0])
        new = ord(packet['data'][1])
        #print str(old) + '->' + str(new)

        name = self.friends.order[old]
        user = self.friends.user[name]
        self.friends.del_user(name)
        self.friends.add_user(name, user, new)

        self.bot.events.call('ui', 'list', 'friends', 'upd_entry',
                             [old,
                              user,
                              user['username'],
                              get_status(user['status']),
                              get_loc(user['loc'],
                                      user['loc_name'])],
                             {'color': self.pick_color(user['loc']),
                              'newidx': new})

    def recv_remove(self, packet):
        idx = ord(packet['data'][0])
        name = self.friends.order[idx]

        if self.friends.user[name]['loc'] != 0x00:
            self.friends.online -= 1

        self.friends.del_user(name)
        self.bot.events.call('ui', 'list', 'friends', 'remove_entry',
                             [idx])

        self.update_header()

    def recv_new(self, packet):
        curr = packet['data']
        info = {'flags': 0} #Needed for automatic icon handling by gui_wx
        sepf = curr.find('\0')
        info['username'] = curr[:sepf]
        curr = curr[sepf + 1:]

        info['status'] = ord(curr[0])
        info['loc'] = ord(curr[1])
        info['product'] = get_prod(curr[2:6])
        curr = curr[6:]

        sepf = curr.find('\0')
        info['loc_name'] = curr[:sepf]
        curr = curr[sepf + 1:]

        self.friends.add_user(info['username'].lower(), info, -1)

        self.bot.events.call('ui', 'list', 'friends', 'add_entry',
                             [info,
                              info['username'],
                              get_status(info['status']),
                              get_loc(info['loc'],
                                      info['loc_name'])],
                              {'color': self.pick_color(info['loc'])})

        if info['loc'] != 0x00:
            self.friends.online += 1

        self.update_header()

    def recv_update(self, packet):
        entry_no, status, loc = unpack('<3B', packet['data'][:3])
        prod = packet['data'][3:7]
        loc_name = packet['data'][7:-1]

        if entry_no in self.friends.updating:
            un = self.friends.order[entry_no]
            user = self.friends.user[un]

            if user['loc'] == 0x00 and loc != 0x00:
                self.friends.online += 1
            elif loc == 0x00 and user['loc'] != 0x00:
                self.friends.online -= 1
            
            user.update({'status': status,
                         'product': get_prod(prod),
                         'loc': loc,
                         'loc_name': loc_name})
            
            self.bot.events.call('ui', 'list', 'friends', 'upd_entry',
                                 [entry_no,
                                  0, user,
                                  1, user['username'],
                                  2, get_status(user['status']),
                                  3, get_loc(user['loc'],
                                             user['loc_name'])],
                                  {'color': self.pick_color(user['loc'])})
            
            self.friends.updating.remove(entry_no)
        else:
            self.bot.BNCS.insert_byte(entry_no)
            self.bot.BNCS.BNCSsend(0x66)
            self.friends.updating.append(entry_no)

    def recv_friends(self, packet):
        num = ord(packet['data'][0])
        if num == 0:
            return

        curr = packet['data'][1:]
        for x in range(num):
            info = {'flags': 0} #Needed for automatic icon handling by gui_wx
            sepf = curr.find('\0')
            info['username'] = curr[:sepf]
            curr = curr[sepf + 1:]

            info['status'] = ord(curr[0])
            info['loc'] = ord(curr[1])
            info['product'] = get_prod(curr[2:6])
            curr = curr[6:]

            sepf = curr.find('\0')
            info['loc_name'] = curr[:sepf]
            curr = curr[sepf + 1:]

            if info['loc'] != 0x00:
                self.friends.online += 1

            self.friends.add_user(info['username'].lower(), info, -1)

        self.reset_list()
