from threading import *
from time import sleep

cond = Condition()
cond2 = Condition()


def Thread1(condition):
    condition.acquire()
    while True:
        condition.notify()
        condition.wait(0.1)
        print('out of condition')


def Thread2(condition):
    condition.acquire()
    while True:
        condition.release()
        print("I just released the lock, I'm free!")
        sleep(4)
        print("good sleep, I'll work")
        condition.acquire()
        for i in range(6):
            print("working")
            condition.notify()
            condition.wait()


if __name__ == '__main__':
    condition = Condition()
    threads = []
    t = Thread(target=Thread1, args=(condition,))
    t.start()
    threads.append(t)
    t = Thread(target=Thread2, args=(condition, ))
    t.start()
    threads.append(t)
