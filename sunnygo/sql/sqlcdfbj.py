# coding: utf-8

import logging
from sql.base import *
from db import session_cls
from sqlalchemy import func
from sqlalchemy import or_,and_


logger = logging.getLogger(__name__)


class SqlCdfBj(object):
    """sql helper for cdf bj"""

    def __init__(self):
        self._session = session_cls()

    def insert_update_user(self, item):
        try:
            query = self._session.query(User).filter(User.id == item['user_id'])
            user = query.first()
            if user is not None:
                logger.info('user[{0}] already exists, just update[{1}].'.format(user, item))
                user.update(item)
            else:
                logger.info('insert new user[{0}].'.format(item))
                user = User.from_item(item)
                self.add(user)
            self._session.commit()
            return True
        except Exception as e:
            logger.exception('insert update user[{0}] exception[{1}].'.format(item, e))
            self._session.rollback()
            return False

    def insert_update_cdfbj_subscriber_info(self, item):
        try:
            query = self._session.query(CdfBjSubscriberInfo).filter(CdfBjSubscriberInfo.user_id == item['user_id'])\
                .filter(CdfBjSubscriberInfo.goods_id == item['goods_id'])
            info = query.first()
            if info is not None:
                logger.info('cdfbj subscriber info[{0}] already exists, just update[{1}].'.format(info, item))
                info.update(item)
            else:
                logger.info('insert new cdfbj subscriber info[{0}].'.format(item))
                info = CdfBjSubscriberInfo.from_item(item)
                self.add(info)
            self._session.commit()
            return True
        except Exception as e:
            logger.exception('insert update cdfbj subscriber info[{0}] exception[{1}].'.format(item, e))
            self._session.rollback()
            return False

    def insert_cdfbj_goods_info(self, item):
        try:
            goods_info = CdfBjGoodsInfo.from_item(item)
            self.add(goods_info)
            self._session.commit()
            return True
        except Exception as e:
            logger.exception('insert cdfbj goods info[{0}] exception[{1}].'.format(item, e))
            self._session.rollback()
            return False

    def update_cdfbj_goods_info(self):
        try:
            pass
        except Exception as e:
            logger.exception('update ')

    def get_cdfbj_goods_id_subscribe_info(self):
        """获取cdf北京产品（补货提醒or折扣提醒）的订阅信息"""

        try:
            query = self._session.query(CdfBjSubscriberInfo.goods_id, func.count('1'))\
                .filter(or_(CdfBjSubscriberInfo.replenishment_switch == 1, CdfBjSubscriberInfo.discount_switch == 1))\
                .group_by(CdfBjSubscriberInfo.goods_id)\
                .order_by(func.count('1').desc())
            return query.all()
        except Exception as e:
            logger.exception('get_cdfbj_goods_id_subscribe_info exception[{0}].'.format(e))
            self._session.rollback()

    def get_ip_activated(self, time_remaining=30):
        try:
            expire_time = datetime.datetime.now() + datetime.timedelta(seconds=time_remaining)
            query = self._session.query(IpPool)\
                .filter(IpPool.expire_time >= expire_time)
            items = [ip.to_item() for ip in query.all()]
            logger.info('get ip activated[{0}] success[{1}].'.format(time_remaining, items))
            return items
        except Exception as e:
            logger.exception('get ip activated[{0}] exception[{1}].'.format(time_remaining, e))

    def get_cdfbj_goods_info(self, goods_id):
        try:
            query = self._session.query(CdfBjGoodsInfo).filter(CdfBjGoodsInfo.goods_id == goods_id)
            goods_info = query.first()
            if goods_info is not None:
                item = goods_info.to_item()
                logger.info('get cdfbj goods info[{0}] success[{1}].'.format(goods_id, item))
                return item
        except Exception as e:
            logger.exception('get cdfbj goods info[{0}] exception[{1}].'.format(goods_id, e))

    @staticmethod
    def parse_goods_info(goods_id, goods_info):
        return CdfBjGoodsInfo.parse(goods_id, goods_info)
