from socket import *
from threading import Thread, Condition
from lib import lib
"""
SR协议的接收方
"""


class SrRecver:
    def __init__(self, addr):
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.bind(addr)
        self.__window = []
        # 定义窗口中最前端的数据的seq
        self.__seq_range = []
        self.__max_seq = 255
        self.__window_size = 10
        self.__notify_recv = Condition()
        self.__recv_cache = []
        t = Thread(target=self.__recv_thread)
        t.start()

    def recv(self):
        """
        提供给上层应用调用的接口，用来接收数据。
        :return: bytes类型的数据
        """
        self.__notify_recv.acquire()
        while len(self.__recv_cache) == 0:
            self.__notify_recv.wait()
        self.__notify_recv.release()
        data = self.__recv_cache[0]
        del self.__recv_cache[0]
        return data

    def __find_index(self, seq):
        """
        查找seq是不是在窗口中，如果是的话返回其在窗口中的index，如果不在的话返回None
        :param seq: 要查找的seq
        :return:
        """
        for i in range(self.__window_size):
            if self.__seq_range[i] == seq:
                return i
        return None

    def __recv_thread(self):
        # 初始化seq_range和window为固定大小的数组
        for i in range(self.__window_size):
            self.__seq_range.append(i + 1)
            self.__window.append(None)
        while True:
            data, addr = self.__sock.recvfrom(4096)
            if lib.checksum(data) == 0xffff:
                seq = data[1]
                if seq in self.__seq_range:
                    ack = bytes([255, seq])
                    ack += (lib.checksum(ack) ^ 0xffff).to_bytes(2, 'big')
                    self.__sock.sendto(ack, addr)
                    index = self.__find_index(seq)
                    self.__window[index] = data
                    # 移动窗口，将接收到的数据移动到缓存中
                    while self.__window[0] is not None:
                        data = self.__window[0]
                        self.__min_seq = data[1] + 1
                        if self.__min_seq == self.__max_seq:
                            self.__min_seq = 0
                        data_len = int.from_bytes(data[2:6], 'big')
                        self.__recv_cache.append(self.__window[0][6:6+data_len])
                        self.__notify_recv.acquire()
                        self.__notify_recv.notify()
                        self.__notify_recv.release()
                        self.__window.pop(0)
                        self.__seq_range.pop(0)
                        self.__window.append(None)
                        # 维护可以接收的seq范围
                        seq = self.__seq_range[self.__window_size - 2] + 1
                        if seq > self.__max_seq:
                            seq = 0
                        self.__seq_range.append(seq)