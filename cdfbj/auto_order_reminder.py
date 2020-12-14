# coding: utf-8

import util
import json
import time
import reader
import random
import logging
import datetime
import auto_order
from sql.sqlcdfbj import SqlCdfBj
from auto_order_remind_worker import Worker


logger = logging.getLogger(__name__)


class AutoOrderReminder(object):
    message_queue = None
    goods_user_info = None      # 产品用户字典，记录产品订阅的用户
    user_info_dict = None       # 用户信息字典，包含用户名、密码、邮箱、订阅的产品及提醒阈值
    user_status_dict = None     # 用户状态字典，记录用户订阅的产品是否已经发起过提醒

    workers = []

    def __init__(self, config):
        self.name = 'cdfbj_auto_order'
        self.config = config
        self.message_queue = set()
        self._update_time = None
        self._tag = json.dumps({'WORKER_NUM': self.config.get('worker_num', 1)})
        self._sql_helper = SqlCdfBj()
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

            self.workers.append(Worker(thread_id, self.config, self.message_queue, self.goods_user_info,
                                       self.user_info_dict, self.user_status_dict, goods_ids_slice))

        for worker in self.workers:
            # logger.info('[{0}] [{1}].'.format(worker.id, len(worker.goods_user_info.keys())))
            worker.start()

    def get_random_goods_ids(self):
        goods_ids = []
        for goods_id in self.goods_user_info.keys():
            # user_num = len(self.goods_user_info.get(goods_id, []))
            # goods_ids.extend([goods_id] * user_num)
            goods_ids.append(goods_id)
        random.shuffle(goods_ids)
        return goods_ids

    def start_to_monitor(self):
        self.__heart_beats()

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

                if last_time is None or (time.time() - last_time) > time_interval:
                    user = self.user_info_dict[users[next_user_index]]
                    self.init_lock_user_info(user)
                    # auto_order.save_goods_lock_info()
                    last_time = time.time()
                    next_user_index = next_user_index + 1
                    if next_user_index == len(users):
                        next_user_index = 0

                time.sleep(10)
                self.__heart_beats()
            except Exception as e:
                logger.exception('on sale reminder exception: [{0}].'.format(e))

    def __heart_beats(self):
        if self._update_time is None or time.time() - self._update_time > 10:
            session = self._sql_helper.create_session()
            try:
                seeker_info = {'id': self.name, 'tag': self._tag, 'ip': None, 'register_time': datetime.datetime.now()}
                self._sql_helper.update_seeker(session, seeker_info)
            except Exception as e:
                logger.exception('heart beats exception[{0}].'.format(e))
                session.rollback()
            finally:
                self._sql_helper.close_session(session)
            self._update_time = time.time()

    def init_lock_user_info(self, user):
        logger.info('init lock user info: [{0}].'.format(user))
        host, port = None, 8888
        auto_order.init_user_info(user, host, port)

    def execute(self):
        self.load_goods_user_info()     # 从excel读取用户信息和产品订阅信息
        self.load_user_status()         # 读取过去存储的用户字典
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
