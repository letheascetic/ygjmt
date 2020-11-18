# coding: utf-8

from sql.base import *
from db import session_cls
from sqlalchemy import func
from sqlalchemy import or_, and_


logger = logging.getLogger(__name__)


class SqlCdfBj(object):
    """sql helper for cdf bj"""

    def __init__(self):
        self.session_cls = session_cls

    @staticmethod
    def create_session():
        return session_cls()

    @staticmethod
    def close_session(session):
        if session is not None:
            try:
                session.commit()
                session.close()
            except Exception as e:
                logger.info('close session exception[{0}].'.format(e))
                session.rollback()
            session = None

    @staticmethod
    def insert_update_user(session, item):
        try:
            query = session.query(User).filter(User.id == item['user_id'])
            user = query.first()
            if user is not None:
                logger.info('user[{0}] already exists, just update[{1}].'.format(user, item))
                user.update(item)
            else:
                logger.info('insert new user[{0}].'.format(item))
                user = User.from_item(item)
                session.add(user)
            session.commit()
            return True
        except Exception as e:
            logger.exception('insert update user[{0}] exception[{1}].'.format(item, e))
            session.rollback()
            return False

    @staticmethod
    def insert_update_cdfbj_subscriber_info(session, item):
        try:
            query = session.query(CdfBjSubscriberInfo).filter(CdfBjSubscriberInfo.user_id == item['user_id'])\
                .filter(CdfBjSubscriberInfo.goods_id == item['goods_id'])
            info = query.first()
            if info is not None:
                logger.info('cdfbj subscriber info[{0}] already exists, just update[{1}].'.format(info, item))
                info.update(item)
            else:
                logger.info('insert new cdfbj subscriber info[{0}].'.format(item))
                info = CdfBjSubscriberInfo.from_item(item)
                session.add(info)
            session.commit()
            return True
        except Exception as e:
            logger.exception('insert update cdfbj subscriber info[{0}] exception[{1}].'.format(item, e))
            session.rollback()
            return False

    @staticmethod
    def insert_cdfbj_goods_info(session, item):
        try:
            goods_info = CdfBjGoodsInfo.from_item(item)
            session.add(goods_info)
            session.commit()
            return True
        except Exception as e:
            logger.exception('insert cdfbj goods info[{0}] exception[{1}].'.format(item, e))
            session.rollback()
            return False

    @staticmethod
    def get_cdfbj_goods_id_subscribe_info(session):
        """获取cdf北京产品（补货提醒or折扣提醒）的订阅信息"""

        try:
            query = session.query(CdfBjSubscriberInfo.goods_id, func.count('1'))\
                .filter(or_(CdfBjSubscriberInfo.replenishment_switch == 1, CdfBjSubscriberInfo.discount_switch == 1))\
                .group_by(CdfBjSubscriberInfo.goods_id)\
                .order_by(func.count('1').desc())
            return query.all()
        except Exception as e:
            logger.exception('get cdfbj goods id_subscribe info exception[{0}].'.format(e))
            session.rollback()

    @staticmethod
    def get_ip_activated(session, time_remaining=30):
        try:
            expire_time = datetime.datetime.now() + datetime.timedelta(seconds=time_remaining)
            query = session.query(IpPool)\
                .filter(IpPool.expire_time >= expire_time)
            items = [ip.to_item() for ip in query.all()]
            logger.info('get ip activated[{0}] success[{1}].'.format(time_remaining, items))
            return items
        except Exception as e:
            logger.exception('get ip activated[{0}] exception[{1}].'.format(time_remaining, e))
            session.rollback()

    @staticmethod
    def get_cdfbj_goods_info(session, goods_id):
        try:
            query = session.query(CdfBjGoodsInfo).filter(CdfBjGoodsInfo.goods_id == goods_id)
            goods_info = query.first()
            if goods_info is not None:
                item = goods_info.to_item()
                logger.info('get cdfbj goods info[{0}] success[{1}].'.format(goods_id, item))
                return item
        except Exception as e:
            logger.exception('get cdfbj goods info[{0}] exception[{1}].'.format(goods_id, e))
            session.rollback()

    @staticmethod
    def parse_goods_info(goods_id, goods_info):
        return CdfBjGoodsInfo.parse(goods_id, goods_info)
