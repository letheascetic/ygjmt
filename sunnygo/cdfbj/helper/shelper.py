# coding: utf-8


import logging
from utils import reader


class SHelper(object):

    def __init__(self, config, sql_helper):
        self._config = config
        self._sql_helper = sql_helper

    def init_sync_db(self):
        """启动同步数据库"""

        sys_goods_list = reader.load_sys_goods_file(self._config['sys_goods_file'])
        sys_user_dict = reader.load_sys_user_file(self._config['sys_user_file'])

        for user_id in sys_user_dict:
            # 更新db中的user表[用户存在则更新，不存在则插入新用户]
            self._sql_helper.insert_update_user(sys_user_dict[user_id])
            # 更新db中的cdfbj_subscriber_info表，为用户更新或添加对应的订阅信息
            
