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

    def __init__(self, id, message_queue, goods_user_info, user_info_dict, user_status_dict, ip_pool, goods_sale_info_dict, goods_ids, http_util):
        threading.Thread.__init__(self)
        self.id = id
        self.m_running = True
        self.goods_user_info = goods_user_info
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

    def send_mail(self, info, user, self_sender=True, title=None, sys_mail=False):
        if title is not None:
            goods_title = title
        else:
            goods_title = info['title']

        content = {'商品': info['title'], '状态': info['status'], '库存': info['stock'],
                   '价格': info['price'], '折扣': info['discount'], '链接': info['url']}
        content = str(content)

        # content = '商品： {0}  状态： {1}  库存： {2}  价格： {3}  折扣： {4}  \n链接：\n {5}\n\n'.format(info['title'],
        #                                                                                  info['status'], info['stock'],
        #                                                                                  info['price'], info['discount'],
        #                                                                                  info['url'])

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

    def update_query_user_status(self, goods_id, goods_info):
        update_flag = False
        stock = goods_info['stock']
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

    def update_query_goods_sale_info(self, goods_id, goods_info):
        update_flag = False
        mail_users = []
        if goods_info['status'] == '下架':
            return update_flag, mail_users

        if goods_id not in self.goods_sale_info_dict.keys():
            self.goods_sale_info_dict[goods_id] = {'price': goods_info['price'], 'discount': goods_info['discount']}
            update_flag = True

        goods_sale_info = self.goods_sale_info_dict[goods_id]
        if goods_sale_info['price'] != goods_info['price'] or goods_sale_info['discount'] != goods_info['discount']:
            self.goods_sale_info_dict[goods_id] = {'price': goods_info['price'], 'discount': goods_info['discount']}
            update_flag = True
            mail_users = self.goods_user_info.get(goods_id, [])

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
        last_time = time.time()
        while self.m_running:
            i = i + 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info('thread[{0}] [{1}], start [{2}] times........................'.format(self.id, current_time, i))

            random.shuffle(self.goods_ids)
            for goods_id in self.goods_ids:
                try:
                    time.sleep(random.random() * config.ON_SALE_REMINDER_CONFIG['interval'] * 2)
                    while len(self.ip_pool) == 0:
                        logger.info('ip pool is empty, waiting.')
                        time.sleep(3)

                    ip_info = random.choice(self.ip_pool)
                    host, port = self.get_proxy(ip_info)

                    goods_info = self.get_goods_info_with_http_util(goods_id, host, port)

                    if goods_info['status'] is None:  # 访问失败或出错，直接返回
                        continue

                    logger.info('goods info: [{0}].'.format(goods_info))

                    # if goods_info['status'] == '在售':
                    #     logger.info('goods on sale: [{0}].'.format(goods_info))

                    update_flag, mail_users = self.update_query_goods_sale_info(goods_id, goods_info)
                    if update_flag:
                        self.message_queue.add('goods_sale_info_dict')

                    mail_title = None
                    if mail_users:
                        update_flag, _ = self.update_query_user_status(goods_id, goods_info)
                        mail_title = '折扣/价格变化了-{0}'.format(goods_info['title'])
                    else:
                        update_flag, mail_users = self.update_query_user_status(goods_id, goods_info)

                    random.shuffle(mail_users)

                    if mail_users:
                        logger.info('goods[{0}] send mail to [{1}].'.format(goods_info, mail_users))
                        self_send_mail_users = set()
                        for user in mail_users:
                            if self.user_info_dict[user]['email_code'] is not None:
                                self_send_mail_users.add(user)

                        for user in self_send_mail_users:
                            self.send_mail(goods_info, user, title=mail_title)
                            self.user_status_dict[user][goods_id] = True

                        if self.send_mail(goods_info, mail_users[0], self_sender=False, title=mail_title):
                            rest_mail_users = set(mail_users) - self_send_mail_users
                            for user in rest_mail_users:
                                self.user_status_dict[user][goods_id] = True

                        if goods_info['stock'] >= config.ON_SALE_REMINDER_CONFIG['sys_mail_threshold'] or mail_title is not None:
                            self.send_mail(goods_info, mail_users[0], self_sender=False, title=mail_title, sys_mail=True)

                    # for user in mail_users:
                    #     logger.info('goods[{0}] send mail to [{1}].'.format(goods_info, self.user_info_dict[user]))
                    #     if self.send_mail(goods_info, user):  # 发送成功，用户状态字典中对应的状态变为True
                    #         self.user_status_dict[user][goods_id] = True
                    #     else:
                    #         logger.info('failed goods[{0}] send mail to [{1}].'.format(goods_info, self.user_info_dict[user]))

                    if update_flag:
                        self.message_queue.add('user_status_dict')

                    # time.sleep(random.random())
                except Exception as e:
                    logger.exception('process goods[{0}] exception: [{1}].'.format(goods_id, e))

            if time.time() - last_time > 600:
                last_time = time.time()
                logger.info('thread[{0}] request statistics: [{1}].'.format(self.id, self.request_statistics))

    def stop(self):
        self.m_running = False
