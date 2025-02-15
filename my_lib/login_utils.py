from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import pickle
import os
import time


def save_cookie(driver, path):
    """保存cookie到文件"""
    with open(path, "wb") as filehandler:
        pickle.dump(driver.get_cookies(), filehandler)


def load_cookie(driver, path):
    """从文件加载cookie"""
    with open(path, "rb") as cookiesfile:
        cookies = pickle.load(cookiesfile)
        for cookie in cookies:
            driver.add_cookie(cookie)


def login(driver):
    """登录知乎"""
    driver.get(r"https://www.zhihu.com/")
    try:
        driver.find_elements(By.CLASS_NAME, "SignFlow-tab")[1].click()
    except:
        pass
    toggle = []
    ti = 1
    while toggle == [] and ti < 600:
        toggle = driver.find_elements(By.ID, "Popover15-toggle")
        time.sleep(3)
        if ti % 10 == 0:
            print(
                "等待输入账号并点击登录，登录以后请不要执行任何操作，10分钟后自动退出........."
            )
        ti += 3
    toggle = driver.find_elements(By.ID, "Popover15-toggle")
    if toggle == []:
        print("还没有登陆的，还请登录保存cookie.......")
        driver.quit()
        exit(0)
    return driver


def login_loadsavecookie(driver, cookie_path):
    """登录并管理cookie"""
    try:
        load_cookie(driver, cookie_path)
        driver.get(r"https://www.zhihu.com/")
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.ID, "Popover15-toggle")
        )
        toggle = driver.find_element(By.ID, "Popover15-toggle")
    except Exception as e:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
            print("浏览器cookie失效了，删除了之前的cookie，需要再次登录并保存cookie。")
        else:
            print("需要登陆并保存cookie，下次就不用登录了。")
        driver = login(driver)
        save_cookie(driver, cookie_path)
        print(f"cookie保存好了的放在了：{cookie_path}")
        time.sleep(3)

    try:
        driver.find_element(By.ID, "Popover15-toggle").click()
        driver.find_element(By.CLASS_NAME, "Menu-item").click()
    except:
        time.sleep(6)
        driver.get(r"https://www.zhihu.com/")
        time.sleep(3)
        driver.find_element(By.ID, "Popover15-toggle").click()
        driver.find_element(By.CLASS_NAME, "Menu-item").click()
    url = driver.current_url
    username = url.split("/")[-1]
    return driver, username
