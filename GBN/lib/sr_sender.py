from socket import *
from threading import Lock, Condition, Thread, Timer
from lib import lib


class SrSender:
    def __init__(self, addr):
        self.__sock = socket(AF_INET, SOCK_DGRAM)
        self.__sock.connect(addr)
        self.__cache = []
        self.__timer = []
        self.__timer_lock = []
        self.__wait_send = []
        self.__win_size = 10
        self.__interval = 4.
        self.__notify_sender = Condition()
        # 用于控制对缓存的访问
        self.__lock = Lock()
        self.__seq = 0
        self.__min_seq = 0
        self.__SEQ_SIZE = 255
        t = Thread(target=self.__ack_thread)
        t.start()
        t = Thread(target=self.__send_thread)
        t.start()

    def __get_seq(self):
        self.__seq += 1
        if self.__seq == self.__SEQ_SIZE:
            self.__seq = 0
        return self.__seq

    def __find_index(self, seq):
        """
        通过seq查找index,在查找过程中会获得缓存的锁。
        :param seq: seq
        :return: 如果查找到了返回True，否则返回False
        """
        self.__lock.acquire()
        for i in range(len(self.__cache)):
            if self.__cache[i][1] == seq:
                self.__lock.release()
                return i
        self.__lock.release()
        return None

    def __send_thread(self):
        """
        包发送线程，被发送方法send唤醒之后发送待发送缓存中数据（不一定是所有），并将数据发乳到窗口中。
        :return:
        """
        self.__notify_sender.acquire()
        while True:
            while len(self.__wait_send) == 0:
                self.__notify_sender.wait()
            num_send = min(len(self.__wait_send), self.__win_size - len(self.__cache))
            for i in range(num_send):
                # 构造分组
                seq = self.__get_seq()
                data = bytes([0, seq]) + len(self.__wait_send[i]).to_bytes(4, 'big') + self.__wait_send[i]
                # 计算校验和
                data += (lib.checksum(data) ^ 0xffff).to_bytes(2, 'big')
                assert lib.checksum(data) == 0xffff
                self.__sock.send(data)
                self.__lock.acquire()
                self.__cache.append(data)
                t = Timer(4, self.__timer_thread, args=(seq,))
                self.__timer.append(t)
                self.__timer_lock.append(Lock())
                self.__lock.release()
                t.start()
            for i in range(num_send):
                self.__wait_send.pop(0)

    def send(self, data):
        """
        向用户提供的API接口，用于发送数据
        :param data: 需要发送的数据，应该是bytes类型的；
        :return:
        """
        if len(data) % 2 == 1:
            data += b'\x00'
        self.__wait_send.append(data)
        self.__notify_sender.acquire()
        self.__notify_sender.notify()
        self.__notify_sender.release()

    def __timer_thread(self, seq):
        """
        每一个数据包的定时器线程,在函数执行的过程中会获取数据包的锁。
        :param seq: 数据包的seq
        :return: 无
        """
        index = self.__find_index(seq)
        assert index is not None
        lock = self.__timer_lock[index]
        lock.acquire()
        self.__sock.send(self.__cache[index])
        timer = Timer(self.__interval, self.__timer_thread, args=(seq, ))
        timer.start()
        self.__timer[index] = timer
        lock.release()

    def __ack_thread(self):
        while True:
            data = self.__sock.recv(1024)
            seq = data[1]
            index = self.__find_index(seq)
            if index is None:
                continue
            lock = self.__timer_lock[index]
            lock.acquire()
            timer = self.__timer[index]
            timer.cancel()
            self.__timer[index] = None
            lock.release()
            self.__lock.acquire()
            while len(self.__timer) > 0 and self.__timer[0] is None:
                self.__timer.pop(0)
                self.__cache.pop(0)
                self.__timer_lock.pop(0)
            self.__lock.release()


