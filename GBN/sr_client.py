from lib import SrSender


def main():
    print('socket initialize..')
    client = SrSender(('localhost', 9090))
    print('initialize finished')
    print('please input something to send to server')
    while True:
        data = input('>>>')
        client.send(data.encode('utf-8'))


if __name__ == '__main__':
    main()
