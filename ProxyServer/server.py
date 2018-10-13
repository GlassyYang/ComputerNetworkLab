from socket import *
import threading

def loop(s):
    while True:
        data = s.recv(4096)
        if data[:5] == b'CONNECT':
            s.send(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        print(data)

def main():
    s = socket(AF_INET, SOCK_STREAM)
    s.bind(('localhost', 9090))
    s.listen(10)
    threads = []
    while True:
        client, addr = s.accept()
        print("Connect from %s" % addr[0])
        t = threading.Thread(target=loop, args=(client,))
        t.setDaemon(True)
        t.start()
        threads.append(t)

if __name__ == "__main__":
    main()
