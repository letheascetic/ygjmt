# coding: utf-8


import logging
from sql.base import *
from sqlalchemy import func
from sqlalchemy import or_,and_
from sql.sqlutil import ISqlHelper
from sqlalchemy.ext.declarative import declarative_base


_Base = declarative_base()
logger = logging.getLogger(__name__)


class SqlCdfBj(ISqlHelper):
    """sql helper for cdf bj"""

    def __init__(self, config):
        super(SqlCdfBj, self).__init__(config)

    def insert_update_user(self, item):
        try:
            query = self.session.query(User).filter(User.id == item['user_id'])
            user = query.first()
            if user is not None:
                logger.info('user[{0}] already exists, just update[{1}].'.format(user, item))
                user.update(item)
            else:
                logger.info('insert new user[{0}].'.format(item))
                user = User.from_item(item)
                self.add(user)
            self.session.commit()
            return True
        except Exception as e:
            logger.exception('insert update user[{0}] exception[{1}].'.format(item, e))
            self.session.rollback()
            return False

    def insert_update_cdfbj_subscriber_info(self, item):
        try:
            query = self.session.query(CdfBjSubscriberInfo).filter(CdfBjSubscriberInfo.user_id == item['user_id'])\
                .filter(CdfBjSubscriberInfo.goods_id == item['goods_id'])
            info = query.first()
            if info is not None:
                logger.info('cdfbj subscriber info[{0}] already exists, just update[{1}].'.format(info, item))
                info.update(item)
            else:
                logger.info('insert new cdfbj subscriber info[{0}].'.format(item))
                info = User.from_item(item)
                self.add(info)
            self.session.commit()
            return True
        except Exception as e:
            logger.exception('insert update user[{0}] exception[{1}].'.format(item, e))
            self.session.rollback()
            return False
