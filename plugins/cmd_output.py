import random
from string import join

class __init__():
    """Commands that echoes arguments, possible in a different format"""
    def __init__(self, bot):
        self.bot = bot
        random.seed()
        self.bot.events.add(self, 'commands', 0, 0,
                            'start', self.cmds_start)

        self.cmds_start()

    def cmds_start(self):
        self.bot.events.add(self, 'command', 0, 0,
                            'say', self.cmd_say,
                            'shout', self.cmd_shout)
        
    def cmd_say(self, cmd):
        strp = cmd['arg'].strip()
        if strp[0] == '-':
            f_end = strp.find(' ')
            if f_end != -1:
                ret = strp[f_end+1:]
                format = strp[1:f_end].upper()

                for kind in format:
                    if kind == 'U':
                        ret = ret.upper()
                    elif kind == 'L':
                        ret = ret.lower()
                    elif kind == 'R':
                        ret = ''.join(reversed(ret))
                    elif kind == 'H':
                        ret = ret.encode('hex')
                    elif kind == 'S':
                        ret_list = list(ret)
                        random.shuffle(ret_list)
                        ret = ''.join(ret_list)
                    elif kind == 'E':
                        ret = join(ret, ' ')

                cmd['arg'] = ret
        if cmd['arg'][0] == '/':
            cmd['text']['text'] = self.config['trigger'][0] + cmd['arg'][1:]
            self.parse_user(cmd['text'])
        else:
            self.bot.respond(cmd, cmd['arg'], 'send')

    def cmd_shout(self, cmd):
        ret = cmd['arg'].upper()
        if cmd['arg'][0] == '/':
            cmd['text']['text'] = self.config['trigger'][0] + ret[1:]
            self.parse_user(cmd['text'])
        else:
            self.bot.respond(cmd, ret, 'send')
