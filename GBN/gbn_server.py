from lib import GbnRecver


def server():
    print('initialize server...')
    client = GbnRecver(('localhost', 8080))
    while True:
        data = client.recv()
        print('data receive: ' + data.decode('utf-8'))


if __name__ == '__main__':
    server()
