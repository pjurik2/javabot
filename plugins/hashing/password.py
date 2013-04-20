from ctypes import c_byte, c_int32, c_uint32


def insert_byte(buf, loc, b):
    the_int = loc / 4
    the_byte = loc % 4

    replace_int = buf[the_int]

    new_byte = ord(b) << (8 * the_byte)

    if the_byte == 0:
        replace_int &= 0xFFFFFF00
    elif the_byte == 1:
        replace_int &= 0xFFFF00FF
    elif the_byte == 2:
        replace_int &= 0xFF00FFFF
    elif the_byte == 3:
        replace_int &= 0x00FFFFFF

    replace_int |= new_byte

    buf[the_int] = replace_int
    

class XSha1():
    def __init__(self, h):
        self.h = h
    def calc_hash_buffer(self, hash_data):
        hash_buffer = [0x67452301,
                       0xEFCDAB89,
                       0x98BADCFE,
                       0x10325476,
                       0xC3D2E1F0] + [0] * 0x10
        i = 0
        while i < len(hash_data):
            sub_len = len(hash_data) - i

            if sub_len > 0x40:
                sub_len = 0x40

            j = 0
            while j < sub_len:
                insert_byte(hash_buffer, j + 20, hash_data[j + i])
                j += 1

            if sub_len < 0x40:
                j = sub_len
                while j < 0x40:
                    insert_byte(hash_buffer, j + 20, '\0')
                    j += 1

            #print map(hex, hash_buffer)
            self.do_hash(hash_buffer)
            #print map(hex, hash_buffer)

            i += 0x40

        return hash_buffer[:5]

    def do_hash(self, hash_buffer):
        buf = [0] * 0x50

        i = 0
        while i < 0x10:
            buf[i] = hash_buffer[i + 5]
            i += 1

        while i < 0x50:
            dw = buf[i - 0x3] ^ buf[i - 0x8] ^ buf[i - 0x10] ^ buf[i - 0xE]
            dw = c_byte(dw).value
            buf[i] = rol(1, dw)
            i += 1

        #Used to assign directly from list, until I found the value of uint32
        a = c_uint32(hash_buffer[0]).value
        b = c_uint32(hash_buffer[1]).value
        c = c_uint32(hash_buffer[2]).value
        d = c_uint32(hash_buffer[3]).value
        e = c_uint32(hash_buffer[4]).value
        p = 0

        while p < 20:
            dw = rol(a, 5) + ((~b & d) | (c & b)) + e + buf[p] + 0x5a827999
            dw = c_uint32(dw).value
            e = d
            d = c
            c = c_uint32(rol(b, 0x1E)).value
            b = a
            a = dw
            
            p += 1
            i += 1

        while p < 40:
            dw = (d ^ c ^ b) + e + rol(a, 5) + buf[p] + 0x6ED9EBA1
            dw = c_uint32(dw).value
            e = d
            d = c
            c = c_uint32(rol(b, 0x1E)).value
            b = a
            a = dw

            p += 1

        while p < 60:
            dw = ((c & b) | (d & c) | (d & b)) + e + rol(a, 5) + buf[p] - 0x70E44324
            dw = c_uint32(dw).value
            e = d
            d = c
            c = c_uint32(rol(b, 0x1E)).value
            b = a
            a = dw

            p += 1

        while p < 80:
            dw = rol(a, 5) + e + (d ^ c ^ b) + buf[p] - 0x359D3E2A
            dw = c_uint32(dw).value
            e = d
            d = c
            c = c_uint32(rol(b, 0x1E)).value
            b = a
            a = dw

            p += 1

        hash_buffer[0] = c_int32(hash_buffer[0] + a).value
        hash_buffer[1] = c_int32(hash_buffer[1] + b).value
        hash_buffer[2] = c_int32(hash_buffer[2] + c).value
        hash_buffer[3] = c_int32(hash_buffer[3] + d).value
        hash_buffer[4] = c_int32(hash_buffer[4] + e).value


def rol(num, shift):
    shift &= 0x1F
    return lshift(num, shift) | rshift(num, 32 - shift)

def lshift(val, shift):
    if shift > 32:
        return 0
    elif shift < 0:
        return 0

    return val << shift

def rshift(val, shift):
    if shift > 32:
        return 0
    elif shift < 0:
        return 0

    return val >> shift
