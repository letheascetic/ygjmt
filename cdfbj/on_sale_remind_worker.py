# coding: utf-8

import time
import json
import random
import requests
import smtplib
import logging
import threading

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class Worker(threading.Thread):

    m_running = 1
    id = None
    goods_user_info = None
    user_info_dict = None
    goods_status_dict = None

    def __init__(self, id, goods_user_info, user_info_dict, goods_status_dict):
        threading.Thread.__init__(self)
        self.id = id
        self.goods_user_info = goods_user_info
        self.user_info_dict = user_info_dict
        self.goods_status_dict = goods_status_dict

    def get_goods_info(self, goods_id):
        try:
            url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}".format(goods_id)
            header = {'Host': 'mbff.yuegowu.com', 'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
                      'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
                      'Content-Type': 'application/json'}

            r = requests.get(url, timeout=10, headers=header)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                context = content['context']
                if context is None:
                    status = '下架'
                    return None, None, None, None
                else:
                    info = context['goodsInfos'][0]
                    stock = info['stock']
                    title = info['goodsInfoName']
                    if stock > 0:
                        status = '在售'
                    else:
                        status = '缺货'
                    return title, header['Referer'], stock, status
            else:
                logger.info('thread[{0}] request url[{1}] failed with return code: [{2}].'.format(self.id ,url, r.status_code))
                return None, None, None, None
        except Exception as e:
            logger.exception('thread[{0}] get goods info[{1}] failed: [{2}].'.format(self.id, goods_id, e))
            return None, None, None, None

    def send_mail(self, info, users):
        goods_title = info['title']
        content = str(info)

        from_addr = 'cdf_bj_updater@163.com'

        to_addrs = list(users)
        random.shuffle(to_addrs)

        code = 'ZYMXQVJTZRVBEJMS'
        # code = 'MQQAHYSFJKZDZWIE'       # 授权码（这个要填自己获取到的）
        smtp_server = 'smtp.163.com'  # 固定写死
        smtp_port = 465  # 固定端口

        users_list = list(users)
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
                    subject = '{0}: 库存{1}-{2}'.format('cdf北京', info['库存'], goods_title)
                    message['Subject'] = Header(subject)  # 邮件标题
                    stmp.sendmail(from_addr, to_addrs, message.as_string())
                    break
                except Exception as e:
                    i = i + 1
                    logger.exception('thread[{0}] send mail[{1}][{2}] failed; [{3}].'.format(self.id, info, users, e))
                    time.sleep(2)

    def run(self):
        i = 0
        while self.m_running:
            i = i + 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info('thread[{0}] [{1}], start [{2}] times........................'.format(self.id, current_time, i))

            goods_ids = list(self.goods_user_info.keys())
            random.shuffle(goods_ids)

            info = {}
            new_info = {}
            for goods_id in goods_ids:
                title, url, stock, status = self.get_goods_info(goods_id)
                if url is not None:
                    info[goods_id] = {'title': title, 'url': url, 'status': status, '库存': stock}    # 获取到新的数据
                    # self.send_mail(info[goods_id], {'yizhifight@163.com', 'letheascetic@163.com', 'wc1148728402@163.com'})
                    if goods_id not in old_info.keys():     # 新的goods id
                        new_info[goods_id] = info[goods_id]
                        if info[goods_id]['status'] == '在售':  # 在售，需要发送邮件
                            logger.info('thread[{0}] new goods info on sale, send mail[{1}] to [{2}].'.format(
                                self.id, info[goods_id], self.goods_user_info[goods_id]))
                            self.send_mail(info[goods_id], self.goods_user_info[goods_id])
                        else:
                            logger.info('thread[{0}] new goods info off sale: [{1}].'.format(self.id, info[goods_id]))
                    elif info[goods_id]['status'] != old_info[goods_id]['status']:
                        new_info[goods_id] = info[goods_id]
                        if info[goods_id]['status'] == '在售':
                            logger.info('thread[{0}] goods info change to on sale, send mail[{1}] to [{2}].'.format(
                                self.id, info[goods_id], self.goods_user_info[goods_id]))
                            self.send_mail(info[goods_id], self.goods_user_info[goods_id])
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
