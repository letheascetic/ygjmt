# coding: utf-8


import time
import logging
import threading


logger = logging.getLogger(__name__)


class SWorker(threading.Thread):

    def __init__(self, name, config, sql_helper, http_util, ip_util, goods_id_list):
        threading.Thread.__init__(self)
        self.name = name
        self._running = True
        self._config = config
        self._sql_helper = sql_helper
        self._http_util = http_util
        self._ip_util = ip_util
        self._goods_id_list = goods_id_list     # 负责查询的产品id
        self._update_time = None
        self._mutex = threading.Lock()

    def stop(self):
        self._running = False

    def update_goods_id_list(self, goods_id_list):
        self._mutex.acquire()
        self._goods_id_list = goods_id_list
        self._mutex.release()

    def __get_goods_info(self, goods_id):
        ip_item = None

        # 确认是否使用IP代理，若使用则获取一个IP Proxy
        if self._config.get('PROXY_ENABLE', True):
            ip_item = self._ip_util.get_proxy()
            if not ip_item:
                return None
            host, port = ip_item['ip'], ip_item['port']
        else:
            host, port = '', -1

        # 获取产品详情
        goods_info = self._http_util.cdfbj_get_goods_info(goods_id, host, port)

        # 如果使用IP代理，则记录访问结果
        if self._config.get('PROXY_ENABLE', True):
            self._ip_util.feedback(ip_item, goods_info)

        return goods_info

    def run(self):
        i = 0
        while self._running:
            i = i + 1
            logger.info('thread[{0}], start [{1}] times........................'.format(self.name, i))

            # 得到goods_id_list的拷贝
            self._mutex.acquire()
            goods_id_list = self._goods_id_list.copy()
            self._mutex.release()

            # 对于每个
            for goods_id in goods_id_list:
                goods_info = self.__get_goods_info(goods_id)

            pass
