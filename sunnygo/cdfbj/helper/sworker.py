# coding: utf-8


import time
import logging
import threading


logger = logging.getLogger(__name__)


class SWorker(threading.Thread):

    def __init__(self, name, config, sql_helper, http_util, goods_id_list):
        threading.Thread.__init__(self)
        self.name = name
        self._running = True
        self._config = config
        self._sql_helper = sql_helper
        self._http_util = http_util
        self._goods_id_list = goods_id_list     # 负责查询的产品id
        self._update_time = None

    # def __get_proxy(self):
    #     # 不使能ip proxy，直接返回
    #     if not self._config.get('PROXY_ENABLE', True):
    #         return None
    #
    #     if self._update_time is None or (time.time() - self._update_time) > 30

    def stop(self):
        self._running = False

    def run(self):

        while self._running:
            pass
