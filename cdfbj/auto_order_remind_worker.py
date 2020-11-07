# coding: utf-8

import uuid
import time
import json
import config
import random
import smtplib
import logging
import threading
import auto_order

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class Worker(threading.Thread):

    def __init__(self, id, message_queue, goods_user_info, user_info_dict, user_status_dict, ip_pool, goods_ids, http_util):
        threading.Thread.__init__(self)
        self.id = id
        self.m_running = True
        self.goods_user_info = goods_user_info
        self.user_info_dict = user_info_dict
        self.user_status_dict = user_status_dict
        self.message_queue = message_queue
        self.ip_pool = ip_pool
        self.goods_ids = goods_ids
        self.request_statistics = {'total': 0, 'success': 0, 'failed': 0, 'exception': 0, 'total_time_span': 0, 'success_time_span': 0, 'total_avg_time': 0, 'success_avg_time': 0}
        self.http_util = http_util

    def get_proxy(self, ip_info):
        host = ip_info.get('ip', None)
        port = ip_info.get('port', None)
        if host is None or port is None:
            return None, None
        return host, port

    def get_goods_info_with_http_util(self, goods_id, host, port):
        goods_info = {'title': None, 'url': None, 'status': None, 'stock': None, 'price': None, 'discount': None}
        if not host:
            host = ''
            port = 8888

        start = time.time()
        try:
            url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}?regId={1}".format(goods_id, uuid.uuid4())
            goods_info['url'] = 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id)

            response = self.http_util.getGoodsInfo(url, host, port)
            try:
                content = json.loads(str(response))
                context = content['context']
                if context is None:
                    goods_info['status'] = '下架'
                    goods_info['stock'] = 0
                else:
                    info = context['goodsInfos'][0]
                    goods_info['stock'] = info['stock']
                    goods_info['title'] = info['goodsInfoName']
                    if goods_info['stock'] > 0:
                        goods_info['status'] = '在售'
                    else:
                        goods_info['status'] = '缺货'

                    goods_info['price'] = info['salePrice']
                    if len(info['marketingLabels']) > 0:
                        goods_info['discount'] = info['marketingLabels'][0]['marketingDesc']

                self.request_statistics['success'] = self.request_statistics['success'] + 1
                time_span = time.time() - start
                self.request_statistics['success_time_span'] = self.request_statistics['success_time_span'] + time_span
                self.request_statistics['success_avg_time'] = self.request_statistics['success_time_span'] / self.request_statistics['success']
            except:
                # logger.info('thread[{0}] request url[{1}] using proxy[{2}:{3}] failed with return code: [{4}].'.format(self.id, goods_id, host, port, e))
                # ip_info['failed_times'] = ip_info['failed_times'] + 1

                # self.request_statistics['failed'] = self.request_statistics['failed'] + 1
                time_span = time.time() - start

        except Exception as e:
            logger.info('thread[{0}] get goods info[{1}] using proxy[{2}:{3}] exception[{4}].'.format(self.id, goods_id, host, port, e))

            self.request_statistics['exception'] = self.request_statistics['exception'] + 1
            time_span = time.time() - start

        self.request_statistics['total'] = self.request_statistics['total'] + 1
        self.request_statistics['total_time_span'] = self.request_statistics['total_time_span'] + time_span
        self.request_statistics['total_avg_time'] = self.request_statistics['total_time_span'] / self.request_statistics['total']

        return goods_info

    def query_user_status(self, goods_id, goods_info):
        stock = goods_info['stock']
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
        while i < 1:
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

            random.shuffle(self.goods_ids)
            for goods_id in self.goods_ids:
                try:
                    # time.sleep(config.AUTO_ORDER_REMINDER_CONFIG['interval'])
                    time.sleep(random.random() * config.AUTO_ORDER_REMINDER_CONFIG['interval'] * 2)
                    while len(self.ip_pool) == 0:
                        logger.info('ip pool is empty, waiting.')
                        time.sleep(3)

                    ip_info = random.choice(self.ip_pool)
                    host, port = self.get_proxy(ip_info)

                    goods_info = self.get_goods_info_with_http_util(goods_id, host, port)
                    if goods_info['status'] is None:  # 访问失败或出错，直接返回
                        continue

                    # logger.info('goods info: [{0}].'.format(goods_info))

                    if goods_info['status'] == '在售':
                        logger.info('goods on sale: [{0}].'.format(goods_info))

                    if config.AUTO_ORDER_REMINDER_CONFIG['auto_order_use_proxy'] is False:
                        host, port = None, 8888

                    mail_users = self.query_user_status(goods_id, goods_info)

                    # 没有要锁单的用户，且当前库存数不为0，则把产品添加到想要锁单这个产品的用户购物车中
                    if len(mail_users) == 0 and goods_info['stock'] > 0:
                        users = self.goods_user_info.get(goods_id, [])
                        random.shuffle(users)
                        for user in users:
                            logger.info('add goods[{0}] to user[{1}] cart.'.format(goods_info, user))
                            auto_order.add_cart(self.user_info_dict[user], goods_id, host, port, goods_info['stock'], goods_info['discount'])

                    # 有要锁单的用户，则开启锁单
                    while len(mail_users) != 0:
                        user = None
                        for super_user in config.AUTO_ORDER_REMINDER_CONFIG['super_users']:
                            if super_user in mail_users:
                                user = super_user
                                break

                        if user is None:
                            user = random.choice(mail_users)

                        if auto_order.lock_order(self.user_info_dict[user], goods_id, host, port, goods_info['discount']):
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
                        host, port = self.get_proxy(ip_info)

                        goods_info = self.get_goods_info_with_http_util(goods_id, host, port)
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
