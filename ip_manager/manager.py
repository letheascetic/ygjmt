# coding: utf-8

import util
import time
import logging
import datetime
import requests
from vendor.zmhttp import ZmHttp
from sql.sqlim import SqlIpManager


from scrapy.selector import Selector


logger = logging.getLogger(__name__)


class Manager(object):
    def __init__(self, config):
        self.name = 'ip_manager'
        self.config = config
        self.sql_helper = SqlIpManager(config['DBCONFIG'])
        self.vendors = []
        for vendor_name in config.get('VENDORS', []):
            if config['VENDORS'][vendor_name]['enabled']:
                logger.info('activated vendor[{0}] with config[{1}].'.format(vendor_name, config['VENDORS'][vendor_name]))
                self.vendors.append(ZmHttp(config['VENDORS'][vendor_name], self.sql_helper, vendor_name))
        self.seeker_info = None
        self.update_time = time.time()

    def __get_local_ip(self):
        url = 'https://ip.tool.lu/'
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                logger.info('get local ip response[{0}].'.format(r.text))
                local_ip = r.text.split('\r\n')[0].split(':')[-1].strip()
                return local_ip
            logger.info('[{0}] get local ip from url[{1}] failed[{2}].'.format(self.name, url, r.text))
        except Exception as e:
            logger.exception('[{0}] get local ip from url[{1}] exception[{2}].'.format(self.name, url, e))

    def __init(self):
        self.seeker_info = self.sql_helper.query_seeker(self.name)
        ip = self.__get_local_ip()

        # 第一次使用ip manager，需要在seeker中注册ip manager
        if ip is not None and self.seeker_info is None:
            self.seeker_info = {'id': self.name, 'tag': None, 'ip': ip, 'register_time': datetime.datetime.now()}
            self.sql_helper.update_seeker(self.seeker_info)

        # 本地ip发生变更，更新seeker中ip manager数据
        if ip is not None and ip != self.seeker_info['ip']:
            logger.info('local ip changed from [{0}] to [{1}].'.format(self.seeker_info['ip'], ip))
            self.seeker_info['ip'] = ip

        # 启动后初始化，需要更新seeker中ip manager数据，同时更新各ip vendor
        self.sql_helper.update_seeker(self.seeker_info)

        # 更新各ip vendor
        for vendor in self.vendors:
            vendor.init_vendor(self.seeker_info['ip'])

    def __update(self):
        time_span = time.time() - self.update_time
        if time_span < 600:
            return

        self.update_time = time.time()

        # 获取本地ip
        ip = self.__get_local_ip()
        if ip is None:
            return

        # 更新register time
        self.seeker_info['register_time'] = datetime.datetime.now()

        # 本地ip发生变更，更新seeker info中的ip
        if self.seeker_info['ip'] != ip:
            logger.info('local ip changed from [{0}] to [{1}].'.format(self.seeker_info['ip'], ip))
            self.seeker_info['ip'] = ip
            # 更新各vendor
            for vendor in self.vendors:
                vendor.vendor_initialized = False
                vendor.init_vendor(self.seeker_info['ip'])

        # 本地ip没有发生变化，只更新没有初始化成功的vendor
        else:
            for vendor in self.vendors:
                if not vendor.vendor_initialized:
                    vendor.init_vendor(ip)

        # 更新ip manager到seeker表
        self.sql_helper.update_seeker(self.seeker_info)

    def __push_ips(self):
        for vendor in self.vendors:
            vendor.check_activated_ips()

    def execute(self):
        # 初始化
        self.__init()

        while True:
            try:
                time.sleep(10)
                self.__push_ips()
                self.__update()
            except Exception as e:
                logger.exception('execute [{0}] exception[{1}].'.format(self.name, e))


if __name__ == "__main__":
    util.config_logger('ip manager')

    import config
    manager = Manager(config.IP_MANAGER_CONFIG)
    manager.execute()
    pass
