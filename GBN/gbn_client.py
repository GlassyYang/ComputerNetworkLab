from lib.gbn_sender import GbnSender


def client():
    print('initialize socket....')
    server = GbnSender(('localhost', 8080))
    server.initialize()
    print("initialize finished. please input something to send to server, '.' in a single line means over" )
    while True:
        data = input('>>>')
        if data == '.':
            break
        server.send(data.encode('utf-8'))
    return


if __name__ == '__main__':
    client()

