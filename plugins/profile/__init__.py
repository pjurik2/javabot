from struct import unpack
from status_list import cookie_handler
from time_format import ft_ct

def create_tag(tag):
    rev = reversed(tag.ljust(4, '\0'))

    ret = ''
    for x in rev:
        ret += x

    return ret[:4]

profile_keys = ['profile\\sex',
                'profile\\age',
                'profile\\location',
                'profile\\description',
                'record\\%(product)s\\0\\wins',
                'record\\%(product)s\\0\\losses',
                'record\\%(product)s\\0\\disconnects',
                'record\\%(product)s\\0\\last game',
                'record\\%(product)s\\0\\last game result']

#                'System\\Account Created',
#                'System\\Last Logon',
#                'System\\Last Logoff',
#                'System\\Time Logged',

class __init__():
    def __init__(self, bot):
        self.bot = bot
        self.BNCS = self.bot.BNCS

        self.bot.events.add(self, 'BNCSRecv', -1, 0,
                            0x26, self.recv_0x26,
                            0x35, self.recv_0x35)

        self.bot.events.add(self, 'profile', 0, 0,
                            'request', self.request,
                            'write', self.write)

        self.requests = cookie_handler()


    def write(self, name, keys, values):
        self.BNCS.insert_long(1) #No. accounts
        self.BNCS.insert_long(len(keys)) #No. keys
        self.BNCS.insert_string(name) #Profile's username

        for key in keys:
            self.BNCS.insert_string(key) #Key to update
            
        for value in values:
            self.BNCS.insert_string(value) #Values for respective keys

        self.BNCS.BNCSsend(0x27) #SID_WRITEUSERDATA

    def request(self, names='', kind='profile'):
        res = names.rpartition('@')
        if self.bot.config['login']['product'] in ['WAR3', 'W3XP']:
            if res[1] == '':
                self.send_0x35(names)
            elif len(res[2]) < 4:
                self.send_0x35(names)
            else:
                self.send_0x26(names)
        else:
            if res[1] == '':
                self.send_0x26(names)
            elif len(res[2]) < 4:
                self.send_0x26(names)
            else:
                self.send_0x35(names)

    def send_0x35(self, names):
        req_id = self.requests.add({'username': names})

        self.BNCS.insert_long(req_id)
        self.BNCS.insert_string(names)
        self.BNCS.BNCSsend(0x35)

    def recv_0x35(self, packet):
        cookie, success = unpack('<LB', packet['data'][:5])

        if len(packet['data']) == 5:
            self.requests.pop(cookie)
            return

        name = self.requests.pop(cookie)['username']
        descr, loc = packet['data'][5:-5].split('\0', 1)
        clan = packet['data'][-4:]
        clan_tag = create_tag(clan)

        
        fkeys = [['Name', 'text', name, False],
                 ['Clan', 'text', clan_tag, False],
                 ['Location', 'text', loc, 'profile\\location'],
                 ['Description', 'big_text', descr, 'profile\\description']]

        self.bot.events.call('profile', 'received', [name, fkeys])
            

    def send_0x26(self, names, keys=profile_keys):
        if type(names) == str:
            names = [names] #Force list

        req_id = self.requests.add([names, keys])
            
        self.BNCS.insert_long(len(names))
        self.BNCS.insert_long(len(keys))
        self.BNCS.insert_long(req_id)
        for name in names:
            self.BNCS.insert_string(name)
        for key in keys:
            self.BNCS.insert_string(key % self.bot.config['login'])

        self.BNCS.BNCSsend(0x26)
        return req_id

    def recv_0x26(self, packet):
        results = unpack('<3L', packet['data'][:12])

        keys = packet['data'][12:].split('\0')[:-1]
        req = self.requests.pop(results[2])

        passed = 0
        key_len = len(keys) / len(req[0])
        for name in req[0]:
            now = keys[passed:key_len]
            passed += key_len
            
            record = '%s/%s/%s' % (keys[4].zfill(1),
                                   keys[5].zfill(1),
                                   keys[6].zfill(1))
            if keys[8] == '' or keys[7] == '':
                lg = 'Never played'
            else:
                lg = keys[8] + ' @ ' + ft_ct(keys[7])
                
                    
            fkeys = [['Name', 'text', name, False],
                     ['Sex', 'text', keys[0], 'profile\\sex'],
                     ['Age', 'text', keys[1], False],
                     ['Location', 'text', keys[2], 'profile\\location'],
                     ['Description', 'big_text', keys[3], 'profile\\description'],
                     ['Record', 'text', record, False],
                     ['Last Game', 'text', lg, False]]

            self.bot.events.call('profile', 'received', [name, fkeys])
