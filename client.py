import socket
import threading
import cv2
import struct
import pickle
import asyncio
import pyaudio

class Client():
    def __init__(self, ip='127.0.0.1', sport=5000, tport=6000, vport=7000, aport=8000):
        self.name = None
        self.opname = None
        self.ip = ip
        self.sport = sport
        self.tport = tport
        self.vport = vport
        self.aport = aport
        self.FORMAT = 'utf-8'
        self.DISCONNECT_MSG = 'Killed'
        self.VIDEO_MSG = 'VideoC'
        self.SEARCH_MSG = 'SReady'
        self.AUDIO_MSG = 'Audioc'
        self.NUM_MSG = 'NumMsg'
        self.FIRSTNUM = 'FRSNUM'
        self.CONNECTED = 'conect'
        self.YOURTURN = 'goahad'
        self.RESMSG = 'resmsg'
        self.STARTMSG = 'startm'
        self.WINMSG = 'youwon'
        self.LOSSMSG = 'youlos'
        self.lock = threading.Lock()

    def connect(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.ip, self.sport))
        while True:
            token = self.server.recv(6)
            if not token:
                continue
            self.token = token.decode(self.FORMAT)
            self.tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rvsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.svsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tsock.connect((self.ip, self.tport))
            self.rvsock.connect((self.ip, self.vport+500))
            self.svsock.connect((self.ip, self.vport))
            self.rasock.connect((self.ip, self.aport+500))
            self.sasock.connect((self.ip, self.aport))
            self.tsock.send(token)
            self.rvsock.send(token)
            self.svsock.send(token)
            self.rasock.send(token)
            self.sasock.send(token)
            self.saudio = True
            self.CHUNK = 1024
            self.AFORMAT = pyaudio.paInt16
            self.CHANNELS = 2
            self.RATE = 44100
            audio=pyaudio.PyAudio()
            self.stream=audio.open(format=self.AFORMAT,channels=self.CHANNELS, rate=self.RATE, input=True, output = True,frames_per_buffer=self.CHUNK)
            self.name = input('Enter your name: ')
            msg = self.SEARCH_MSG.encode(self.FORMAT)
            msg += struct.pack('i', len(self.name)) + self.name.encode(self.FORMAT)
            self.server.sendall(msg)
            while True:
                res = self.server.recv(6).decode(self.FORMAT)
                if res == self.CONNECTED:
                    print(res)
                    name_lenght = int(struct.unpack('i', self.server.recv(4))[0])
                    self.opname = self.server.recv(name_lenght).decode(self.FORMAT)
                    self.play()
                    break
            break
        

    def play(self):
        t1 = threading.Thread(target=self.start_game)
        t2 = threading.Thread(target=self.send_video)
        t3 = threading.Thread(target=self.get_video)
        t4 = threading.Thread(target=self.get_audio)
        t5 =threading.Thread(target=self.send_audio)
        t1.start()
        t2.start()
        t3.start()
        t4.start()
        t5.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        t5.join()
                


    def start_game(self):
        num = self.input_number()
        self.tsock.send(self.FIRSTNUM.encode(self.FORMAT)+num.encode(self.FORMAT))
        while True:
            com = self.tsock.recv(6).decode(self.FORMAT)
            if com == self.YOURTURN:
                print('Guess your oponent number')
                guess_num = self.input_number()
                self.tsock.sendall(self.NUM_MSG.encode(self.FORMAT) + guess_num.encode(self.FORMAT))
            elif com == self.RESMSG:
                res = self.tsock.recv(2).decode(self.FORMAT)
                print(f'{res[0]} maches {res[1]} in place')
            elif com == self.WINMSG:
                print('YOU WON!!!!')        
                cv2.destroyAllWindows()
                break
            elif com == self.LOSSMSG:
                print('YOU LOSS!!!')
                cv2.destroyAllWindows()
                break

    def input_number(self):
        a = {'1', '2', '3', '4', '5', '6', '7', '8', '9'}
        while True:
            num = input('Enter your number: ')
            if len(set(num).intersection(a)) == 4 and len(num) ==4:
                return num

    def get_video(self):
        connected = True
        while True:
            pframe = b''
            while len(pframe) < 921765:
                pframe += self.rvsock.recv(921765 - len(pframe))
            if not connected: break
            frame = pickle.loads(pframe)
            cv2.imshow('Oponent camera: '+ self.opname, frame)
            key = cv2.waitKey(1) & 0xFF
            if key  == ord('q'):
                break

    def send_video(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while cap.isOpened():
            rat, frame = cap.read()
            if not rat: continue
            pframe = pickle.dumps(frame) 
            self.svsock.sendall(pframe)
            cv2.imshow('My camera: ' + self.name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key  == ord('q'):
                break
        
    def get_audio(self):
        
        connected = True
        while True:
            data = b''
            while len(data) < 16384:
                data += self.rasock.recv(16384 - len(data))
            if not connected: break
            self.stream.write(data)

    def send_audio(self):
        while True:
            data = self.stream.read(self.CHUNK * 4)
            self.sasock.sendall(data)
        

if __name__ == '__main__':
    cl = Client(ip='127.0.0.1')
    cl.connect()



