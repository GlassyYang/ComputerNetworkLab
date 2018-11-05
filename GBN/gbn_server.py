from lib import GbnRecver, GbnServer


def server():
    print('initialize server...')
    client = GbnRecver(('localhost', 8080))
    while True:
        data = client.recv()
        print('data receive: ' + data.decode('utf-8'))


def server_d():
    print('initialize server...')
    client = GbnServer(('localhost', 8080))
    print("initialize finished. please input something to send to server, '.' in a single line means over")

    while True:
        data = client.recv()
        print('client said: ' + data.decode('utf-8'))
        data = input('>>>')
        if data == '.':
            break
        client.send(data.encode('ascii'))


if __name__ == '__main__':
    # 二选一
    server()    # 用GBN协议实现的server
    # server_d()  # 用双向GBN协议实现的server

