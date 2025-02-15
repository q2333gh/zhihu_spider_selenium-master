import time
from datetime import datetime


def now():
    """返回当前时间戳"""
    return time.time()


def nowtime():
    """返回当前时间的格式化字符串"""
    nowtm = datetime.fromtimestamp(time.time()).isoformat().replace(":", "_")
    return nowtm


def crawlsleep(times):
    """爬虫休眠函数"""
    time.sleep(times)
