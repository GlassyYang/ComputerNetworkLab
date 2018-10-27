from socket import *


def main():
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(('localhost', 8080))
    while True:
        data, addr = sock.recvfrom(1024)
        seq = data[2]
        print(data)
        ack = bytes([255, seq])
        sock.sendto(ack, addr)


if __name__ == '__main__':
    main()
