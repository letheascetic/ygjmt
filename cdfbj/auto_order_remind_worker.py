# coding: utf-8

import time
import random
import smtplib
import logging
import threading
import auto_order

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText

from utils.ip_util import IpUtil
from sql.sqlcdfbj import SqlCdfBj
from utils.http_util import HttpUtil


logger = logging.getLogger(__name__)


class Worker(threading.Thread):

    def __init__(self, id, config, message_queue, goods_user_info, user_info_dict, user_status_dict, goods_ids):
        threading.Thread.__init__(self)
        self.id = id
        self.m_running = True
        self._config = config
        self.message_queue = message_queue
        self.goods_user_info = goods_user_info
        self.user_info_dict = user_info_dict
        self.user_status_dict = user_status_dict
        self.goods_ids = goods_ids

        self._ip_util = IpUtil(config)
        self._sql_helper = SqlCdfBj()
        self._http_util = HttpUtil(config)
        self._update_time = time.time()

    def stop(self):
        self.m_running = False

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
            sender = random.choice(self._config['mail_senders'])
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

    def lock_order(self, user, goods_id, host, port, goods_info):
        try:
            if auto_order.lock_order(self.user_info_dict[user], goods_id, host, port, goods_info['discount']):
                logger.info('[{0}] auto order [{1}] success.'.format(user, goods_info))
                self.user_status_dict[user][goods_id] = self.user_status_dict[user][goods_id] - 1
                self.send_mail(goods_info, user)
                if self.user_info_dict[user]['email_code'] is not None:
                    self.send_mail(goods_info, user, self_sender=False)
                self.message_queue.add('user_status_dict')
        except Exception as e:
            logger.exception('user[{0}] lock order[{0}] exception: [{1}].'.format(user, goods_id, e))

    def run(self):
        i = 0
        while self.m_running:
            i = i + 1
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            logger.info('thread[{0}] [{1}], start [{2}] times........................'.format(self.id, current_time, i))

            random.shuffle(self.goods_ids)
            for goods_id in self.goods_ids:
                try:
                    goods_info = self.__get_goods_info(goods_id)
                    if goods_info is None:
                        continue

                    # logger.info('goods info: [{0}].'.format(goods_info))

                    if goods_info['status'] != '在售':
                        continue

                    logger.info('goods on sale: [{0}].'.format(goods_info))

                    # if self._config['auto_order_use_proxy'] is False:
                    host, port = None, 8888

                    mail_users = self.query_user_status(goods_id, goods_info)

                    if goods_id in self._config['monitor_goods_ids']:
                        if goods_info['discount'] is None:  # 针对这些产品，折扣没有的情况下，不锁单
                            logger.info('goods[{0}] no discount[{1}], no need to auto order for these users[{2}].'.format(goods_id, goods_info, mail_users))
                            mail_users = []
                        else:
                            logger.info('goods[{0}] on sale with discount[{1}], auto order for these users[{2}].'.format(goods_id, goods_info, mail_users))

                    # 没有要锁单的用户，且当前库存数不为0，则把产品添加到想要锁单这个产品的用户购物车中
                    if len(mail_users) == 0 and goods_info['stock'] > 0:
                        users = self.goods_user_info.get(goods_id, [])
                        random.shuffle(users)
                        logger.info('add goods[{0}] to users[{1}] cart.'.format(goods_info, users))
                        for user in users:
                            # logger.info('add goods[{0}] to user[{1}] cart.'.format(goods_info, user))
                            auto_order.add_cart(self.user_info_dict[user], goods_id, host, port, goods_info['stock'], goods_info['discount'])

                    # 有要锁单的用户，则开启锁单
                    while len(mail_users) != 0:
                        user = None
                        for super_user in self._config['super_users']:
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

                        goods_info = self.__get_goods_info(goods_id)
                        if goods_info is None:  # 访问失败或出错，直接返回
                            break

                        if goods_info['status'] == '在售':
                            logger.info('goods on sale: [{0}].'.format(goods_info))

                        mail_users = self.query_user_status(goods_id, goods_info)

                except Exception as e:
                    logger.exception('process goods[{0}] exception: [{1}].'.format(goods_id, e))

            if (time.time() - self._update_time) > 600:
                self._update_time = time.time()
                self._http_util.log()

    def __get_goods_info(self, goods_id):
        """获取产品详情"""

        ip_item = None

        # 确认是否使用IP代理，若使用则获取一个IP Proxy
        if self._config.get('use_proxy', True):
            ip_item = self._ip_util.get_proxy()
            if not ip_item:
                time.sleep(5)
                return None
            host, port = ip_item['ip'], ip_item['port']
        else:
            host, port = '', -1

        # 获取产品详情
        goods_info = self._http_util.cdfbj_get_goods_info(goods_id, host, port)
        # if goods_info is not None:
        #     logger.info('cdfbj get goods info with ip proxy[{0}:{1}] response[{2}].'.format(host, port, goods_info))

        # 如果使用IP代理，则记录访问结果
        if self._config.get('use_proxy', True):
            self._ip_util.feedback(ip_item, goods_info)

        return goods_info
