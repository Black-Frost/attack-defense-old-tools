import types
import struct
import threading
import select
import re
import os

from time import time
from base64 import b64decode
from socket import *

from flagcheck import IsValidInput, IsValidOutput
from origin_mapping import mapping_origin_dest

SO_ORIGINAL_DST = 80
IP_TRANSPARENT = 19

PAYLOAD = []
PAYLOAD_LOCK = threading.Lock()


class Payload():
    __slots__ = ['time', 'chall', 'pid', 'connaddr', 'source', 'data', 'isFlag']
    def __init__(self, chall, pid, connaddr, source, data, isFlag):
        self.time = time()
        self.chall = chall
        self.pid = pid
        self.connaddr = connaddr
        self.source = source
        self.data = data
        self.isFlag = 'T' if isFlag else 'F'
        # It would be better if we have log for every request,
        # but it will hit `Too many open files`, change the maximum files to open may got forgoten
        # So we just write requests to 1 file for each challenge, greping with pid works
        with open('./log/proxylog-{}.txt'.format(chall, pid), 'a+') as f:
            f.write(str(self) + '\n')

    def __repr__(self):
        return '{:.3f}: [{}] [{:6d}] [{:7s}] [{},{}] [{}]'.format(
            self.time, self.isFlag, self.pid, self.chall, self.connaddr, self.source, self.data
        )

    def filter(self, challname, **kwargs):
        if self.chall != challname:
            return False
        time = kwargs.get('time', 0)
        if time != 0 and self.time < time:
            return False

        # TODO: Remodel this filtering
        pid = kwargs.get('pid', -1)
        isFlag = kwargs.get('isFlag', '')
        if pid == -1 and isFlag == '':
            return True
        if self.pid == pid:
            return True
        if self.source == "CHALL" and isFlag == self.isFlag:
            if pid == -1 or self.pid == pid:
                return True
        return False

class Client(threading.Thread):
    __slots__ = ['conn', 'connaddr', 'origin_dest', 'origin_dest', 'chall']
    def __init__(self, conn, connaddr, pid):
        threading.Thread.__init__(self)
        self.conn = conn
        self.connaddr = connaddr
        self.pid = pid

        sockaddr_in = conn.getsockopt(SOL_IP, SO_ORIGINAL_DST, 16)
        (proto, port, a, b, c, d) = struct.unpack('!HHBBBB', sockaddr_in[:8])
        self.origin_dest = ('{}.{}.{}.{}'.format(a,b,c,d), port)
        self.forward_sock = socket(AF_INET, SOCK_STREAM)
        chall_dest, chall = mapping_origin_dest(self.origin_dest)
        self.chall = chall
        try:
            self.forward_sock.connect(chall_dest)
        except:
            self.forward_sock = None

    def run(self):
        # TODO: Make a class of Proxy that controls connections for a challenge
        #       - Capture only what neccessary
        #       - Automatically forwards traffic to another team but keeps connection
        #       - Input/Output filtering handler for each challenge, @Override able
        #       - Delete good request
        #       - AI detection of BOT
        global PAYLOAD_LOCK
        global PAYLOAD
        if self.forward_sock is None:
            print("Connection to {}/{} is not well established".format(self.chall_dest, self.chall))
            self.conn.close()
            return
        print("Connection from : ", self.connaddr)
        print("Connection to   : ", self.origin_dest)
        while True:
            r,w,e = select.select([self.forward_sock],[],[],0)
            for rs in r:
                data = rs.recv(4096)
                if not data:
                    break
                if not IsValidOutput(data, self.chall):
                    # TODO: What to do when output is not valid?
                    # This should be handle by Challenge class which will override this behavior
                    pass
                self.conn.send(data)
                if self.chall != 'others':
                    print("response [{}] [{}] [{}] :: ".format(isFlag, self.chall, self.pid), data)
                    PAYLOAD_LOCK.acquire()
                    PAYLOAD += [Payload(self.chall, self.pid, self.connaddr, "CHALL", data, isFlag)]
                    PAYLOAD_LOCK.release()
            r,w,e = select.select([self.conn],[],[],0)
            for rs in r:
                data = rs.recv(4096)
                if not data:
                    break
                if not IsValidInput(data, self.chall):
                    # TODO: What to do when input is not valid?
                    # This should be handle by Challenge class which will override this behavior
                self.forward_sock.send(data)
                if self.chall != 'others':
                    print("client input [{}] [{}] :: ".format(self.chall, self.pid), data)
                    PAYLOAD_LOCK.acquire()
                    PAYLOAD += [Payload(self.chall, self.pid, self.connaddr, "CLIENT", data, None)]
                    PAYLOAD_LOCK.release()
        print("Client at ", clientAddress , " disconnected...")
        self.forward_sock.close()
        self.conn.close()


def proxyRun():
    # FIXME: Handle edge case `Address already in used` when closing proxy
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_IP, IP_TRANSPARENT, 1)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 4444))
    s.listen()
    try:
        pid = 0
        while True:
            conn, connaddr = s.accept()
            thread = Client(conn, connaddr, pid)
            thread.start()
            pid += 1
    except KeyboardInterrupt:
        s.close()


def menuPrint():
    import importlib
    import origin_mapping
    import flagcheck
    while True:
        print('1. Reload Chall Mapping')
        print('2. Reload Flag rules')
        try:
            i = int(input('>>> '))
        except:
            continue
        # FIXME: Reloading seems not working
        if i == 1:
            importlib.reload(origin_mapping)
            from origin_mapping import mapping_origin_dest
        if i == 2:
            importlib.reload(flagcheck)
            from flagcheck import checkflag


def webserverRun():
    # TODO: Create better api route
    from flask import Flask, jsonify, request
    app = Flask(__name__)

    @app.route('/check')
    def check():
        return jsonify(success=True)

    @app.route('/some_random_route/<string:challname>', methods=['GET'])
    def haha(challname):
        global PAYLOAD
        time = int(request.args.get('time', 0))
        pid = int(request.args.get('pid', -1))
        isFlag = int(request.args.get('flag', -1))
        result = list(map(str, filter(lambda x: x.filter(challname, time=time, pid=pid, isFlag=isFlag),PAYLOAD)))
        return jsonify(result=result)

    app.run(host="0.0.0.0", port=6789, debug=False)


if not os.path.exists('./log'):
    os.makedirs('./log')


# TODO: Because proxy prevent traffic other than port 22 and challenge port, we will forward the
# web server to another server online and query back the result from that
# using ngrok is good but try not to make things difficult to handle

# TODO: Handle closing of proxy

proxy = threading.Thread(target=proxyRun)
menu = threading.Thread(target=menuPrint)
proxy.start()
menu.start()
webserverRun()
proxy.join()
menu.join()
