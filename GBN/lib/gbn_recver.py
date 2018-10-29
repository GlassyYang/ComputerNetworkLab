from socket import *
from threading import Lock, Thread, Condition
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
        self.__eseq = 1
        self.__BUFSIZE = 255
        self.__notify_recv = Condition()
        t = Thread(target=self.__recv_thread)
        t.start()

    def recv(self):
        """
        阻塞函数，如果没有收到数据，那么函数会一直阻塞，直到从发送端接收到数据
        :return:
        """
        self.__lock.acquire()
        length = len(self.__recv_cache)
        self.__lock.release()
        self.__notify_recv.acquire()
        while length == 0:
            self.__notify_recv.wait()
            self.__lock.acquire()
            length = len(self.__recv_cache)
            self.__lock.release()
        self.__lock.acquire()
        data = self.__recv_cache.pop(0)
        self.__lock.release()
        return data

    def __recv_thread(self):
        while True:
            data, addr = self.__sock.recvfrom(1024)
            data_len = int.from_bytes(data[2:6], 'big')
            if lib.checksum(data) != 0xffff:
                print(hex(lib.checksum(data)))
                return
            seq = data[1]
            if seq == self.__eseq:
                self.__eseq = seq + 1
                if self.__eseq > self.__BUFSIZE:
                    self.__eseq = 0
                data = data[6:6+data_len]
                self.__lock.acquire()
                self.__recv_cache.append(data)
                self.__lock.release()
                self.__notify_recv.acquire()
                self.__notify_recv.notify()
                self.__notify_recv.release()
                ack = bytes([255, seq])
                self.__sock.sendto(ack, addr)
            else:
                ack = bytes([255, self.__eseq - 1])
                self.__sock.sendto(ack, addr)
