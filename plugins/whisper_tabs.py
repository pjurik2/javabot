class __init__():
    def __init__(self, bot):
        self.bot = bot
        self.bot.events.add(self, 'BNCSChat', 0, 0,
                            0x04, self.EID_WHISPER,
                            0x0A, self.EID_WHISPERSENT)
        self.bot.events.add(self, 'ui', 0, 0,
                            'start', self.ui_start)
        self.whispered = []

    def ui_start(self):
        self.whispered = []

    def closed(self, name):
        try:
            self.whispered.remove(name[6:])
            self.bot.events.remove('ui', 'disp', 'closed', name)
        except ValueError:
            pass

    def addwhisper(self, user, *args):
        usa = 'whisp_' + user
        if (user in self.whispered) == False:
            res = user.rpartition('@')
            if res[1] == '':
                un = user
            elif len(res[2]) < 4:
                un = user
            else:
                un = res[0]
            if args[-1].startswith('Your friend %s' % un):
                return
                
            self.bot.events.call('ui', 'disp', 'add',
                                 ['disp', usa, 'Whisper: ' + user])
            self.bot.events.add(self, 'ui', 'disp', usa, 0, 0,
                                'send', self.sent_tab)
            self.bot.events.add(self, 'ui', 'disp', 'closed', 0, 0,
                                usa, self.closed)
            self.whispered.append(user)
                
        self.bot.events.call('ui', 'disp', usa, 'append',
                             list(args))

    def EID_WHISPER(self, chat):
        self.addwhisper(chat['username'],
                        'whisperuser', '<From %s> ' % chat['username'],
                        'whisper', chat['text'])

    def EID_WHISPERSENT(self, chat):
        self.addwhisper(chat['username'],
                        'whisperuser', '<To %s> ' % chat['username'],
                        'whisper', chat['text'])

    def sent_tab(self, msg):
        if msg[1][0] == '/':
            return
        user = msg[0][6:]
        if user == 'your friends':
            msg[1] = '/f m ' + msg[1]
        else:  
            msg[1] = '/w %s %s' % (user, msg[1])
