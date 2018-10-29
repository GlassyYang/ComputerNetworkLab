from socket import *


def primary_test():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 9090))
    while True:
        data, addr = sock.recvfrom(1024)
        print(data)


if __name__ == '__main__':
    primary_test()