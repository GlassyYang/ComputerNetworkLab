from lib.gbn_recver import GbnRecver


def server():
    print('initialize server...')
    client = GbnRecver(('localhost', 8080))
    while True:
        data = client.recv()
        for i in data:
            print('data receive: ' + i.encoding('utf-8'))


if __name__ == '__main__':
    server()
