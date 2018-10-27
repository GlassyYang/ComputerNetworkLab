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
head = b'Content-Type: text/html;charset=UTF-8\r\nContent-Length: %d\r\nConnection: %b\r\n\r\n'

# 用于代理服务器认证设置。
user_connect = False    # 使用代理服务器认证的标志，如果为False则不进行代理服务器代理服务器认证；
user_allow = False      # 允许访问的标志，如果为false则浏览器发起的request都不会被处理；
user_list = []          # 白名单，比黑名单更安全。里面存储着允许访问的用户，在服务器开始工作时初始化；
unauthorized = b'HTTP/1.1 407 Unauthorized\r\nProxy-Authenticate: Basic realm="Access to the internal site"'\
                + b'\r\nContent-Type: text/html;charset=UTF-8\r\nContent-length: %d\r\nConnection: close\r\n\r\n'
file = 'unauthorized.html'

# 用于网站引导。
redirected_filter = None           # 用于网站引导的过滤器，在main函数中初始化，然后每个子线程将会访问这个过滤器。
redirected_file = 'redirect.html'   # 默认的引导的页面，会将所有匹配的网站网页引导到这个网页。
redirected_header = b'HTTP/1.1 200 OK\r\n' + head # 进行钓鱼的http头部，匹配时会将该头部连同redirected_file中的内容一起返回


# 用于网站过滤
web_filter = None       # 用于网站过滤的过滤器,当满足过滤要求时，发送
filter_header = b'HTTP/1.1 403 Forbidden\r\n' + head
filter_file = 'forbidden.html'
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
    index = 8
    index_e = index
    while data[index_e] != ord(b':'):
        index_e += 1
    url = str(data[index:index_e], encoding='ascii')
    index = index_e + 1
    index_e = index
    while ord(b'0') <= data[index_e] < ord(b'9'):
        index_e += 1
    port = int(data[index:(index_e + 1)].decode('ascii'))
    if port not in (80, 443):
        return
    server = socket(AF_INET, SOCK_STREAM)
    try:
        server.connect((gethostbyname(url), port))
    except TimeoutError or ConnectionRefusedError:
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
                    length = server.send(data)
                    assert len(data) == length
                except timeout:
                    break
            while True:
                try:
                    data = server.recv(BUFSIZE)
                    length = sock.send(data)
                    assert len(data) == length
                except timeout:
                    break
    except ConnectionAbortedError:
        return


def validate(sock, data):
    """
    对浏览器连接进行验证
    :param sock: 浏览器与代理服务器之间的连接
    :param data: 浏览器向代理服务器发送的请求
    :return: 如果验证成功，返回True；否则返回False
    """
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
        while data[index_e] != ord(b'\r'):
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
        index = data.find(b'\r\nProxy-Connection')
        if index == -1:
            index = data.find(b'\r\nConnection:')
        else:
            data = data.replace(b'\r\nProxy-Connection', b'\r\nConnection')
        request = data[:index] + b'\r\nIf-Modified-Since: ' + time_stamp + data[index:]
        server.send(request)
        print('"if-modified-since" header send')
        server.settimeout(4)
        data = b''
        # 从服务器完整的接收数据
        while True:
            try:
                temp = server.recv(BUFSIZE)
                if len(temp) == 0:
                    break
                data += temp
            except timeout:
                break
        if data.find(b'304 Not Modified') != -1:
            print("304 status code received.")
            index = data.find(b'Date: ')
            assert index != -1
            index_e = data.find(b'GMT\r\n')
            index += 5
            index_e += 3
            assert index_e != -1
            data = cache.get_data(filename, data)
            return data
        else:
            print("200 status code received.")
            # 当发现从服务器返回的response中的Content-Length为0时，不缓存数据；
            if data.find(b'Content-Length: 0') != -1:
                return data
            lock.acquire()
            cache.cache(data, filename)
            lock.release()
            return data
    else:
        server.send(data)
        server.settimeout(1)
        data = b''
        while True:
            try:
                temp = server.recv(BUFSIZE)
                if len(temp) == 0:
                    break
                data += temp
            except timeout:
                break
            except ConnectionAbortedError:
                break
        if data.find(b'Content-Length: 0') != -1:
            return data
        lock.acquire()
        cache.cache(data, filename)
        lock.release()
        return data


# 子线程的主要处理函数，sock为接收到的客户端连接的socket
def thread_main(sock):
    # 进行全局变量引用的申明：
    global user_allow, user_connect, user_list  # 用于进行用户验证的变量
    global cache    # 用于网页缓存的变量对象
    global redirected_filter, redirected_file, redirected_header    # 用于进行网页重定向的对象
    global web_filter, filter_file, filter_header   # 用于进行网站过滤的对象
    pre_url = b''
    server = None
    while True:
        try:
            data = sock.recv(BUFSIZE)
            if len(data) == 0:
                break
        except timeout as e:
            print(e)
            break
        except ConnectionAbortedError:
            break
        if data.find(b'CONNECT') != -1:
            # 尝试进行HTTPS代理隧道的构建
            tunnel(sock, data)
            break
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
                # 当获取到host地址的时候，检查是否需要对地址进行过滤以及是否需要进行钓鱼
                if web_filter is not None:
                    if web_filter.match(url):
                        data_send, length = open_data(filter_file)
                        sock.send((filter_header % (length, b'close')) + data_send)
                        break
                if redirected_filter is not None:
                    if redirected_filter.match(url):
                        data_send, length = open_data(redirected_file)
                        sock.send((filter_header % (length, b'keep-alive')) + data_send)
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
                # 检测是否应该关闭连接
                if data.find(b"Connection: keep-alive") == -1:
                    close = True
                else:
                    close = False
                # 判断是否启用缓存功能
                if data.find(b'GET') != -1 and cache is not None:
                    data = cache_oper(data, server)
                    sock.send(data)
                    if close:
                        break
                    continue
                # 如果缓存功能没有启用，则直接向服务器发送请求，并得到服务请返回的数据，将其发送给浏览器端
                # 传输从服务器到客户端的数据
                server.settimeout(4)
                try:
                    server.send(data)
                except timeout as e:
                    print(e)
                while True:
                    try:
                        data = server.recv(BUFSIZE)
                        if len(data) == 0:
                            break
                    except timeout:
                        break
                    except ConnectionAbortedError:
                        break
                    try:
                        length = sock.send(data)
                        if len(data) == 0:
                            break
                    except timeout:
                        break
                    except ConnectionAbortedError:
                        break
                    assert length == len(data)
                if close:
                    break
            else:
                try:
                    sock.send(badRequest)
                except timeout as e:
                    print(e)
                break
    if server is not None:
        server.shutdown(SHUT_RDWR)
        sleep(1)
        server.close()
    sock.shutdown(SHUT_RDWR)
    sleep(1)
    sock.close()


# 程序的主线程：
def main():
    print("Server initialize...")
    global web_filter, redirected_filter, user_connect, user_list, cache
    command = input("Whether execute website filter or not?y/n")
    if command == 'y' or command == 'yes':
        web_filter = lib.filter.Filter()
    command = input("Whether execute website phishing or not? y/n")
    if command == 'y' or command == 'yes':
        redirected_filter = lib.filter.Filter()
    command = input("Whether execute cache or not? y/n")
    if command == 'y' or command == 'yes':
        cache = lib.cache.CacheManager()
    command = input("Whether enable user authorization? y/n")
    if command == 'y' or command == 'yes':
        user_connect = True
        print("Please input username and password, separates with':', and ends with '.' in a single line:")
        print('example: "admin:123"')
        while True:
            data = input(">>>")
            if data == '.':
                break
            if data.find(":") == -1:
                print("invalid input!")
                continue
            user_list.append(data.encode('ascii'))
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
