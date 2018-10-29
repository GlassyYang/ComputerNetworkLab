from lib import SrRecver


def main():
    print('socket initialize...')
    server = SrRecver(('localhost', 9090))
    print('initialize finished')
    while True:
        data = server.recv()
        print(data.decode('utf-8'))


if __name__ == '__main__':
    main()
