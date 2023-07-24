from os import name

from game import Client, Game
import socket
import cv2
import threading
import pickle
import struct
import time
from queue import Queue
import random
import sys
import config
import hashlib
# from setup_db import TivDB

class Server():
    def __init__(self, ip='127.0.0.1', sport=5000, tport=6000, vport=7000, aport=8000):
        self.ip = ip
        self.sport = sport
        self.tport = tport
        self.vport = vport
        self.aport = aport
        self.FORMAT = 'utf-8'
        self.dicon_m = 'killed'
        self.SEARCH_MSG = 'SReady'
        self.LOGOUT = 'logout'
        self.NUM_MSG = 'NumMsg'
        self.FIRSTNUM = 'FRSNUM'
        self.LOGMSG = 'logmsg'
        self.VIDEO_MSG = 'VideoC'
        self.CONNECTED = 'conect'
        self.YOURTURN = 'goahad'
        self.RESMSG = 'resmsg'
        self.WINMSG = 'youwon'
        self.LOSSMSG = 'youlos'
        self.CONFMSG = 'confir'
        self.NOTCONF = 'notcon'
        self.chmail = 'chmail'
        self.chname = 'chname'
        self.REGMSG = 'regmsg'
        self.lock = threading.Lock()
        self.active = False
        self.clients = {}
        # self.db = TivDB()
        
    
    def con_server(self):
        self.sersock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.svsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sersock.bind((self.ip, self.sport))
        self.tsock.bind((self.ip, self.tport))
        self.rvsock.bind((self.ip, self.vport))
        self.svsock.bind((self.ip, self.vport+500))
        self.rasock.bind((self.ip, self.aport))
        self.sasock.bind((self.ip, self.aport+500))
        # self.db.connect()

    def start_server(self):
        self.sersock.listen()
        self.active = True
        print('Server started:')
        while True:
            conn, addr = self.sersock.accept()
            token = self.__get_token()
            cl = Client()
            cl.sconn = conn
            self.clients[token] = cl
            conn.send(token.encode(self.FORMAT))
            thread = threading.Thread(name=token, target=self.handle_client, args=(conn, addr, token))
            thread.daemon = True
            thread.start()
            print(f'New connection {addr}')

    def text_server(self):
        self.tsock.listen()
        print('Text Server started:')
        while True:
            conn, addr = self.tsock.accept()
            thread = threading.Thread(target=self.handle_text, args=(conn, addr))
            thread.start()

    def video_recv(self):
        self.rvsock.listen()
        print('Server video recv:')
        while True:
            conn, addr = self.rvsock.accept()
            thread = threading.Thread(target=self.handle_rvideo, args=(conn, addr))
            thread.start()
    
    def video_send(self):
        self.svsock.listen()
        print('Server video sending:')
        while True:
            conn, addr = self.svsock.accept()
            thread = threading.Thread(target=self.handle_svideo, args=(conn, addr))
            thread.start()
    


    def audio_recv(self):
        self.rasock.listen()
        print('Server audio recv:')
        while True:
            conn, addr = self.rasock.accept()
            thread = threading.Thread(target=self.handle_raudio, args=(conn, addr))
            thread.start()
    
    def audio_send(self):
        self.sasock.listen()
        print('Server audio sending:')
        while True:
            conn, addr = self.sasock.accept()
            thread = threading.Thread(target=self.handle_saudio, args=(conn, addr))
            thread.start()


    
    def handle_client(self, conn, addr, token):
        while True:
            try:
                com = conn.recv(6).decode(self.FORMAT)
            except ConnectionError:
                conn.close()
                break
            if com == self.SEARCH_MSG:
                while True:
                    size = int(struct.unpack('i', conn.recv(4))[0])
                    if size:
                        while True:
                            name = conn.recv(size).decode(self.FORMAT)
                            self.clients[token].name = name
                            self.clients[token].issearching = True
                            break
                        break
            elif com == self.REGMSG:
                while True:
                    size = int(struct.unpack('i', conn.recv(4))[0])
                    if size:
                        name = conn.recv(size).decode(self.FORMAT)
                        res = self.db.validate_name(name)
                        if res:
                            conn.send(self.CONFMSG.encode(self.FORMAT))
                            break
                        else:
                            conn.send(self.NOTCONF.encode(self.FORMAT))
            
                while True:
                    size = int(struct.unpack('i', conn.recv(4))[0])
                    if size:
                        email = conn.recv(size).decode(self.FORMAT)
                        res = self.db.validate_email(email)
                        if res:
                            conn.send(self.CONFMSG.encode(self.FORMAT))
                            break
                        else:
                            conn.send(self.NOTCONF.encode(self.FORMAT))
                while True:
                    size = int(struct.unpack('i', conn.recv(4))[0])
                    if size:
                        password = conn.recv(size).decode(self.FORMAT)
                        password = self.set_password(password)

                        break
                self.db.insert_user(name, email, password)

            elif com == self.LOGMSG:
                email = conn.recv(int(struct.unpack('i', conn.recv(4))[0])).decode(self.FORMAT)
                password = conn.recv(int(struct.unpack('i', conn.recv(4))[0])).decode(self.FORMAT)
                password = self.set_password(password)
                res = self.db.check_log(email, password)
                if res:
                    name, id = res
                    conn.send(self.CONFMSG.encode(self.FORMAT) + struct.pack('i', len(name)) + name.encode(self.FORMAT))
                    self.clients[token].name = name
                    self.clients[token].id = id
                    self.clients[token].isauthorised = True
                    print(self.clients[token])
                else:
                    conn.send(self.NOTCONF.encode(self.FORMAT))
            
            elif com == self.LOGOUT:
                self.clients[token].name = None
                self.clients[token].id = None
                self.clients[token].isauthorised = False

    def handle_text(self, conn, addr):
        while True:
            try:
                token = conn.recv(6).decode(self.FORMAT)
            except ConnectionError:
                conn.close()
                break
            if token.isnumeric():
                self.clients[token].tconn = conn
                break
    
    def handle_rvideo(self, conn, addr):
        while True:
            try:
                token = conn.recv(6).decode(self.FORMAT)
            except ConnectionError:
                conn.close()
                break
            if token.isnumeric():
                self.clients[token].rvconn = conn
                break
    
    def handle_svideo(self, conn, addr):
        while True:
            try:
                token = conn.recv(6).decode(self.FORMAT)
            except ConnectionError:
                conn.close()
                break
            if token.isnumeric():
                self.clients[token].svconn = conn
                break
    
    def handle_raudio(self, conn, addr):
        while True:
            try:
                token = conn.recv(6).decode(self.FORMAT)
            except ConnectionError:
                
                break
            if token.isnumeric():
                self.clients[token].raconn = conn
                break
    
    def handle_saudio(self, conn, addr):
        while True:
            try:
                token = conn.recv(6).decode(self.FORMAT)
            except ConnectionError:
                
                break
            if token.isnumeric():
                self.clients[token].saconn = conn
                break


    def search_pair(self):
        while True:
            dict = self.clients.copy()
            ready = [token for token, cl in dict.items() if cl.tconn != None and cl.svconn != None and cl.rvconn != None and cl.issearching == True]
            if len(ready) >= 2:
                l1, l2 = random.sample(ready, k=2)
                self.clients[l1].issearching = False
                self.clients[l2].issearching = False
                cl1 = self.clients[l1]
                cl2 = self.clients[l2]
                cl1.sconn.sendall(self.CONNECTED.encode(self.FORMAT) + struct.pack('i', len(cl2.name)) + cl2.name.encode(self.FORMAT))
                cl2.sconn.sendall(self.CONNECTED.encode(self.FORMAT) + struct.pack('i', len(cl1.name)) + cl1.name.encode(self.FORMAT))
                print(l1, l2)
                game = Game(cl1, cl2)
                print('----------------------------')
                t1= threading.Thread(target=game.start_game)
                t2 = threading.Thread(target=game.c1video_handle)
                t3 = threading.Thread(target=game.c2video_handle)
                t4 = threading.Thread(target=game.c1audio_handle)
                t5 = threading.Thread(target=game.c2audio_handle)
                t1.start()
                t2.start()
                t3.start()
                t4.start()
                t5.start()

    def __get_token(self):
        return str(random.randint(100000,999999))
    
    def set_password(self, password):
        return hashlib.pbkdf2_hmac(
            'sha256', bytes(password, 'utf8'),
            config.SALT, 150000).hex()

Ser = Server()
Ser.con_server()
t1 = threading.Thread(target=Ser.start_server, daemon=True)
t2 = threading.Thread(target=Ser.text_server, daemon=True)
t3 = threading.Thread(target=Ser.video_recv, daemon=True)
t4 = threading.Thread(target=Ser.video_send, daemon=True)
# t2 = threading.Thread(target=Ser.stop_server)
t5 = threading.Thread(target=Ser.search_pair, daemon=True)
t6 = threading.Thread(target=Ser.audio_recv, daemon=True)
t7 = threading.Thread(target=Ser.audio_send, daemon=True)
t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()
t7.start()
t1.join()
t2.join()
t3.join()
t4.join()
t5.join()
t6.join()
t7.join()