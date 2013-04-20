from password import XSha1
from struct import pack

val2 = []
priv = []

def factor(n, noduplicates = True):
    intn = int(n)
    factors = {}
    lastfactor = n
    i = 0

    # 1 is a special case
    if n == 1:
        return {1: 1}

    while 1:
        i += 1

        # avoid duplicates like {1: 3, 3: 1}
        if noduplicates and lastfactor <= i:
            break

        # stop when i is bigger than n
        if i > n:
            break

        if n % i == 0:
            factors[i] = n / i
            lastfactor = n / i

    return factors



class num():
    def __init__(self, key, do=True):
        self.do = do
        self.xsha1 = XSha1(self)
        self.orig = key
        self.key = key
        self.lkey = list(key)
        if len(self.key) != 13:
            raise ValueError(self.key)

        self.sc()

    def sc(self):
        if self.verify():
            self.shuffle()
            self.get_final_value()
            if False:
                print '%s      %s         %s|%s           %s|%s' % (self.orig,
                    self.get_product(),
                                                                str(self.get_val1()).rjust(7, '0'),
                                                                   self.get_val1_hex(),
                                                                   str(self.get_val2()).rjust(3, '0'),
                                                                   self.get_val2_hex())
            val2.append([self.get_product(), self.get_val2(), self.get_val1()])
            #pub_match[self.get_product()].append(self.get_val1())
        else:
            raise ValueError(self.key)

    def verify(self):
        accum = 3
        key = self.key.lower()

        for i in range(len(key) - 1):
            accum += (ord(key[i]) - 48) ^ (accum * 2)

        return (accum % 10) == (ord(key[12]) - 48)

    def shuffle(self):
        pos = 0x0B

        for i in range(0xC2, 0x06, -0x11):
            self.swap(pos, i % 0x0C)
            pos -= 1

    def swap(self, a, b):
        self.lkey[a], self.lkey[b] = self.lkey[b], self.lkey[a]
        self.key = ''.join(self.lkey)

    def get_final_value(self):
        hash_key = 0x13AC9741

        for i in range(len(self.key) - 2, -1, -1):
            if self.key[i] <= '7':
                self.lkey[i] = chr(ord(self.lkey[i]) ^ (hash_key & 7))
                hash_key >>= 3
            elif self.key[i] < 'A':
                self.lkey[i] = chr(ord(self.lkey[i]) ^ (i & 1))

        self.key = ''.join(self.lkey)

    def get_val2_hex(self):
        return pack('>L', int(self.key[9:12])).encode('hex')[4:]
    def get_val1_hex(self):
        return pack('>L', int(self.key[2:9])).encode('hex')

    def get_product(self):
        return int(self.key[0:2])
    def get_val2(self):
        return int(self.key[9:12])
    def get_val1(self):
        return int(self.key[2:9])
    def get_key_hash(self, ctoken, stoken):
        return self.xsha1.calc_hash_buffer(pack('6L',
                                                ctoken,
                                                stoken,
                                                self.get_product(),
                                                self.get_val1(),
                                                0,
                                                self.get_val2()))


def encode(public, private, product=1):
    key_len = 13
    hash_key = 0x13AC9741

    cdkey = "%02u%07lu%03lu0" % (product, public, private)
    cdkey = list(cdkey.upper())
    for i in range(key_len - 2, -1, -1):
        if cdkey[i] <= '7':
            cdkey[i] = chr(ord(cdkey[i]) ^ (hash_key & 7))
            hash_key >>= 3
        elif cdkey[i] < 'A':
            cdkey[i] = chr(ord(cdkey[i]) ^ (i & 7))

    pos = 0
    for i in range(7, 0xC3, 0x11):
        temp = cdkey[i % 0x0C]
        cdkey[i % 0x0C] = cdkey[pos]
        cdkey[pos] = temp
        pos += 1

    accum = 3
    for i in range(key_len - 1):
        accum += (ord(cdkey[i].lower()) - ord('0')) ^ (accum * 2)

    cdkey[12] = chr((accum % 10) + ord('0'))

    return ''.join(cdkey)

f = open('keys.txt')
keys = f.readlines()
f.close()
print 'CDKey              Product   Val1                       Val2'
for key in keys:
    key = key.strip(' \n\r')[:13]
    if key[-1] == key[-2]:
        print key
    try:
        num(key)
    except ValueError:
        print key + ' failed the verify check.'
##
##print list(set(priv))
##
#val2.sort()
##print 'Prod      Public           Private'
#print 'Prod      Private    Public'
#for val in val2:
#    print '%s        %s        %s' % (str(val[0]).rjust(2, '0'), str(val[1]).rjust(3, '0'), str(val[2]).rjust(7, '0'))


#print set(pub_match[1]) & set(pub_match[2])
