# coding: utf-8

import util
import json
import time
import jpype
import reader
import random
import smtplib
import logging
import datetime
import requests
import auto_order
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText
from auto_order_remind_worker import Worker


logger = logging.getLogger(__name__)


class AutoOrderReminder(object):
    message_queue = None
    goods_user_info = None      # 产品用户字典，记录产品订阅的用户
    user_info_dict = None       # 用户信息字典，包含用户名、密码、邮箱、订阅的产品及提醒阈值
    user_status_dict = None     # 用户状态字典，记录用户订阅的产品是否已经发起过提醒

    workers = []
    ip_pool = []
    ip_alert = False
    ip_pool_statistics = {'used': 0, 'expired': 0, 'bad': 0, 'recent': []}

    def __init__(self, config):
        self.config = config
        self.message_queue = set()

        jvmPath = jpype.getDefaultJVMPath()
        jarPath = 'demo12345.jar'
        # jpype.startJVM(jvmPath, "-Djava.class.path={0}".format(jarPath))
        self.HttpClientUtil = jpype.JClass('com.fizzy.sistertao.utils.OkHttpUtil')
        pass

    def load_goods_user_info(self):
        filename = self.config['goods_user_file']
        self.goods_user_info, self.user_info_dict = reader.load_auto_order_goods_user_info(filename)
        filename = self.config['user_info_file']
        reader.update_auto_order_user_info(filename, self.user_info_dict)

    def load_user_status(self):
        try:
            f = open(self.config['user_status_file'], 'r')
            content = f.read()
            if not content.strip():
                content = '{}'
        except:
            content = '{}'
        self.user_status_dict = json.loads(content)
        self.update_user_status()
        self.save_user_status()
        logger.info('user status dict: ------------------------------------------------------------------')
        logger.info(self.user_status_dict)
        logger.info('---------------------------------------------------------------------------------')

    def update_user_status(self):
        # 将新增的订阅者和订阅者新增的产品订阅添加到用户状态字典中
        for user, info in self.user_info_dict.items():
            if user not in self.user_status_dict.keys():
                self.user_status_dict[user] = {}
                logger.info('new auto order remind user[{0}].'.format(user))
            for goods_id in info.get('goods', {}).keys():
                if goods_id not in self.user_status_dict[user].keys():
                    self.user_status_dict[user][goods_id] = info['goods'][goods_id][1]      # 初始化为要锁单的次数
                    logger.info('new auto order remind goods[{0}] for user[{1}].'.format(goods_id, user))

        # 将不再订阅的用户和用户不再订阅的产品从用户状态字典中删去
        canceled_users = []
        canceled_good_ids = []
        for user, status in self.user_status_dict.items():
            if user not in self.user_info_dict.keys():
                canceled_users.append(user)
                # self.user_status_dict.pop(user)
                logger.info('cancel auto order remind user[{0}].'.format(user))
                continue
            for goods_id in status.keys():
                if goods_id not in self.user_info_dict[user]['goods'].keys():
                    canceled_good_ids.append((user, goods_id))
                    # self.user_status_dict[user].pop(goods_id)
                    logger.info('cancel auto order remind goods[{0}] for user[{1}].'.format(goods_id, user))

        for user in canceled_users:
            self.user_status_dict.pop(user)

        for user, goods_id in canceled_good_ids:
            self.user_status_dict[user].pop(goods_id)

    def save_user_status(self):
        try:
            content = json.dumps(self.user_status_dict)
            f = open(self.config['user_status_file'], 'w', encoding='utf-8')
            f.write(content)
            f.close()
        except Exception as e:
            logger.exception('save user status to [{0}] exception: [{1}].'.format(self.config['user_status_file'], e))

    def activate_workers(self):
        worker_num = self.config.get('worker_num', 1)
        goods_ids = self.get_random_goods_ids()
        goods_per_thread = int(len(goods_ids) / worker_num)

        for i in range(worker_num):
            thread_id = i + 1
            if i == worker_num-1:
                goods_ids_slice = goods_ids[i*goods_per_thread:]
            else:
                goods_ids_slice = goods_ids[i*goods_per_thread:(i+1)*goods_per_thread]

            self.workers.append(Worker(thread_id, self.message_queue, self.goods_user_info,
                                       self.user_info_dict, self.user_status_dict, self.ip_pool,
                                       goods_ids_slice, self.HttpClientUtil))

        for worker in self.workers:
            # logger.info('[{0}] [{1}].'.format(worker.id, len(worker.goods_user_info.keys())))
            worker.start()

    def update_proxies(self, num):
        if not self.config.get('use_proxy', False):
            if len(self.ip_pool) == 0:
                self.ip_pool.append({'ip': None, 'host': None, 'failed_times': 0})
            return

        for ip_info in self.ip_pool:
            expire_time = datetime.datetime.strptime(ip_info['expire_time'], '%Y-%m-%d %H:%M:%S')
            time_rest = (expire_time - datetime.datetime.now()).total_seconds()
            if time_rest < 30:
                logger.info('pop time expired proxy: [{0}].'.format(ip_info))
                self.ip_pool.remove(ip_info)
                self.ip_pool_statistics['expired'] = self.ip_pool_statistics['expired'] + 1
                self.ip_pool_statistics['used'] = self.ip_pool_statistics['used'] + 1
                self.ip_pool_statistics['recent'].append((ip_info, 'expired'))
            if ip_info.get('failed_times', 0) >= 15:
                logger.info('pop bad proxy: [{0}].'.format(ip_info))
                self.ip_pool.remove(ip_info)
                self.ip_pool_statistics['bad'] = self.ip_pool_statistics['bad'] + 1
                self.ip_pool_statistics['used'] = self.ip_pool_statistics['used'] + 1
                self.ip_pool_statistics['recent'].append((ip_info, 'bad'))

        if len(self.ip_pool_statistics['recent']) > 30:
            while len(self.ip_pool_statistics['recent']) > 30:
                self.ip_pool_statistics['recent'].pop(0)

            bad_num = len([x for x in self.ip_pool_statistics['recent'] if x[-1] == 'bad'])
            bad_num_ratio = bad_num / len(self.ip_pool_statistics['recent'])
            logger.info('bad ip proxy ratio: [{0}].'.format(bad_num_ratio))

            if bad_num_ratio > 0.75 and not self.ip_alert:
                if self.send_alert_mail(self.ip_pool_statistics['recent']):
                    self.ip_alert = True

        if self.ip_alert:
            return

        new_num = num - len(self.ip_pool)
        if new_num <= 0:
            return

        order_id = random.choice(['110169', '124824'])
        # order_id = random.choice(['124824'])

        # 直连IP
        # url = 'http://webapi.http.zhimacangku.com/getip?num={0}&type=2&pro=&city=0&yys=0&port=11&pack=110169&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions='
        # 隧道IP
        url = 'http://http.tiqu.alicdns.com/getip3?num={0}&type=2&pro=&city=0&yys=0&port=11&pack={1}&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions='
        # 独享IP
        # url = 'http://http.tiqu.alicdns.com/getip3?num={0}&type=2&pro=&city=0&yys=0&port=11&pack=110169&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions=&gm=4'
        url = url.format(new_num, order_id)

        try:
            r = requests.get(url, timeout=30)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                if content['code'] == 0:
                    logger.info('get proxies success.')
                    for ip_info in content.get('data', []):
                        ip_info['failed_times'] = 0
                        logger.info('push new proxy: [{0}].'.format(ip_info))
                        self.ip_pool.append(ip_info)
        except Exception as e:
            logger.exception('get proxies exception: [{0}].'.format(e))

        logger.info('ip pool statistics: [{0}].'.format(self.ip_pool_statistics))

    def send_alert_mail(self, info):
        if config.ON_SALE_REMINDER_CONFIG.get('sys_mail_senders', None):
            sender = random.choice(config.ON_SALE_REMINDER_CONFIG['sys_mail_senders'])
        else:
            sender = random.choice(config.ON_SALE_REMINDER_CONFIG['mail_senders'])

        from_addr, code = sender['email'], sender['code']
        to_addrs = [from_addr]

        content = str(info)

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
                subject = '报警提醒：坏的IP代理太多.'
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                return True
            except Exception as e:
                i = i + 1
                logger.exception('thread[{0}] send alert mail[{1}] failed; [{2}].'.format(self.id, info, e))
                time.sleep(2)
        return False

    def get_random_goods_ids(self):
        goods_ids = []
        for goods_id in self.goods_user_info.keys():
            # user_num = len(self.goods_user_info.get(goods_id, []))
            # goods_ids.extend([goods_id] * user_num)
            goods_ids.append(goods_id)
        random.shuffle(goods_ids)
        return goods_ids

    def start_to_monitor(self):
        proxy_num = self.config.get('ip_pool_num', 1)

        users = [user for user in self.user_info_dict.keys() if len(self.user_info_dict[user]['goods']) != 0]

        for user_key in users:
            user = self.user_info_dict[user_key]
            self.init_lock_user_info(user)
            time.sleep(10)

        user_num = len(users)
        time_interval = 3600 / user_num
        last_time = None
        next_user_index = 0
        while True:
            try:
                while len(self.message_queue) != 0:
                    message = self.message_queue.pop()
                    if message == 'user_status_dict':
                        self.save_user_status()
                self.update_proxies(proxy_num)

                if last_time is None or (time.time() - last_time) > time_interval:
                    user = self.user_info_dict[users[next_user_index]]
                    self.init_lock_user_info(user)
                    # auto_order.save_goods_lock_info()
                    last_time = time.time()
                    next_user_index = next_user_index + 1
                    if next_user_index == len(users):
                        next_user_index = 0

                time.sleep(10)
            except Exception as e:
                logger.exception('on sale reminder exception: [{0}].'.format(e))

    def get_proxy(self, ip_info):
        host = ip_info.get('ip', None)
        port = ip_info.get('port', None)
        if host is None or port is None:
            return None, 8888
        return host, port

    def init_lock_user_info(self, user):
        logger.info('init lock user info: [{0}].'.format(user))
        if not self.config.get('auto_order_use_proxy', True):   # 自助下单，默认使用代理IP
            host, port = None, 8888
            auto_order.init_user_info(user, host, port)
        elif len(self.ip_pool) != 0:
            ip_info = random.choice(self.ip_pool)
            host, port = self.get_proxy(ip_info)
            auto_order.init_user_info(user, host, port)

    def execute(self):
        # auto_order.load_goods_lock_info()
        self.load_goods_user_info()     # 从excel读取用户信息和产品订阅信息
        self.load_user_status()         # 读取过去存储的用户字典
        proxy_num = self.config.get('ip_pool_num', 1)
        self.update_proxies(proxy_num)
        self.activate_workers()         # 激活workers，开始监控
        self.start_to_monitor()
        pass


if __name__ == '__main__':
    util.config_logger('auto_order_reminder')

    import config
    reminder = AutoOrderReminder(config.AUTO_ORDER_REMINDER_CONFIG)
    reminder.execute()
    # reminder.send_alert_mail('测试程序2')
    pass
