# coding: utf-8

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
from scrapy.selector import Selector


logger = logging.getLogger(__name__)


class Worker(threading.Thread):
    id = None
    m_running = True

    def __init__(self, id, message_queue, goods_user_info, user_info_dict, user_status_dict, ip_pool, goods_sale_info_dict):
        threading.Thread.__init__(self)
        self.id = id
        self.m_running = True
        self.goods_user_info = goods_user_info
        self.user_info_dict = user_info_dict
        self.user_status_dict = user_status_dict
        self.message_queue = message_queue
        self.ip_pool = ip_pool
        self.goods_sale_info_dict = goods_sale_info_dict
        # self.request_statistics = {'total': 0, 'success': 0, 'failed': 0, 'exception': 0, 'total_time_span': 0, 'success_time_span': 0, 'total_avg_time': 0, 'success_avg_time': 0}

    def get_proxy(self, ip_info):
        host = ip_info.get('ip', None)
        port = ip_info.get('port', None)
        proxies = {
            'http': 'http://{0}:{1}'.format(host, port),
            'https': 'https://{0}:{1}'.format(host, port)
        }
        return proxies

    def get_goods_info(self, goods_id):
        goods_info = {'title': None, 'url': None, 'status': None, 'price': None, 'discount': None}
        try:
            url = "https://m.hndfbg.com/goods/detail?goods_id={0}".format(goods_id)
            goods_info['url'] = url

            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                selector = Selector(response=r)
                title = selector.xpath('//section[@class = "goods-title"]/div/h3/text()').extract_first()
                status = selector.xpath('//a[@class = "btn_sold_out"]/text()').extract_first()
                price = selector.xpath('//div[@class = "goods_contaier_base"]/section[@class = "goods-price"]/p/span/text()').extract_first()
                discount = selector.xpath('//div[@class = "goods_contaier_base"]/section[@class = "goods-price"]/p/em/text()').extract_first()
                if not status and title is not None:
                    goods_info['title'] = title
                    goods_info['status'] = '在售'
                elif status and title is not None:
                    goods_info['status'] = status
                    goods_info['title'] = title
                else:
                    goods_info['title'] = None
                    goods_info['status'] = None
                goods_info['discount'] = discount
                goods_info['price'] = price
            else:
                logger.info('thread[{0}] request url[{1}] failed with return code: [{2}].'.format(self.id, url, r.status_code))
        except Exception as e:
            logger.info('thread[{0}] get goods info exception: [{1}].'.format(self.id, e))

        return goods_info

    def send_mail(self, info, user, self_sender=True, title=None):
        if title is not None:
            goods_title = title
        else:
            goods_title = info['title']
        content = str(info)

        user_email = self.user_info_dict[user]['email']
        if self_sender and self.user_info_dict[user]['email_code'] is not None:
            from_addr, code = user_email, self.user_info_dict[user]['email_code']
            to_addrs = [user_email]
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
                subject = '{0}-{1}'.format('海免补货', goods_title)
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
        users = self.goods_user_info.get(goods_id, [])
        mail_users = []
        for user in users:
            # 在售且尚未被通知，则加入待通知队列
            if goods_info['status'] == '在售' and self.user_status_dict[user][goods_id] is False:
                mail_users.append(user)
                update_flag = True
            # 缺货且已通知，则变更为待通知状态
            elif goods_info['status'] != '在售' and self.user_status_dict[user][goods_id] is True:
                self.user_status_dict[user][goods_id] = False
                update_flag = True
        return update_flag, mail_users

    def update_query_goods_sale_info(self, goods_id, goods_info):
        update_flag = False
        mail_users = []
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

                    if goods_info['status'] == '在售':
                        logger.info('goods on sale: [{0}].'.format(goods_info))

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
                            mail_users = set(mail_users) - self_send_mail_users
                            for user in mail_users:
                                self.user_status_dict[user][goods_id] = True

                    if update_flag:
                        self.message_queue.add('user_status_dict')
                except Exception as e:
                    logger.exception('process goods[{0}] exception: [{1}].'.format(goods_id, e))

            # logger.info('thread[{0}] request statistics: [{1}].'.format(self.id, self.request_statistics))

    def stop(self):
        self.m_running = 0
