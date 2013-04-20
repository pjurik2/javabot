from hashlib import sha1
from struct import unpack
from ctypes import c_byte
import random

def str_to_big_num(string):
    #This is probably inefficient!
    return int(''.join(reversed(string)).encode('hex'), 16)

def big_num_to_str(num, pad=0):
    #This is probably inefficient!
    ret = hex(num)[2:].rstrip('L')
    ret = ret.ljust(len(ret) + (len(ret) % 2), '0')
    ret = ''.join(reversed(ret.decode('hex')))
    return ret.ljust(pad, '\0')

def rev_hex(string):
    return ''.join(reversed(string.decode('hex'))).encode('hex')

class SRP():
    def __init__(self, username, password):
        self.N = 0xF8FF1A8B619918032186B68CA092B5557E976C78C73212D91216F6658523C787
        self.g = 47L

        self.username = username.upper()
        self.password = password.upper()

        random.seed()
        self.a = random.getrandbits(256)
        self.I = 'l\x0e\x97\xed\n\xf9k\xab\xb1X\x89\xeb\x8b\xba%\xa4\xf0\x8c\x01\xf8'

    def get_x(self, salt):
        mdx = sha1()
        mdx.update(self.username)
        mdx.update(':')
        mdx.update(self.password)
        ret = mdx.digest()
        
        mdx = sha1()
        mdx.update(salt)
        mdx.update(ret)
        ret = mdx.digest()

        self.x = str_to_big_num(ret)
        return self.x

    def get_v(self, salt):
        self.v = pow(self.g, self.get_x(salt), self.N)
        return self.v

    def get_A(self):
        self.A = pow(self.g, self.a, self.N)
        return self.A

    def get_u(self, B):
        self.u = unpack('>L', sha1(B).digest()[:4])[0]
        return self.u

    def get_S(self, s, B):
        S_base = ((self.N + B) - self.v) % self.N
        S_exp = self.a + (self.u * self.get_x(s))
        self.S = pow(S_base, S_exp, self.N)
        return self.S

    def get_K(self, S):
        K = []
        hbuf1 = []
        hbuf2 = []

        for i in range(0, len(S), 2):
            hbuf1.append(S[i])
            hbuf2.append(S[i + 1])

        hout1 = sha1(''.join(hbuf1)).digest()
        hout2 = sha1(''.join(hbuf2)).digest()

        for i in range(len(hout1)):
            K.append(hout1[i])
            K.append(hout2[i])

        self.K = ''.join(K)
        return self.K

    def get_M1(self, s, B):
        total_Ctx = sha1()
        total_Ctx.update(self.I)
        total_Ctx.update(sha1(self.username).digest())
        total_Ctx.update(s)
        total_Ctx.update(big_num_to_str(self.A))
        total_Ctx.update(B)
        total_Ctx.update(self.K)

        self.M1 = total_Ctx.digest()
        return self.M1

    def get_M2(self, s, B):
        A = self.get_A()
        M = self.get_M1(s, B)
        K = self.get_K(self.get_S(s, B))

        M2 = sha1()
        M2.update(A)
        M2.update(M)
        M2.update(K)

        self.M2 = M2.digest()
        return self.M2


if __name__ == '__main__':
    salt = '\0' * 32
    s_num = str_to_big_num(salt)
    srp = SRP('username', 'password')
    print "v: " + hex(srp.get_v(salt))
    print "A: " + hex(srp.get_A())
    print "u: " + hex(srp.get_u(salt))
    print "S: " + hex(srp.get_S(salt, s_num))
    print "K: " + srp.get_K(big_num_to_str(srp.S)).encode('hex')
    print "M1: " + srp.get_M1(salt, salt).encode('hex')
