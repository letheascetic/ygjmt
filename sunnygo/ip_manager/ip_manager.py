# coding: utf-8


import time
import logging
import datetime
import requests
from utils import util
from functools import reduce
from utils.mailer import Mailer
from sql.sqlim import SqlIpManager
from sqlalchemy import func, or_, and_
from ip_manager.vendor.zmhttp import ZmHttp
from ip_manager.vendor.horocn import Horocn
from sql.base import User, IpPool, CdfBjSubscriberInfo, CdfBjGoodsInfo


logger = logging.getLogger(__name__)


class IpManager(object):
    def __init__(self, config):
        self.name = 'ip_manager'
        self.config = config
        self.sql_helper = SqlIpManager()
        self._mailer = Mailer(config)
        self.vendors = []
        self._vendor_initialized = True
        for vendor_name in config.get('VENDORS', []):
            logger.info('vendor[{0}] with config[{1}].'.format(vendor_name, config['VENDORS'][vendor_name]))
            if config['VENDORS'][vendor_name]['enabled']:
                if vendor_name == 'zmhttp':
                    self.vendors.append(ZmHttp(config['VENDORS'][vendor_name], self.sql_helper, vendor_name))
                elif vendor_name == 'horocn':
                    self.vendors.append(Horocn(config['VENDORS'][vendor_name], self.sql_helper, vendor_name))
                else:
                    logger.warning('unknown vendor[{0}] with config[{1}].'.format(vendor_name, config['VENDORS'][vendor_name]))
        self.seeker_info = None
        self.update_time = datetime.datetime.now()

        today = datetime.datetime.now()
        report_time_str = '{0}-{1}-{2} {3}'.format(today.year, today.month, today.day, config['ROUTINE'].get('report_time', '23:55:00'))
        self._next_report_time = datetime.datetime.strptime(report_time_str, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.now() > self._next_report_time:
            self._next_report_time = self._next_report_time + datetime.timedelta(days=1)

    def __get_local_ip(self):
        url = 'https://ip.tool.lu/'
        try:
            r = requests.get(url, timeout=10, verify=False)
            if r.status_code == requests.codes.ok:
                logger.info('get local ip response[{0}].'.format(r.text))
                local_ip = r.text.split('\r\n')[0].split(':')[-1].strip()
                return local_ip
            logger.info('[{0}] get local ip from url[{1}] failed[{2}].'.format(self.name, url, r.text))
        except Exception as e:
            logger.exception('[{0}] get local ip from url[{1}] exception[{2}].'.format(self.name, url, e))

    def __init(self):
        # 开启会话
        self.sql_helper.begin_session()

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

        self._vendor_initialized = reduce(lambda x, y: x and y, [vendor.vendor_initialized for vendor in self.vendors])

        # 结束会话
        self.sql_helper.close_session()

    def __update(self):
        # 如果有vendor初始化没成功，则尝试再次初始化
        if not self._vendor_initialized:
            ip = self.__get_local_ip()
            if ip is not None:
                self._vendor_initialized = reduce(
                    lambda x, y: x and y,
                    [vendor.init_vendor(ip) for vendor in self.vendors if not vendor.vendor_initialized])

        time_span = (datetime.datetime.now() - self.update_time).total_seconds()
        if time_span < 300:
            return

        # 日期改变，则清除过时的数据
        # if datetime.datetime.now().day != self.update_time.day:
        #     self.sql_helper.delete_stale_data(days=30)

        self.update_time = datetime.datetime.now()

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
                # if not vendor.vendor_initialized:
                vendor.init_vendor(ip)

        # 更新ip manager到seeker表
        self.sql_helper.update_seeker(self.seeker_info)

    def __push_ips(self):
        total_ip = 0
        seekers = ['cdfbj_subscriber', 'cdfbj_auto_order']
        for seeker_id in seekers:
            seeker_info = self.sql_helper.query_seeker(seeker_id)
            if seeker_info and (datetime.datetime.now() - seeker_info['register_time']).total_seconds() <= 300:
                if seeker_info['tag']:
                    total_ip = total_ip + int(seeker_info['tag'])
        logger.info('[{0}] total ip are needed.'.format(total_ip))

        initialized_vendors = [vendor for vendor in self.vendors if vendor.vendor_initialized]
        ips = [total_ip/len(initialized_vendors) for i in range(len(initialized_vendors))]
        ips[-1] = ips[-1] + total_ip - sum(ips)
        for i in range(len(initialized_vendors)):
            initialized_vendors[i].check_activated_ips(ips[i])

    def __report(self):
        if datetime.datetime.now() < self._next_report_time:
            return

        session = self.sql_helper.get_session()
        try:
            # 统计当天Ip的使用情况
            ip_statistics = {}
            create_time = self._next_report_time - datetime.timedelta(days=1)
            query = session.query(IpPool.vendor, func.count('1')).filter(IpPool.create_time > create_time)\
                .filter(or_(IpPool.failed_num <= 30, IpPool.success_num / (IpPool.success_num + IpPool.failed_num) >= 0.85))\
                .group_by(IpPool.vendor)
            for vendor, num in query.all():
                ip_statistics[vendor] = {'good_ip': num, 'bad_ip': 0, 'total_ip': num}

            query = session.query(IpPool.vendor, func.count('1')).filter(IpPool.create_time > create_time)\
                .filter(IpPool.failed_num > 30).\
                filter(IpPool.success_num / (IpPool.success_num + IpPool.failed_num) < 0.85).group_by(IpPool.vendor)
            for vendor, num in query.all():
                ip_statistics[vendor].update({'bad_ip': num})
                ip_statistics[vendor]['total_ip'] = ip_statistics[vendor]['good_ip'] + ip_statistics[vendor]['bad_ip']

            query = session.query(IpPool.vendor, func.sum(IpPool.failed_num), func.sum(IpPool.success_num))\
                .filter(IpPool.create_time > create_time).group_by(IpPool.vendor)
            for vendor, failed, success in query.all():
                ip_statistics[vendor].update({'failed_num': int(failed), 'success_num': int(success),
                                              'total_num': int(failed + success)})

            # 统计当前用户情况
            total_user = session.query(func.count(User.id)).first()[0]

            query = session.query(func.count(func.distinct(CdfBjSubscriberInfo.user_id)))\
                .filter(or_(CdfBjSubscriberInfo.replenishment_switch == 1, CdfBjSubscriberInfo.discount_switch == 1))
            subscriber = query.first()[0]

            query = session.query(User.id, User.email, User.email_code).filter(User.email_status >= 10)
            users = [user for user in query.all()]

            user_statistics = {'total': total_user, 'subscriber': subscriber,
                               'email_error': len(users), 'email_error_users': users}

            # 统计产品情况
            query = session.query(func.count(func.distinct(CdfBjSubscriberInfo.goods_id)))\
                .filter(or_(CdfBjSubscriberInfo.replenishment_switch == 1, CdfBjSubscriberInfo.discount_switch == 1))
            subscribe_goods = query.first()[0]

            total_goods = session.query(func.count(CdfBjGoodsInfo.goods_id)).first()[0]

            goods_statistics = {'total': total_goods, 'subscribe': subscribe_goods}

            # 发送邮件
            mail_title = '{0} daily report'.format(self._next_report_time.strftime('%Y-%m-%d %H:%M:%S'))
            self._mailer.send_report_mail(mail_title, ip_statistics, user_statistics, goods_statistics)

            # 更新下次统计的日期
            self._next_report_time = self._next_report_time + datetime.timedelta(days=1)
        except Exception as e:
            logger.info('report exception[{0}].'.format(e))

    def execute(self):
        # 初始化
        self.__init()

        while True:
            try:
                time.sleep(10)
                self.sql_helper.begin_session()
                self.__push_ips()
                self.__update()
                self.__report()
                self.sql_helper.close_session()
            except Exception as e:
                logger.exception('execute [{0}] exception[{1}].'.format(self.name, e))


if __name__ == "__main__":
    util.config_logger('ip manager')

    import config
    manager = IpManager(config.IP_MANAGER_CONFIG)
    manager.execute()
    pass
