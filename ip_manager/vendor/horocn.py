# coding: utf-8


import json
import time
import logging
import datetime
import requests


logger = logging.getLogger(__name__)


class Horocn(object):
    def __init__(self, config, sql_helper, vendor_name=None):
        self.vendor = vendor_name
        if vendor_name is None:
            self.vendor = 'horocn'
        self._config = config
        self._sql_helper = sql_helper
        self.vendor_initialized = False
        self._package = {'token': '3bdc6a5207ae488f54b52c1741e314a5', 'order_id': 'ICKQ1683498489690861'}
        self.update_time = None

    def init_vendor(self, ip):
        if self.ip_in_white_list(ip):
            self.vendor_initialized = True
            return self.vendor_initialized
        if self.add_to_white_list(ip):
            self.vendor_initialized = True
        logger.info('init vendor[{0}] with ip[{1}] result[{2}].'.format(self.vendor, ip, self.vendor_initialized))
        return self.vendor_initialized

    def check_activated_ips(self):
        if self.update_time is not None and (time.time() - self.update_time) < self._config['interval']:
            return

        # 为初始化成功，则打印提示
        if not self.vendor_initialized:
            logger.info('vendor[{0}] not initialized.'.format(self.vendor))
            return

        # 寻找符合条件的package
        package = self._package

        # 获取可用的ip
        ip_items = self._get_ip_available(package, self._config['ip_num'])

        # 添加到ip pool
        if ip_items:
            self._sql_helper.insert_ip_pool(ip_items)

        # 查询当前正在使用的ip数，计算需要添加的ip数
        ip_activated = self._sql_helper.query_ip_activated(self.vendor, 10)

        if ip_activated >= self._config['ip_num']:
            self.update_time = time.time()

    def _get_ip_available(self, package, ip_num):
        url = 'https://proxyapi.horocn.com/api/v2/proxies?order_id={0}&num={1}&format=json&line_separator=win&can_repeat=yes&user_token={2}'
        url = url.format(package['order_id'], ip_num, package['token'])
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] get ip available[{1}|{2}] response[{3}].'.format(self.vendor, package, ip_num, content))
                if content.get('code', None) == 0:
                    ip_items = []
                    for ip_info in content['data']:
                        ip_item = {'ip': ip_info['host'], 'port': ip_info['port'], 'city': ip_info['city_cn'],
                                   'vendor': self.vendor,
                                   'expire_time': datetime.datetime.now() + datetime.timedelta(seconds=60),
                                   'create_time': datetime.datetime.now()}
                        ip_items.append(ip_item)
                    return ip_items
            logger.info('[{0}] get ip available[{1}|{2}] failed[{3}].'.format(self.vendor, package, ip_num, r.text))
        except Exception as e:
            logger.exception('[{0}] get ip available[{1}|{2}] exception[{3}].'.format(self.vendor, package, ip_num, e))

    def query_white_list(self):
        try:
            url = 'https://proxyapi.horocn.com/api/ip/whitelist'
            data = {'token': self._package['token']}
            r = requests.get(url, timeout=10, params=data, verify=False)

            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] query white list response[{1}].'.format(self.vendor, content))
                if content.get('code', None) == 0:
                    return content['data']
            logger.info('[{0}] query white list failed[{1}].'.format(self.vendor, r.text))
        except Exception as e:
            logger.exception('[{0}] query white list exception[{1}].'.format(self.vendor, e))

    def ip_in_white_list(self, ip):
        white_list = self.query_white_list()
        if white_list is not None:
            if ip in white_list:
                logger.info('[{0}] ip[{1}] in white list[{1}].'.format(self.vendor, ip, white_list))
                return True
            else:
                logger.info('[{0}] ip[{1}] not in white list[{1}].'.format(self.vendor, ip, white_list))
                return False

    def add_to_white_list(self, ip):
        try:
            url = 'https://proxyapi.horocn.com/api/ip/whitelist'
            data = {'token': self._package['token'], 'ip': ip}
            r = requests.put(url, timeout=10, params=data, verify=False)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] add ip[{1}] to white list response[{2}].'.format(self.vendor, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] add ip[{1}] to white list exception[{2}].'.format(self.vendor, ip, e))

    def delete_ip_from_white_list(self, ip):
        if not self.ip_in_white_list(ip):
            return

        try:
            url = 'https://proxyapi.horocn.com/api/ip/whitelist'
            data = {'token': self._package['token'], 'ip': ip}
            r = requests.delete(url, timeout=10, params=data, verify=False)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] delete ip[{1}] from white list response[{2}].'.format(self.vendor, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] delete ip[{1}] from white list exception[{2}].'.format(self.vendor, ip, e))
