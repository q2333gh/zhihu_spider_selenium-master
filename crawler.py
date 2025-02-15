#################
###ZouJiu-202306
#################
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver import EdgeOptions
import os
from selenium.webdriver.common.by import By
import time
import pickle
import json
from selenium.webdriver.support.wait import WebDriverWait
import requests
from copy import deepcopy
import argparse
from datetime import datetime

# from selenium.webdriver.common import keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin

# import numpy as np
import shutil

# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.print_page_options import PrintOptions

# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
import base64
from zipfile import ZipFile
from bs4 import BeautifulSoup
import re
import platform

abspath = os.path.abspath(__file__)
filename = abspath.split(os.sep)[-1]
abspath = abspath.replace(filename, "")

import sys

sys.path.append(abspath)
sys.path.append(os.path.join(abspath, "../../my_lib"))

from my_lib.thinkdeal import *
from my_lib.driver_utils import downloaddriver, edgeopen
from my_lib.login_utils import login_loadsavecookie
from my_lib.time_utils import now, nowtime, crawlsleep


def get_max_pages(driver):
    """获取分页的最大页数"""
    try:
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CLASS_NAME, "Pagination")
        )
        pages = driver.find_elements(By.CLASS_NAME, "PaginationButton")[-2]
        assert isinstance(int(pages.text), int)
        maxpages = int(pages.text)
    except:
        pages = driver.find_elements(By.CLASS_NAME, "PaginationButton")
        if len(pages) == 0:
            maxpages = 1
        else:
            pages = pages[-2]
            assert isinstance(int(pages.text), int)
            maxpages = int(pages.text)
    return maxpages


def save_links_to_file(links, filepath):
    """保存链接到文件"""
    with open(filepath, "w", encoding="utf-8") as obj:
        for link_data in links:
            if isinstance(link_data, tuple):
                obj.write(f"{link_data[0]} {link_data[1]}\n")
            else:
                obj.write(f"{link_data}\n")


def crawl_paginated_content(driver, base_url, page_url, extract_items_func):
    """通用的分页内容爬取函数

    Args:
        driver: webdriver实例
        base_url: 基础URL
        page_url: 分页URL模板
        extract_items_func: 提取每页项目的函数
    """
    driver.get(base_url)
    maxpages = get_max_pages(driver)

    all_items = []
    for p in range(1, maxpages + 1):
        driver.get(page_url + str(p))
        items = extract_items_func(driver)
        all_items.extend(items)
        crawlsleep(sleeptime)

    return all_items


def crawl_article_links(driver: webdriver, username: str):
    def extract_articles(driver):
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CLASS_NAME, "ArticleItem")
        )
        items = driver.find_elements(By.CLASS_NAME, "ArticleItem")
        page_items = {}
        for a in items:
            introduce = a.get_attribute("data-zop")
            itemId = json.loads(introduce)
            links = a.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
            title = str(itemId["title"]).strip()
            page_items[str(title)] = links
        return [(v, k) for k, v in page_items.items()]

    base_url = f"https://www.zhihu.com/people/{username}/posts"
    page_url = f"https://www.zhihu.com/people/{username}/posts?page="

    all_items = crawl_paginated_content(driver, base_url, page_url, extract_articles)
    save_links_to_file(all_items, os.path.join(articledir, "article.txt"))


def crawl_answers_links(driver: webdriver, username: str):
    def extract_answers(driver):
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CLASS_NAME, "Pagination")
        )
        items = driver.find_elements(By.CLASS_NAME, "AnswerItem")
        page_items = []
        for i in items:
            introduce = i.get_attribute("data-zop")
            itemId = json.loads(introduce)
            links = i.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
            title = str(itemId["title"])
            page_items.append((links, title))
        return page_items

    base_url = f"https://www.zhihu.com/people/{username}/answers"
    page_url = f"https://www.zhihu.com/people/{username}/answers?page="

    all_items = crawl_paginated_content(driver, base_url, page_url, extract_answers)
    save_links_to_file(all_items, os.path.join(answerdir, "answers.txt"))


def crawl_think_links(driver: webdriver, username: str):
    # crawl think links
    think = f"https://www.zhihu.com/people/{username}/pins"
    think_one = f"https://www.zhihu.com/people/{username}/pins?page="

    driver.get(think)
    try:
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CLASS_NAME, "Pagination")
        )
        pages = driver.find_elements(By.CLASS_NAME, "PaginationButton")[-2]
        assert isinstance(int(pages.text), int)
        maxpages = int(pages.text)
    except:
        pages = driver.find_elements(By.CLASS_NAME, "PaginationButton")
        if len(pages) == 0:
            maxpages = 1
        else:
            pages = pages[-2]
            assert isinstance(int(pages.text), int)
            maxpages = int(pages.text)

    # all_think_detail = []
    # how many pages of think
    allbegin = now()
    numberpage = 1e-6
    for p in range(1, maxpages + 1):
        driver.get(think_one + str(p))
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CLASS_NAME, "Pagination")
        )
        items = driver.find_elements(By.CLASS_NAME, "PinItem")
        # crawl answer one by one
        for i in range(len(items)):
            begin = now()
            RichContent = items[i].find_element(By.CLASS_NAME, "RichContent-inner")
            clockitem = items[i].find_element(By.CLASS_NAME, "ContentItem-time")
            try:
                WebDriverWait(items[i], timeout=10).until(lambda d: len(d.text) > 2)
            except:
                driver.get(think_one + str(p))
                WebDriverWait(driver, timeout=10).until(
                    lambda d: d.find_element(By.CLASS_NAME, "Pagination")
                )
                items = driver.find_elements(By.CLASS_NAME, "PinItem")
                RichContent = items[i].find_element(By.CLASS_NAME, "RichContent-inner")
                clockitem = items[i].find_element(By.CLASS_NAME, "ContentItem-time")
                WebDriverWait(items[i], timeout=10).until(lambda d: len(d.text) > 2)
            # clockspan = clockitem.find_element(By.TAG_NAME, 'span')
            clock = clockitem.text
            clock = clock[3 + 1 :].replace(":", "_")
            dirthink = os.path.join(thinkdir, clock)
            if os.path.exists(dirthink):
                print(f"{dirthink}已经爬取过了，不再重复爬取")
                continue
            os.makedirs(dirthink, exist_ok=True)
            try:
                RichContent.find_element(By.CLASS_NAME, "Button").click()
                WebDriverWait(items[i], timeout=10).until(
                    lambda d: d.find_element(By.CLASS_NAME, "RichContent-inner")
                )
                RichContent = items[i].find_element(By.CLASS_NAME, "RichContent-inner")
            except:
                pass
            content = RichContent.find_element(By.CLASS_NAME, "RichText")
            links_col = content.find_elements(By.TAG_NAME, "a")
            links = []
            for itext in links_col:
                try:
                    links.append(itext.get_attribute("href"))
                except:
                    continue
            text = content.text.strip()
            if len(text) != 0:
                with open(
                    os.path.join(dirthink, clock + ".txt"), "w", encoding="utf-8"
                ) as obj:
                    obj.write(
                        text.replace("<br>", "\n").replace(
                            '<br data-first-child="">', "\n"
                        )
                        + "\n"
                    )
                    for itext in links:
                        obj.write(itext + "\n")
                    # all_think_detail.append([text])
            try:
                items[i].find_elements(By.CLASS_NAME, "Image-PreviewVague")[0].click()
            except:
                continue
            cnt = 0
            while True:
                WebDriverWait(driver, timeout=10).until(
                    lambda d: d.find_element(By.CLASS_NAME, "ImageGallery-Inner")
                )
                img = driver.find_element(
                    By.CLASS_NAME, "ImageGallery-Inner"
                ).find_element(By.TAG_NAME, "img")
                imglink = img.get_attribute("data-original")
                if imglink == None:
                    imglink = img.get_attribute("src")
                try:
                    response = requests.get(imglink, timeout=30)
                except:
                    try:
                        response = requests.get(imglink, timeout=30)
                    except:
                        continue
                if response.status_code == 200:
                    with open(
                        os.path.join(dirthink, clock + "_" + str(cnt) + ".jpg"), "wb"
                    ) as obj:
                        obj.write(response.content)
                    cnt += 1
                    crawlsleep(sleeptime)
                try:
                    disable = driver.find_element(
                        By.CLASS_NAME, "ImageGallery-arrow-right"
                    )
                    if "disabled" in disable.get_attribute("class"):
                        driver.find_element(By.CLASS_NAME, "ImageGallery-close").click()
                        break
                    else:
                        disable.click()
                except:
                    break
            crawlsleep(sleeptime)
            end = now()
            print("爬取一篇想法耗时：", clock, round(end - begin, 3))
            logfp.write(
                "爬取一篇想法耗时：" + clock + " " + str(round(end - begin, 3)) + "\n"
            )
        numberpage += 1
        # crawlsleep(600)
    allend = now()
    print("平均爬取一篇想法耗时：", round((allend - allbegin) / numberpage, 3))
    logfp.write(
        "平均爬取一篇想法耗时："
        + str(round((allend - allbegin) / numberpage, 3))
        + "\n"
    )

    dealthink(thinkdir)


def cleartxt(kkk):
    while " " in kkk:
        kkk = kkk.replace(" ", "")
    while "\n" in kkk:
        kkk = kkk.replace("\n", "")
    return kkk


def parser_beautiful(innerHTML, article, number, dircrea, bk=False):
    if not innerHTML:
        return article, number
    # if bk:
    #     article += "**"
    if isinstance(innerHTML, str):
        article += innerHTML.text
        return article, number

    inname = innerHTML.name
    allchild = [i for i in innerHTML.children]
    for idk, chi in enumerate(innerHTML.children):
        # article, number = parser_beautiful(chi, article, number, dircrea, bk)
        tag_name = chi.name
        if isinstance(chi, str):
            article += chi.text
            continue
        else:
            cll = [c for c in chi.children]
        # if tag_name in ['table', 'tbody', 'tr', 'td', 'u', 'em']:
        if tag_name in ["table", "tbody", "tr", "td", "u", "article", "pre", "ul"]:
            article, number = parser_beautiful(chi, article, number, dircrea, bk)
        elif tag_name == "li":
            # article += "\n* "
            art, _ = parser_beautiful(chi, "", 0, dircrea, bk)
            article += "\n* " + art + "\n"
        elif tag_name == "em":
            article += " *" + chi.text + "* "
        elif tag_name == "br":
            article += "\n"
        elif tag_name == "blockquote":
            if len(cll) > 1:
                art, _ = parser_beautiful(chi, "", 0, dircrea, True)
                art = re.sub(r"\n\n+", "\n", art)
                article += "\n>" + art + "\n"
            else:
                article += "\n>" + chi.text + "\n"
        elif tag_name == "br":
            if inname == "p" and tag_name == "br":
                kk = list(innerHTML.children)
                if len(kk) >= 2 and kk[1].name == "a":
                    linksite = None
                    title = None
                    if "href" in kk[1].attrs.keys():
                        linksite = kk[1].attrs["href"]
                    if "title" in kk[1].attrs.keys():
                        title = kk[1].attrs["title"]
                    if linksite and title:
                        article += f"[{title}]({linksite})\n\n"
                    break
            article += "\n"
        elif tag_name == "p":
            article, number = parser_beautiful(chi, article, number, dircrea, bk)
            article += "\n\n"
        # elif tag_name=="br":
        #     article += "<br>\n"
        elif tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            article += "#" * int(tag_name[-1]) + " "
            article, number = parser_beautiful(chi, article, number, dircrea, bk)
            article += "\n\n"
        elif tag_name == "span":
            datatex = None
            classc = None
            if "data-tex" in chi.attrs.keys():
                datatex = chi.attrs["data-tex"]
            if "class" in chi.attrs.keys():
                classc = chi.attrs["class"]
            if datatex and classc and "ztext-math" in classc:
                content = chi.attrs["data-tex"]
                while len(content) > 0 and " " == content[0]:
                    content = content[1:]
                while len(content) > 0 and " " == content[-1]:
                    content = content[:-1]
                if len(content) > 0:
                    if article[-3 - 1 :] == "<br>" or article[-1:] == "\n":
                        article += "\n$" + content + "$"
                    else:
                        article += "$" + content + "$"
            else:
                article, number = parser_beautiful(chi, article, number, dircrea, bk)
                # article += nod.text
        elif tag_name == "u":
            article, number = parser_beautiful(chi, article, number, dircrea, bk)
        elif tag_name == "a":
            linksite = None
            if "href" in chi.attrs.keys():
                linksite = chi.attrs["href"]
            if linksite:
                linksite = linksite.replace(
                    "//link.zhihu.com/?target=https%3A", ""
                ).replace("//link.zhihu.com/?target=http%3A", "")
                ar, _ = parser_beautiful(chi, "", 0, dircrea, False)
                if len(article) > 0 and article[-1] == "\n":
                    article += "[" + ar + "]" + "(" + linksite + ")"
                elif len(article) > 0 and article[-1] not in ["\n", " "]:
                    article += " [" + ar + "]" + "(" + linksite + ")"
                else:
                    article += "\n\n[" + ar + "]" + "(" + linksite + ")"
            if idk != len(allchild) - 1 and allchild[idk + 1].name == "a":
                article += "\n\n"
        elif tag_name == "b" or tag_name == "strong":
            if len(cll) > 1:
                art, _ = parser_beautiful(chi, "", 0, dircrea, False)
                article += "**" + art + "**"
            else:
                txt = chi.text
                while len(txt) > 0 and txt[-1] == " ":
                    txt = txt[:-1]
                article += " **" + txt + "** "
        elif tag_name == "figure":
            noscript = chi.find_all("noscript")
            if len(noscript) > 0:
                chi.noscript.extract()
            imgchunk = chi.find_all("img")
            for i in range(len(imgchunk)):
                imglink = None
                if "data-original" in imgchunk[i].attrs.keys():
                    imglink = imgchunk[i].attrs["data-original"]

                if "data-actualsrc" in imgchunk[i].attrs.keys():
                    imglink = imgchunk[i].attrs["data-actualsrc"]

                if imglink == None:
                    imglink = imgchunk[i].attrs["src"]
                try:
                    response = requests.get(imglink, timeout=30)
                except:
                    try:
                        response = requests.get(imglink, timeout=30)
                    except:
                        continue
                if response.status_code == 200:
                    article += """ <img src="%d.jpg" width="100%%"/> \n\n""" % number
                    # article += '''<img src="%d.jpg"/>'''%number
                    with open(os.path.join(dircrea, str(number) + ".jpg"), "wb") as obj:
                        obj.write(response.content)
                    number += 1
                    crawlsleep(sleeptime)
        elif tag_name == "div":
            prenode = chi.find_all("code")
            if len(prenode) > 0:
                for i in prenode:
                    language = "text"
                    if "class" in i.attrs.keys():
                        lan = i.attrs["class"]
                        if len(lan) > 0:
                            if "language-" in lan[0]:
                                language = lan[0].split("-")[-1]
                    article += "\n\n```%s []\n" % language + i.text + "\n```\n\n"
            else:
                article, number = parser_beautiful(chi, article, number, dircrea, bk)
                article += "\n\n"
    # if bk:
    #     article += "**"
    article = article.replace("\n\n\n\n\n", "\n\n")
    article = article.replace("\n\n\n\n", "\n\n")
    article = article.replace("\n\n\n", "\n\n")
    return article, number


def recursion(nod, article, number, driver, dircrea, bk=False):
    if isinstance(nod, dict):
        if "nodeName" in nod.keys() and nod["nodeName"] == "#text":
            kkk = cleartxt(nod["textContent"])
            if len(kkk) > 0:
                if bk:
                    article += "**"
                article += nod["textContent"]
                if bk:
                    article += "**"
            return article, number

    elif isinstance(nod, webdriver.remote.webelement.WebElement):
        tag_name = nod.tag_name
        if tag_name == "br":
            article += "<br>\n"
        elif tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            article += "\n" + "#" * int(tag_name[-1]) + " "
            try:
                p_childNodes = driver.execute_script(
                    "return arguments[0].childNodes;", nod
                )
                for pnode in p_childNodes:
                    article, number = recursion(
                        pnode, article, number, driver, dircrea, bk
                    )
            except:
                pass
            article += "\n"
        elif tag_name == "span":
            datatex = nod.get_attribute("data-tex")
            classc = nod.get_attribute("class")
            if datatex and classc and "ztext-math" in classc:
                if article[-3 - 1 :] == "<br>" or article[-1:] == "\n":
                    article += "\n$" + nod.get_attribute("data-tex") + "$"
                else:
                    article += "$" + nod.get_attribute("data-tex") + "$"
            else:
                imgchunk = nod.find_elements(By.TAG_NAME, "img")
                achunk = nod.find_elements(By.TAG_NAME, "a")
                if len(imgchunk) == 0 and len(achunk) == 0:
                    if bk:
                        article += "**"
                    article += nod.text
                    if bk:
                        article += "**"
                else:
                    p_childNodes = driver.execute_script(
                        "return arguments[0].childNodes;", nod
                    )
                    for pnode in p_childNodes:
                        article, number = recursion(
                            pnode, article, number, driver, dircrea, bk
                        )
        elif tag_name == "a":
            linksite = nod.get_attribute("href")
            if linksite:
                linksite = linksite.replace(
                    "//link.zhihu.com/?target=https%3A", ""
                ).replace("//link.zhihu.com/?target=http%3A", "")
                if article[-3 - 1 :] == "<br>" or article[-1:] == "\n":
                    article += "\n\n[" + nod.text + "]" + "(" + linksite + ")"
                else:
                    article += "[" + nod.text + "]" + "(" + linksite + ")"
        elif tag_name == "b" or tag_name == "strong":
            try:
                p_childNodes = driver.execute_script(
                    "return arguments[0].childNodes;", nod
                )
                for pnode in p_childNodes:
                    article, number = recursion(
                        pnode, article, number, driver, dircrea, True
                    )
            except:
                txt = nod.text
                while len(txt) > 0 and txt[-1] == " ":
                    txt = txt[:-1]
                article += " **" + txt + "** "
        elif tag_name == "em":
            if bk:
                article += "**"
            article += nod.text
            if bk:
                article += "**"
        elif tag_name in ["table", "tbody", "tr", "td", "u"]:
            p_childNodes = driver.execute_script("return arguments[0].childNodes;", nod)
            for pnode in p_childNodes:
                article, number = recursion(pnode, article, number, driver, dircrea, bk)
        elif tag_name == "p":
            try:
                p_childNodes = driver.execute_script(
                    "return arguments[0].childNodes;", nod
                )
                for pnode in p_childNodes:
                    article, number = recursion(
                        pnode, article, number, driver, dircrea, bk
                    )
            except:
                article += nod.text
            article += "\n"
        elif tag_name == "div":
            prenode = nod.find_elements(By.TAG_NAME, "code")
            if len(prenode) > 0:
                for i in prenode:
                    article += "<br>\n```\n" + i.text + "\n```\n<br>"
            else:
                p_childNodes = driver.execute_script(
                    "return arguments[0].childNodes;", nod
                )
                for pnode in p_childNodes:
                    article, number = recursion(
                        pnode, article, number, driver, dircrea, bk
                    )
        elif tag_name == "figure":
            imgchunk = nod.find_elements(By.TAG_NAME, "img")
            for i in range(len(imgchunk)):
                imglink = imgchunk[i].get_attribute("data-original")
                if imglink == None:
                    imglink = imgchunk[i].get_attribute("src")
                try:
                    response = requests.get(imglink, timeout=30)
                except:
                    try:
                        response = requests.get(imglink, timeout=30)
                    except:
                        continue
                if response.status_code == 200:
                    article += """ <img src="%d.jpg" width="100%%"/> """ % number
                    with open(os.path.join(dircrea, str(number) + ".jpg"), "wb") as obj:
                        obj.write(response.content)
                    number += 1
                    crawlsleep(sleeptime)
    return article, number


def scroll_page_for_pdf(driver, content_class=None):
    """专门为PDF生成滚动页面以加载所有内容"""
    if content_class:
        scroll_height = driver.execute_script(
            f"""return document.getElementsByClassName("{content_class}")[0].scrollHeight"""
        )
    else:
        scroll_height = driver.execute_script(
            """return document.documentElement.scrollHeight"""
        )

    footer = driver.find_element(By.TAG_NAME, "html")
    scroll_origin = ScrollOrigin.from_element(
        footer, 0, -60 if not content_class else 0
    )
    ActionChains(driver).scroll_from_origin(scroll_origin, 0, -100000).perform()

    for i in range(18):
        try:
            ActionChains(driver).scroll_from_origin(
                scroll_origin, 0, scroll_height // 18
            ).perform()
        except:
            try:
                ActionChains(driver).scroll_from_origin(
                    scroll_origin, 0, -scroll_height // 18
                ).perform()
            except:
                pass
        crawlsleep(0.8)


def prepare_page_for_pdf(driver, url, content_type):
    """准备页面用于PDF生成"""
    # 滚动页面加载所有内容
    scroll_page_for_pdf(driver)

    # 移除不需要的元素
    unwanted_elements = (
        ["Post-Sub", "ColumnPageHeader-Wrapper", "RichContent-actions"]
        if content_type == "article"
        else [
            "Post-Sub",
            "ColumnPageHeader-Wrapper",
            "RichContent-actions",
            "QuestionHeader-footer",
        ]
    )
    remove_unwanted_elements(driver, unwanted_elements)

    # 为文章添加URL信息
    if content_type == "article":
        driver.execute_script(
            'const para = document.createElement("h2"); \
            const br = document.createElement("br"); \
            const node = document.createTextNode("%s");\
            para.appendChild(node);\
            const currentDiv = document.getElementsByClassName("Post-Header")[0];\
            currentDiv.appendChild(br); \
            currentDiv.appendChild(para);'
            % url
        )


def crawl_detail(driver, content_type="article"):
    """统一处理文章和回答的爬取逻辑"""
    base_dir = articledir if content_type == "article" else answerdir
    file_name = "article.txt" if content_type == "article" else "answers.txt"
    content_class = (
        "Post-RichText" if content_type == "article" else "RichContent-inner"
    )

    website_col = {}

    # 清理旧的数字命名目录
    for i in os.listdir(base_dir):
        try:
            kk = int(i)
            shutil.rmtree(os.path.join(base_dir, i))
        except:
            pass

    # 读取待爬取的链接
    with open(os.path.join(base_dir, file_name), "r", encoding="utf-8") as obj:
        for line in obj.readlines():
            line = line.strip()
            if not line:
                continue
            ind = line.index(" ")
            website = line[:ind]
            title = line[ind + 1 :].strip()
            if title:
                website_col[website] = title

    allbegin = now()
    numberpage = 1e-6

    for website, title in website_col.items():
        begin = now()

        # 处理文件名
        nam = sanitize_filename(title)
        temp_name = nam

        # 检查是否已经爬取过
        exists, existing_file = check_existing_content(base_dir, nam)
        if exists:
            print(f"{existing_file}已经爬取过了，不再重复爬取")
            continue

        # 创建保存目录
        dircrea = os.path.join(base_dir, temp_name)
        os.makedirs(dircrea, exist_ok=True)

        # 获取页面内容
        driver.get(website)
        if content_type == "article":
            WebDriverWait(driver, timeout=20).until(
                lambda d: d.find_element(By.CLASS_NAME, "Post-Topics")
            )
        else:
            WebDriverWait(driver, timeout=20).until(
                lambda d: d.find_element(By.CLASS_NAME, "QuestionHeader-title")
            )

        Created = ""
        Modified = ""

        if MarkDown_FORMAT:
            # 处理正文内容
            content_element = driver.find_element(By.CLASS_NAME, content_class)
            title_element = driver.find_element(
                By.CLASS_NAME,
                "Post-Title" if content_type == "article" else "QuestionHeader-title",
            )

            article, number = process_content(
                driver,
                content_element,
                dircrea,
                is_question=(content_type != "article"),
            )

            # 添加URL信息
            article += f"<br>\n\n[{driver.current_url}]({driver.current_url})<br>\n"

            # 获取时间信息
            if content_type == "article":
                clocktxt = driver.find_element(
                    By.CLASS_NAME, "Post-NormalMain"
                ).find_element(By.CLASS_NAME, "ContentItem-time")
                Created = clocktxt.text[3 + 1 :].replace(":", "_")
                Modified = ""
            else:
                try:
                    Created = driver.find_element(
                        By.CSS_SELECTOR, "div.ContentItem-time"
                    ).text.split("发布于 ")[1]
                    Modified = driver.find_element(
                        By.CSS_SELECTOR, "div.ContentItem-time>span.ContentItem-time"
                    ).text.split("编辑于 ")[1]
                except:
                    Created = ""
                    Modified = ""

            # 保存Markdown内容
            md_file_path = os.path.join(dircrea, nam[:3] + "_.md")
            save_markdown_content(
                article, title_element.text, md_file_path, Created, Modified
            )

        # 保存PDF
        if SAVE_PDF:
            prepare_page_for_pdf(driver, driver.current_url, content_type)
            pagetopdf(
                driver,
                dircrea,
                temp_name,
                nam,
                base_dir,
                driver.current_url,
                Created=Created if content_type == "article" else "",
            )

        crawlsleep(sleeptime)

        end = now()
        content_type_cn = "文章" if content_type == "article" else "回答"
        print(f"爬取一篇{content_type_cn}耗时：{title} {round(end - begin, 3)}")
        logfp.write(
            f"爬取一篇{content_type_cn}耗时：{title} {str(round(end - begin, 3))}\n"
        )
        numberpage += 1

    allend = now()
    content_type_cn = "文章" if content_type == "article" else "回答"
    print(
        f"平均爬取一篇{content_type_cn}耗时：{round((allend - allbegin) / numberpage, 3)}"
    )
    logfp.write(
        f"平均爬取一篇{content_type_cn}耗时：{str(round((allend - allbegin) / numberpage, 3))}\n"
    )


def crawl_article_detail(driver):
    """爬取文章详情"""
    crawl_detail(driver, content_type="article")


def crawl_answer_detail(driver):
    """爬取回答详情"""
    crawl_detail(driver, content_type="answer")


def pagetopdf(driver, dircrea, temp_name, nam, destdir, url, Created=""):
    fileexit = os.path.exists(os.path.join(dircrea, temp_name + "_.pdf"))
    if fileexit:
        try:
            os.remove(os.path.join(dircrea, temp_name + "_.pdf"))
        except:
            pass

    printop = PrintOptions()
    printop.shrink_to_fit = True
    printop.background = True
    printop.scale = 1.0

    try:
        pdf = driver.print_page(print_options=printop)
        with open(os.path.join(dircrea, nam[:3] + "_.pdf"), "wb") as obj:
            obj.write(base64.b64decode(pdf))
    except:
        with open(os.path.join(dircrea, nam[:3] + "_pdf.txt"), "w") as obj:
            obj.write(
                'the page is too large, can not save, you should save pdf using "Ctrl+P or Ctrl+Shift+P"\n'
            )

    clock = Created
    with open(os.path.join(dircrea, clock + ".txt"), "w", encoding="utf-8") as obj:
        obj.write(clock + "\n")
        obj.write(url)

    clocktmp = clock.split(".")[0].replace("T", "_")
    clock = clocktmp.split("・")[0].replace(" ", "_")
    address = ""
    try:
        address += clocktmp.split("・")[1].replace(" ", "_")
    except:
        pass
    try:
        os.rename(dircrea, os.path.join(destdir, clock + "_" + nam + "_" + address))
    except Exception as e0:
        crawlsleep(3 + addtime)
        try:
            os.rename(dircrea, os.path.join(destdir, clock + "_" + nam + "_" + address))
        except Exception as e1:
            pass


def open_zhihu():
    global driverpath
    website = r"https://www.zhihu.com/signin"

    # login and save cookies of zhihu
    driver = edgeopen(driverpath)
    driver.get(website)
    return driver


def start_crawl():
    global driverpath
    try:
        downloaddriver(abspath)
        driver = open_zhihu()
    except Exception as e:
        if os.path.exists(driverpath):
            os.remove(driverpath)
        downloaddriver(abspath)
        driver = open_zhihu()

    driver, username = login_loadsavecookie(driver, cookie_path)

    # 爬取收藏夹
    if favorite_id:
        crawl_favorite_detail(driver, favorite_id)
        logfp.write(nowtime() + f", 收藏夹 {favorite_id} 爬取已经好了的\n")

    # 爬取想法
    if crawl_think:
        crawl_think_links(driver, username)
        logfp.write(nowtime() + ", 想法爬取已经好了的\n")

    # 爬取文章
    if crawl_article:
        if not os.path.exists(os.path.join(articledir, "article.txt")):
            crawl_article_links(driver, username)
            logfp.write(nowtime() + ", article weblink爬取已经好了的\n")
        else:
            if crawl_links_scratch:
                os.rename(
                    os.path.join(articledir, "article.txt"),
                    os.path.join(articledir, "article_%s.txt" % nowtime()),
                )
                crawl_article_links(driver, username)
                logfp.write(nowtime() + ", article weblink爬取已经好了的\n")
            else:
                pass
        crawl_article_detail(driver)
        logfp.write(nowtime() + ", article爬取已经好了的\n")

    # 爬取回答
    if crawl_answer:
        if not os.path.exists(os.path.join(answerdir, "answers.txt")):
            crawl_answers_links(driver, username)
            logfp.write(nowtime() + ", 回答 weblink爬取已经好了的\n")
        else:
            if crawl_links_scratch:
                os.rename(
                    os.path.join(answerdir, "answers.txt"),
                    os.path.join(answerdir, "answers_%s.txt" % nowtime()),
                )
                crawl_answers_links(driver, username)
                logfp.write(nowtime() + ", 回答 weblink爬取已经好了的\n")
            else:
                pass
        crawl_answer_detail(driver)
        logfp.write(nowtime() + ", 回答爬取已经好了的\n")

    driver.quit()


def sanitize_filename(title, max_length=100):
    """清理并规范化文件名"""
    replacements = {
        ":": "_",
        "?": "_问号_",
        "/": "_",
        "\\": "_",
        '"': "_",
        "*": "_",
        "|": "_",
        "？": "_问号_",
        "！": "_感叹号_",
        "<": "小于",
        ">": "大于",
        "(": "",
        ")": "",
        ",": "_逗号_",
        "，": "_逗号_",
        "   ": "_空格_",
        "  ": "_空格_",
        " ": "_空格_",
        "：": "_冒号_",
        "、": "_顿号_",
    }

    name = title
    for old, new in replacements.items():
        name = name.replace(old, new)

    if len(name) > max_length:
        name = name[:max_length]

    name = name.strip()
    return name


def check_existing_content(base_dir, name):
    """检查内容是否已经存在"""
    for dir_name in os.listdir(base_dir):
        if name in dir_name and os.path.isdir(os.path.join(base_dir, dir_name)):
            dir_path = os.path.join(base_dir, dir_name)
            for file_name in os.listdir(dir_path):
                if file_name.endswith(".pdf"):
                    if os.path.getsize(os.path.join(dir_path, file_name)) > 0:
                        return True, os.path.join(dir_path, file_name)
    return False, None


def scroll_page(driver, content_class=None):
    """滚动页面以加载所有内容"""
    if content_class:
        scroll_height = driver.execute_script(
            f"""return document.getElementsByClassName("{content_class}")[0].scrollHeight"""
        )
    else:
        scroll_height = driver.execute_script(
            """return document.documentElement.scrollHeight"""
        )

    footer = driver.find_element(By.TAG_NAME, "html")
    scroll_origin = ScrollOrigin.from_element(
        footer, 0, -60 if not content_class else 0
    )
    ActionChains(driver).scroll_from_origin(scroll_origin, 0, -100000).perform()

    for i in range(18):
        try:
            ActionChains(driver).scroll_from_origin(
                scroll_origin, 0, scroll_height // 18
            ).perform()
        except:
            try:
                ActionChains(driver).scroll_from_origin(
                    scroll_origin, 0, -scroll_height // 18
                ).perform()
            except:
                pass
        crawlsleep(0.8)


def save_markdown_content(
    content, title, file_path, created_time="", modified_time="", extra_info=""
):
    """保存Markdown格式的内容"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            if content:
                f.write(f"{content}\n\n\n")
            if created_time:
                f.write(f"Created: {created_time}\n")
            if modified_time:
                f.write(f"Modified: {modified_time}\n")
            if extra_info:
                f.write(f"\n{extra_info}\n")
    except:
        # 如果文件名太长，使用截断的文件名
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        shortened_name = file_name[: len(file_name) // 2]
        new_path = os.path.join(dir_path, shortened_name)
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            if content:
                f.write(f"{content}\n\n\n")
            if created_time:
                f.write(f"Created: {created_time}\n")
            if modified_time:
                f.write(f"Modified: {modified_time}\n")
            if extra_info:
                f.write(f"\n{extra_info}\n")


def remove_unwanted_elements(driver, element_classes):
    """移除不需要的页面元素"""
    for class_name in element_classes:
        try:
            driver.execute_script(
                f"""document.getElementsByClassName("{class_name}")[0].remove();"""
            )
        except:
            pass


def process_content(driver, content_element, dir_path, is_question=False):
    """处理内容（文章或回答）"""
    article = ""
    number = 0

    if is_question:
        article += "# question： <br>\n"

    inner = driver.execute_script("return arguments[0].innerHTML;", content_element)
    innerHTML = BeautifulSoup(inner, "html.parser")
    article, number = parser_beautiful(innerHTML, article, number, dir_path)

    # 清理文本
    article = (
        article.replace("修改\n", "")
        .replace("开启赞赏\n", "开启赞赏, ")
        .replace("添加评论\n", "")
        .replace("分享\n", "")
        .replace("收藏\n", "")
        .replace("设置\n", "")
    )

    return article, number


def extract_favorite_items(driver):
    """提取收藏夹中的条目"""
    # 等待内容加载
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_elements(By.CLASS_NAME, "CollectionDetailPageItem")
    )

    items = driver.find_elements(By.CLASS_NAME, "CollectionDetailPageItem")
    page_items = []

    for item in items:
        try:
            # 获取链接和标题
            link_element = item.find_element(By.CSS_SELECTOR, "h2.ContentItem-title a")
            link = link_element.get_attribute("href")
            title = link_element.text.strip()

            if link and title:
                # 判断链接类型
                if "/answer/" in link:
                    page_items.append(("answer", link, title))
                elif "/article/" in link:
                    page_items.append(("article", link, title))
        except:
            continue

    return page_items


def crawl_favorite_links(driver: webdriver, collection_id: str):
    """爬取收藏夹中的链接"""
    base_url = f"https://www.zhihu.com/collection/{collection_id}"
    page_url = f"https://www.zhihu.com/collection/{collection_id}?page="

    # 创建收藏夹目录
    favorite_dir = os.path.join(savepath, f"favorite_{collection_id}")
    os.makedirs(favorite_dir, exist_ok=True)

    # 创建答案和文章子目录
    favorite_answer_dir = os.path.join(favorite_dir, "answers")
    favorite_article_dir = os.path.join(favorite_dir, "articles")
    os.makedirs(favorite_answer_dir, exist_ok=True)
    os.makedirs(favorite_article_dir, exist_ok=True)

    # 爬取所有页面的内容
    driver.get(base_url)
    maxpages = get_max_pages(driver)
    print(f"收藏夹共有 {maxpages} 页内容")

    answer_items = []
    article_items = []

    for p in range(1, maxpages + 1):
        print(f"正在爬取第 {p} 页...")
        driver.get(page_url + str(p))
        items = extract_favorite_items(driver)
        for item_type, link, title in items:
            if item_type == "answer":
                answer_items.append((link, title))
            else:
                article_items.append((link, title))
        crawlsleep(sleeptime)

    # 保存链接到对应文件
    if answer_items:
        print(f"共找到 {len(answer_items)} 个回答")
        save_links_to_file(
            answer_items, os.path.join(favorite_answer_dir, "answers.txt")
        )
    if article_items:
        print(f"共找到 {len(article_items)} 篇文章")
        save_links_to_file(
            article_items, os.path.join(favorite_article_dir, "articles.txt")
        )

    return favorite_answer_dir, favorite_article_dir


def crawl_favorite_detail(driver: webdriver, collection_id: str):
    """爬取收藏夹中的详细内容"""
    global answerdir, articledir

    # 爬取链接
    favorite_answer_dir, favorite_article_dir = crawl_favorite_links(
        driver, collection_id
    )

    # 临时保存原来的目录设置
    original_answer_dir = answerdir
    original_article_dir = articledir

    try:
        # 修改全局目录到收藏夹对应目录
        answerdir = favorite_answer_dir
        articledir = favorite_article_dir

        # 爬取答案内容
        if os.path.exists(os.path.join(favorite_answer_dir, "answers.txt")):
            crawl_answer_detail(driver)

        # 爬取文章内容
        if os.path.exists(os.path.join(favorite_article_dir, "articles.txt")):
            crawl_article_detail(driver)

    finally:
        # 恢复原来的目录设置
        answerdir = original_answer_dir
        articledir = original_article_dir


if __name__ == "__main__":
    from viztracer import VizTracer

    tracer = VizTracer(output_file="./log/zhihu_crawler_trace.json", max_stack_depth=20)
    tracer.start()

    if sys.platform == "win32":
        driverpath = os.path.join(abspath, "msedgedriver" + os.sep + "msedgedriver.exe")
    else:
        driverpath = os.path.join(abspath, "msedgedriver" + os.sep + "msedgedriver")

    # 创建output根目录
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    # 修改所有输出路径到output目录下
    savepath = output_dir
    cookiedir = os.path.join(savepath, "cookie")
    thinkdir = os.path.join(savepath, "think")
    answerdir = os.path.join(savepath, "answer")
    articledir = os.path.join(savepath, "article")
    logdir = os.path.join(savepath, "log")

    # 其他路径保持不变
    logfile = os.path.join(logdir, nowtime() + "_log.txt")
    os.makedirs(cookiedir, exist_ok=True)
    os.makedirs(thinkdir, exist_ok=True)
    os.makedirs(answerdir, exist_ok=True)
    os.makedirs(articledir, exist_ok=True)
    os.makedirs(logdir, exist_ok=True)
    logfp = open(logfile, "w", encoding="utf-8")
    cookie_path = os.path.join(cookiedir, "cookie_zhihu.pkl")

    parser = argparse.ArgumentParser(
        description=r"crawler zhihu.com, 爬取知乎的想法, 回答, 文章, 包括数学公式"
    )
    parser.add_argument(
        "--sleep_time",
        type=float,
        default=1,
        help=r"crawler sleep time during crawling, 爬取时的睡眠时间, 避免给知乎服务器带来太大压力, \
                        可以日间调试好，然后深夜运行爬取人少, 给其他小伙伴更好的用户体验, 避免知乎顺着网线过来找人, 默认: 6s",
    )
    parser.add_argument(
        "--computer_time_sleep",
        type=float,
        default=0,
        help=r"computer running sleep time 默认:0, 电脑运行速度的sleep时间, 默认:0",
    )
    parser.add_argument(
        "--think",
        action="store_true",
        help=r"crawl think, 是否爬取知乎的想法, 已经爬取过的想法不会重复爬取, 所以可以多次爬取断了也没关系",
    )
    parser.add_argument(
        "--answer",
        action="store_true",
        help=r"crawl answer, 是否爬取知乎的回答, 保存到pdf、markdown以及相关图片等，已经爬取过的不会重复爬取，\
                    断了再次爬取的话，可以配置到--links_scratch，事先保存好website",
    )
    parser.add_argument(
        "--article",
        action="store_true",
        help=r"crawl article, 是否爬取知乎的文章, 保存到pdf、markdown以及相关图片等，已经爬取过的不会重复爬取，\
                    断了再次爬取的话，可以配置到--links_scratch，事先保存好website",
    )
    parser.add_argument("--MarkDown", action="store_true", help=r"save MarkDown")
    parser.add_argument(
        "--links_scratch",
        action="store_true",
        help=r"crawl links scratch for answer or article, 是否使用已经保存好的website和title, 否则再次爬取website",
    )
    parser.add_argument(
        "--save_pdf",
        action="store_true",
        help=r"save PDF format, 是否保存PDF格式, 默认不保存",
    )
    parser.add_argument(
        "--favorite",
        type=str,
        help=r"crawl favorite collection by collection id, 爬取指定收藏夹的内容, 例如: 698890579",
    )
    args = parser.parse_args()
    sleeptime = args.sleep_time
    crawl_think = args.think
    crawl_answer = args.answer
    crawl_article = args.article
    crawl_links_scratch = args.links_scratch
    addtime = args.computer_time_sleep
    MarkDown_FORMAT = args.MarkDown
    SAVE_PDF = args.save_pdf
    favorite_id = args.favorite

    try:
        start_crawl()
    finally:
        logfp.close()
        tracer.stop()
        tracer.save()  # 保存性能分析结果

        # python crawler.py --answer --MarkDown --links_scratch
        # performance analysis:
        # python -m viztracer.viewer ./log/zhihu_crawler_trace.json
