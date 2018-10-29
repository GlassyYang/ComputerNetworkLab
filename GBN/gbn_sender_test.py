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
    测试超时重传机制。选择元组将要发送的包中的其中一个包，在这之后的包都不发送ack，而是在第二次收到该包的时候再发送ack。
    预期结果是在该包之前的包只发送一次，而在这之后的包发送两次。
    :return:
    """
    select = 3
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 8080))
    while True:
        data, addr = sock.recvfrom(1024)
        if data[1] >= select:
            break
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
    test1()
