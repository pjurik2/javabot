from status_list import status_list, cookie_handler
from os import sep
from struct import pack, unpack
from sys import maxint as no_cookie

dd = 'icons' + sep + 'clan' + sep

icon = {'Chieftain': dd + 'chieftain.gif',
        'Shaman': dd + 'shaman.gif',
        'Grunt': dd + 'grunt.gif',
        'Peon (>1 week)': dd + 'peon.gif',
        'Peon (<1 week)': dd + 'peon2.gif'}
        
ranks = ['Chieftain',
         'Shaman',
         'Grunt',
         'Peon (>1 week)',
         'Peon (<1 week)']

rank_idx = ['c',
            's',
            'g',
            'p']

statuses = ['offline',
            'online',
            'in a channel',
            'in a public game',
            'in a private game']

set_results = {0x00: 'Rank change was successful.',
               0x01: 'Rank change failed.',
               0x02: 'You cannot change that user\'s rank yet.',
               0x04: 'Rank change declined.',
               0x05: 'Rank change failed.',
               0x07: 'You are not authorized to change ranks because your rank is too low.',
               0x08: 'You are not authorized to change the specified user\'s rank because of his/her current rank.'}

invite_results = {0x00: 'Invitation accepted.',
                  0x04: 'Invitation declined.',
                  0x05: 'Failed to invite user.',
                  0x09: 'Invite failed because clan is full.'}

find_cand_results={0x00: 'Successfully found candidates.',
                   0x01: 'Clan tag is already taken.',
                   0x02: 'Candidate search failed because bot CD key has been used to create a clan in past week.',
                   0x08: 'This account is already in a clan.',
                   0x0A: 'Invalid clan tag.'}

create_results = {0x00: 'Clan created successfully.',
                  0x04: 'Somebody declined the invite.',
                  0x05: 'An invited user was unavailable.'}
                  

def create_tag(tag):
    rev = reversed(tag.ljust(4, '\0'))

    ret = ''
    for x in rev:
        ret += x

    return ret[:4]

def rank_change_result(status):
    try:
        return set_results[status]
    except KeyError:
        return 'Rank change failed for an unknown reason.'


def format_tag(tag):
    it = reversed(tag)
    ret = ''
    for x in it:
        ret += x

    for x in range(4 - len(ret)):
        ret += '\0'

    return ret

class __init__():
    def __init__(self, bot):
        self.bot = bot
        self.invite = {}
        self.responses = cookie_handler()

        self.clanned = False
        self.creating = False
        
        
        self.bot.events.add(self, 'ui', 1, 0,
                            'reload', self.ui_reload)
        self.bot.events.add(self, 'bot', 1, 0,
                            'disc', self.disc,
                            'connected', self.get_clan)

        #self.bot.events.add(self, 'ui', 'list', 'clan', 0, 0,
        #                    'selected', self.get_clan)

        self.bot.events.add(self, 'BNCSRecv', -1, 0,
                            0x70, self.recv_cand,
                            0x71, self.recv_mult_invite,
                            0x73, self.recv_disband,
                            0x74, self.recv_chief,
                            0x75, self.recv_info,
                            0x76, self.recv_quit,
                            0x77, self.recv_invite,
                            0x78, self.recv_set_rank,
                            0x79, self.recv_invited,
                            0x7A, self.recv_set_rank,
                            0x7C, self.recv_motd,
                            0x7D, self.recv_clan,
                            0x7E, self.recv_removed,
                            0x7F, self.recv_status,
                            0x81, self.recv_rank_change,
                            0x82, self.recv_member_info)

        self.bot.events.add(self, 'commands', 0, 0,
                            'start', self.add_commands)

        self.add_commands()

    def ui_reload(self):
        self.ui_start()
        self.reset_list()

    def in_clan(self):
        self.clanned = True
        self.clan = status_list(self.bot, 'clan')
        self.bot.clan = self.clan

        self.ui_start()

    def out_clan(self):
        if self.clanned:
            self.clanned = False
            self.clan.clear()
            try:
                del self.clan
                del self.bot.clan
            except NameError:
                pass

            self.bot.events.call('ui', 'list', 'remove', ['clan'])
            self.bot.events.call('ui', 'menu', 'remove', ['clan'])

    def clear(self):
        self.clan.clear()
        self.clan.online = 0
        self.bot.events.call('ui', 'list', 'clan', 'clear')

    def ui_start(self):
        self.bot.events.call('ui', 'list', 'add',
                             ['list', 'clan', 'Clan', 31, 19,
                              'Icon', 2, 39,
                              'Username', 0, 135,
                              'Location', 0, 100],  icon)

        self.bot.events.call('ui', 'menu', 'add',
                             ['Clan',
                              'Get MOTD', self.get_motd,
                              'Leave Clan', self.remove_self,
                              'Disband', self.get_disband])

        self.bot.events.call('ui', 'list', 'clan', 'menu',
                             ['Make Chieftain', self.set_rank_chieftain,
                              'Make Shaman', self.set_rank_shaman,
                              'Make Grunt', self.set_rank_grunt,
                              'Make Peon', self.set_rank_peon,
                              'Remove', self.remove_user,
                              'Profile', self.get_profile])
        
        self.tab = True

    def add_commands(self):
        self.bot.events.add(self, 'command', 0, 0,
                            'motd', self.get_motd,
                            'setmotd', self.set_motd,
                            'accept', self.get_accept,
                            'cwhois', self.get_member_info,
                            'setrank', self.set_rank,
                            'invite', self.invite_user,
                            'makeclan', self.find_cand)

    def clan_user(self):
        return self.clan.name_from_idx(self.bot.status['selected'].pop())

    def invite_user(self, rest):
        if type(rest) == list:
            for x in range(len(self.bot.status['selected'])):
                self.bot.BNCS.insert_long(no_cookie)
                self.bot.BNCS.insert_string(self.clan_user())
                self.bot.BNCS.BNCSsend(0x77)
        else:
            self.bot.BNCS.insert_long(self.responses.add(rest))
            self.bot.BNCS.insert_string(rest['arg'])
            self.bot.BNCS.BNCSsend(0x77)        

    def remove_self(self, *rest):
        self.remove = self.bot.status['username']
        self.bot.confirm('Quit Clan',
                         'Are you sure you want to leave the clan?',
                         self.really_remove_user)

    def remove_user(self, *rest):
        for x in range(len(self.bot.status['selected'])):
            self.remove = self.clan_user()
            self.bot.confirm('Remove User', 'Are you sure you want to remove ' +
                             self.remove + ' from the clan?',
                             self.really_remove_user)

    def really_remove_user(self):
        self.bot.BNCS.insert_long(no_cookie)
        self.bot.BNCS.insert_string(self.remove)
        self.bot.BNCS.BNCSsend(0x78)

        del self.remove

    def set_rank_peon(self, *rest):
        for x in range(len(self.bot.status['selected'])):
            self.set_rank(self.clan_user(), 0x01)
    def set_rank_grunt(self, *rest):
        for x in range(len(self.bot.status['selected'])):
            self.set_rank(self.clan_user(), 0x02)
    def set_rank_shaman(self, *rest):
        for x in range(len(self.bot.status['selected'])):
            self.set_rank(self.clan_user(), 0x03)
    def set_rank_chieftain(self, *rest):
        self.bot.confirm('Give Chieftain',
                         'Are you sure you want to give up chieftain to this user?',
                         self.really_set_rank_chief_from_menu)

    def really_set_rank_chief_from_menu(self):
        self.really_set_rank_chief(self.clan_user(),
                                   no_cookie)
        
    def really_set_rank_chief(self, un, cookie):
        self.bot.BNCS.insert_long(cookie)
        self.bot.BNCS.insert_string(un)
        self.bot.BNCS.BNCSsend(0x74)

    def set_rank(self, rest, rank=0):
        if type(rest) == str:
            self.bot.BNCS.insert_long(no_cookie)
            self.bot.BNCS.insert_string(rest)
        else:
            user, rank = rest['arg'].split(' ', 1)

            try:
                rank = int(rank)
            except ValueError:
                try:
                    rank = rank_idx.index(rank[0].lower())
                except ValueError:
                    self.bot.respond(rest, 'No such rank')
                    return

            if rank == 0x00:
                self.really_set_rank_chief(user, self.responses.add(rest))
                return
                

            self.bot.BNCS.insert_long(self.responses.add(rest))
            self.bot.BNCS.insert_string(user)

        self.bot.BNCS.insert_byte(rank)
        self.bot.BNCS.BNCSsend(0x7A)

    def set_motd(self, cmd):
        self.bot.BNCS.insert_long(0)
        self.bot.BNCS.insert_string(cmd['arg'])
        self.bot.BNCS.BNCSsend(0x7B)

        self.bot.respond(cmd, 'New message of the day set.')

    def get_member_info(self, cmd):
        tag, name = cmd['arg'].strip().split(' ', 1)
        cmd['arg'] = {'name': name,
                      'tag': tag}
        
        name = name.lower()
        tag = format_tag(tag)


        self.bot.BNCS.insert_long(self.responses.add(cmd))
        self.bot.BNCS.insert_raw(tag)
        self.bot.BNCS.insert_string(name)
        self.bot.BNCS.BNCSsend(0x82)

    def get_accept(self, cmd):
        tag = cmd['arg'].strip().lower()

        try:
            info = self.invite[tag]
        except KeyError:
            self.bot.respond(cmd, 'There is no record of an invite from Clan ' +\
                             cmd['arg'] + '.')
            return

        self.bot.BNCS.insert_long(info[1]) #Cookie
        self.bot.BNCS.insert_long(info[4]) #Clan tag as DWORD
        self.bot.BNCS.insert_string(info[3]) #Inviter
        self.bot.BNCS.insert_byte(0x06) #Accept code
        self.bot.BNCS.BNCSsend(info[0])

        self.bot.respond(cmd, 'Invitation to Clan ' + info[2] + ' accepted.')

    def disc(self):
        #self.clear()
        self.invite = {}
        self.out_clan()

    def get_profile(self, *rest):
        for x in range(len(self.bot.status['selected'])):
            self.bot.events.call('profile', 'request',
                                 [self.clan_user()])

    def get_motd(self, *rest):
        if type(rest[0]) == dict:
            self.bot.BNCS.insert_long(self.responses.add(rest[0]))
        else:
            self.bot.BNCS.insert_long(no_cookie)
        self.bot.BNCS.BNCSsend(0x7C)

    def get_disband(self, *rest):
        self.bot.confirm('Disband Clan',
                         'Do you really want to disband the clan?',
                         self.get_really_disband)

    def get_really_disband(self, *rest):
        self.bot.BNCS.insert_long(0)
        self.bot.BNCS.BNCSsend(0x73)

    def pick_color(self, online):
        if online:
            return '#00FF00'
        else:
            return '#FF0000'

    def get_clan(self, username=''):
        if (self.bot.config['login']['product'] in ['WAR3', 'W3XP']) == False:
            return
        self.bot.BNCS.insert_long(0)
        self.bot.BNCS.BNCSsend(0x7D)

    def find_cand(self, cmd):
        if self.creating:
            self.cand.clear()
            self.bot.events.call('ui', 'list', 'cand', 'clear')
            
        self.bot.BNCS.insert_long(self.responses.add(cmd))
        self.bot.BNCS.insert_raw(create_tag(cmd['arg'].split(' ', 1)[0]))
        self.bot.BNCS.BNCSsend(0x70)

    def create_invite(self, *rest):
        if self.creating == False:
            self.bot.addchat('error', 'Clan creation not enabled.')
            return
        if len(self.bot.status['selected']) < 9:
            self.bot.addchat('error', 'Not enough users selected.')
            return
        
        self.bot.BNCS.insert_long(no_cookie)
        self.bot.BNCS.insert_string(self.cand.name)
        self.bot.BNCS.insert_raw(create_tag(self.cand.tag))
        self.bot.BNCS.insert_byte(9)

        for x in self.bot.status['selected'][:9]:
            self.bot.BNCS.insert_string(self.cand.name_from_idx(x))

        self.bot.BNCS.BNCSsend(0x71)

        self.bot.addchat('clan', 'Invites sent.')

    def recv_mult_invite(self, packet):
        cookie, result = unpack('<LB', packet['data'][:5])
        users = packet['data'][5:].split('\0')[:-1]
        self.out_cand()

        self.bot.addchat('clan', create_results[result])

        if users != []:
            build = users[0]
            if len(user) > 1:
                for user in users[1:-1]:
                    build += ', ' + users

                build += ', and ' + users[-1]
                
            self.bot.addchat('error', 'Invites for these user(s) failed: ' + build)

    def recv_cand(self, packet):
        cookie, status, num = unpack('<L2B', packet['data'][:6])
        users = packet['data'][6:].split('\0')[:-1]
        users.sort()

        cmd = self.responses.pop(cookie)
        

        if num == 0 and status == 0x00:
            self.bot.respond(cmd, 'No candidates found.')
            return

        self.bot.respond(cmd, find_cand_results[status])
        
        self.cand = status_list(self.bot, 'cand')
        self.cand.tag, self.cand.name = cmd['arg'].split(' ', 1)

        if self.creating == False:
            self.bot.events.call('ui', 'list', 'add',
                                 ['list', 'cand', 'Candidates', 31, 19,
                                  'Username', 0, 175,
                                  'Type', 0, 75],  {})
            self.bot.events.call('ui', 'list', 'cand', 'menu',
                                 ['Invite', self.create_invite])

        self.creating = True

        for user in users:
            if self.bot.channel.has_user(user):
                info = {'username': user,
                        'type': 'Channel'}
            else:
                info = {'username': user,
                        'type': 'Friend'}

            self.cand.add_user(user, info, -1)

        self.reset_cand_list()

    def update_cand_header(self):
        self.bot.events.call('ui', 'list', 'cand', 'header',
                             ['Clan ' + self.cand.tag + ' (' +\
                              str(self.cand.count) + ')'])

    def reset_cand_list(self):
        self.bot.events.call('ui', 'list', 'cand', 'clear')

        for x in self.cand.order:
            self.bot.events.call('ui', 'list', 'cand', 'add_entry',
                                 [self.cand.user[x]['username'],
                                  self.cand.user[x]['type']],
                                 {'color': '#FFFFFF'})


        self.update_cand_header()

    def out_cand(self):
        if self.creating:
            self.creating = False
            try:
                del self.cand
            except NameError:
                pass

            self.bot.events.call('ui', 'list', 'remove', ['cand'])

    def recv_make_invited(self, packet):
        cookie, tag_long = unpack('<2L', packet['data'][:8])
        tag = pack('>L', tag_long).strip('\0 ')
        rest = packet['data'][8:].split('\0', 2)
        clan_name = rest[0]
        inviter = rest[1]
        num_invited = ord(rest[2][0])

        users = rest[2][1].split('\0')[:-1]

        self.bot.addchat('clan', 'You have been invited to Clan ' +\
                         clan_name + ' (' + tag + ') by ' + inviter)
        if num_invited != 0:
            self.bot.addchat('clan', str(num_invited) + ' others were invited: ' +\
                             str(users))
        self.bot.addchat('clan', 'Type "/accept ' + tag + '" to accept this invitation.')

        self.invite[tag.lower()] = [packet['id'],
                                    cookie, tag, inviter, tag_long]


    def recv_invited(self, packet):
        cookie, tag_long = unpack('<2L', packet['data'][:8])
        tag = pack('>L', tag_long).strip('\0 ')
        rest = packet['data'][8:].split('\0', 1)
        clan_name = rest[0]
        inviter = rest[1][:-1]

        self.bot.addchat('clan', 'You have been invited to Clan ' +\
                         clan_name + ' (' + tag + ') by ' + inviter)
        self.bot.addchat('clan', 'Type "/accept ' + tag + '" to accept this invitation.')

        self.invite[tag.lower()] = [packet['id'],
                                    cookie, tag, inviter, tag_long]

    def recv_invite(self, packet):
        cookie, result = unpack('<LB', packet['data'][:5])
        
        try:
            cmd = self.responses.pop(cookie)
        except KeyError:
            self.bot.addchat('clan', invite_results[result])
        else:
            self.bot.respond(cmd, invite_results[result])

    def recv_info(self, packet):
        rank = ranks[4 - ord(packet['data'][5])]
        clan = pack('>L', unpack('<L', packet['data'][1:-1])[0]).strip('\0 ')
        self.bot.addchat('clan', 'You are a ' + rank + ' in Clan ' + clan + '.')

        self.in_clan()
        self.clan.tag = clan

    def recv_motd(self, packet):
        cookie = unpack('<L', packet['data'][:4])[0]
        try:
            cmd = self.responses.pop(cookie)
        except KeyError:
            self.bot.addchat('clan', packet['data'][8:-1])
        else:
            self.bot.respond(cmd, packet['data'][8:-1])

    def recv_quit(self, packet):
        self.bot.addchat('clan', 'You have been removed from the clan.')
        self.out_clan()

    def recv_status(self, packet):
        sp = packet['data'].find('\0')
        name = packet['data'][:sp]
        rank = 4 - ord(packet['data'][sp + 1])
        rank_name = ranks[rank]
        status = ord(packet['data'][sp + 2])
        loc = packet['data'][sp+3:-1]

        un = self.clan.user[name.lower()]

        if un['rank'] != rank_name:
            self.bot.addchat('clan', 'Clan member ' + name + ' (Currently ' + \
                             statuses[status] + ') is now a ' + rank_name + '.')
        else:
            self.bot.addchat('clan',
                             'Clan member ' + name + ' (' + rank_name +\
                             ') is now ' + statuses[status] +\
                             (loc == '' and '.' or (' (' + loc + ').')))

        self.update_user(username=name, rank=rank,
                         status=status, location=loc)

    def update_user(self, **kw):
        old = self.clan.user[kw['username'].lower()]
        old_idx = self.clan.order.index(kw['username'].lower())
        del self.clan.sorted[old_idx]

        kw['online'] = bool(kw['status'])

        if kw['online'] and not old['online']:
            self.clan.online += 1
        elif not kw['online'] and old['online']:
            self.clan.online -= 1
        
        info = [kw['rank'], (1 - kw['status']), kw['location'], kw['username']]
        
        self.clan.sorted.append(info)
        self.clan.sorted.sort()
        new_idx = self.clan.sorted.index(info)

        kw['rank'] = ranks[kw['rank']]

        if old_idx == new_idx:
            self.bot.events.call('ui', 'list', 'clan', 'upd_entry',
                                 [old_idx,
                                  0, str(kw['rank']),
                                  1, kw['username'],
                                  2, kw['location']],
                                 {'color': self.pick_color(kw['online'])})
        else:
            self.bot.events.call('ui', 'list', 'clan', 'upd_entry',
                                 [old_idx,
                                  str(kw['rank']),
                                  kw['username'],
                                  kw['location']],
                                 {'color': self.pick_color(kw['online']),
                                  'newidx': new_idx})

        self.clan.del_user(kw['username'])
        self.clan.add_user(kw['username'].lower(), kw, new_idx)
        self.update_header()

    def del_user(self, name):
        try:
            idx = self.clan.order.index(name.lower())
        except ValueError:
            return

        if self.clan.user[name]['online']:
            self.clan.online -= 1
            
        self.clan.del_user(name)

        self.bot.events.call('ui', 'list', 'clan', 'remove_entry',
                             [idx])

        self.update_header()
        

    def recv_rank_change(self, packet):
        if len(packet['data']) < 3:
            return
        old = ord(packet['data'][0])
        new = ord(packet['data'][1])

        if old == new: #why?
            return
        
        name = packet['data'][2:]

        self.bot.addchat('clan',
                         'You were ' +\
                         (new > old and 'promoted' or 'demoted') +\
                         ' to ' + ranks[4 - new] + ' (used to be ' +\
                         ranks[4 - old] + ') by ' + name)

    def recv_set_rank(self, packet):
        cookie, status = unpack('<LB', packet['data'][:5])

        try:
            cmd = self.responses.pop(cookie)
        except KeyError:
            self.bot.addchat('clan', rank_change_result(status))
        else:
            self.bot.respond(cmd, rank_change_result(status))

    def recv_chief(self, packet):
        cookie, status = unpack('<LB', packet['data'][:5])

        try:
            cmd = self.responses.pop(cookie)
        except KeyError:
            self.bot.addchat('clan', rank_change_result(status))
        else:
            self.bot.respond(cmd, rank_change_result(status))

    def recv_removed(self, packet):
        name = packet['data'][:-1]
        self.bot.addchat('clan', name + ' has been removed from the clan.')
        self.del_user(name)
        
    def recv_disband(self, packet):
        res = ord(packet['data'][4])

        if res == 0x00:
            self.bot.addchat('success', 'The clan disbanded successfully.')
        elif res == 0x02:
            self.bot.addchat('error', 'You cannot disband the clan because it is not yet one week old.')
        elif res == 0x07:
            self.bot.addchat('error', 'You are not authorized to disband the clan.')
        else:
            self.bot.addchat('error', 'There was an unknown error in disbanding the clan (' + str(res) + ')')

    def recv_member_info(self, packet):
        slen = len(packet['data']) - 15
        cookie, status, clan_name, rank, joined =\
                unpack('<LB' + str(slen) +\
                       'sxB8s', packet['data'])
        rank = ranks[4 - rank]
        
        try:
            cmd = self.responses.pop(cookie)
        except:
            return

        self.bot.respond(cmd, cmd['arg']['name'] + ' is a ' + \
                         rank + ' in Clan ' + clan_name + ' (' +\
                         cmd['arg']['tag'] + ').')

    def update_header(self):
        self.bot.events.call('ui', 'list', 'clan', 'header',
                             ['Clan ' + self.clan.tag + ' (' +\
                              str(self.clan.online) + '/' +\
                              str(self.clan.count) + ')'])

    def reset_list(self):
        self.bot.events.call('ui', 'list', 'clan', 'clear')

        for x in self.clan.order:
            self.bot.events.call('ui', 'list', 'clan', 'add_entry',
                                 [str(self.clan.user[x]['rank']),
                                  self.clan.user[x]['username'],
                                  self.clan.user[x]['location']],
                                 {'color': self.pick_color(self.clan.user[x]['online'])})


        self.update_header()

    def recv_clan(self, packet):
        self.clear()
        
        num = ord(packet['data'][4])
        info = packet['data'][5:]
        users = []

        for x in range(num):
            sp = info.find('\0')

            name = info[:sp]
            rank = 4 - ord(info[sp+1])
            status = 1 - ord(info[sp+2])

            if not status:
                self.clan.online += 1

            info = info[sp+3:]
            sp = info.find('\0')
            loc = info[:sp]

            info = info[sp+1:]

            users.append([rank, status, loc, name])

        users.sort()

        self.clan.sorted = users
        
        for x in users:
            info = {'rank': ranks[x[0]],
                    'username': x[3],
                    'online': not bool(x[1]),
                    'location': x[2]}
            self.clan.add_user(x[3].lower(), info, -1)

        self.reset_list()
