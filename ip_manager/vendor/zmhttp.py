# coding: utf-8

import json
import time
import logging
import datetime
import requests


logger = logging.getLogger(__name__)


class ZmHttp(object):
    def __init__(self, config, sql_helper, vendor_name=None):
        self.vendor = vendor_name
        if vendor_name is None:
            self.vendor = 'zmhttp'
        self._config = config
        self._sql_helper = sql_helper
        self.vendor_initialized = False
        self._packages = [{'appkey': 'beefce6b397e3f7eecbc56f692aef9c3', 'package': '124824'},
                          {'appkey': '2252f48ef2c1c33117eb6986dd90e6e6', 'package': '110169'}]
        self._package_index = 0
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

        self.update_time = time.time()

        # 为初始化成功，则打印提示
        if not self.vendor_initialized:
            logger.info('vendor[{0}] not initialized.'.format(self.vendor))
            return

        # 查询当前正在使用的ip数，计算需要添加的ip数
        ip_activated = self._sql_helper.query_ip_activated(self.vendor, 60)
        ip_to_add = self._config['ip_num'] - ip_activated
        if ip_to_add <= 0:
            return

        # 寻找符合条件的package
        package = self._get_selected_package(ip_to_add)

        # 获取可用的ip
        ip_items = self._get_ip_available(package['package'], ip_to_add)

        # 添加到ip pool
        if ip_items:
            self._sql_helper.insert_ip_pool(ip_items)

    def _get_selected_package(self, ip_num):
        for package_index in range(self._package_index, len(self._packages)):
            package = self._packages[package_index]
            ip_available = self._query_ip_available(package['appkey'], package['package'])
            # 获取到可用ip数，且大于需要的ip数量，则当前package可用
            if ip_available is not None and ip_available >= ip_num:
                return package
            # 获取到可用ip数，但小于需要的ip数量，如果是最后一个package，则直接返回这个package，不是最后一个package，则查询下一个package
            elif ip_available is not None and ip_available < ip_num:
                if package_index == len(self._packages) - 1:
                    return package
                else:
                    time.sleep(3)
                    continue
            # 获取可用ip数失败，则直接返回当前package
            else:
                return package

    def query_white_list(self):
        try:
            url = 'http://wapi.http.cnapi.cc/index/index/white_list?neek=158245&appkey=237d0703818d39a61a4153c2dd8b3aff'
            r = requests.get(url, timeout=10)

            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] query white list response[{1}].'.format(self.vendor, content))
                if content.get('code', None) == 0:
                    white_list = [ip_info['mark_ip'] for ip_info in content['data']['lists']]
                    return white_list
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
            url = 'http://wapi.http.cnapi.cc/index/index/save_white?neek=158245&appkey=237d0703818d39a61a4153c2dd8b3aff&white={ip}'.format(ip=ip)
            r = requests.get(url, timeout=10)
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
            url = 'http://wapi.http.cnapi.cc/index/index/del_white?neek=158245&appkey=237d0703818d39a61a4153c2dd8b3aff&white={ip}'.format(ip=ip)
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] delete ip[{1}] from white list response[{2}].'.format(self.vendor, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] delete ip[{1}] from white list exception[{2}].'.format(self.vendor, ip, e))

    def _query_ip_available(self, appkey, package):
        url = 'http://wapi.http.cnapi.cc/package_balance?neek=158245&appkey={0}&ac={1}'.format(appkey, package)
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] query ip available[{1}|{2}] response[{3}].'.format(self.vendor, appkey, package, content))
                if content.get('code', None) == 0:
                    return content['data'].get('package_balance', None)
            logger.info('[{0}] query ip available[{1}|{2}] failed[{3}].'.format(self.vendor, appkey, package, r.text))
        except Exception as e:
            logger.exception('[{0}] query ip available[{1}|{2}] exception[{3}].'.format(self.vendor, appkey, package, e))

    def _get_ip_available(self, package, ip_num):
        url = 'http://http.tiqu.alicdns.com/getip3?num={0}&type=2&pro=&city=0&yys=0&port=11&pack={1}&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions='
        url = url.format(ip_num, package)
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] get ip available[{1}|{2}] response[{3}].'.format(self.vendor, package, ip_num, content))
                if content.get('code', None) == 0:
                    ip_items = []
                    for ip_info in content['data']:
                        ip_item = {'ip': ip_info['ip'], 'port': ip_info['port'], 'city': ip_info['city'],
                                   'vendor': self.vendor, 'expire_time': ip_info['expire_time'],
                                   'create_time': datetime.datetime.now()}
                        ip_items.append(ip_item)
                    return ip_items
            logger.info('[{0}] get ip available[{1}|{2}] failed[{3}].'.format(self.vendor, package, ip_num, r.text))
        except Exception as e:
            logger.exception('[{0}] get ip available[{1}|{2}] exception[{3}].'.format(self.vendor, package, ip_num, e))