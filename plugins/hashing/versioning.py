import os
import time
from struct import unpack
hash_codes = [0xE7F4CB62, 0xF6A14FFC, 0xAA5504AF, 0x871FCDC2, 0x11BF6A18,
              0xC57292E6, 0x7927D27E, 0x2FEC8733]

files = {'D2DV': ['Game.exe',
                  'Bnclient.dll',
                  'D2Client.dll'],
         'D2XP': ['game.exe',
                  'Bnclient.dll',
                  'D2Client.dll'],
         'DRTL': ['Diablo.exe',
                  'Storm.dll',
                  'Battle.snp'],
         'DSHR': ['Diablo_s.exe',
                  'Storm.dll',
                  'Battle.snp'],
         'JSTR': ['StarCraftJ.exe',
                  'storm.dll',
                  'battle.snp'],
         'SEXP': ['StarCraft.exe',
                  'storm.dll',
                  'battle.snp']
         'STAR': ['StarCraft.exe',
                  'storm.dll',
                  'battle.snp'],
         'W2BN': ['Warcraft II BNE.exe',
                  'storm.dll',
                  'battle.snp'],
         'W3XP': ['War3.exe',
                  'Game.dll',
                  'Storm.dll'],
         'WAR3': ['War3.exe',
                  'Game.dll',
                  'Storm.dll']}

def get_files(prod):
    prod = prod.upper() + os.sep
    get = files[prod[:-1]]

    return [prod + get[0],
            prod + get[1],
            prod + get[2]]

def get_mpq_num(fname):
    build = fname[:-4]
    x = -1
    while build[x].isdigit():
        x -= 1
    return int(build[x+1:])

def check_revision(version_string, prod, mpq):
    tok = version_string.split(' ')
    del tok[3] #num = tok.pop(3)
    for x in range(len(tok)):
        tok[x] = tok[x].split('=') #Everything's an assignment
        if tok[x][1].isdigit(): #If it's a number, make it an integer
            tok[x][1] = int(tok[x][1])
            
    v = dict(tok[:3]) #Dictionary for greater flexibility
    tok = tok[3:]

    fnames = get_files(prod)
    mpq_num = get_mpq_num(mpq)
    v['A'] ^= hash_codes[mpq_num]

    for fname in fnames:
        f = open(fname, 'rb')
        data = f.read()
        f.close()

        for j in range(0, len(data), 4):
            s = unpack('<L', data[j:j+4])[0]
            for t in tok:
                v[t[0]] = eval(t[1], v)

    checksum = v['C']

def get_info(exe):
    stat = os.stat(exe)
    last = time.localtime(stat.st_mtime)
    #02/03/91 04:25:54 3496834983
    return time.strftime('%m/%d/%y %H:%M:%S ', last) + (' %d' % stat.st_size)


def get_version(
