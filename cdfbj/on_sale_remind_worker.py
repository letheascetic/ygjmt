# coding: utf-8

import uuid
import time
import json
import config
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

    m_running = True
    id = None
    goods_user_info = None
    user_info_dict = None
    user_status_dict = None
    message_queue = None

    def __init__(self, id, message_queue, goods_user_info, user_info_dict, user_status_dict):
        threading.Thread.__init__(self)
        self.id = id
        self.goods_user_info = goods_user_info
        self.user_info_dict = user_info_dict
        self.user_status_dict = user_status_dict
        self.message_queue = message_queue

    def get_goods_info(self, goods_id):
        goods_info = {'title': None, 'url': None, 'status': None, '库存': None}
        try:
            url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}?regId={1}".format(goods_id, uuid.uuid4())
            header = {'Host': 'mbff.yuegowu.com', 'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
                      'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
                      'Content-Type': 'application/json'}
            r = requests.get(url, timeout=10, headers=header)

            goods_info['url'] = header['Referer']

            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                context = content['context']
                if context is None:
                    goods_info['status'] = '下架'
                    goods_info['库存'] = 0
                else:
                    info = context['goodsInfos'][0]
                    goods_info['库存'] = info['stock']
                    goods_info['title'] = info['goodsInfoName']
                    if goods_info['库存'] > 0:
                        goods_info['status'] = '在售'
                    else:
                        goods_info['status'] = '缺货'
            else:
                logger.info('thread[{0}] request url[{1}] failed with return code: [{2}].'.format(self.id, url, r.status_code))
        except Exception as e:
            logger.exception('thread[{0}] get goods info[{1}] failed: [{2}].'.format(self.id, goods_id, e))
        return goods_info

    def send_mail(self, info, user):
        goods_title = info['title']
        content = str(info)
        user_email = self.user_info_dict[user]['email']
        to_addrs = [user_email]

        sender = random.choice(config.ON_SALE_REMINDER_CONFIG['mail_senders'])
        from_addr, code = sender['email'], sender['code']

        smtp_server = 'smtp.163.com'      # 固定写死
        smtp_port = 465                   # 固定端口

        i = 0
        while i < 3:
            try:
                # 配置服务器
                stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
                stmp.login(from_addr, code)
                # 组装发送内容
                message = MIMEText(content, 'plain')  # 发送的内容
                message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
                message['To'] = ','.join(to_addrs)        # 收件人
                subject = '{0}: 库存{1}-{2}'.format('cdf北京', info['库存'], goods_title)
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                return True
            except Exception as e:
                i = i + 1
                logger.exception('thread[{0}] send mail[{1}] to [{2}] failed; [{3}].'.format(self.id, info, user, e))
                time.sleep(2)
        return False

    def update_query_user_status(self, goods_id, goods_info):
        update_flag = False
        stock = goods_info['库存']
        users = self.goods_user_info.get(goods_id, [])
        mail_users = []
        for user in users:
            # 存库大于等于订阅阈值且还没被通知过，则需要发送邮件
            if stock >= self.user_info_dict[user]['goods'][goods_id] and self.user_status_dict[user][goods_id] is False:
                mail_users.append(user)
                update_flag = True
            # 存库小于订阅阈值且已经被通知过，则变更为待通知状态
            elif stock < self.user_info_dict[user]['goods'][goods_id] and self.user_status_dict[user][goods_id] is True:
                self.user_status_dict[user][goods_id] = False
                update_flag = True
        return update_flag, mail_users

    def save_user_status(self):
        goods_status_file = config.ON_SALE_REMINDER_CONFIG['goods_status_file']
        try:
            content = json.dumps(self.user_status_dict)
            f = open(goods_status_file, 'w', encoding='utf-8')
            f.write(content)
            f.close()
        except Exception as e:
            logger.info('save user status to [{0}] exception: [{1}].'.format(goods_status_file, e))

    def run(self):
        i = 0
        while self.m_running:
            i = i + 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info('thread[{0}] [{1}], start [{2}] times........................'.format(self.id, current_time, i))

            goods_ids = list(self.goods_user_info.keys())
            random.shuffle(goods_ids)

            for goods_id in goods_ids:
                try:
                    goods_info = self.get_goods_info(goods_id)
                    if goods_info['status'] is None:  # 访问失败或出错，直接返回
                        continue

                    logger.info('goods info: [{0}].'.format(goods_info))

                    if goods_info['status'] == '在售':
                        logger.info('goods on sale: [{0}].'.format(goods_info))

                    update_flag, mail_users = self.update_query_user_status(goods_id, goods_info)

                    random.shuffle(mail_users)
                    for user in mail_users:
                        logger.info('goods[{0}] send mail to [{1}].'.format(goods_info, self.user_info_dict[user]))
                        if self.send_mail(goods_info, user):  # 发送成功，用户状态字典中对应的状态变为True
                            self.user_status_dict[user][goods_id] = True

                    if update_flag:
                        self.message_queue.add('user_status_dict')

                    time.sleep(random.random() * 5)
                except Exception as e:
                    logger.exception('process goods[{0}] exception: [{1}].'.format(goods_id, e))

    def stop(self):
        self.m_running = False
