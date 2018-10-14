#! /usr/bin/env python
# -*- coding: utf-8 -*-
from socket import *
from threading import Thread
from time import sleep
import lib  # 导入本地的扩展包
BUFSIZE = 8193
connect_recv = b'HTTP/1.1 200\r\nConnection Established\r\n\r\n'
badRequest = b'HTTP/1.1 400 Bad Request\r\nConnection: Close\r\n\r\n'

# 用于代理服务器认证设置。
user_connect = False    # 使用代理服务器认证的标志，如果为False则不进行代理服务器代理服务器认证；
user_allow = False      # 允许访问的标志，如果为false则浏览器发起的request都不会被处理；
user_list = []          # 白名单，比黑名单更安全。里面存储着允许访问的用户，在服务器开始工作时初始化；

# 用于网站引导。

fitter = lib.Filter()   # 将该过滤器中匹配的网站访问引导至另一个模拟网站
redirected_file = 'redirect.html'   # 默认的引导的页面，会将所有匹配的网站网页引导到这个网页。
redirected_header = ''  # 进行钓鱼的http头部，匹配时服务器会将该头部连同redirected_file中的内容一起返回


# 子线程的主要处理函数，sock为接收到的客户端连接的socket
def thread_main(sock):
    pre_url = b''
    server = None
    while True:
        try:
            data = sock.recv(BUFSIZE)
        except timeout as e:
            print(e)
            break
        except ConnectionAbortedError:
            break
        if data.find(b'CONNECT') != -1:
            sock.send(connect_recv)
        elif data.find(b'GET') != -1 or data.find(b"POST") != -1 or data.find(b'HEAD') != -1:
            if data.find(b'\r\nHost') != -1:
                index = data.find(b'\r\nHost')
                index += 8
                url = []
                while data[index] != ord(b'\r'):
                    url.append(chr(data[index]))
                    index += 1
                url = ''.join(url)
                print(url)
                if pre_url != url:
                    if server is not None:
                        server.shutdown(SHUT_RDWR)
                        sleep(1)
                        server.close()
                    try:
                        ip_addr = gethostbyname(url)
                    except gaierror as e:
                        print(e)
                        try:
                            sock.send(badRequest)
                        except timeout as e:
                            print(e)
                            break
                        break
                    server = socket(AF_INET, SOCK_STREAM)
                    try:
                        server.connect((ip_addr, 80))
                    except timeout as e:
                        print(e)
                        break
                    pre_url = url
                try:
                    length = server.send(data)
                except timeout as e:
                    print(e)
                assert length == len(data)
                # 检测是否应该关闭连接
                if data.find(b"Connection: keep-alive") == -1:
                    close = True
                else:
                    close = False
                # 传输从服务器到客户端的数据
                server.settimeout(4)
                while True:
                    try:
                        data = server.recv(BUFSIZE)
                    except timeout:
                        break
                    length = sock.send(data)
                    assert length == len(data)
                if close:
                    break
            else:
                try:
                    sock.send(badRequest)
                except timeout as e:
                    print(e)
                break
    sock.shutdown()
    sleep(1)
    sock.close()


# 程序的主线程：
def main():
    own = socket(AF_INET, SOCK_STREAM)
    own.bind(('localhost', 9090))
    own.listen()
    print("server started...\n")
    threads = []
    while True:
        sock, addr = own.accept()
        print("Connection established from %s:%s" % (addr[0], addr[1]))
        t = Thread(target=thread_main, args=(sock,))
        t.start()
        threads.append(t)


if __name__ == '__main__':
    main()
