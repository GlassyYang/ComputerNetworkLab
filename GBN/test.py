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


def thread3(ths):
    sleep(1)
    ths.remove(current_thread())
    sleep(1)
    print('after remove..')
    return


def timer_thread(i):
    print('in timer thread')
    print(i)
    return


if __name__ == '__main__':
    condition = Condition()
    threads = []
    # t = Thread(target=Thread1, args=(condition,))
    # t.start()
    # threads.append(t)
    # t = Thread(target=Thread2, args=(condition, ))
    # t.start()
    # threads.append(t)
    # t = Thread(target=thread3, args=(threads,))
    # threads.append(t)
    # t.start()
    t = Timer(2., timer_thread, args=(1,))
    t.start()
    sleep(4)

