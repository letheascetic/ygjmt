# coding: utf-8

import time
import random
import logging
import threading


logger = logging.getLogger(__name__)


class IpUtil(object):
    def __init__(self, config, sql_helper):
        self.name = 'ip_util'
        self._config = config
        self._sql_helper = sql_helper
        self._update_time = None
        self._ip_items = []
        self._mutex = threading.Lock()

    def get_proxy(self):
        # 不使能ip proxy，直接返回
        if not self._config.get('PROXY_ENABLE', True):
            return None

        # 每隔指定的时间，更新本地ip
        if self._update_time is None or (time.time() - self._update_time) > 10:
            ip_items = self._sql_helper.get_ip_activated(time_remaining=60)
            if ip_items:
                self._ip_items = ip_items

        # 没有可用ip，返回None
        if not self._ip_items:
            logger.info('get proxy no ip item[{0}] activated now.'.format(self._ip_items))
            return None

        return random.choice(self._ip_items)

    def feedback(self, ip_item, success):
        """更新指定IP的失败或成功次数"""
        self._mutex.acquire()
        if success:
            ip_item['success_num'] = ip_item['success_num'] + 1
        else:
            ip_item['failed_num'] = ip_item['failed_num'] + 1
        self._mutex.release()
