#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""一个域名过滤器，过滤规则为：输入网站域名，可以使用通配符'*'匹配一个子域名。例如：
规则www.*.hit.edu.cn会匹配www.hit.edu.cn，也会匹配www.scu.edu.cn,*.hit.edu.cn会匹配jwc.hit.edu.cn，也会匹配
cs.hit.edu.cn。而www.hit.edu.cn只会匹配www.hit.edu.cn，不会匹配其他的网站;通配符的作用域为一个子域名，形如jw*.edu.cn的
匹配规则是不正确的。本过滤器没有使用正则表达式，纯粹是为了好玩和实用。
"""


class Filter:
    def __init__(self):
        self.reg = []
        print("请输入过滤规则，可以是完整的host，也可以通过通配符'*',如 *.hit.edu.cn, cs.*.edu.cn, www.hit.edu.cn")
        print("通过单行输入'.'退出过滤规则的输入")
        while True:
            data = input(">>>")
            if data == '.':
                break
            self.reg.append(data.split('.'))

    def match(self, host):
        """将输入的域名与内部的过滤规则进行匹配，成功返回True，失败返回False，要求host是string类型"""
        assert type(host) == str
        part = host.split('.')
        for i in self.reg:
            if len(i) != len(part):
                continue
            count = 0
            for j in range(len(part)):
                if i[j] == '*':
                    count += 1
                    continue
                elif i[j] == part[j]:
                    count += 1
            if count == len(part):
                return True
        return False
