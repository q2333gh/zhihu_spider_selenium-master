from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver import EdgeOptions
import os
import sys
import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile
import platform
import shutil


def downloaddriver(abspath):
    """下载Edge驱动程序"""
    driverpath = (
        os.path.join(abspath, "msedgedriver" + os.sep + "msedgedriver.exe")
        if sys.platform == "win32"
        else os.path.join(abspath, "msedgedriver" + os.sep + "msedgedriver")
    )

    url = "https://msedgedriver.azureedge.net/116.0.1938.62/edgedriver_win64.zip"
    if not os.path.exists(driverpath):
        ret = requests.get(
            "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
        )
        if ret.status_code != 200:
            assert ret.status_code != 200
        ret = BeautifulSoup(ret.content, "html.parser")
        ddl = ret.find_all("a")
        name = "msedgedriver.exe"
        for k in ddl:
            key = k.attrs.keys()
            if "href" not in key:
                continue
            href = k.attrs["href"]
            if "darwin" not in sys.platform:
                if "href" in key and "win64" in href and ".zip" in href:
                    url = href
                    break
            elif "darwin" in sys.platform and "arm" not in platform.processor():
                if (
                    "href" in key
                    and "mac64" in href
                    and "m1" not in href
                    and ".zip" in href
                ):
                    url = href
                    name = "msedgedriver"
                    break
            elif "darwin" in sys.platform and "arm" in platform.processor():
                if "href" in key and "mac64_m1" in href and ".zip" in href:
                    url = href
                    name = "msedgedriver"
                    break
        response = requests.get(url)
        if response.status_code == 200:
            with open(
                os.path.join(abspath, "msedgedriver/edgedriver.zip"), "wb"
            ) as obj:
                obj.write(response.content)
            with ZipFile(
                os.path.join(abspath, "msedgedriver/edgedriver.zip"), "r"
            ) as obj:
                obj.extractall(os.path.join(abspath, "msedgedriver"))
            nth = os.path.join(abspath, "msedgedriver")
            for r, d, f in os.walk(nth):
                kk = 6
                for i in f:
                    if "driver" in i and ".zip" not in i:
                        try:
                            shutil.move(os.path.join(r, i), os.path.join(nth, i))
                        except:
                            pass
                        os.rename(os.path.join(nth, i), os.path.join(nth, name))
                        if "darwin" in sys.platform:
                            print(
                                f"\n\n请执行权限操作再继续执行：\nchmod +x {os.path.join(nth, name)}\n"
                            )
                            exit(0)
                        kk = -6
                        break
                if kk < 0:
                    break
    return driverpath


def edgeopen(driverpath):
    """初始化并返回Edge WebDriver实例"""
    service = Service(executable_path=driverpath)
    edge_options = EdgeOptions()

    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option("useAutomationExtension", False)
    edge_options.add_argument("lang=zh-CN,zh,zh-TW,en-US,en")
    edge_options.add_argument(
        "disable-blink-features=AutomationControlled"
    )  # 就是这一行告诉chrome去掉了webdriver痕迹

    edge_options.page_load_strategy = "normal"

    driver = webdriver.Edge(options=edge_options, service=service)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36"
        },
    )
    driver.set_script_timeout(20)

    return driver
