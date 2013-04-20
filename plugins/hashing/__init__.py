from password import XSha1
import srp
import cdkey
from struct import pack, unpack
from time import time

class __init__():
    def __init__(self, bot):
        self.bot = bot
        self.xsha1 = XSha1(self)
        self.bot.events.add(self, 'hashing', 'get', -1, 0,
                            'pwhash', self.double,
                            'new_pwhash', self.single,
                            'cdkey', self.key,
                            'nls_logon', self.nls_logon,
                            'nls_logon_from_create', self.nls_logon,
                            'nls_logon_proof', self.nls_logon_proof,
                            'nls_create', self.nls_create)
    def nls_create(self):
        v = srp.big_num_to_str(self.srp.get_v(self.bot.status['salt']))
        self.bot.status['new_wc3_account'] = self.bot.status['salt'] +\
                                             v
        self.bot.events.call('hashing', 'recv', 'nls_create')
        return False

    def nls_logon(self):
        self.srp = srp.SRP(self.bot.connfig['login']['username'],
                           self.bot.connfig['login']['password'])
        
        self.bot.status['ckA'] = srp.big_num_to_str(self.srp.get_A())
        self.bot.events.call('hashing', 'recv', 'nls_logon')
        return False

    def nls_logon_proof(self):
        self.srp.B = srp.str_to_big_num(self.bot.status['ckB'])

        self.srp.get_v(self.bot.status['salt'])
        self.srp.get_u(self.bot.status['ckB'])
        self.srp.get_S(self.bot.status['salt'],
                       self.srp.B)
        self.srp.get_K(srp.big_num_to_str(self.srp.S))
        self.srp.get_M1(self.bot.status['salt'],
                        self.bot.status['ckB'])

        self.bot.status['M1'] = self.srp.M1
        self.bot.events.call('hashing', 'recv', 'nls_logon_proof')

        del self.srp
        return False

    def key(self):
        try:
            self.bot.status['ctoken'] = int(time())
            key = self.bot.connfig['login']['cdkey']
            key_len = len(key)
            if key_len == 13:
                x = cdkey.num(self, key)
            elif key_len == 16:
                x = cdkey.alphanum(self, key)
                if self.bot.connfig['login']['product'] in ['D2XP', 'W3XP']:
                    x2 = cdkey.alphanum(self, self.bot.connfig['login']['expcdkey'])
                    self.exp_update(x2)
            elif key_len == 26:
                x = cdkey.alphanumex(self, key)
                if self.bot.connfig['login']['product'] in ['D2XP', 'W3XP']:
                    x2 = cdkey.alphanumex(self, self.bot.connfig['login']['expcdkey'])
                    self.exp_update(x2)
            else:
                return
            
            r = x.get_key_hash(self.bot.status['ctoken'],
                               self.bot.status['stoken'])
            #print 'PRODUCT: %d' % x.get_product()
            #print 'PUBLIC: %d' % x.get_val1()
            self.bot.status['keyhash'] = pack('9l',
                                              key_len,
                                              x.get_product(),
                                              x.get_val1(),
                                              0,
                                              *r)
        except ValueError, key:
            self.bot.addchat('error', 'Invalid cd-key: ' + str(key))
        else:
            self.bot.events.call('hashing', 'recv', 'cdkey')

        return False
        
    def exp_update(self, x2):
        r = x2.get_key_hash(self.bot.status['ctoken'],
                            self.bot.status['stoken'])
        self.bot.status['expkeyhash'] = pack('9l',
                                             len(self.bot.connfig['login']['expcdkey']),
                                             x2.get_product(),
                                             x2.get_val1(),
                                             0,
                                             *r)
        
    def single(self):
        a = self.xsha1.calc_hash_buffer(self.bot.connfig['login']['password'].lower())
        self.bot.status['new_pwhash'] = pack('<5l', *a)
        self.bot.events.call('hashing', 'recv', 'new_pwhash')

        return False

    def double(self):
        a = self.xsha1.calc_hash_buffer(self.bot.connfig['login']['password'].lower())
        bu = pack('<2L5l', self.bot.status['ctoken'],
                  self.bot.status['stoken'],
                  *a)
        b = self.xsha1.calc_hash_buffer(bu)
        self.bot.status['pwhash'] = pack('<5l', *b)
        self.bot.events.call('hashing', 'recv', 'pwhash')
        
        return False
