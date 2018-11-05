from socket import *
from lib import lib


# 发送序列号1,2,3,4,6,7,8,9,回复应该是1,2,3,4,4,4,4,4
def test():
    sock = socket(AF_INET, SOCK_DGRAM)
    test = b'test'
    test = len(test).to_bytes(4, 'big') + test
    sock.connect(('localhost', 8080))
    mod = 3
    for i in range(1, 100):
        if i == 5:
            continue
        data = bytes([0, i]) + test
        data += (lib.checksum(data) ^ 0xffff).to_bytes(2, 'big')
        sock.send(data)
        ack, addr = sock.recvfrom(1024)
        print(ack[1])


if __name__ == '__main__':
    test()
