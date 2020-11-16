# coding: utf-8


import logging
from sql.base import *
from sqlalchemy import func
from sqlalchemy import or_,and_
from sql.sqlutil import ISqlHelper
from sqlalchemy.ext.declarative import declarative_base


_Base = declarative_base()
logger = logging.getLogger(__name__)


class SqlIpManager(ISqlHelper):
    """sql helper for ip manager"""

    def __init__(self, config):
        super(SqlIpManager, self).__init__(config)

    def query_seeker(self, seeker_id):
        try:
            query = self.session.query(Seeker).filter(Seeker.id == seeker_id)
            seeker = query.first()
            if seeker is not None:
                seeker_info = seeker.to_item()
                logger.info('query seeker[{0}] success[{1}].'.format(seeker_id, seeker_info))
                return seeker_info
        except Exception as e:
            logger.exception('query seeker[{0}] exception[{1}]'.format(seeker_id, e))

    def update_seeker(self, seeker_info):
        try:
            query = self.session.query(Seeker).filter(Seeker.id == seeker_info['id'])
            seeker = query.first()
            if seeker is not None:
                seeker.ip = seeker_info['ip']
                seeker.register_time = seeker_info['register_time']
            else:
                seeker = Seeker(id=seeker_info['id'], ip=seeker_info['ip'],
                                register_time=seeker_info['register_time'], tag=seeker_info['tag'])
                self.add(seeker)
            self.session.commit()
            logger.info('update seeker[{0}] success.'.format(seeker_info))
            return True
        except Exception as e:
            logger.exception('update seeker[{0}] exception[{1}].'.format(seeker_info, e))
            self.session.rollback()
            return False

    def query_ip_activated(self, vendor, time_remaining=0):
        try:
            expire_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=time_remaining)
            query = self.session.query(func.count('1')).filter(IpPool.vendor == vendor)\
                .filter(IpPool.expire_time >= expire_time)
            num = query.one()[0]
            logger.info('query ip activated[{0}|{1}] success[{2}].'.format(vendor, time_remaining, num))
            return num
        except Exception as e:
            logger.exception('query ip activated[{0}|{1}] success[{2}].'.format(vendor, time_remaining, e))

    def insert_ip_pool(self, ip_items):
        try:
            for ip_item in ip_items:
                row = IpPool.from_item(item=ip_item)
                self.add(row)
            logger.info('insert ip pool[{0}] success.'.format(ip_items))
            return True
        except Exception as e:
            logger.exception('insert ip pool[{0}] exception[{1}].'.format(ip_items, e))
            self.session.rollback()
        return False
