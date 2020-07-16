# coding: utf-8

import time
import json
import random
import requests
import smtplib

from email.utils import formataddr
from email.header import Header
from email.mime.text import MIMEText
from scrapy.selector import Selector


def get_goods_id(filename):
    goods_id = set()
    for line in open(filename, "r"):
        if line.strip():
            goods_id.add(line.strip())
    return goods_id


def get_goods_user_info(filename):
    f = open(filename, 'r')
    content = f.read()
    content = json.loads(content)

    goods_user_dict = {}
    for user, goods_ids in content.items():
        for goods_id in goods_ids:
            if goods_id not in goods_user_dict.keys():
                goods_user_dict[goods_id] = set()
            goods_user_dict[goods_id].add(user)
    return goods_user_dict


def get_goods_id2(filename):
    goods_ids_list = set()
    f = open(filename, 'r')
    content = f.read()
    content = json.loads(content)
    for user, goods_ids in content.items():
        for goods_id in goods_ids:
            if goods_id not in goods_ids_list:
                goods_ids_list.add(goods_id)
    return goods_ids_list


def get_goods_info(goods_id):
    try:
        # time.sleep(random.random() * 0.5)
        url = "https://m.hndfbg.com/goods/detail?goods_id={0}".format(goods_id)
        r = requests.get(url, timeout=10)
        if r.status_code == requests.codes.ok:
            selector = Selector(response=r)
            title = selector.xpath('//section[@class = "goods-title"]/div/h3/text()').extract_first()
            status = selector.xpath('//a[@class = "btn_sold_out"]/text()').extract_first()
            if not status and title is not None:
                status = '在售'
            return title, url, status
        else:
            print('request url[{0}] failed with return code: [{1}].'.format(url, r.status_code))
            return None, None, None
    except Exception as e:
        print('get goods info failed: [{0}].'.format(e))
        return None, None, None


def get_all_goods_info(goods_ids):
    info = {}
    for goods_id in goods_ids:
        title, url, status = get_goods_info(goods_id)
        if url is not None:
            info[goods_id] = {'title': title, 'url': url, 'status': status}
    return info


def get_old_info():
    f = open('info.txt', 'r')
    content = f.read()
    if not content.strip():
        content = '{}'
    info = json.loads(content)
    return info


def get_config():
    f = open('config.txt', 'r')
    content = f.read()
    config = json.loads(content)
    return config


def send_mail(info, users):
    goods_title = info['title']
    content = str(info)

    from_addr = 'buhuoupdater@163.com'
    # from_addr = 'yizhifight@163.com'    # 邮件发送账号
    # to_addrs = 'wc1148728402@163.com'   # 接收邮件账号
    to_addrs = list(users)
    code = 'SKJKHLBZEBRLUVDM'
    # code = 'MQQAHYSFJKZDZWIE'       # 授权码（这个要填自己获取到的）
    smtp_server = 'smtp.163.com'    # 固定写死
    smtp_port = 465  # 固定端口

    for user in users:
        # 配置服务器
        stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
        stmp.login(from_addr, code)

        i = 0
        while i < 3:
            try:
                # 组装发送内容
                message = MIMEText(content, 'plain')  # 发送的内容
                # message['From'] = from_addr
                message['From'] = formataddr(["海免补货通知", from_addr])
                # message['To'] = ','.join(to_addrs)        # 收件人
                message['To'] = user
                message['Cc'] = from_addr
                subject = goods_title
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, user, message.as_string())
                break
            except Exception as e:
                i = i + 1
                print('send mail[{0}][{1}] failed; [{2}].'.format(info, user, e))
                time.sleep(2)


def save_info(info):
    content = json.dumps(info)
    f = open('info.txt', 'w+', encoding='utf-8')
    f.write(content)
    f.close()


def execute(goods_user_info):
    # goods_user_info = get_goods_user_info('id_user.txt')
    # print('goods user info: [{0}].'.format(goods_user_info))

    goods_ids = list(goods_user_info.keys())
    random.shuffle(goods_ids)
    # goods_ids = get_goods_id('id.txt')
    # print('goods ids: [{0}].'.format(goods_ids))

    old_info = get_old_info()
    # print('old goods info: [{0}].'.format(old_info))

    info = {}
    new_info = {}
    for goods_id in goods_ids:
        title, url, status = get_goods_info(goods_id)
        if url is not None:
            info[goods_id] = {'title': title, 'url': url, 'status': status}     # 获取到新的数据
            if goods_id not in old_info.keys():     # 新的goods id
                new_info[goods_id] = info[goods_id]
                if info[goods_id]['status'] == '在售':    # 在售，需要发送邮件
                    # mail_content = str(info[goods_id])
                    print('new goods info on sale, send mail[{0}] to [{1}].'.format(info[goods_id], goods_user_info[goods_id]))
                    send_mail(info[goods_id], goods_user_info[goods_id])
                else:
                    print('new goods info off sale: [{0}].'.format(info[goods_id]))
            elif info[goods_id]['status'] != old_info[goods_id]['status']:
                new_info[goods_id] = info[goods_id]
                if info[goods_id]['status'] == '在售':
                    # mail_content = str(info[goods_id])
                    print('goods info change to on sale, send mail[{0}] to [{1}].'.format(info[goods_id], goods_user_info[goods_id]))
                    send_mail(info[goods_id], goods_user_info[goods_id])
                else:
                    print('goods info change to off sale: [{0}].'.format(info[goods_id]))
            else:
                if info[goods_id]['status'] == '在售':
                    print('old goods info on sale: [{0}].'.format(info[goods_id]))
                else:
                    pass

    if new_info:
        # print('goods info change, save to file: [{0}].'.format(info))
        save_info(info)
        pass
