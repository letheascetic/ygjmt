# coding: utf-8

import time
import json
import random
import requests
import smtplib
import logging
import threading

from email.utils import formataddr
from email.header import Header
from email.mime.text import MIMEText
from scrapy.selector import Selector


logger = logging.getLogger(__name__)


class Worker(threading.Thread):

    m_running = 1
    id = None
    goods_user_info = {}

    def __init__(self, id, goods_user_info):
        threading.Thread.__init__(self)
        self.id = id
        self.goods_user_info = goods_user_info

    def get_old_info(self):
        try:
            f = open('info[{0}].txt'.format(self.id), 'r')
            content = f.read()
            if not content.strip():
                content = '{}'
        except Exception as e:
            content = '{}'
        info = json.loads(content)
        return info

    def get_goods_info(self, goods_id):
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
                logger.info('thread[{0}] request url[{1}] failed with return code: [{2}].'.format(self.id ,url, r.status_code))
                return None, None, None
        except Exception as e:
            logger.exception('thread[{0}] get goods info failed: [{1}].'.format(self.id, e))
            return None, None, None

    def send_mail(self, goods_id, info, users):
        goods_title = info['title']
        content = str(info)

        from_addr = 'buhuoupdater@163.com'
        # to_addrs = 'wc1148728402@163.com'   # 接收邮件账号

        code = 'SKJKHLBZEBRLUVDM'
        smtp_server = 'smtp.163.com'  # 固定写死
        smtp_port = 465  # 固定端口

        users_list = list(users)
        random.shuffle(users_list)
        user_count = len(users_list)
        n = 0
        while n < user_count:
            to_addrs = users_list[n:n+1]
            n = n+1
            i = 0
            while i < 3:
                try:
                    # 配置服务器
                    stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
                    stmp.login(from_addr, code)
                    # 组装发送内容
                    message = MIMEText(content, 'plain')  # 发送的内容
                    # message['From'] = from_addr
                    message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
                    message['To'] = ','.join(to_addrs)        # 收件人
                    # message['To'] = user
                    # message['Cc'] = from_addr
                    subject = '{0}-{1}'.format('海免补货', goods_title)
                    message['Subject'] = Header(subject)  # 邮件标题
                    stmp.sendmail(from_addr, to_addrs, message.as_string())
                    break
                except Exception as e:
                    i = i + 1
                    logger.exception('thread[{0}] send mail[{1}][{2}] failed; [{3}].'.format(self.id, info, users, e))
                    time.sleep(2)

    def save_info(self, info):
        content = json.dumps(info)
        f = open('info[{0}].txt'.format(self.id), 'w', encoding='utf-8')
        f.write(content)
        f.close()

    def run(self):
        i = 0
        while self.m_running:
            i = i + 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info('thread[{0}] [{1}], start [{2}] times........................................................................'.format(self.id, current_time, i))

            goods_ids = list(self.goods_user_info.keys())
            random.shuffle(goods_ids)

            old_info = self.get_old_info()

            info = {}
            new_info = {}
            for goods_id in goods_ids:
                title, url, status = self.get_goods_info(goods_id)
                if url is not None:
                    info[goods_id] = {'title': title, 'url': url, 'status': status}  # 获取到新的数据
                    # self.send_mail(goods_id, info[goods_id], {'yizhifight@163.com', 'letheascetic@163.com'})
                    if goods_id not in old_info.keys():     # 新的goods id
                        new_info[goods_id] = info[goods_id]
                        if info[goods_id]['status'] == '在售':  # 在售，需要发送邮件
                            logger.info('thread[{0}] new goods info on sale, send mail[{1}] to [{2}].'.format(
                                self.id, [goods_id], self.goods_user_info[goods_id]))
                            self.send_mail(goods_id, info[goods_id], self.goods_user_info[goods_id])
                        else:
                            logger.info('thread[{0}] new goods info off sale: [{1}].'.format(self.id, info[goods_id]))
                    elif info[goods_id]['status'] != old_info[goods_id]['status']:
                        new_info[goods_id] = info[goods_id]
                        if info[goods_id]['status'] == '在售':
                            logger.info('thread[{0}] goods info change to on sale, send mail[{1}] to [{2}].'.format(
                                self.id, info[goods_id], self.goods_user_info[goods_id]))
                            self.send_mail(goods_id, info[goods_id], self.goods_user_info[goods_id])
                        else:
                            logger.info('thread[{0}] goods info change to off sale: [{1}].'.format(self.id, info[goods_id]))
                    else:
                        if info[goods_id]['status'] == '在售':
                            logger.info('thread[{0}] old goods info on sale: [{1}].'.format(self.id, info[goods_id]))
                        else:
                            pass

            if new_info:
                # logger.info('goods info change, save to file: [{0}].'.format(info))
                self.save_info(info)
                pass

    def stop(self):
        self.m_running = 0
