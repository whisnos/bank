import threading

from trade.models import OrderInfo


def printHello():
    print("start")
    OrderInfo
    timer = threading.Timer(5, printHello)
    timer.start()


if __name__ == "__main__":
    printHello() 