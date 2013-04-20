from struct import pack, unpack
from ctypes import c_byte, c_int32, c_uint32
from hashlib import sha1

translate =  [0x09,  0x04,  0x07,  0x0F,  0x0D,
              0x0A,  0x03,  0x0B,  0x01,  0x02,  0x0C,  0x08,  0x06,
              0x0E,  0x05,  0x00,  0x09,  0x0B,  0x05,  0x04,  0x08,
              0x0F,  0x01,  0x0E,  0x07,  0x00,  0x03,  0x02,  0x0A,
              0x06,  0x0D,  0x0C,  0x0C,  0x0E,  0x01,  0x04,  0x09,
              0x0F,  0x0A,  0x0B,  0x0D,  0x06,  0x00,  0x08,  0x07,
              0x02,  0x05,  0x03,  0x0B,  0x02,  0x05,  0x0E,  0x0D,
              0x03,  0x09,  0x00,  0x01,  0x0F,  0x07,  0x0C,  0x0A,
              0x06,  0x04,  0x08,  0x06,  0x02,  0x04,  0x05,  0x0B,
              0x08,  0x0C,  0x0E,  0x0D,  0x0F,  0x07,  0x01,  0x0A,
              0x00,  0x03,  0x09,  0x05,  0x04,  0x0E,  0x0C,  0x07,
              0x06,  0x0D,  0x0A,  0x0F,  0x02,  0x09,  0x01,  0x00,
              0x0B,  0x08,  0x03,  0x0C,  0x07,  0x08,  0x0F,  0x0B,
              0x00,  0x05,  0x09,  0x0D,  0x0A,  0x06,  0x0E,  0x02,
              0x04,  0x03,  0x01,  0x03,  0x0A,  0x0E,  0x08,  0x01,
              0x0B,  0x05,  0x04,  0x02,  0x0F,  0x0D,  0x0C,  0x06,
              0x07,  0x09,  0x00,  0x0C,  0x0D,  0x01,  0x0F,  0x08,
              0x0E,  0x05,  0x0B,  0x03,  0x0A,  0x09,  0x00,  0x07,
              0x02,  0x04,  0x06,  0x0D,  0x0A,  0x07,  0x0E,  0x01,
              0x06,  0x0B,  0x08,  0x0F,  0x0C,  0x05,  0x02,  0x03,
              0x00,  0x04,  0x09,  0x03,  0x0E,  0x07,  0x05,  0x0B,
              0x0F,  0x08,  0x0C,  0x01,  0x0A,  0x04,  0x0D,  0x00,
              0x06,  0x09,  0x02,  0x0B,  0x06,  0x09,  0x04,  0x01,
              0x08,  0x0A,  0x0D,  0x07,  0x0E,  0x00,  0x0C,  0x0F,
              0x02,  0x03,  0x05,  0x0C,  0x07,  0x08,  0x0D,  0x03,
              0x0B,  0x00,  0x0E,  0x06,  0x0F,  0x09,  0x04,  0x0A,
              0x01,  0x05,  0x02,  0x0C,  0x06,  0x0D,  0x09,  0x0B,
              0x00,  0x01,  0x02,  0x0F,  0x07,  0x03,  0x04,  0x0A,
              0x0E,  0x08,  0x05,  0x03,  0x06,  0x01,  0x05,  0x0B,
              0x0C,  0x08,  0x00,  0x0F,  0x0E,  0x09,  0x04,  0x07,
              0x0A,  0x0D,  0x02,  0x0A,  0x07,  0x0B,  0x0F,  0x02,
              0x08,  0x00,  0x0D,  0x0E,  0x0C,  0x01,  0x06,  0x09,
              0x03,  0x05,  0x04,  0x0A,  0x0B,  0x0D,  0x04,  0x03,
              0x08,  0x05,  0x09,  0x01,  0x00,  0x0F,  0x0C,  0x07,
              0x0E,  0x02,  0x06,  0x0B,  0x04,  0x0D,  0x0F,  0x01,
              0x06,  0x03,  0x0E,  0x07,  0x0A,  0x0C,  0x08,  0x09,
              0x02,  0x05,  0x00,  0x09,  0x06,  0x07,  0x00,  0x01,
              0x0A,  0x0D,  0x02,  0x03,  0x0E,  0x0F,  0x0C,  0x05,
              0x0B,  0x04,  0x08,  0x0D,  0x0E,  0x05,  0x06,  0x01,
              0x09,  0x08,  0x0C,  0x02,  0x0F,  0x03,  0x07,  0x0B,
              0x04,  0x00,  0x0A,  0x09,  0x0F,  0x04,  0x00,  0x01,
              0x06,  0x0A,  0x0E,  0x02,  0x03,  0x07,  0x0D,  0x05,
              0x0B,  0x08,  0x0C,  0x03,  0x0E,  0x01,  0x0A,  0x02,
              0x0C,  0x08,  0x04,  0x0B,  0x07,  0x0D,  0x00,  0x0F,
              0x06,  0x09,  0x05,  0x07,  0x02,  0x0C,  0x06,  0x0A,
              0x08,  0x0B,  0x00,  0x0F,  0x04,  0x03,  0x0E,  0x09,
              0x01,  0x0D,  0x05,  0x0C,  0x04,  0x05,  0x09,  0x0A,
              0x02,  0x08,  0x0D,  0x03,  0x0F,  0x01,  0x0E,  0x06,
              0x07,  0x0B,  0x00,  0x0A,  0x08,  0x0E,  0x0D,  0x09,
              0x0F,  0x03,  0x00,  0x04,  0x06,  0x01,  0x0C,  0x07,
              0x0B,  0x02,  0x05,  0x03,  0x0C,  0x04,  0x0A,  0x02,
              0x0F,  0x0D,  0x0E,  0x07,  0x00,  0x05,  0x08,  0x01,
              0x06,  0x0B,  0x09,  0x0A,  0x0C,  0x01,  0x00,  0x09,
              0x0E,  0x0D,  0x0B,  0x03,  0x07,  0x0F,  0x08,  0x05,
              0x02,  0x04,  0x06,  0x0E,  0x0A,  0x01,  0x08,  0x07,
              0x06,  0x05,  0x0C,  0x02,  0x0F,  0x00,  0x0D,  0x03,
              0x0B,  0x04,  0x09,  0x03,  0x08,  0x0E,  0x00,  0x07,
              0x09,  0x0F,  0x0C,  0x01,  0x06,  0x0D,  0x02,  0x05,
              0x0A,  0x0B,  0x04,  0x03,  0x0A,  0x0C,  0x04,  0x0D,
              0x0B,  0x09,  0x0E,  0x0F,  0x06,  0x01,  0x07,  0x02,
              0x00,  0x05,  0x08]

key_table =  [0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0x00,  0xFF,  0x01,
              0xFF,  0x02,  0x03,  0x04,  0x05,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0x06,  0x07,  0x08,
              0x09,  0x0A,  0x0B,  0x0C,  0xFF,  0x0D,  0x0E,  0xFF,
              0x0F,  0x10,  0xFF,  0x11,  0xFF,  0x12,  0xFF,  0x13,
              0xFF,  0x14,  0x15,  0x16,  0x17,  0x18,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0x06,  0x07,  0x08,
              0x09,  0x0A,  0x0B,  0x0C,  0xFF,  0x0D,  0x0E,  0xFF,
              0x0F,  0x10,  0xFF,  0x11,  0xFF,  0x12,  0xFF,  0x13,
              0xFF,  0x14,  0x15,  0x16,  0x17,  0x18,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,  0xFF,
              0xFF,  0xFF,  0xFF]

alpha_map =  [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0x00, -1,
              0x01, -1, 0x02, 0x03, 0x04, 0x05, -1, -1, -1, -1, -1,
              -1, -1, -1, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C,
              -1, 0x0D, 0x0E, -1, 0x0F, 0x10, -1, 0x11, -1, 0x12,
              -1, 0x13, -1, 0x14, 0x15, 0x16, -1, 0x17, -1, -1, -1,
              -1, -1, -1, -1, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B,
              0x0C, -1, 0x0D, 0x0E, -1, 0x0F, 0x10, -1, 0x11, -1,
              0x12, -1, 0x13, -1, 0x14, 0x15, 0x16, -1, 0x17, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
              -1, -1]

def get_num_val(char):
    char = char.upper()
    if char.isdigit():
        return ord(char) - 0x30
    return ord(char) - 0x37

def get_hex_val(v):
    v &= 0xF
    if v < 10:
        return chr(v + 0x30)
    return chr(v + 0x37)

# logical-shift-right operator:
def lsr(i,n):
    if n: i = i >> n ^ 0x80000000 >> n - 1
    return i

class alphanumex():
    def __init__(self, h, key):
        self.h = h
        self.key = key
        self.lkey = list(key)

        if len(self.key) != 26:
            raise ValueError(self.key)

        self.key_len = 26
        self.buf_len = 52

        self.val1 = 0
        self.val2 = [0] * 10
        self.prod = 0

        self.table = [0] * 52
        self.values = [0] * 4

        self.table_lookup(self.key.upper(), self.table)

        i = 52
        while i > 0:
            self.mult(4, 5, self.values, self.values, self.table[i-1])
            i -= 1

        self.decode_key_table_pass1(self.values)
        self.decode_key_table_pass2(self.values)

        self.prod = self.values[0] >> 0x0A
        self.val1 = ((self.values[0] & 0x03FF) << 0x10) |\
                    c_int32(c_uint32(self.values[1]).value >> 0x10).value
        
        self.val2[0] = c_byte((self.values[1] & 0x00FF) >> 0).value
        self.val2[1] = c_byte((self.values[1] & 0xFF00) >> 8).value

        self.val2[2:6] = unpack('<4b', pack('<l', self.values[2]))
        self.val2[6:10] = unpack('<4b', pack('<l', self.values[3]))

    def table_lookup(self, key, buf):
        b = 0x21

        for i in range(26):
            a = (b + 0x07B5) % 52
            b = (a + 0x07B5) % 52
            decode = key_table[ord(key[i])]

            buf[a] = (decode / 5)
            buf[b] = (decode % 5)

    def mult(self, rounds, mulx, bufA, bufB, decode_byte):
        posA = rounds-1
        posB = rounds-1

        i = 0
        while i < rounds:
            param1 = bufA[posA]
            param1 &= 0x00000000FFFFFFFFl
            posA -= 1

            param2 = mulx
            param2 &= 0x00000000FFFFFFFFl
            edxeax = param1 * param2

            bufB[posB] = c_int32(decode_byte + c_int32(edxeax).value).value
            decode_byte = c_int32(edxeax >> 32).value
            posB -= 1
            i += 1

    def decode_key_table_pass1(self, key_table):
        var_8 = 29

        for i in range(464, -1, -16):
            esi = (var_8 & 7) << 2
            var_4 = var_8 >> 3
            var_C = (key_table[3 - var_4] & (0x0F << esi)) >> esi

            if i < 464:
                for j in range(29, var_8, -1):
                    ecx = (j & 7) << 2
                    ebp = (key_table[0x03 - (j >> 3)] & (0x0F << ecx)) >> ecx
                    var_C = translate[ebp ^ translate[var_C + i] + i]

            var_8 -= 1
            for j in range(var_8, -1, -1):
                ecx = (j & 7) << 2
                ebp = (key_table[0x03 - (j >> 3)] & (0x0F << ecx)) >> ecx
                var_C = translate[ebp ^ translate[var_C + i] + i]

            index = 3 - var_4
            ebx = (translate[var_C + i] & 0x0F) << esi
            key_table[index] = (ebx | ~(0x0F << esi) & (key_table[index]))

    def decode_key_table_pass2(self, key_table):
        esi = 0
        for i in range(len(key_table)):
            key_table[i] = c_int32(key_table[i]).value
            
        copy = pack('<4l', *key_table)

        edi = 0
        while edi < 120:
            eax = edi & 0x1F
            ecx = esi & 0x1F

            edx = 3 - (edi >> 5)

            location = 12 - ((esi >> 5) << 2)
            ebp = unpack('<l', copy[location:location+4])[0]
            ebp = (ebp & (1 << ecx)) >> ecx

            key_table[edx] = c_int32(((ebp & 1) << eax) |\
                             (~(1 << eax) & key_table[edx])).value
            esi += 0x0B
            if esi >= 120:
                esi -= 120

            edi += 1

    def get_key_hash(self, ctoken, stoken):
        buf = pack('<2L2l10b', ctoken,
                   stoken, self.get_product(),
                   self.get_val1(),
                   *self.val2[:10])

        return unpack('5l', sha1(buf).digest())

    def get_val1(self):
        return self.val1

    def get_product(self):
        return self.prod
        
            

class alphanum():
    def __init__(self, h, key):
        self.h = h
        self.key = key
        self.lkey = list(key)
        if len(self.key) != 16:
            raise ValueError(self.key)
        
        self.alphanum()

    def alphanum(self):
        self.checksum = 0
        self.alpha_hash()

    def alpha_hash(self):
        for i in range(0, len(self.key), 2):
            r = 1
            c1 = alpha_map[ord(self.key[i])]
            n = c1 * 3
            c2 = alpha_map[ord(self.key[i + 1])]
            n = c2 + (n * 8)

            if n >= 0x100:
                n -= 0x100
                self.checksum |= (2 ** (i/2))

            n2 = n
            n2 >>= 4
            self.lkey[i] = get_hex_val(n2)
            self.lkey[i + 1] = get_hex_val(n)

            r <<= 1

        v = 3
        for i in range(16):
            c = ord(self.lkey[i])
            n = get_num_val(self.lkey[i])
            n2 = v * 2
            n ^= n2
            v += n

        v &= 0xFF
        if (v != self.checksum):
            raise ValueError(self.key)

        for i in range(15, -1, -1):
            c = ord(self.lkey[i])
            if i > 8:
                n = i - 9
            else:
                n = 0xF - (8 - i)
            n &= 0xF
            c2 = ord(self.lkey[n])

            self.lkey[i] = chr(c2)
            self.lkey[n] = chr(c)

        v2 = 0x13AC9741
        for i in range(15, -1, -1):
            c = ord(self.lkey[i].upper())
            self.lkey[i] = chr(c)
            if self.lkey[i] <= '7':
                v = v2
                c2 = c_byte(v & 0xFF).value
                c2 &= 7
                c2 ^= c
                v >>= 3
                
                self.lkey[i] = chr(c2)
                v2 = v
                
            elif self.lkey[i] < 'A':
                c2 = c_byte(i).value
                c2 &= 1
                c2 ^= c
                
                self.lkey[i] = chr(c2)
                
        self.key = ''.join(self.lkey)

    def get_product(self):
        return int(self.key[0:2], 0x10)
    def get_val1(self):
        return int(self.key[2:8], 0x10)
    def get_val2(self):
        return int(self.key[8:16], 0x10)
    def get_key_hash(self, ctoken, stoken):
        return self.h.xsha1.calc_hash_buffer(pack('6L',
                                                  ctoken,
                                                  stoken,
                                                  self.get_product(),
                                                  self.get_val1(),
                                                  0,
                                                  self.get_val2()))

class num():
    def __init__(self, h, key):
        self.h = h
        self.key = key
        self.lkey = list(key)
        if len(self.key) != 13:
            raise ValueError(self.key)
        
        self.sc()

    def sc(self):
        if self.verify():
            self.shuffle()
            self.get_final_value()
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

    def get_product(self):
        return int(self.key[0:2])
    def get_val2(self):
        return int(self.key[9:12])
    def get_val1(self):
        return int(self.key[2:9])
    def get_key_hash(self, ctoken, stoken):
        return self.h.xsha1.calc_hash_buffer(pack('6L',
                                                  ctoken,
                                                  stoken,
                                                  self.get_product(),
                                                  self.get_val1(),
                                                  0,
                                                  self.get_val2()))
