from socket import *
from time import sleep
from lib import SrSender, checksum
from threading import Thread
from random import shuffle
addr = ('localhost', 9090)


# 测试sr协议的基本功能
def primary_test():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 9090))
    while True:
        data, addr = sock.recvfrom(1024)
        print(data)


# 测试sender的发送重传功能是否正确，同时不同的包是否有自己的定时器，测试方法为每隔1秒发送一个包，但是丢掉ack；
def test1():
    global addr
    t = Thread(target=test1_thread)
    t.start()
    sock = SrSender(addr)
    for i in range(4):
        sock.send('test'.encode('ascii'))
        sleep(1)


def test1_thread():
    global addr
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(addr)
    while True:
        data, addr = sock.recvfrom(1024)
        print('receive data seq: %d' % data[1])


# 测试sr发送方的窗口移动是否正确。发送20个数据报，观察协议发送的数据
def test2():
    t = Thread(target=test2_thread)
    t.start()
    global addr
    sock = SrSender(addr)
    cont = b'test'
    for i in range(20):
        sock.send(cont)


def test2_thread():
    global addr
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(addr)
    while True:
        data, cli = sock.recvfrom(1024)
        data = bytes([255, data[1]])
        data += (checksum(data) ^ 0xff).to_bytes(2, 'big')
        print('send ack: %d' % data[1])
        sock.sendto(data, cli)


# 接收发送的数据并发送ack，发送ack的顺序是随机选的；
def test3_thread():
    global addr
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(addr)
    lv = .3
    acks = []
    while len(acks) < 10:
        data, cli = sock.recvfrom(1024)
        acks.append(data[1])
    print("data received: %d" % len(acks))
    shuffle(acks)
    drop_acks = []
    for i in range(int(lv * len(acks))):
        drop_acks.append(acks.pop(i))
    for i in range(len(acks)):
        data = bytes([255, acks[i]])
        data += (checksum(data) ^ 0xff).to_bytes(2, 'big')
        print('send ack: %d' % acks[i])
        sock.sendto(data, cli)
        sleep(.1)
    sleep(2)
    for i in range(10):
        data, cli = sock.recvfrom(1024)
        print(data[1])
    for i in range(len(drop_acks)):
        data = bytes([255, drop_acks[i]])
        data += (checksum(data) ^ 0xff).to_bytes(2, 'big')
        print('send ack: %d' % drop_acks[i])
        sock.sendto(data, cli)
    while True:
        data, cli = sock.recvfrom(1024)
        print(data[1])



# 测试丢包
def test3():
    t = Thread(target=test3_thread)
    t.start()
    sock = SrSender(addr)
    test = b'test %d'
    for i in range(10):
        sock.send(test % i)
    t.join()
    sleep(2)


if __name__ == '__main__':
    test3()
