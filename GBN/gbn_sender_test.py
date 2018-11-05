from socket import *


def test1():
    """
    测试累积确认机制，对收到的第一个包不发送ack，而是对后面收到的包发送ack，预期结果是每个包只发送了一次
    :return:
    """
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 8080))
    flag = True
    while True:
        data, addr = sock.recvfrom(1024)
        print(data[1])
        if flag:
            print('throw package %d' % data[1])
            flag = False
            continue
        seq = data[1]
        data_len = int.from_bytes(data[2:6], 'big')
        data = data[6:6 + data_len]
        print(data)
        ack = bytes([255, seq])
        print('send ack %d' % seq)
        sock.sendto(ack, addr)


def test2():
    """
    测试概率丢包
    :return:
    """
    select = 3       # 概率值，所有被该变量整除的seq的包都会被丢弃。
    count = 0
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 8080))
    while True:
        data, addr = sock.recvfrom(1024)
        if data[1] % select == 0 and count < 5:
            print(data[1])
            count += 1
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


if __name__ == '__main__':
    test2()     # 概率丢包
    # test1()     # 累积确认
