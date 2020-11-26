# coding: utf-8

import json
import time
import random
import logging
import datetime
import requests
from utils import reader


logger = logging.getLogger(__name__)


class ZmHttp(object):
    def __init__(self, config, sql_helper, vendor_name=None):
        self.vendor = vendor_name
        if vendor_name is None:
            self.vendor = 'zmhttp'
        self._config = config
        self._sql_helper = sql_helper
        self.vendor_initialized = False
        self._packages = [
            #{'appkey': 'beefce6b397e3f7eecbc56f692aef9c3', 'package': '124824'},
            {'appkey': '2252f48ef2c1c33117eb6986dd90e6e6', 'package': '110169'}]
        self._package_index = 0
        self.update_time = None
        self._city_code_dict = reader.load_zmhttp_city_code_dict('zmhttp_city_code_list.xlsx')

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

        # 查询当前正在使用的ip数，计算需要添加的ip数
        ip_activated = self._sql_helper.query_ip_activated(self.vendor, 60)

        # 如果不是刚启动且当前可用的IP数量>=需要的IP数量，则直接返回
        if self.update_time is not None and ip_activated and ip_activated >= self._config['ip_num']:
            # self.update_time = time.time()
            return

        if self.update_time is None:
            ip_num = self._config['ip_num']
        else:
            ip_num = self._config['ip_num'] - ip_activated

        # 寻找符合条件的package
        package = self._get_selected_package(ip_num)

        # 获取满足条件的city
        # city_list = self._sql_helper.query_city_ip_rank(self.vendor, self._config['ip_threshold'])
        city_list = self._sql_helper.query_city_ip_rank2(self.vendor, 20, self._config['ip_threshold'])

        if city_list:
            city_code = self._get_city_code(random.choice(city_list))
        else:
            city_code = '0'

        # 获取可用的ip
        ip_items = self._get_ip_available(package['package'], ip_num, city_code)
        # 添加到ip pool
        if ip_items:
            self._sql_helper.insert_ip_pool(ip_items)

        # 查询当前正在使用的ip数，计算需要添加的ip数
        ip_activated = self._sql_helper.query_ip_activated(self.vendor, 60)

        if ip_activated >= self._config['ip_num']:
            self.update_time = time.time()

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
            i = 0
            while i < 2:
                i = i + 1
                r = requests.get(url, timeout=10)
                if r.status_code == requests.codes.ok:
                    content = json.loads(r.text)
                    logger.info('[{0}] add ip[{1}] to white list response[{2}].'.format(self.vendor, ip, content))
                    if content.get('code', None) == 0:
                        return True
                    else:
                        time.sleep(3)
                        continue
            return False
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

    def _get_ip_available(self, package, ip_num, city_code='0'):
        url = 'http://http.tiqu.alicdns.com/getip3?num={0}&type=2&pro=&city={1}&yys=0&port=11&pack={2}&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=2&regions='
        url = url.format(ip_num, city_code, package)
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

    def _get_city_code(self, city):
        for city_name in self._city_code_dict.keys():
            if city in city_name:
                return self._city_code_dict[city_name]
        return '0'
