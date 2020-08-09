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

    def get_goods_info(self, goods_id):
        goods_info = {'title': None, 'url': None, 'status': None, '库存': None}

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

    def send_mail(self, info, user, self_sender=True):
        goods_title = info['title']
        content = str(info)
        # content = self.make_mail_content(info, user)
        # subject = self.make_mail_header(info, user)

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
                # message['Cc'] = from_addr
                subject = '{0}: 库存{1}-{2}'.format('cdf北京', info['库存'], goods_title)
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                return True
            except Exception as e:
                i = i + 1
                logger.exception('thread[{0}] send mail[{1}] to [{2}] failed; [{3}].'.format(self.id, info, user, e))
                time.sleep(2)
        return False

    def make_mail_content(self, info, user):
        user_email = self.user_info_dict[user]['email']

        hello = random.choice(['hello', 'hi', '嗨', '你好', '您好', 'hey', '亲爱的', '亲', '哇', '嘿嘿', '哈哈', '恭喜', 'congratulations'])
        name = user_email.split('@')[0]
        str1 = random.choice(['商品', '产品', '东东', '', '货品'])
        str2 = info['title']
        str3 = random.choice(['有货', '上架', '补货'])
        str4 = info['库存']
        str5 = random.choice(['马上', '尽快', '赶紧', '加油', ' ', '请'])
        str6 = random.choice(['下单', '购买', '支付', '查看'])
        str7 = random.choice(['商品', '产品', '东东', '宝贝', '货品'])
        str8 = random.choice(['Best Regards', 'Regards', 'Best wishes'])

        content = """
        {hello}，{name}：

            你关注的{str1}“{str2}”{str3}了，现在还有{str4}件，{str5}去{str6}吧。
            
            {str7}链接：{url}
        
        {str8}
        
        阳光姐妹淘鸭！~
        """.format(hello=hello, name=name, str1=str1, str2=str2, str3=str3,
                   str4=str4, str5=str5, str6=str6, str7=str7, url=info['url'], str8=str8)

        return content

    def make_mail_header(self, info, user):
        user_email = self.user_info_dict[user]['email']
        name = random.choice(['hello', 'hi', '嗨', '你好', '您好', 'hey', '亲爱的', '亲', '哇', user_email.split('@')[0]])
        company = random.choice(['北京cdf', 'cdf北京'])
        title = info['title']
        message = random.choice(['补货了', '有货了', '有更新了', '有存库了'])
        header = '{name}, {company} {title} {message} '.format(name=name, company=company, title=title, message=message)
        return header

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
                    time.sleep(random.random() * config.ON_SALE_REMINDER_CONFIG['interval'] * 2)
                    goods_info = self.get_goods_info(goods_id)
                    if goods_info['status'] is None:  # 访问失败或出错，直接返回
                        continue

                    # logger.info('goods info: [{0}].'.format(goods_info))

                    if goods_info['status'] == '在售':
                        logger.info('goods on sale: [{0}].'.format(goods_info))

                    update_flag, mail_users = self.update_query_user_status(goods_id, goods_info)

                    random.shuffle(mail_users)

                    if mail_users:
                        logger.info('goods[{0}] send mail to [{1}].'.format(goods_info, mail_users))
                        self_send_mail_users = set()
                        for user in mail_users:
                            if self.user_info_dict[user]['email_code'] is not None:
                                self_send_mail_users.add(user)

                        for user in self_send_mail_users:
                            self.send_mail(goods_info, user)
                            self.user_status_dict[user][goods_id] = True

                        if self.send_mail(goods_info, mail_users[0], self_sender=False):
                            mail_users = set(mail_users) - self_send_mail_users
                            for user in mail_users:
                                self.user_status_dict[user][goods_id] = True

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

            logger.info('thread[{0}] request statistics: [{1}].'.format(self.id, self.request_statistics))

    def stop(self):
        self.m_running = False
