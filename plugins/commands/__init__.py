from getopt import gnu_getopt
from xml.dom import minidom
from time_format import time_diff
import time
from os import sep
import re

class __init__():
    def __init__(self, bot):
        self.bot = bot
        bot.cmd = self
        self.bot.access_cmp = self.can_edit

        self.bot.events.add(self, 'bot', 0, 0,
                            'load_config', self.load_config)

        self.bot.events.add(self, 'IO', -1000, 0,
                            'send', self.parse_self)
                            

        self.bot.events.add(self, 'BNCSChat', 0, 0,
                            0x04, self.parse_user,
                            0x05, self.parse_user)

        self.builtin = ('version', self.cmd_ver,
                        'help', self.cmd_help,
                        'whois', self.cmd_whois,
                        'group', self.cmd_group,
                        'adduser', self.cmd_user_add,
                        'deluser', self.cmd_user_del,
                        'ping', self.cmd_ping,
                        'home', self.cmd_home,
                        'bnetcmd', self.cmd_bnet,
                        'trigger', self.cmd_trig,
                        'uptime', self.cmd_uptime,
                        'cq', self.cmd_cq,
                        'scq', self.cmd_scq,
                        'lasttalk', self.cmd_lasttalk,
                        'reload', self.cmd_reload,
                        'path', self.cmd_path,
                        'time', self.cmd_time)
        
        self.load_config()

    def load_config(self):
        default = {'users': self.bot.path+'users.txt',
                   'commands': self.bot.path+'commands.xml',
                   'access': self.bot.path+'access.xml',
                   'trigger': '.'}
        try:
            default.update(self.bot.config['access'])
        except KeyError:
            pass
        finally:
            self.bot.config['access'] = default
        self.config = self.bot.config['access']
        
        if type(self.config['trigger']) != tuple:
            self.config['trigger'] = tuple(self.config['trigger'].split('/%/'))

        self.load_commands()
        self.load_access()
        self.load_users()

    def load_users(self):
        self.user = {} #{self.bot.config['login']['username']: set([])}
        self.bot.access = self.user
        self.load_access_file('users.txt')
        self.load_access_file(self.config['users'])

    def load_access_file(self, fname):
        try:
            f_access = open(fname, 'r')
        except IOError:
            return #No access file

        entries = f_access.readlines()

        for entry in entries:
            indiv = entry.strip('\n\r ').split(' ', 1)
            if len(indiv) > 1:
                self.user[indiv[0].lower()] = self.parse_user_access(indiv[1])
        f_access.close()

    def parse_user_access(self, string):
        indiv = string.strip('\n\r ').split(' ')
        groups, flags, num = [], [], 0

        for access in indiv:
            if access.isalpha():
                if len(access) == 1:
                    flags.append(access)
                else:
                    groups.append(access)
            elif access.isdigit():
                new = int(access)
                if new > num:
                    num = new

        inh_groups = []
        inh_flags = [] + flags
        inh_num = num
            
        for group in groups:
            if group in self.group:
                inh = self.group[group]['inherit']
                inh_groups += inh['group']
                inh_flags += inh['flag']
                
                if inh_num < inh['num']:
                    inh_num = inh['num']

        man_groups = []
        man_flags = [] + flags
        for group in groups:
            if group in self.group:
                man= self.group[group]['manage']
                man_groups += man['group']
                man_flags += man['flag']
                
        return {'groups': set(groups),
                'flags': set(flags),
                'num': num,
                'inh_groups': set(inh_groups),
                'inh_flags': set(inh_flags),
                'inh_num': inh_num,
                'man_groups': set(man_groups),
                'man_flags': set(man_flags),
                'access': string}
        

    def load_access(self):
        self.group = {}
        self.group_alias = {}
        
        self.load_access_xml('access.xml')
        self.load_access_xml(self.config['access'])
        group_default = ''

        for name in self.group.iterkeys():
            self.get_group_inherit(name)
            self.get_group_manage(name)

            if self.group[name]['type'] == 'default':
                if group_default == '':
                    group_default = name
                else:
                    group_default += ' ' + name

        self.group_default = self.parse_user_access(group_default)

        #for k, v in self.group.iteritems():
        #    print '+++++%s+++++' % k
        #    for a, b in v.iteritems():
        #        print '--' + a
        #        print b



    def get_group_inherit(self, group):
        try:
            gn = self.group_alias[group]
        except KeyError:
            return False

        visited = []
        queue = [gn]
        
        num = 0
        group = [gn]
        flags = []

        while queue != []:
            name = queue.pop(0)
            visited.append(name)
            gr = self.group[name]
            flags += gr['inherit']['flag']
            if num < gr['inherit']['num']:
                num = gr['inherit']['num']

            for each in gr['inherit']['group']:
                try:
                    new = self.group_alias[each]
                except KeyError:
                    pass
                else:
                    group.append(new)
                    if (new in visited) == False:
                        queue.append(new)

        self.group[gn]['inherit'] = {'flag': flags,
                                     'group': group,
                                     'num': num}

    def get_group_manage(self, group):
        try:
            gn = self.group_alias[group]
        except KeyError:
            return False

        visited = []
        queue = [gn]
        first = True
        
        num = 0
        group = []
        flags = []

        while queue != []:
            name = queue.pop(0)
            visited.append(name)
            gr = self.group[name]
            flags += gr['manage']['flag']

            for each in gr['manage']['group']:
                try:
                    new = self.group_alias[each]
                except KeyError:
                    pass
                else:
                    if first and gn == new:
                        first = False        
                    group.append(new)
                    if (new in visited) == False:
                        queue.append(new)

            if not first:
                flags += gr['inherit']['flag']

                for each in gr['inherit']['group']:
                    try:
                        new = self.group_alias[each]
                    except KeyError:
                        pass
                    else:
                        group.append(new)
                    if (new in visited) == False:
                        queue.append(new)
            else:
                first = False
                    
        self.group[gn]['manage'] = {'flag': flags,
                                     'group': group}

    def load_access_xml(self, fname):
        try:
            xml_acc_doc = minidom.parse(fname)
        except IOError:
            return
        
        xml_access = xml_acc_doc.childNodes[0]

        if xml_access.nodeName != 'access':
            return False #Unknown node name

        xml_version = xml_access.getAttribute('version')
        if xml_version != '1.0':
            return False #Unsupported version number

        xml_acc_list = xml_access.childNodes

        for xml_acc_indiv in xml_acc_list:
            if xml_acc_indiv.nodeName == 'group':
                xml_acc_attrs = xml_acc_indiv.childNodes
                group_name = str(xml_acc_indiv.getAttribute('name'))

                if (group_name in self.group) == False:
                    self.group[group_name] = {'inherit': {'flag': [],
                                                          'num': 0,
                                                          'group': []},
                                              'manage': {'flag': [],
                                                         'group': []},
                                              'event': {},
                                              'type': str(xml_acc_indiv.getAttribute('type'))}
                    self.group_alias[group_name] = group_name
                g = self.group[group_name]

                for xml_acc_attr in xml_acc_attrs:
                    name = str(xml_acc_attr.nodeName)
                    if name == 'alias':
                        alias = str(xml_acc_attr.firstChild.data.strip())

                        #self.group[group_name]['alias'].append(alias)
                        self.group_alias[alias] = group_name
                        
                    #elif name == 'description':
                    #    self.cmd[cmd_name]['description'] = \
                    #    str(xml_cmd_attr.firstChild.data.strip())

                    elif name == 'inherit':
                        xml_acc_sets = xml_acc_attr.childNodes
                        
                        for xml_acc_set in xml_acc_sets:
                            nn = str(xml_acc_set.nodeName)
                            if nn == 'group':
                                g['inherit']['group'].append(\
                                    str(xml_acc_set.firstChild.data.strip().lower()))
                            elif nn == 'flag':
                                g['inherit']['flag'] += list(\
                                    str(xml_acc_set.firstChild.data).strip())
                            elif nn == 'access':
                                prop = int(xml_acc_set.firstChild.data)
                                if g['inherit']['num'] < prop:
                                    g['inherit']['num'] = prop
                    elif name == 'manage':
                        xml_acc_sets = xml_acc_attr.childNodes
                        
                        for xml_acc_set in xml_acc_sets:
                            nn = str(xml_acc_set.nodeName)
                            if nn == 'group':
                                g['manage']['group'].append(\
                                    str(xml_acc_set.firstChild.data.strip().lower()))
                            elif nn == 'flag':
                                g['manage']['flag'] += list(\
                                    str(xml_acc_set.firstChild.data).strip())
                            elif nn == 'access':
                                #Should use an inherit tag for this, but we'll handle it
                                prop = int(xml_acc_set.firstChild.data)
                                if g['inherit']['num'] < prop:
                                    g['inherit']['num'] = prop
        

    def load_commands(self):
        self.cmd = {}
        self.alias = {}
        self.bot.events.remove('command')

        self.load_cmd_xml('commands.xml')
        self.load_cmd_xml(self.config['commands'])

        self.bot.events.add(self, 'command', 0, 0,
                            *self.builtin)
        self.bot.events.call('commands', 'start')
        

    def load_cmd_xml(self, fname):
        try:
            xml_cmd_doc = minidom.parse(fname)
        except IOError:
            return
        
        xml_commands = xml_cmd_doc.childNodes[0]

        if xml_commands.nodeName != 'commands':
            return False #Unknown node name

        xml_version = xml_commands.getAttribute('version')
        if xml_version != '1.0':
            return False #Unsupported version number

        xml_cmd_list = xml_commands.childNodes

        for xml_cmd_indiv in xml_cmd_list:
            if xml_cmd_indiv.nodeName == 'command':
                xml_cmd_attrs = xml_cmd_indiv.childNodes
                cmd_name = str(xml_cmd_indiv.getAttribute('name'))

                if (cmd_name in self.cmd) == False:
                    self.cmd[cmd_name] = {'description': '',
                                          'group': [],
                                          'flag': [],
                                          'num': 10000}

                for xml_cmd_attr in xml_cmd_attrs:
                    name = str(xml_cmd_attr.nodeName)
                    if name == 'alias':
                        alias = str(xml_cmd_attr.firstChild.data.strip())

                        #self.cmd[cmd_name]['alias'].append(alias)
                        self.alias[alias] = cmd_name
                        
                    elif name == 'description':
                        self.cmd[cmd_name]['description'] = \
                        str(xml_cmd_attr.firstChild.data.strip())

                    elif name == 'access':
                        xml_cmd_sets = xml_cmd_attr.childNodes
                        
                        for xml_cmd_set in xml_cmd_sets:
                            nn = str(xml_cmd_set.nodeName)
                            if nn == 'group':
                                self.cmd[cmd_name]['group'].append(\
                                    str(xml_cmd_set.firstChild.data.strip().lower()))
                            elif nn == 'flag':
                                self.cmd[cmd_name]['flag'] += list(\
                                    xml_cmd_set.firstChild.data.strip())
                            elif nn == 'access':
                                prop = int(xml_cmd_set.firstChild.data)
                                if self.cmd[cmd_name]['num'] > prop:
                                    self.cmd[cmd_name]['num'] = prop

                self.cmd[cmd_name]['group'] = set(self.cmd[cmd_name]['group'])
                self.cmd[cmd_name]['flag'] = set(self.cmd[cmd_name]['flag'])

    def save_users(self):
        f_access = open(self.config['users'], 'w')
        for k, s in self.user.iteritems():
            f_access.write(k + ' ' + s['access']+'\n')
        f_access.close()

    def can_edit(self, editor, edited):
        if (editor['man_groups'] & edited['inh_groups']) != edited['inh_groups'] or\
           (editor['man_flags'] & edited['inh_flags']) != edited['inh_flags'] or\
           (editor['inh_num'] < edited['inh_num']):
            return False
        else:
            return True

    def del_user(self, user, gp=-1):
        try:
            if gp != -1 and self.can_edit(self.user[gp], self.user[user]) == False:
                    return 'User was not removed because they have more access than you.'
            
            del self.user[user]
        except KeyError:
            return 'User not found'

        self.save_users()
        return 'User successfully removed'

    def add_user(self, user, access, update=True, gp=-1):
        if (user in self.user):
            access += ' ' + self.user[user]['access']

        new = self.parse_user_access(access)

        if gp != -1:
            if self.can_edit(self.user[gp], new) == False:
                return 'User was not added because you do not have enough access.'

        self.user[user] = new
        self.save_users()
        return 'User successfully added'

    def whois_user(self, name):
        try:
            user = self.user[name]
            ret = ''
        except KeyError:
            ret = '(default) '
            user = self.group_default

        w = list(user['flags'])
        w.sort()
        build = ''
        for x in w:
            build += x

        if user['groups'] == set([]):
            ret += 'no groups'
        else:
            ret += 'groups ' + str(user['groups'])[5:-2]

        ret += ' with ' + str(user['num']) + ' access'

        if build != '':
            ret += ' and flags ' + build

        ret += '.'
        return ret
        
    def parse_self(self, text):
        if 'send_now' in text:
            return
        if text == '':
            return

        text['send_now'] = True

        user = self.bot.config['login']['username'].lower()
        
        if text['text'][0] == '/':
            arg = text['text'][1:]
            
            if arg[0] == '/':
                arg = arg[1:]
                output = 'send'
            elif arg[0] == '.':
                text['text'] = '/' + arg[1:]
                self.bot.send(**text)
                return False
            else:
                output = 'addchat'
                
            cmd = arg.lstrip(' ').split(' ', 1)

            if len(cmd) > 1:
                arg = cmd[1]
            else:
                arg = ''

            cmd = cmd[0].lower()
            try:
                cmd_root = self.alias[cmd]
            except KeyError:
                cmd_root = cmd

            ref = {'command': cmd,
                   'arg': arg,
                   'text': text,
                   'trigger': '/',
                   'output': output,
                   'username': user,
                   'internal': True}

            if self.bot.events.call('command', cmd_root, [ref]):
                return False

    def parse_user(self, chat):
        cmd = False

        user = chat['username'].lower()

        if chat['text'].lower() == '?trigger':
            trigger = '?'
            cmd = ['trigger']
        else:
            #wouldn't it be nice to use .startswith here?
            for x in self.config['trigger']:
                try:
                    if chat['text'][:len(x)] == x:
                        trigger = x
                        cmd = chat['text'][len(x):].lstrip().split(' ', 1)
                        break
                except IndexError:
                    pass
            if cmd == False:
                name_trig = re.split('(:|,)', chat['text'], 1)
                if len(name_trig) > 2:
                    try:
                        res = re.search('^' + name_trig[0].replace('*', '(.*)') + '$', self.bot.status['username'], re.I)
                    except re.error:
                        return
                    if res != None:
                        trigger = name_trig[0]
                        cmd = name_trig[2].lstrip().split(' ', 1)

        if cmd == False:
            return

        if len(cmd) > 1:
            arg = cmd[1]
        else:
            arg = ''

        cmd = cmd[0].lower()
        try:
            cmd_root = self.alias[cmd]
        except KeyError:
            cmd_root = cmd

        try:
            acc = self.user[user]
        except KeyError:
            acc = self.group_default

        try:
            if (acc['inh_groups'] & self.cmd[cmd_root]['group']) == set([]) and \
               (acc['inh_flags'] & self.cmd[cmd_root]['flag']) == set([]) and \
               acc['inh_num'] < self.cmd[cmd_root]['num']:
                return #no group, flag, or access match
        except KeyError:
            return

        ref = {'command': cmd,
               'arg': arg,
               'text': chat,
               'trigger': trigger,
               'output': chat['id'] == 0x04 and 'whisper' or 'send',
               'username': user,
               'internal': False}

        self.bot.events.call('command', cmd_root, [ref])

    def cmd_ver(self, cmd):
        self.bot.respond(cmd, self.bot.ver())

    def cmd_help(self, cmd):
        if cmd['arg'] == '':
            cmd['arg'] = 'help'
            
        if cmd['arg'] in self.alias:
            self.bot.respond(cmd, self.cmd[self.alias[cmd['arg']]]['description'])
        else:
            self.bot.respond(cmd, 'Command was not found.')

    def cmd_user_add(self, cmd):
        if cmd['command'].find('set') == -1:
            update = True
        else:
            update = False
            
        args = cmd['arg'].split(' ', 1)

        if cmd['internal']:
            self.bot.respond(cmd, self.add_user(args[0], args[1], update))
        else:
            self.bot.respond(cmd, self.add_user(args[0], args[1], update, cmd['username']))

    def cmd_user_del(self, cmd):
        if cmd['internal']:
            self.bot.respond(cmd, self.del_user(cmd['arg']))
        else:
            self.bot.respond(cmd, self.del_user(cmd['arg'], cmd['username']))

    def cmd_whois(self, cmd):
        if cmd['internal']:
            if self.bot.channel.has_user(cmd['arg']):
                self.bot.addchat(cmd['arg'] + ' is in the channel using '+\
                                 self.bot.channel.user[cmd['arg'].lower()]['display'])
            if cmd['text']['text'][:2] != '//':
                self.bot.respond(cmd, cmd['text']['text'], 'send')
        
        if cmd['arg'] == '':
            cmd['arg'] = cmd['username']
    
        user = cmd['arg'].lower()
            
        found = self.whois_user(user)
        if found == False:
            self.bot.respond(cmd, cmd['arg'] + ' has no access')
        elif cmd['arg'] == '':
            self.bot.respond(cmd, 'You were found in '+found)
        else:
            self.bot.respond(cmd, cmd['arg'] + ' is in '+found)

    def cmd_group(self, cmd):
        users = []

        if cmd['arg'] == '':
            self.bot.respond(cmd, 'No group was selected.')
        
        group = set(cmd['arg'].split())

        for k, v in self.user.iteritems():
            if v & group != set([]):
                users.append(k)

        if len(group) == 1:
            groupdescr = 'that group.'
        else:
            groupdescr = 'those groups.'
            

        if users == []:
            self.bot.respond(cmd, 'No users were found in '+groupdescr)
        elif len(users) == 1:
            self.bot.respond(cmd, users[0] + ' was found in '+groupdescr)
        else:
            build = users[0]
            for x in users[1:]:
                build = build + ', ' + x
                
            self.bot.respond(cmd, build + ' were found in '+groupdescr)

    def cmd_ping(self, cmd):
        if cmd['arg'] == '':
            cmd['arg'] = cmd['username']
            
        user = cmd['arg'].lower()

        if self.bot.channel.has_user(user) == False:
            self.bot.respond(cmd, cmd['arg'] + ' is not in the channel.')
            return
        
        self.bot.respond(cmd, str(self.bot.channel.user[user]['ping'])+'ms')

    def cmd_uptime(self, cmd):
        self.bot.respond(cmd, self.bot.uptime())

    def cmd_home(self, cmd):
        self.bot.respond(cmd, '/join ' + self.bot.config['login']['home'], 'send')

    def cmd_bnet(self, cmd):
        self.bot.respond(cmd, '/' + cmd['command'] + ' ' + cmd['arg'], 'send')

    def cmd_cq(self, cmd):
        self.bot.events.call('bot', 'clear_queue')
        self.bot.respond(cmd, 'Queue cleared.')

    def cmd_scq(self, cmd):
        self.bot.events.call('bot', 'clear_queue')

    def cmd_lasttalk(self, cmd):
        if cmd['arg'] == '':
            cmd['arg'] = cmd['username']
        
        user = cmd['arg'].lower()

        if self.bot.channel.has_user(user) == False:
            self.bot.respond(cmd, 'No such user in the channel.')
            return

        talked = self.bot.channel.user[user]['talked']

        if talked == -1:
            self.bot.respond(cmd, cmd['arg'] +\
                         ' has not said anything since I entered the channel.')
        else:
            self.bot.respond(cmd, cmd['arg'] + ' last said something ' +\
                         time_diff(talked, time.time()) + ' ago.')

    def cmd_trig(self, cmd):
        if len(self.config['trigger']) == 1:
            self.bot.respond(cmd, 'Current trigger: ' + str(self.config['trigger'])[1:-2] + '.')
        else:
            self.bot.respond(cmd, 'Current triggers: ' + str(self.config['trigger'])[1:-1] + '.')

    def cmd_reload(self, cmd):
        if self.bot.plugins.reset_class(cmd['arg']) != False:
            self.bot.respond(cmd, '"' + cmd['arg'] + '" plugin successfully reloaded.')
            return False

        self.bot.respond(cmd, '"' + cmd['arg'] + '" failed to reload.')

    def cmd_path(self, cmd):
        self.bot.respond(cmd, 'The current bot\'s path is "'+sep+self.bot.path+'"')

    def cmd_time(self, cmd):
        self.bot.respond(cmd, 'It is currently ' + time.strftime('%c %Z', time.localtime()))
            
                            
