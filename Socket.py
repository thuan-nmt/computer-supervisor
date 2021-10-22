from socket import *
import pickle

# socket wrapper
class Socket():
    def __init__(self, socket = None, DELIM=b'\x00'):
        self.socket = socket;
        self.DELIM = DELIM
        self.buff = b''

    # pure send & recv
    def send(self, data):
        return self.socket.send(data)

    def recv(self, buff_size):
        return self.socket.recv(buff_size)

    # advanced recv
    def recv_until(self, DELIM=None):
        if DELIM == None:
            DELIM = self.DELIM

        while True:
            pos = self.buff.find(DELIM)
            if (pos != -1):
                val = self.buff[:pos]
                self.buff = self.buff[pos + len(DELIM):]

                return val
            else:
                self.buff += self.socket.recv(1024)

    def recv_size(self, size):
        while True:
            sizeBuff = len(self.buff)
            if (sizeBuff >= size):
                val = self.buff[:size]
                self.buff = self.buff[size:]

                return val
            else:
                self.buff += self.socket.recv(1024)

    # send & recv string
    def send_str(self, string, DELIM=None):
        if DELIM == None:
            DELIM = self.DELIM
        return self.send(str(string).encode() + DELIM)

    def recv_str(self, DELIM=None):
        if DELIM == None:
            DELIM = self.DELIM
        return self.recv_until().decode()

    # send & recv object
    def send_obj(self, object):
        obj = pickle.dumps(object)
        obj_size = len(obj)

        self.send_str(obj_size)
        return self.send(obj)

    def recv_obj(self):
        obj_size = int(self.recv_str())
        obj = self.recv_size(obj_size)

        return pickle.loads(obj)

    # send & recv state
    def send_state(self, state):
        self.send_str(state)

    def recv_state(self):
        return eval(self.recv_str())