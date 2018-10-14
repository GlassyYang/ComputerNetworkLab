#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""这个文件是一个库，用来实现网页文件的cache，cache是指将服务端的网页缓存在本地，当浏览器试图访问该网页时，
如果网页没有过期，代理服务器则直接返回该网页。具体的实现方法为：
当从浏览器接收文件时，代理服务器缓存该文件，缓存方法为：将文件的url地址使用MD5散列作为缓存文件的文件名，保存在
cache文件夹中；
当浏览器请求一个文件时，代理服务器通过MD5计算文件URL的MD5散列值，然后试图以只读的方式打开该文件；如果打开不了该文件，
则说明该网页没有缓存；否则获取该文件的最后一次修改的日期，然后向浏览器发送if-modified-since头部，如果浏览器返回304，
说明该文件之后没有被修改，代理服务器则直接返回缓存的数据；如果返回200，则代理服务器向浏览器返回服务器返回的数据并更新
该文件的缓存。"""

from hashlib import md5
#from binascii import hex

class CacheManager(object):
    def __init__(self):
        self.__filename = None
        self.file = None
        # 定义缓存文件存储的路径
        self.route = './cache/'
        pass

    def ana_filename(self, data):
        """通过浏览器发送的request请求得到文件名，当成功得到文件名之后，函数返回True，否则返回False。该函数必须在
        进行该类的任何操作之前调用"""
        begin_index = data.find(b'host: ')
        if begin_index == -1:
            return False
        url = []
        begin_index += 6
        while begin_index < len(data) and data[begin_index] != ord(b'\r'):
            url.append(chr(data[begin_index]))
        if begin_index == len(data):
            return False
        begin_index = -1
        for i in range(len(data)):
            if data[i] == ord(b' '):
                begin_index = i
                break
        if begin_index == -1:
            return False
        while begin_index < len(data) and data[begin_index] != ord(b' '):
            url.append(chr(data[begin_index]))
        if begin_index == len(data):
            return False
        url = bytes(''.join(url))
        self.__filename = md5().update(url).hexdigest()
        return True

    def cached(self):
        """检查url是否缓存，要求之前必须调用ana_filename函数；如果缓存函数返回True，没有缓存返回False"""
        assert self.__filename is not None
        try:
            f = open(self.route + self.__filename, 'rb')
            self.file = f
        except FileNotFoundError:
            return False
        else:
            return True

    def get_data(self):
        """得到缓存的数据，前提是在此之前调用了aya_filename函数并且数据已经缓存（调用cached函数返回True）
        函数返回缓存的数据"""
        if self.__filename is None or not self.cached():
            return None
        assert self.file is not None
        return self.file.read()

    def cache(self, data):
        """将数据缓存起来。data为要缓存的数据，在调用该函数之前必须先调用ana_filename函数"""
        with open(self.route + self.__filename) as f:
            f.write(data)

    def __del__(self):
        if self.file is not None:
            self.file.close()
