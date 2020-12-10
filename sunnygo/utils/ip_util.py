# coding: utf-8

import time
import random
import logging
import threading
from sql.base import IpPool
from sql.sqlcdfbj import SqlCdfBj


logger = logging.getLogger(__name__)


class IpUtil(object):

    _ip_items = []

    def __init__(self, config):
        self.name = 'ip_util'
        self._config = config
        self._sql_helper = SqlCdfBj()
        self._update_time = None

        self._mutex = threading.Lock()

    def get_proxy(self):
        # 不使能ip proxy，直接返回
        if not self._config.get('PROXY_ENABLE', True):
            return None

        # 每隔指定的时间，更新本地ip，并将Ip Proxy的访问成功次数和失败次数同步到db
        if self._update_time is None or (time.time() - self._update_time) > 30:
            ip_id_list = [ip['id'] for ip in IpUtil._ip_items]
            session = self._sql_helper.create_session()
            try:
                query = session.query(IpPool).filter(IpPool.id.in_(ip_id_list))
                for ip_data in query.all():
                    ip_index = ip_id_list.index(ip_data.id)
                    ip_data.success_num = ip_data.success_num + IpUtil._ip_items[ip_index]['success_num']
                    ip_data.failed_num = ip_data.failed_num + IpUtil._ip_items[ip_index]['failed_num']

                session.commit()
                IpUtil._ip_items = self._sql_helper.get_ip_activated(session, time_remaining=30)
            except Exception as e:
                logger.exception('get proxy exception[{0}].'.format(e))
                session.rollback()
            finally:
                self._sql_helper.close_session(session)

            self._update_time = time.time()

        # 没有可用ip，返回None
        if not IpUtil._ip_items:
            logger.info('get proxy no ip item[{0}] activated now.'.format(IpUtil._ip_items))
            return None

        return random.choice(IpUtil._ip_items)

    def feedback(self, ip_item, success):
        """更新指定IP的失败或成功次数"""
        self._mutex.acquire()
        if success:
            ip_item['success_num'] = ip_item['success_num'] + 1
        else:
            ip_item['failed_num'] = ip_item['failed_num'] + 1
        self._mutex.release()
