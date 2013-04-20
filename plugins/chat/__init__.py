from styles import color, out_colors
from random import randint, seed

from status_list import status_list
from statstring import statstring, parse_chan_flags

import time

class __init__():
    def __init__(self, bot):
        self.bot = bot

        self.channel = status_list(bot, 'channel')
        self.reset_colors()
        seed()
        self.bot.channel = self.channel
        
        self.bot.events.add(self, 'BNCSChat', -1, 0,
                            0x01, self.EID_SHOWUSER,
                            0x02, self.EID_JOIN,
                            0x03, self.EID_LEAVE,
                            0x04, self.EID_WHISPER,
                            0x05, self.EID_TALK,
                            0x06, self.EID_BROADCAST,
                            0x07, self.EID_CHANNEL,
                            0x09, self.EID_USERFLAGS,
                            0x0A, self.EID_WHISPERSENT,
                            0x0D, self.EID_CHANNELFULL,
                            0x0E, self.EID_CHANNELDOESNOTEXIST,
                            0x0F, self.EID_CHANNELRESTRICTED,
                            0x12, self.EID_INFO,
                            0x13, self.EID_ERROR,
                            0x17, self.EID_EMOTE)
        self.bot.events.add(self, 'ui', 0, 0,
                            'start', self.ui_start,
                            'reload', self.reload_list)
        self.bot.events.add(self, 'bot', 0, 0,
                            'disc', self.clear)

        self.bot.events.add(self, 'commands', 0, 0,
                            'start', self.cmd_start)
        self.cmd_start()

    def reset_colors(self):
        self.channel.add_persistent('color', [] + color)

    def pick_color(self):
        if len(self.channel.color) == 1:
            choice = hex(self.channel.color[0])
            self.reset_colors()
        else:
            choice = hex(self.channel.color.pop(randint(0,
                                                   len(self.channel.color) - 1)))
        return 'user#'+choice[2:].zfill(6)

    def free_color(self, color):
        readd = int(color[5:], 0x10)
        try:
            self.channel.color.index(readd) #Make sure it's not in there
        except ValueError:
            self.channel.color.append(readd)

    def cmd_start(self):
        self.bot.events.add(self, 'command', 0, 0,
                            'chan', self.cmd_chan,
                            'profile', self.cmd_profile)

    def cmd_profile(self, cmd):
        self.bot.events.call('profile', 'request', [cmd['arg']])

    def cmd_chan(self, cmd):
        args = cmd['arg'].split(' ', 1)
        if len(args) == 1:
            return

        if self.channel.has_user(args[0]):
            try:
                self.bot.respond(cmd, args[0] + ' has ' + args[1] + ' of ' +\
                                 str(self.channel.user[args[0].lower()]\
                                     [args[1].lower()]) + '.')
            except KeyError:
                self.bot.respond(cmd, 'Property not found.')

        else:
            self.bot.respond(cmd, 'User "' + args[0] + '" not found')
        
    def ui_start(self):
        self.bot.events.call('ui', 'list', 'add',
                             ['list', 'channel', 'Channel', 28, 18,
                              'Pic', 2, 39,
                              'User', 0, 158,
                              'Lag', 2, 34,
                              'Clan', 0, 43], {})

        self.bot.events.call('ui', 'list', 'channel', 'menu',
                             ['Whisper', self.chan_whisper,
                              'Add to friends list', self.chan_friend,
                              'Ban', self.chan_ban,
                              'Kick', self.chan_kick,
                              'Squelch/Unsquelch', self.chan_squelch,
                              'Profile', self.chan_profile])

    def chan_friend(self, cmd=None):
        for x in self.bot.status['selected']:
            self.bot.send('/f a ' + self.channel.name_from_idx(x))

    def chan_profile(self, cmd=None):
        for x in self.bot.status['selected']:
            self.bot.events.call('profile', 'request',
                                 [self.channel.name_from_idx(x)])

    def chan_ban(self, cmd=None):
        for x in self.bot.status['selected']:
            self.bot.send('/ban ' + self.channel.name_from_idx(x))

    def chan_kick(self, cmd=None):
        for x in self.bot.status['selected']:
            self.bot.send('/kick ' + self.channel.name_from_idx(x))

    def chan_squelch(self, cmd=None):
        for x in self.bot.status['selected']:
            un = self.channel.name_from_idx(x)
            if self.channel.user[un.lower()]['squelched']:
                self.bot.send('/unsquelch ' + un)
            else:
                self.bot.send('/squelch ' + un)

    def chan_whisper(self, cmd=None):
        for x in self.bot.status['selected']:
            self.bot.events.call('ui', 'send', 'send',
                                 {'pre': '/w ' + self.channel.name_from_idx(x) +\
                                  ' ', 'clear': False})

        self.bot.events.call('ui', 'send', 'clear')

    def reload_list(self):
        x = 0
        for user in self.channel.order:
            info = self.channel.user[user]
            
            if 'clan' in info:
                if info['clan'] == False:
                    clan = ''
                else:
                    clan = info['clan']
            else:
                clan = ''

            kw = {'idx': x,
                  'color': info['color'][4:]}

            if info['ops']:
                #kw['bgcolor'] = '#333333'
                kw['bold'] = True
            
            self.bot.events.call('ui', 'list', 'channel', 'add_entry',
                                 [info,
                                  info['username'],
                                  (info['ping'], info['flags']),
                                  clan],
                                  kw)
            x += 1
        self.update_header()

    def add_user(self, chat, user_info):
        self.channel.add_user(chat['username'].lower(), user_info, chat['idx'])

        kw = {'idx': chat['idx'],
              'color': user_info['color'][4:]}

        if user_info['ops']:
            #kw['bgcolor'] = '#333333'
            kw['bold'] = True

        if 'clan' in user_info:
            if user_info['clan'] == False:
                clan = ''
            else:
                clan = user_info['clan']
        else:
            clan = ''
        
        self.bot.events.call('ui', 'list', 'channel', 'add_entry',
                             [user_info,
                              chat['username'],
                              (chat['ping'], chat['flags']),
                              clan],
                              kw)
        self.update_header()

    def del_user(self, idx, name):
        self.channel.del_user(name)
        
        self.bot.events.call('ui', 'list', 'channel', 'remove_entry',
                             [idx])
        self.update_header()

    def update_user(self, idx, chat, user_info, newidx=-1):
        if 'clan' in user_info:
            if user_info['clan'] == False:
                clan = ''
            else:
                clan = user_info['clan']
        else:
            clan = ''

        if user_info['ops']:
            kw = {'color': user_info['color'][4:],
                  'newidx': newidx}
            #kw['bgcolor'] = '#333333'
            kw['bold'] = True
            
        if newidx == -1:
            self.bot.events.call('ui', 'list', 'channel', 'upd_entry',
                                 [idx,
                                  0, user_info,
                                  1, chat['username'],
                                  2, (chat['ping'], chat['flags']),
                                  3, clan])
        else:
            self.bot.events.call('ui', 'list', 'channel', 'upd_entry',
                                 [idx,
                                  user_info,
                                  chat['username'],
                                  (chat['ping'], chat['flags']),
                                  clan],
                                 kw)

    def update_header(self):
        count = str(self.channel.count)
        self.bot.events.call('ui', 'list', 'channel', 'header',
                             ['%s (%s)' % (self.bot.status['channel'],
                                           count)])

    def clear(self):
        self.reset_colors()
        self.channel.clear()
        self.bot.events.call('ui', 'list', 'channel', 'clear')
        
    def EID_SHOWUSER(self, chat):
        un = chat['username']
        if self.channel.has_user(un):
            update = True
        else:
            update = False
        
        ops = (chat['flags'] & 0x02) == 0x02
        
        user_info = {'username': un,
                     'flags': chat['flags'],
                     'ping': chat['ping'],
                     'ops': ops,
                     'squelched': ((chat['flags'] & 0x20) == 0x20),
                     'joined': -1,
                     'talked': -1}
        user_info.update(statstring(chat['text']))
        if chat['username'] == self.bot.status['username']:
            user_info['color'] = 'user' + out_colors['me']
        else:
            user_info['color'] = self.pick_color()
        if ops:
            chat['idx'] = 0
        else:
            chat['idx'] = self.channel.count

        if update:
            x = self.channel.user[un.lower()]
            x.update(user_info)
            self.update_user(self.channel.order.index(un.lower()),
                             chat,
                             x)
        else:
            self.add_user(chat, user_info)
        
        
    def EID_JOIN(self, chat):
        user_info = {'username': chat['username'],
                     'flags': chat['flags'],
                     'ping': chat['ping'],
                     'ops': False,
                     'squelched': ((chat['flags'] & 0x20) == 0x20),
                     'joined': time.time(),
                     'talked': -1}
        user_info.update(statstring(chat['text']))
        if chat['username'] == self.bot.status['username']:
            user_info['color'] = 'user' + out_colors['me']
        else:
            user_info['color'] = self.pick_color()

        chat['idx'] = self.channel.count
        
        self.bot.addchat(user_info['color'], chat['username'],
                         'joinleave', ' [' + str(user_info['ping']) +\
                         'ms] has joined the channel using ' +\
                         user_info['display'])

        self.add_user(chat, user_info)
        
    def EID_LEAVE(self, chat):
        name = chat['username'].lower()
        user = self.channel.user[name]
        idx = self.channel.order.index(name)

        self.bot.addchat(user['color'], chat['username'],
                         'joinleave', ' has left the channel')

        self.free_color(user['color'])
        self.del_user(idx, name)
        
    def EID_WHISPER(self, chat):
        if self.channel.has_user(chat['username']):
            user = self.channel.user[chat['username'].lower()]
            user['talked'] = time.time()
            style = user['color']
        else:
            idx = -1
            style = 'whisperuser'
        
        self.bot.addchat('whisperuser', '<From ',
                         style, chat['username'],
                         'whisperuser', '> ',
                         'whisper', chat['text'])
        
    def EID_TALK(self, chat):
        key = chat['username'].lower()
        
        self.bot.addchat(self.channel.user[key]['color'], '<'+chat['username']+'> ',
                          'chat', chat['text'])

        self.channel.user[key]['talked'] = time.time()
        
    def EID_BROADCAST(self, chat):
        self.bot.addchat('Broadcast: '+chat['text'])
        
    def EID_CHANNEL(self, chat):
        self.bot.addchat('Joined ' + parse_chan_flags(chat['flags']) +\
                         ' channel: '+chat['text'])

        self.bot.status['channel'] = chat['text']
        self.clear()

        #if chat['text'].lower() == 'the void':
        #    self.bot.send('/unignore ' + self.bot.status['username'])
        
    def EID_USERFLAGS(self, chat):
        if self.channel.has_user(chat['username']):
            key = chat['username'].lower()
            idx = self.channel.order.index(key)
            ops = bool(chat['flags'] & 0x02)
            
            if ops == True and self.channel.user[key]['ops'] == False:
                self.bot.addchat(self.channel.user[key]['color'], chat['username'],
                                 'info', ' has gained operator status.')
                newidx = 0
                del self.channel.order[idx]
                self.channel.order.insert(newidx, key)
            else:
                newidx = -1

            self.channel.user[key]['flags'] = chat['flags']
            self.channel.user[key]['ops'] = ops
            self.channel.user[key]['squelched'] = ((chat['flags'] & 0x20) == 0x20)
                
            self.update_user(idx, chat, self.channel.user[key], newidx)
        else:
            un = chat['username']
            
            ops = (chat['flags'] & 0x02) == 0x02
            
            user_info = {'username': un,
                         'flags': chat['flags'],
                         'ping': chat['ping'],
                         'ops': ops,
                         'squelched': ((chat['flags'] & 0x20) == 0x20),
                         'joined': -1,
                         'talked': -1}
            if chat['username'] == self.bot.status['username']:
                user_info['color'] = 'user' + out_colors['me']
            else:
                user_info['color'] = self.pick_color()
            user_info.update(statstring(chat['text']))

            if ops:
                chat['idx'] = 0
            else:
                chat['idx'] = self.channel.count
                
            self.add_user(chat, user_info)
                                 
        
    def EID_WHISPERSENT(self, chat):
        if self.channel.has_user(chat['username']):
            style = self.channel.user[chat['username'].lower()]['color']
        else:
            style = 'whisperuser'

        self.bot.addchat('whisperuser', '<To ',
                          style, chat['username'],
                          'whisperuser', '> ',
                          'whisper', chat['text'])

    def EID_CHANNELFULL(self, chat):
        self.bot.addchat('error', 'Channel is full.')
    def EID_CHANNELDOESNOTEXIST(self, chat):
        self.bot.addchat('error', 'Channel does not exist.')
    def EID_CHANNELRESTRICTED(self, chat):
        self.bot.addchat('error', 'Channel is restricted.')
    def EID_INFO(self, chat):
        self.bot.addchat(chat['text'])
    def EID_ERROR(self, chat):
        self.bot.addchat('error', chat['text'])
    def EID_EMOTE(self, chat):  
        self.bot.addchat('emote', '<',
                         self.channel.user[chat['username'].lower()]['color'], chat['username'],
                         'emote', ' '+chat['text']+'>')
