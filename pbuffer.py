from struct import pack
from socket import socket
import threading

def make_word(word):
    return pack('<H', word)

def debug_output(data):
    out = ""
    for x in range(len(data)):
        byte = hex(ord(data[x]))[2:].upper()
        if len(byte) == 1:
            byte = "0"+byte
        out = out+" "+byte
        
    return out[1:]

class PacketBuffer():
    def __init__(self):
        self.clear()
    
    def insert_byte(self, byte):
        self.data = self.data + chr(byte)

    def insert_string(self, string):
        self.data = self.data + string + chr(0)

    def insert_long(self, dword):
        self.data = self.data + pack('<L', dword)

    def insert_short(self, word):
        self.data = self.data + make_word(word)

    def insert_raw(self, raw):
        self.data = self.data + raw

    def clear(self):
        self.data = ''

class conn (PacketBuffer):
    def __init__(self):
        self.bot = None
        self.connected = False

    def close(self):
        try:
            if self.bot != None:
                self.bot.del_socket(self.socket)

            self.socket.close()
            del self.socket
        except AttributeError:
            pass #It doesn't exist.

    def connect(self, server, port):
        self.server = server
        self.port = port

        self.reset()
        
        self.socket.connect((self.server, self.port))
        self.connected = True

        return True

    def send(self):
        self.socket.sendall(self.data)
        self.clear()

    def recv(self, recvlen=4):
        try:
            return self.socket.recv(recvlen)
        except:
            return None #Socket died

    def reset(self):
        self.clear()
        self.close()
        
        self.connected = False
        self.socket = socket()

    def need_setting(self, missing, sendfunc): #ahhhhright
        self.clear()
        self.bot.need_setting(missing, sendfunc)

    def packet_debug(self, packet, length, data):
        print "Packet: "+hex(packet)
        print "Length: "+str(length)+"/"+hex(length)
        print "Data: "+debug_output(data)

class new_socket(threading.Thread):
    def __init__(self, connected, recv):
        threading.Thread.__init__(self)

    def run(self):
        try:        
            self.connect(server, 6112)
            self.bot.add_socket(self.socket, self.BNCSrecv)
        except socket.error, (errno, descr):
            self.bot.addchat('error', 'Error #'+str(errno)+': '+descr)
        except socket.herror, (errno, descr):
            self.bot.addchat('error', 'Address-related error #'+str(errno)+': '+descr)
        except socket.gaierror, (errno, descr):
            self.bot.addchat('error', 'Failed to get address, got error #'+\
                             str(errno)+': '+descr)
        except KeyError, missing:
            self.bot.need_setting(missing, self.BNCSconnect)
        except:
            self.bot.addchat('error', 'Connection attempt failed for an unknown reason')
        else:
            self.bot.addchat('success', 'Connected to Battle.net')
            self.send_0x50()
            return
        
