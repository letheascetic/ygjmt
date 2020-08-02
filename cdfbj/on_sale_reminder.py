# coding: utf-8

import util
import json
import time
import reader
import logging
import datetime
import requests
from on_sale_remind_worker import Worker


logger = logging.getLogger(__name__)


class OnSaleReminder(object):

    config = None
    message_queue = None
    goods_user_info = None      # 产品用户字典，记录产品订阅的用户
    user_info_dict = None       # 用户信息字典，包含用户名、密码、邮箱、订阅的产品及提醒阈值
    user_status_dict = None     # 用户状态字典，记录用户订阅的产品是否已经发起过提醒
    # goods_status_dict = None    # 产品状态字典，记录产品最近的状态信息，包括产品名、链接、状态、库存
    workers = []
    ip_pool = []
    ip_pool_statistics = {'used': 0, 'expired': 0, 'bad': 0}

    def __init__(self, config):
        self.config = config
        self.message_queue = set()
        pass

    def load_goods_user_info(self):
        filename = self.config['goods_user_file']
        self.goods_user_info, self.user_info_dict = reader.load_goods_user_info_v3(filename)

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
                logger.info('new on sale remind user[{0}].'.format(user))
            for goods_id in info.get('goods', {}).keys():
                if goods_id not in self.user_status_dict[user].keys():
                    self.user_status_dict[user][goods_id] = False
                    logger.info('new on sale remind goods[{0}] for user[{1}].'.format(goods_id, user))

        # 将不再订阅的用户和用户不再订阅的产品从用户状态字典中删去
        canceled_users = []
        canceled_good_ids = []
        for user, status in self.user_status_dict.items():
            if user not in self.user_info_dict.keys():
                canceled_users.append(user)
                # self.user_status_dict.pop(user)
                logger.info('cancel on sale remind user[{0}].'.format(user))
                continue
            for goods_id in status.keys():
                if goods_id not in self.user_info_dict[user]['goods'].keys():
                    canceled_good_ids.append((user, goods_id))
                    # self.user_status_dict[user].pop(goods_id)
                    logger.info('cancel on sale remind goods[{0}] for user[{1}].'.format(goods_id, user))

        for user in canceled_users:
            self.user_status_dict.pop(user)

        for user, goods_id in canceled_good_ids:
            self.user_status_dict[user].pop(goods_id)

    def load_goods_status(self):
        try:
            f = open(self.config['goods_status_file'], 'r')
            content = f.read()
            if not content.strip():
                content = '{}'
        except:
            content = '{}'
        self.goods_status_dict = json.loads(content)

    def get_goods_status_slice(self, goods_list):
        goods_status_slice = {}
        for goods_id in goods_list:
            if goods_id in self.goods_status_dict.keys():
                goods_status_slice[goods_id] = self.goods_status_dict[goods_id]
        return goods_status_slice

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
        goods_per_thread = int(len(self.goods_user_info.keys()) / worker_num)

        goods_count = 0
        thread_id = 1
        goods_user_info_slice = {}
        for goods_id in self.goods_user_info.keys():
            goods_count = goods_count + 1
            goods_user_info_slice[goods_id] = self.goods_user_info[goods_id]

            if thread_id == worker_num:
                continue
            elif goods_count == goods_per_thread:
                self.workers.append(Worker(thread_id, self.message_queue, goods_user_info_slice,
                                           self.user_info_dict, self.user_status_dict, self.ip_pool))
                goods_count = 0
                thread_id = thread_id + 1
                goods_user_info_slice = {}

        self.workers.append(Worker(thread_id, self.message_queue, goods_user_info_slice,
                                   self.user_info_dict, self.user_status_dict, self.ip_pool))

        for worker in self.workers:
            # logger.info('[{0}] [{1}].'.format(worker.id, len(worker.goods_user_info.keys())))
            worker.start()

    def update_proxies(self, num):
        for ip_info in self.ip_pool:
            expire_time = datetime.datetime.strptime(ip_info['expire_time'], '%Y-%m-%d %H:%M:%S')
            time_rest = (expire_time - datetime.datetime.now()).total_seconds()
            if time_rest < 30:
                logger.info('pop time expired proxy: [{0}].'.format(ip_info))
                self.ip_pool.remove(ip_info)
                self.ip_pool_statistics['expired'] = self.ip_pool_statistics['expired'] + 1
                self.ip_pool_statistics['used'] = self.ip_pool_statistics['used'] + 1
            if ip_info.get('failed_times', 0) >= 15:
                logger.info('pop bad proxy: [{0}].'.format(ip_info))
                self.ip_pool.remove(ip_info)
                self.ip_pool_statistics['bad'] = self.ip_pool_statistics['bad'] + 1
                self.ip_pool_statistics['used'] = self.ip_pool_statistics['used'] + 1

        new_num = num - len(self.ip_pool)
        if new_num <= 0:
            return

        url = 'http://http.tiqu.alicdns.com/getip3?num={0}&type=2&pro=&city=0&yys=0&port=11&pack=110169&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions=&gm=4'
        # url = 'http://http.tiqu.alicdns.com/getip3?num={0}&type=2&pro=&city=0&yys=0&port=11&pack=110169&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions=&gm=4'
        url = url.format(new_num)

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

    def start_to_monitor(self):
        proxy_num = self.config.get('ip_pool_num', 1)
        while True:
            try:
                while len(self.message_queue) != 0:
                    message = self.message_queue.pop()
                    if message == 'user_status_dict':
                        self.save_user_status()
                self.update_proxies(proxy_num)
                time.sleep(10)
            except Exception as e:
                logger.exception('on sale reminder exception: [{0}].'.format(e))

    def execute(self):
        self.load_goods_user_info()     # 从excel读取用户信息和产品订阅信息
        self.load_user_status()         # 读取过去存储的用户字典
        proxy_num = self.config.get('ip_pool_num', 1)
        self.update_proxies(proxy_num)
        self.activate_workers()         # 激活workers，开始监控
        self.start_to_monitor()
        pass


if __name__ == '__main__':
    util.config_logger('on_sale_reminder')

    import config
    reminder = OnSaleReminder(config.ON_SALE_REMINDER_CONFIG)
    reminder.execute()
    pass
