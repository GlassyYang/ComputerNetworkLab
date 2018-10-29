from socket import *
from time import sleep
from lib import checksum, SrSender
from threading import Thread

# 测试sender的发送重传功能是否正确，同时不同的包是否有自己的定时器，测试方法为每隔1秒发送一个包，但是丢掉ack；
def test1():
    t = Thread(target=test1_thread)
    t.start()
    addr = ('localhost', 9090)
    sock = SrSender(addr)
    for i in range(4):
        sock.send('test'.encode('ascii'))
        sleep(1)


def test1_thread():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 9090))
    while True:
        data, addr = sock.recvfrom(1024)
        print('receive data seq: %d' % data[1])


# 测试sr发送方的
def test2():
    pass


if __name__ == '__main__':
    test1()
