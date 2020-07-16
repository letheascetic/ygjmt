# coding: utf-8

import json
import reader
import logging
from queue import ThreadSafeQueue
from on_sale_remind_worker import Worker


logger = logging.getLogger(__name__)


class OnSaleReminder(object):

    config = None
    mail_info_queue = None
    goods_user_info = None
    user_info_dict = None
    user_status_dict = None
    workers = []

    def __init__(self, config, max_queue_size=0):
        self.config = config
        self.mail_info_queue = ThreadSafeQueue(max_size=max_queue_size)
        pass

    def load_goods_user_info(self):
        filename = self.config['goods_user_file']
        self.goods_user_info, self.user_info_dict = reader.load_goods_user_info_v2(filename)

    def load_user_status(self):
        try:
            f = open(self.config['user_status_file'], 'r')
            content = f.read()
            if not content.strip():
                content = '{}'
        except:
            content = '{}'
        self.user_status_dict = json.loads(content)

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
        for user, status in self.user_status_dict.items():
            if user not in self.user_info_dict.keys():
                self.user_status_dict.pop(user)
                logger.info('cancel on sale remind user[{0}].'.format(user))
                continue
            for goods_id in status.keys():
                if goods_id not in self.user_info_dict[user]['goods'].keys():
                    self.user_status_dict[user].pop(goods_id)
                    logger.info('cancel on sale remind goods[{0}] for user[{1}].'.format(goods_id, user))

    def save_user_status(self):
        try:
            # self.goods_status_dict.update(goods_status)
            content = json.dumps(self.user_status_dict)
            f = open(self.config['goods_status_file'], 'w', encoding='utf-8')
            f.write(content)
            f.close()
        except Exception as e:
            logger.info('save user status to [{0}] exception: [{1}].'.format(self.config['user_status_file'], e))

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
                self.workers.append(Worker(thread_id, goods_user_info_slice))
                goods_count = 0
                thread_id = thread_id + 1
                goods_user_info_slice = {}

        self.workers.append(Worker(thread_id, goods_user_info_slice))

        for worker in self.workers:
            logger.info('[{0}] [{1}].'.format(worker.id, len(worker.goods_user_info.keys())))
            worker.start()

    def start_to_monitor(self):
        while True:
            try:
                mail_info = self.mail_info_queue.pop()
                if mail_info is not None:
                    self.send_mail(mail_info)
                    self.save_user_status()
            except Exception as e:
                logger.exception('on sale reminder exception: [{0}].'.format(e))

    def send_mail(self, mail_info):
        pass

    def execute(self):
        self.load_goods_user_info()     # 从excel读取用户信息和产品订阅信息
        self.load_user_status()         # 读取过去存储的用户字典
        self.update_user_status()       # 更新用户状态字典
        self.save_user_status()         # 保存新的用户状态字典
        self.activate_workers()         # 激活workers，开始监控
        self.start_to_monitor()
        pass
