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
import auto_order

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class Worker(threading.Thread):

    def __init__(self, id, message_queue, goods_user_info, user_info_dict, user_status_dict, ip_pool):
        threading.Thread.__init__(self)
        self.id = id
        self.m_running = True
        self.goods_user_info = goods_user_info
        self.user_info_dict = user_info_dict
        self.user_status_dict = user_status_dict
        self.message_queue = message_queue
        self.ip_pool = ip_pool
        self.request_statistics = {'total': 0, 'success': 0, 'failed': 0, 'exception': 0, 'total_time_span': 0, 'success_time_span': 0, 'total_avg_time': 0, 'success_avg_time': 0}

    def get_proxy(self, ip_info):
        host = ip_info.get('ip', None)
        port = ip_info.get('port', None)
        proxies = {
            'http': 'http://{0}:{1}'.format(host, port),
            'https': 'https://{0}:{1}'.format(host, port)
        }
        return proxies

    def get_goods_info(self, goods_id, ip_info, proxies):
        goods_info = {'title': None, 'url': None, 'status': None, '库存': None}
        start = time.time()
        try:
            url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}?regId={1}".format(goods_id, uuid.uuid4())
            header = {'Host': 'mbff.yuegowu.com', 'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
                      'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
                      'Content-Type': 'application/json'}

            r = requests.get(url, timeout=5, headers=header, proxies=proxies)

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

                if ip_info['failed_times'] != 0:
                    ip_info['failed_times'] = ip_info['failed_times'] - 1

                self.request_statistics['success'] = self.request_statistics['success'] + 1
                time_span = time.time() - start
                self.request_statistics['success_time_span'] = self.request_statistics['success_time_span'] + time_span
                self.request_statistics['success_avg_time'] = self.request_statistics['success_time_span'] / self.request_statistics['success']

            else:
                logger.info('thread[{0}] request url[{1}] using proxy[{2}] failed with return code: [{3}].'.format(self.id, url, proxies, r.status_code))
                ip_info['failed_times'] = ip_info['failed_times'] + 1

                self.request_statistics['failed'] = self.request_statistics['failed'] + 1
                time_span = time.time() - start

        except Exception as e:
            logger.info('thread[{0}] get goods info[{1}] using proxy[{2}] exception.'.format(self.id, goods_id, proxies))
            ip_info['failed_times'] = ip_info['failed_times'] + 1

            self.request_statistics['exception'] = self.request_statistics['exception'] + 1
            time_span = time.time() - start

        self.request_statistics['total'] = self.request_statistics['total'] + 1
        self.request_statistics['total_time_span'] = self.request_statistics['total_time_span'] + time_span
        self.request_statistics['total_avg_time'] = self.request_statistics['total_time_span'] / self.request_statistics['total']

        return goods_info

    def query_user_status(self, goods_id, goods_info):
        stock = goods_info['库存']
        users = self.goods_user_info.get(goods_id, [])
        mail_users = []
        for user in users:
            # 存库大于等于订阅阈值且还没锁单，加入锁单列表
            if stock >= self.user_info_dict[user]['goods'][goods_id][0] and self.user_status_dict[user][goods_id] > 0:
                if 'login_user' in self.user_info_dict[user].keys() and 'login_password' in self.user_info_dict[user].keys():
                    mail_users.append(user)
        return mail_users

    def send_mail(self, info, user, self_sender=True):
        goods_title = info['title']
        content = '{0}: {1} 锁单成功了,请尽快支付.'.format(self.user_info_dict[user]['wechat'], goods_title)

        user_email = self.user_info_dict[user]['email']
        if self_sender and self.user_info_dict[user]['email_code'] is not None:
            from_addr, code = user_email, self.user_info_dict[user]['email_code']
            to_addrs = [user_email]
        else:
            sender = random.choice(config.AUTO_ORDER_REMINDER_CONFIG['mail_senders'])
            from_addr, code = sender['email'], sender['code']
            to_addrs = [from_addr]

        if '163.com' in from_addr:
            smtp_server = 'smtp.163.com'      # 固定写死
            smtp_port = 465                   # 固定端口
        else:
            smtp_server = 'smtp.qq.com'      # 固定写死
            smtp_port = 465                   # 固定端口

        i = 0
        while i < 2:
            try:
                # 配置服务器
                stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
                stmp.login(from_addr, code)
                # 组装发送内容
                message = MIMEText(content, 'plain')  # 发送的内容
                message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
                message['To'] = ','.join(to_addrs)        # 收件人
                # message['Cc'] = from_addr
                subject = '{0}:{1} 你的{2}锁单成功了'.format('cdf北京', self.user_info_dict[user]['wechat'], goods_title)
                message['Subject'] = Header(subject)  # 邮件标题
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                return True
            except Exception as e:
                i = i + 1
                logger.exception('thread[{0}] send mail[{1}] to [{2}] failed; [{3}].'.format(self.id, info, user, e))
                time.sleep(2)
        return False

    def run(self):
        i = 0
        last_time = time.time()
        while self.m_running:
            i = i + 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info('thread[{0}] [{1}], start [{2}] times........................'.format(self.id, current_time, i))

            goods_ids = list(self.goods_user_info.keys())
            random.shuffle(goods_ids)

            for goods_id in goods_ids:
                try:
                    while len(self.ip_pool) == 0:
                        logger.info('ip pool is empty, waiting.')
                        time.sleep(3)

                    ip_info = random.choice(self.ip_pool)
                    proxies = self.get_proxy(ip_info)

                    goods_info = self.get_goods_info(goods_id, ip_info, proxies)
                    if goods_info['status'] is None:  # 访问失败或出错，直接返回
                        continue

                    # logger.info('goods info: [{0}].'.format(goods_info))

                    if goods_info['status'] == '在售':
                        logger.info('goods on sale: [{0}].'.format(goods_info))

                    mail_users = self.query_user_status(goods_id, goods_info)

                    while len(mail_users) != 0:
                        user = random.choice(mail_users)
                        if auto_order.lock_order(self.user_info_dict[user], goods_id, proxies):
                            logger.info('[{0}] auto order [{1}] success.'.format(user, goods_info))
                            self.user_status_dict[user][goods_id] = self.user_status_dict[user][goods_id] - 1
                            self.send_mail(goods_info, user)
                            if self.user_info_dict[user]['email_code'] is not None:
                                self.send_mail(goods_info, user, self_sender=False)
                            self.message_queue.add('user_status_dict')

                        while len(self.ip_pool) == 0:
                            logger.info('ip pool is empty, waiting.')
                            time.sleep(3)

                        ip_info = random.choice(self.ip_pool)
                        proxies = self.get_proxy(ip_info)

                        goods_info = self.get_goods_info(goods_id, ip_info, proxies)
                        if goods_info['status'] is None:  # 访问失败或出错，直接返回
                            break

                        if goods_info['status'] == '在售':
                            logger.info('goods on sale: [{0}].'.format(goods_info))

                        mail_users = self.query_user_status(goods_id, goods_info)

                except Exception as e:
                    logger.exception('process goods[{0}] exception: [{1}].'.format(goods_id, e))

            if time.time() - last_time > 600:
                last_time = time.time()
                logger.info('thread[{0}] request statistics: [{1}].'.format(self.id, self.request_statistics))

    def stop(self):
        self.m_running = False
