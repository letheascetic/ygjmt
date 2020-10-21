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

    def __init__(self, id, message_queue, user_info_dict, user_status_dict, ip_pool, goods_sale_info_dict, goods_ids, http_util):
        threading.Thread.__init__(self)
        self.id = id
        self.m_running = True
        self.user_info_dict = user_info_dict
        self.user_status_dict = user_status_dict
        self.message_queue = message_queue
        self.ip_pool = ip_pool
        self.goods_sale_info_dict = goods_sale_info_dict
        self.goods_ids = goods_ids
        self.request_statistics = {'total': 0, 'success': 0, 'failed': 0, 'exception': 0, 'total_time_span': 0, 'success_time_span': 0, 'total_avg_time': 0, 'success_avg_time': 0}
        self.http_util = http_util

    def get_proxy(self, ip_info):
        host = ip_info.get('ip', None)
        port = ip_info.get('port', None)

        if host is None or port is None:
            return None

        proxies = {
            'http': 'http://{0}:{1}'.format(host, port),
            'https': 'https://{0}:{1}'.format(host, port)
        }
        return proxies

    def get_goods_info_with_http_util(self, goods_id):
        goods_info = {'title': None, 'url': None, 'status': None, 'stock': None, 'price': None, 'discount': None}

        while len(self.ip_pool) == 0:
            logger.info('ip pool is empty, waiting.')
            time.sleep(10)

        ip_info = random.choice(self.ip_pool)
        host = ip_info.get('ip', None)
        port = ip_info.get('port', None)

        start = time.time()
        try:
            url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}?regId={1}".format(goods_id, uuid.uuid4())
            goods_info['url'] = 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id)

            response = self.http_util.doGet(url, None, host, port)
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

                if ip_info['failed_times'] != 0:
                    ip_info['failed_times'] = ip_info['failed_times'] - 1

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
            ip_info['failed_times'] = ip_info['failed_times'] + 1

            self.request_statistics['exception'] = self.request_statistics['exception'] + 1
            time_span = time.time() - start

        self.request_statistics['total'] = self.request_statistics['total'] + 1
        self.request_statistics['total_time_span'] = self.request_statistics['total_time_span'] + time_span
        self.request_statistics['total_avg_time'] = self.request_statistics['total_time_span'] / self.request_statistics['total']

        return goods_info

    def get_goods_info(self, goods_id):
        goods_info = {'title': None, 'url': None, 'status': None, 'stock': None, 'price': None, 'discount': None}

        while len(self.ip_pool) == 0:
            logger.info('ip pool is empty, waiting.')
            time.sleep(10)

        ip_info = random.choice(self.ip_pool)
        proxies = self.get_proxy(ip_info)

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

    def send_mail(self, info, user, self_sender=True, title=None, sys_mail=False):
        if title is not None:
            goods_title = title
        else:
            goods_title = info['title']

        content = {'商品': info['title'], '状态': info['status'], '库存': info['stock'],
                   '价格': info['price'], '折扣': info['discount'], '链接': info['url']}
        content = str(content)

        user_email = self.user_info_dict[user]['email']
        if self_sender and self.user_info_dict[user]['email_code'] is not None:
            from_addr, code = user_email, self.user_info_dict[user]['email_code']
            to_addrs = [user_email]
        elif sys_mail is True:
            sender = random.choice(config.ON_SALE_REMINDER_CONFIG['sys_mail_senders'])
            from_addr, code = sender['email'], sender['code']
            to_addrs = [from_addr]
        else:
            sender = random.choice(config.ON_SALE_REMINDER_CONFIG['mail_senders'])
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
                subject = '{0}: 库存{1}-{2}'.format('cdf北京', info['stock'], goods_title)
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                return True
            except Exception as e:
                i = i + 1
                logger.exception('thread[{0}] send mail[{1}] to [{2}] failed; [{3}].'.format(self.id, info, user, e))
                time.sleep(2)
        return False

    def update_query_goods_sale_info(self, goods_id, goods_info):
        update_flag = 0
        mail_users = []
        if goods_info['status'] == '下架':
            return update_flag, mail_users

        if goods_id not in self.goods_sale_info_dict.keys():
            self.goods_sale_info_dict[goods_id] = goods_info
            update_flag = 1

        goods_sale_info = self.goods_sale_info_dict[goods_id]
        if goods_sale_info['price'] != goods_info['price'] or goods_sale_info['discount'] != goods_info['discount']:
            self.goods_sale_info_dict[goods_id] = {'price': goods_info['price'], 'discount': goods_info['discount']}
            update_flag = 1
            mail_users = list(self.user_info_dict.keys())
        else:
            users = self.user_info_dict.keys()
            stock = goods_info['stock']
            for user in users:
                # 存库大于等于订阅阈值且还没被通知过，则需要发送邮件
                if stock >= config.ON_SALE_REMINDER_CONFIG['goods_stock_threshold'] and self.user_status_dict[user][goods_id] is False:
                    mail_users.append(user)
                    update_flag = 2
                # 存库小于订阅阈值且已经被通知过，则变更为待通知状态
                elif stock < config.ON_SALE_REMINDER_CONFIG['goods_stock_threshold'] and self.user_status_dict[user][goods_id] is True:
                    self.user_status_dict[user][goods_id] = False
                    update_flag = 2
        return update_flag, mail_users

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
                    time.sleep(random.random() * config.ON_SALE_REMINDER_CONFIG['interval'] * 2)
                    # goods_info = self.get_goods_info(goods_id)
                    goods_info = self.get_goods_info_with_http_util(goods_id)

                    if goods_info['status'] is None:  # 访问失败或出错，直接返回
                        continue

                    logger.info('goods info: [{0}].'.format(goods_info))

                    # if goods_info['status'] == '在售':
                    #     logger.info('goods on sale: [{0}].'.format(goods_info))

                    update_flag, mail_users = self.update_query_goods_sale_info(goods_id, goods_info)
                    if update_flag == 1:
                        self.message_queue.add('goods_sale_info_dict')

                        if mail_users:
                            mail_title = '折扣/价格变化了-{0}'.format(goods_info['title'])
                            random.shuffle(mail_users)
                            logger.info('goods[{0}] send mail to [{1}].'.format(goods_info, mail_users))
                            for user in mail_users:
                                self.send_mail(goods_info, user, title=mail_title)

                    elif update_flag == 2:
                        if mail_users:
                            random.shuffle(mail_users)
                            logger.info('goods[{0}] send mail to [{1}].'.format(goods_info, mail_users))
                            for user in mail_users:
                                self.send_mail(goods_info, user, title=None)
                                self.user_status_dict[user][goods_id] = True
                        self.message_queue.add('user_status_dict')

                except Exception as e:
                    logger.exception('process goods[{0}] exception: [{1}].'.format(goods_id, e))

            if time.time() - last_time > 600:
                last_time = time.time()
                logger.info('thread[{0}] request statistics: [{1}].'.format(self.id, self.request_statistics))

    def stop(self):
        self.m_running = False
