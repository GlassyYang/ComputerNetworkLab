from socket import *
from lib import SrRecver, checksum, SrSender
from random import shuffle
from threading import Thread
"""
    文件测试接收方功能是否正常
"""

addr = ('localhost', 9090)


# 发送seq打乱的数据包，观察recver接收到的数据包的顺序是否正常
def test1():
    global addr
    t = Thread(target=test1_thread)
    t.start()
    seqs = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    shuffle(seqs)
    test = (6).to_bytes(4, 'big') + b'test %d'
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.connect(addr)
    for i in range(9):
        data = bytes([0, seqs[i]]) + (test % (seqs[i]))
        data += (checksum(data) ^ 0xffff).to_bytes(2, 'big')
        sock.send(data)
    t.join()


def test1_thread():
    global addr
    recv = SrRecver(addr)
    for i in range(9):
        print('into recv')
        data = recv.recv()
        print(data)


# 测试连续发送多个数据包（大于窗口大小），观察窗口的移动
def test2():
    t = Thread(target=test2_thread())
    t.start()
    global addr
    client = SrSender(addr)
    for i in range(20):
        client.send(b'test %d' % i)
    t.join()


def test2_thread():
    global addr
    server = SrRecver(addr)
    for i in range(20):
        data = server.recv()
        print(data)


# 测试概率丢包
def test3():
    """
        测试超时重传机制。选择元组将要发送的包中的其中一个包，在这之后的包都不发送ack，而是在第二次收到该包的时候再发送ack。
        预期结果是在该包之前的包只发送一次，而在这之后的包发送两次。
        :return:
        """
    select = 3
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 9090))
    t = Thread(target=test3_thread)
    t.start()
    while True:
        data, addr = sock.recvfrom(1024)
        if data[1] % select == 0:
            continue
        ack = bytes([255, data[1]])
        sock.sendto(ack, addr)
        print(data[1])
    print('begin throw package')
    sock.recvfrom(1024)
    while True:
        data, addr = sock.recvfrom(1024)
        if data[1] == select:
            ack = bytes([255, data[1]])
            sock.sendto(ack, addr)
            print(data[1])
            break
        else:
            print('data received and be thrown')
    while True:
        data, addr = sock.recvfrom(1024)
        ack = bytes([255, data[1]])
        sock.sendto(ack, addr)
        print(data[1])


def test3_thread():
    server = SrSender(('localhost', 9090))
    test = b'test %d'
    for i in range(20):
        server.send(test % i)


if __name__ == '__main__':
    test3()
