#! /usr/bin/env python
# -*- coding: utf-8 -*-
from socket import *
from threading import Thread, Lock
from time import sleep
import lib  # 导入本地的扩展包
import base64
BUFSIZE = 10240
connect_recv = b'HTTP/1.1 200 Connection Established\r\n\r\n'
badRequest = b'HTTP/1.1 400 Bad Request\r\nConnection: Close\r\n\r\n'
head = b'Content-Type: text/html;charset=UTF-8\r\nDate: %s\r\nConnection: %s\r\nContent-Length: %s\r\n\r\n'

# 用于代理服务器认证设置。
user_connect = False    # 使用代理服务器认证的标志，如果为False则不进行代理服务器代理服务器认证；
user_allow = False      # 允许访问的标志，如果为false则浏览器发起的request都不会被处理；
user_list = []          # 白名单，比黑名单更安全。里面存储着允许访问的用户，在服务器开始工作时初始化；
unauthorized = b'HTTP/1.1 407 Unauthorized\r\nProxy-Authenticate: Basic realm="Access to the internal site"'\
                + b'\r\nContent-length: %d\r\nConnection: close\r\n\r\n'
file = 'unauthorized.html'

# 用于网站引导。
redirected_filter = None           # 用于网站引导的过滤器，在main函数中初始化，然后每个子线程将会访问这个过滤器。
redirected_file = 'redirect.html'   # 默认的引导的页面，会将所有匹配的网站网页引导到这个网页。
redirected_header = b'HTTP/1.1 200 OK\r\n'  # 进行钓鱼的http头部，匹配时会将该头部连同redirected_file中的内容一起返回

# 用于网站过滤
web_filter = None       # 用于网站过滤的过滤器，在

# 用于网页缓存
cache = None            # 用于缓存网页的cache对象
lock = Lock()           # 用于多线程并发的锁


def open_data(filename):
    """
    open specified html file, return data of it.
    :param filename: specified html file, encoding should be utf-8
    :return: first value is bytes of file, second value is Bytes list, and data of file included.
    """
    try:
        f = open(filename, 'r', encoding='utf-8')
    except FileNotFoundError:
        return None
    data = f.read()
    length = len(data)
    return data.encode('utf-8'), length


def tunnel(sock, data):
    """
    try to establish a tunnel when receive CONNECT method
    :param sock: origin socket, usually is a connect socket between proxy and browser
    :param data: HTTP request using method CONNECT from browser
    :return: nothing
    """
    index = 7
    if data[index] == 0x20:  # 0x20为' '的ASCII码值
        index += 1
    index_e = index
    while data[index] != 0x3a:  # 0x3a为':'的ASCII码值
        index_e += 1
    url = str(data[index:index_e], encoding='ascii')
    print(url)
    index += 1
    index_e = index
    while 0x30 <= data[index_e] < 0x3a:
        index_e += 1
    port = int(data[index:(index_e + 1)].decode('ascii'))
    print(port)
    if port not in (80, 443):
        return
    server = socket(AF_INET, SOCK_STREAM)
    try:
        server.connect((gethostbyname(url, port)))
    except timeout or ConnectionRefusedError:
        server.close()
        return
    sock.send(connect_recv)
    sock.settimeout(2)
    server.settimeout(2)
    try:
        while True:
            while True:
                try:
                    data = sock.recv(BUFSIZE)
                    l = server.send(data)
                    assert len(data) == l
                except timeout:
                    break
            sleep(1)
            while True:
                try:
                    data = server.recv(BUFSIZE)
                    l = sock.send(data)
                    assert len(data) == l
                except timeout:
                    break
    except ConnectionAbortedError:
        return


def validate(sock, data):
    global user_allow
    index = data.find(b"Proxy-Authorization: Basic ")
    # 如果GET方法中没有设置Proxy-Authorization头部，返回未授权的respond
    if index == -1:
        data, length = open_data(file)
        sock.send((unauthorized % length) + data)
        return False
    # 否则对用户名和密码进行验证；
    else:
        index += 27
        index_e = index  # 加上了"Proxy-Authorization: Basic "的长度进行索引的调整
        while data[index_e] != ord(b'\r'):  # 0x0d为\r的ascii表示
            index_e += 1
        user = base64.b64decode(data[index:index_e])
        if user in user_list:
            user_allow = True
            return True
        else:
            data, length = open_data(file)
            sock.send((unauthorized % length) + data)
            return False


def cache_oper(data, server):
    """
    Contact with server and deal with data, including cache data, sending self-made request to server, and return cached
    data from local.
    :param data: request from browser.
    :param server: server socket which request will send
    :return: respond of the request, either from server or local cache.
    """
    global cache
    filename = cache.ana_filename(data)
    if cache.cached(filename):
        time_stamp = cache.timestamp(filename)
        index = data.find(b'\r\n\r\n')
        assert index != -1
        request = data[:index] + b'If-Modified_Since: ' + time_stamp + b'\r\n' + b'\r\n\r\n'
        server.send(request)
        server.settimeout(2)
        data = b''
        # 从服务器完整的接收数据
        while True:
            try:
                temp = server.recv(BUFSIZE)
                data += temp
            except timeout:
                break
        if data.find(b'304 Not Modified') != -1:
            return cache.get_data()
        else:
            cache.cache(data, filename)
            return data
    else:
        server.send(data)
        server.settimeout(2)
        data = b''
        while True:
            try:
                temp = server.recv(BUFSIZE)
                if len(temp) == 0:
                    break
                data += temp
            except timeout:
                break
        cache.cache(data, filename)
        return data


# 子线程的主要处理函数，sock为接收到的客户端连接的socket
def thread_main(sock):
    global web_filter, cache, redirected_filter, user_allow, user_connect, user_list, cache
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
            # 尝试进行HTTPS代理隧道的构建
            tunnel(sock, data)
        # 处理浏览器发送的GET、POST和HEAD请求，其余的请求全部忽略，当做bad request处理
        elif data.find(b'GET') != -1 or data.find(b"POST") != -1 or data.find(b'HEAD') != -1:
            # 在GET方法中进行用户名验证，如果要求的话
            if user_connect and not user_allow:
                if not validate(sock, data):
                    break
            # 获取浏览器请求中的主机地址
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
                # 判断是否启用缓存功能
                if data.find(b'GET') != -1 and cache is not None:
                    data = cache_oper(data, server)
                    sock.send(data)
                    continue
                # 如果缓存功能没有启用，则直接向服务器发送请求，并得到服务请返回的数据，将其发送给浏览器端
                try:
                    server.send(data)
                except timeout as e:
                    print(e)
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
                        if len(data) == 0:
                            break
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
    global web_filter, redirected_filter, user_connect, user_list, cache
    # command = input("Whether execute website filter or not?y/n")
    # if command == 'y' or command == 'yes':
    #     web_filter = lib.filter.Filter()
    # command = input("Whether execute website phishing or not? y/n")
    # if command == 'y' or command == 'yes':
    #     redirected_filter = lib.filter.Filter()
    # command = input("Whether execute cache or not? y/n")
    # if command == 'y' or command == 'yes':
    cache = lib.cache.CacheManager()
    # user_connect = True
    # user_list = [b'admin:123']
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
