from socket import *
from threading import Thread
from time import sleep
BUFSIZE = 4096

data1 = '''CONNECT jwts.hit.edu.cn:443 HTTP/1.1
Host: clients4.google.com:443
Proxy-Connection: keep-alive
User-Agent: Chrome WIN 69.0.3497.100 (8920e690dd011895672947112477d10d5c8afb09-refs/branch-heads/3497@{#948}) channel(stable)

'''

data2 = '''GET / HTTP/1.1
Host: jwts.hit.edu.cn
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: name=value; clwz_blc_pst=83890348.24859; JSESSIONID=L80db1phw2wQLyvFVX1jfPTrQL36hsjMXb89vcGhQ69c1551nTn3!-1814731118
Connection: close

'''
def thread1():
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('localhost', 9090))
    s.send(data1.replace('\n', '\r\n').encode('ascii'))
    data = s.recv(BUFSIZE)
    print("Thread1: " + data.decode('utf-8'))
    s.close()

def thread2():
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(('localhost', 9090))
    s.send(data2.replace('\n', '\r\n').encode('ascii'))
    data = s.recv(BUFSIZE)
    print("Thread2: " + data.decode('utf-8'))
    s.close()

def main():
    threads = []
    t = Thread(target=thread1)
    t.start()
    threads.append(t)
    t = Thread(target=thread2)
    t.start()
    threads.append(t)
    sleep(5)

if __name__ == "__main__":
    main()
    
