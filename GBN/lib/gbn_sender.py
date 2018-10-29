from socket import *
from threading import Condition, Lock, Thread
from . import lib
# from time import sleep
"""
GBN发送方的实现
"""


class GbnSender:
    def __init__(self, addr):
        # 定义seq最大值为255
        self.__BUFSIZE = 255
        # test = bytes((0, 0)) + (4).to_bytes(4, 'big') + b'test'
        # test += (lib.checksum(test) ^ 0xffff).to_bytes(2, 'big')
        self.__send_cache = []
        self.__seq = 0
        self.__pkg_sign = 255
        self.__ack_sign = 0
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.connect(addr)
        self.__window_size = 20
        self.__lock = Lock()
        self.__notify_sender = Condition()
        self.__notify_recver = Condition()
        return

    def initialize(self):
        t = Thread(target=self.__send_thread, daemon=True)
        t.start()
        self.__notify_sender.acquire()
        self.__notify_sender.release()
        t = Thread(target=self.__ack_thread, daemon=True)
        t.start()
        self.__notify_recver.acquire()
        self.__notify_recver.release()

    def __get_seq(self):
        self.__seq += 1
        if self.__seq > self.__BUFSIZE:
            self.__seq = 0
        return self.__seq

    def __mk_pkt(self, data):
        temp = bytes([128, self.__get_seq()]) + len(data).to_bytes(4, byteorder='big') + data
        if len(temp) % 2 != 0:
            temp += bytes([0])
        return temp + (lib.checksum(temp) ^ 0xffff).to_bytes(2, 'big')

    def send(self, data):
        """
        使用GBN协议发送数据，这个方法是上层应用的调用，该方法不会发送数据，而是将数据打包放入发送缓存中，
        并提醒发送线程
        发送数据 。
        :param data: 要发送的数据
        :return: None
        """
        self.__notify_sender.acquire()
        self.__send_cache.append(self.__mk_pkt(data))
        self.__notify_sender.notify()
        self.__notify_sender.release()
        return

    def __send_thread(self):
        """
        真正的发送数据的方法，当实例化该类的对象的时候，该方法作为独立的守护线程在后台运行，将发送缓存中的数据（如果
        有的话）发送给接收方，如果缓存中没有数据则进入挂起状态。刚开始的时候是进入挂起状态的。
        :return: None
        """
        while True:
            # sleep(4)
            self.__notify_sender.acquire()
            # 当发送缓存中没有数据的时候，线程进入挂起状态。
            while len(self.__send_cache) == 0:
                self.__notify_sender.wait()
            self.__notify_sender.release()
            while len(self.__send_cache) > 0:
                self.__lock.acquire()
                for i in range(min(self.__window_size, len(self.__send_cache))):
                    self.__sock.send(self.__send_cache[i])
                self.__lock.release()
                self.__notify_recver.acquire()
                self.__notify_recver.notify()
                flag = self.__notify_recver.wait(4)
                while flag and len(self.__send_cache) > 0:
                    self.__notify_recver.notify()
                    flag = self.__notify_recver.wait(10)
                    print(flag)
                self.__notify_recver.release()

    def __ack_thread(self):
        """
        当对方关闭连接以至于无法向对方发送还没有发送的数据包的时候，会抛出ConnectionResetError异常
        累积确认
        :return:无
        """
        self.__notify_recver.acquire()
        while True:
            while len(self.__send_cache) == 0:
                self.__notify_recver.wait()
            self.__notify_recver.release()
            while len(self.__send_cache) > 0:
                data = self.__sock.recv(1024)
                assert len(data) > 0
                seq = data[1]
                print(seq)
                while len(self.__send_cache) > 0 and self.__send_cache[0][1] <= seq:
                    self.__lock.acquire()
                    self.__send_cache.pop(0)
                    self.__lock.release()
                    self.__notify_recver.acquire()
                    self.__notify_recver.notify()
                    self.__notify_recver.wait()
                    self.__notify_recver.release()
