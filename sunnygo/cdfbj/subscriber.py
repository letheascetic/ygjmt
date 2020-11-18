# coding: utf-8

import random
import logging
from utils import reader
from sql.sqlcdfbj import SqlCdfBj


logger = logging.getLogger(__name__)


class Subscriber(object):

    def __init__(self, config):
        self.name = 'cdfbj_subscriber'
        self._config = config
        self._sql_helper = SqlCdfBj()

    def init_sync_db(self):
        """初始化同步数据库"""

        sys_goods_list = reader.load_sys_goods_file(self._config['SYS_GOODS_FILE'])
        sys_user_dict = reader.load_sys_user_file(self._config['SYS_USER_FILE'])

        # 开启会话
        session = self._sql_helper.create_session()

        for user_id in sys_user_dict:
            # 更新db中的user表[用户存在则更新，不存在则插入新用户]
            self._sql_helper.insert_update_user(session, sys_user_dict[user_id])

            # 更新db中的cdfbj_subscriber_info表，为用户更新或添加对应的订阅信息
            for goods_id in sys_goods_list:
                subscriber_info_item = {'good_id': goods_id, 'user_id': user_id}    # 其他参数使用默认值
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
            goods_id_list.extend([goods_id for i in range(0, subscribe_num)])
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
