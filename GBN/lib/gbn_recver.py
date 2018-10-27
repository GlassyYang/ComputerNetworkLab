from socket import *
from threading import Lock
from . import lib
from time import sleep

class GbnRecver:
    """
    GBN协议的接收方
    """
    def __init__(self, addr):
        self.__recv_cache = []
        self.__lock = Lock()
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.bind(addr)

    def recv(self):
        data = []
        self.__lock.acquire()
        while len(self.__recv_cache) == 0:
            sleep(1)
        while len(self.__recv_cache) > 0:
            data.append(self.__recv_cache.pop(0))
        self.__lock.release()
        return data

    def __recv(self):
        while True:
            data, addr = self.__sock.recvfrom(1024)
            data_len = int.from_bytes(data[2:6], 'big')
            if lib.checksum(data) != 0xffff:
                return
            seq = data[1]
            if seq == self.__recv_cache[len(self.__recv_cache)] + 1:
                data = data[5:5+data_len]
                self.__lock.acquire()
                self.__recv_cache.append(data)
                self.__lock.release()
                ack = bytes([255, seq])
                self.__sock.send(ack)
