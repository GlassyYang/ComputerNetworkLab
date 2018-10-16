#! /usr/bin/env python
# -*- coding: utf-8 -*-
from socket import *
from threading import Thread, Lock
from time import sleep
import lib# 导入本地的扩展包

BUFSIZE = 10240
connect_recv = b'HTTP/1.1 200 Connection Established\r\n\r\n'
badRequest = b'HTTP/1.1 400 Bad Request\r\nConnection: Close\r\n\r\n'
head = b'Content-Type: text/html;charset=UTF-8\r\nDate: %s\r\nConnection: %s\r\nContent-Length: %s\r\n\r\n'

# 用于代理服务器认证设置。
user_connect = False    # 使用代理服务器认证的标志，如果为False则不进行代理服务器代理服务器认证；
user_allow = False      # 允许访问的标志，如果为false则浏览器发起的request都不会被处理；
user_list = []          # 白名单，比黑名单更安全。里面存储着允许访问的用户，在服务器开始工作时初始化；
unauthorized = b'HTTP/1.1 407 Unauthorized\r\n'
file = 'unauthorized.html'

# 用于网站引导。
redirected_filter = None           # 用于网站引导的过滤器，在main函数中初始化，然后每个子线程将会访问这个过滤器。
redirected_file = 'redirect.html'   # 默认的引导的页面，会将所有匹配的网站网页引导到这个网页。
redirected_header = b'HTTP/1.1 200 OK\r\n'  # 进行钓鱼的http头部，匹配时会将该头部连同redirected_file中的内容一起返回

# 用于网站过滤
web_filter = None       # 用于网站过滤的过滤器，在

#用于网页缓存
cache = None            # 用于缓存网页的cache对象
lock = Lock()           # 用于多线程并发的锁

# 子线程的主要处理函数，sock为接收到的客户端连接的socket
def thread_main(sock):
    global web_filter, cache, redirected_filter, user_allow
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
            # 在CONNECT方法中进行代理服务器认证的设置
            print(data)
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
                    except ConnectionAbortedError:
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
    sock.shutdown(SHUT_RDWR)
    sleep(1)
    sock.close()


# 程序的主线程：
def main():
    print("Server initialize...")
    global web_filter, redirected_filter
    command = input("Whether execute website filter or not?y/n")
    if command == 'y' or command == 'yes':
        web_filter = lib.filter.Filter()
    command = input("Whether execute website phishing or not? y/n")
    if command == 'y' or command == 'yes':
        redirected_filter = lib.filter.Filter()
    command = input("Whether execute cache or not? y/n")
    if command == 'y' or command == 'yes':
        redirected_filter = lib.cache.CacheManager()
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
