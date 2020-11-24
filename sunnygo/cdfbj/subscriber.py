# coding: utf-8

import time
import random
import logging
from utils import reader
from sql.base import User
from utils.mailer import Mailer
from sql.sqlcdfbj import SqlCdfBj
from cdfbj.helper.sworker import SWorker


logger = logging.getLogger(__name__)


class Subscriber(object):

    def __init__(self, config):
        self.name = 'cdfbj_subscriber'
        self._config = config
        self._sql_helper = SqlCdfBj()
        self._message_queue = []
        self._mailer = Mailer(config)

    def init_sync_db(self):
        """初始化同步数据库"""

        sys_goods_list = reader.load_sys_goods_file(self._config['SYS_GOODS_FILE'])
        sys_user_dict = reader.load_sys_user_file(self._config['SYS_USER_FILE'])

        # 开启会话
        session = self._sql_helper.create_session()

        for user_id in sys_user_dict.keys():
            # 更新db中的user表[用户存在则更新，不存在则插入新用户]
            self._sql_helper.insert_update_user(session, sys_user_dict[user_id])

            # 更新db中的cdfbj_subscriber_info表，为用户更新或添加对应的订阅信息
            for goods_id in sys_goods_list:
                subscriber_info_item = {'goods_id': goods_id, 'user_id': user_id}    # 其他参数使用默认值
                self._sql_helper.insert_update_cdfbj_subscriber_info(session, subscriber_info_item)

        # 结束会话
        self._sql_helper.close_session(session)

    def __get_goods_id_subscribe_info(self):
        """获取cdf北京产品的订阅情况"""
        session = self._sql_helper.create_session()
        subscribe_info = self._sql_helper.get_cdfbj_goods_id_subscribe_info(session)
        self._sql_helper.close_session(session)
        return subscribe_info

    def __distribute_subscribe_tasks(self):
        """将要订阅的产品分配到不同的Worker"""

        # 获取worker（线程数量）
        worker_num = self._config.get('WORKER_NUM', 1)

        # 获取订阅产品的订阅情况

        subscribe_info = self.__get_goods_id_subscribe_info()

        # 根据订阅人数比例重组产品id，生成goods_id_list
        goods_id_list = []
        for goods_id, subscribe_num in subscribe_info:
            # goods_id_list.extend([goods_id for i in range(0, subscribe_num)])
            goods_id_list.extend([goods_id])
        random.shuffle(goods_id_list)

        # 计算每个worker需要查询的产品id数量
        goods_per_thread = int(len(goods_id_list) / worker_num)

        # 将要查询的产品id平均分配到各个worker
        distributed_goods_id_list = []
        for i in range(0, worker_num):
            if i == worker_num - 1:
                goods_id_slice = goods_id_list[i*goods_per_thread:]
            else:
                goods_id_slice = goods_id_list[i*goods_per_thread:(i+1)*goods_per_thread]
            distributed_goods_id_list.append(goods_id_slice)

        return distributed_goods_id_list

    def __do_monitoring(self):
        while True:
            if len(self._message_queue) != 0:
                session = self._sql_helper.create_session()
                try:
                    while len(self._message_queue) != 0:
                        message = self._message_queue.pop()
                        goods_info, subscriber_user_id_list = message[0], message[1]
                        self.__mail_subscribers(session, goods_info, subscriber_user_id_list)
                except Exception as e:
                    logger.exception('do monitoring exception[{0}].'.format(e))
                    session.rollback()
                finally:
                    self._sql_helper.close_session(session)
            else:
                time.sleep(3)

    def __mail_subscribers(self, session, goods_info, subscriber_user_id_list):
        user_id_both = subscriber_user_id_list[0].intersection(subscriber_user_id_list[1])
        user_id_replenishment = subscriber_user_id_list[0] - subscriber_user_id_list[1]
        user_id_discount = subscriber_user_id_list[1] - subscriber_user_id_list[0]

        user_id_list = list(subscriber_user_id_list[0].union(subscriber_user_id_list[1]))
        if not user_id_list:
            return

        logger.info('goods[{0}] send mail to users[{1}].'.format(goods_info, subscriber_user_id_list))

        if user_id_both or user_id_discount:
            mail_title = '折扣/价格变动 {0}'.format(goods_info['title'])
        else:
            mail_title = '补货提醒 {0}'.format(goods_info['title'])
        self._mailer.send_sys_subscriber_mail(mail_title, goods_info, user_id_list)

        try:
            query = session.query(User).filter(User.id.in_(user_id_list)).filter(User.email.isnot(None))
            user_all_list = [user for user in query.all()]
            random.shuffle(user_all_list)
            # user_all_list = user_all_list[0:4]

            for user_data in user_all_list:
                if user_data.id in user_id_both:
                    mail_title = '折扣/价格变动 {0}'.format(goods_info['title'])
                elif user_data.id in user_id_replenishment:
                    mail_title = '补货提醒 {0}'.format(goods_info['title'])
                else:
                    mail_title = '折扣/价格变动 {0}'.format(goods_info['title'])

                response = self._mailer.send_subscriber_mail(user_data, mail_title, goods_info)
                if response['code'] != 0:
                    user_data.email_status = user_data.email_status + 1
                else:
                    user_data.email_status = 0

        except Exception as e:
            logger.exception('goods[{0}] mail subscribers[{1}] exception[{2}].'.format(
                goods_info, subscriber_user_id_list, e))

    def execute(self):
        # self.init_sync_db()

        distributed_goods_id_list = self.__distribute_subscribe_tasks()
        workers = []

        for i in range(0, len(distributed_goods_id_list)):
            worker = SWorker('worker[{0}]'.format(i+1), self._config, distributed_goods_id_list[i], self._message_queue)
            workers.append(worker)
            worker.start()

        # for worker in workers:
        #     worker.join()

        self.__do_monitoring()
