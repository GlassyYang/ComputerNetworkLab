from lib import GbnSender, GbnClient


def client():
    print('initialize socket....')
    server = GbnSender(('localhost', 8080))
    print("initialize finished. please input something to send to server, '.' in a single line means over")
    while True:
        data = input('>>>')
        if data == '.':
            break
        server.send(data.encode('utf-8'))
    return


def client_d():
    print('initialize socket....')
    server = GbnClient(('localhost', 8080))
    print("initialize finished. please input something to send to server, '.' in a single line means over")
    while True:
        data = input(">>>")
        server.send(data.encode('ascii'))
        data = server.recv()
        print('server said: ' + data.decode('utf-8'))
        # server.send(data.encode('utf-8'))


if __name__ == '__main__':
    # 二选一
    client()    # 用GBN协议实现的client
    # client_d()  # 用双向GBN协议实现的client

