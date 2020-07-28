# coding: utf-8

import datetime
from flaskr.db import Base
from sqlalchemy import Column, Integer, String, BIGINT, VARCHAR, TIMESTAMP


class CdfbjStaticInfo(Base):
    __tablename__ = 'Cdfbj_static_info'
    goods_id = Column(VARCHAR(64), primary_key=True, nullable=False)
    goods_name = Column(VARCHAR(256), nullable=False)
    goods_url = Column(VARCHAR(1024), nullable=False)
    subscriber_num = Column(Integer, nullable=True, default=None, index=True)
    update_time = Column(TIMESTAMP, nullable=False, onupdate=datetime.datetime.utcnow, index=True)

    def __init__(self, goods_id, goods_name, goods_url, subscriber_num=None):
        self.goods_id = goods_id
        self.goods_name = goods_name
        self.goods_url = goods_url
        self.subscriber_num = subscriber_num

    def __repr__(self):
        return '<Goods Static Info [{0}][{1}][{2}]>'.format(self.goods_id, self.goods_name, self.goods_url)


class CdfbjDynamicInfo(Base):
    __tablename__ = 'Cdfbj_dynamic_info'
    id = Column(BIGINT, primary_key=True, autoincrement=True, nullable=False)
    goods_id = Column(VARCHAR(64), nullable=False, index=True)
    goods_status = Column(VARCHAR(64), nullable=False, index=True)
    goods_num = Column(Integer, nullable=True, default=None)
    update_time = Column(TIMESTAMP, default=datetime.datetime.utcnow, index=True)

    def __init__(self, goods_id, goods_status, goods_num=None):
        self.goods_id = goods_id
        self.goods_status = goods_status
        self.goods_num = goods_num

    def __repr__(self):
        return '<Goods Dynamic Info [{0}][{1}][{2}]>'.format(self.goods_id, self.goods_status, self.goods_num)


class CdfbjSubscriberInfo(Base):
    __tablename__ = 'cdfbj_subscriber_info'
    id = Column(BIGINT, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(BIGINT, nullable=False, index=True)
    goods_id = Column(VARCHAR(64), nullable=False, index=True)
    subscribe_status = Column(Integer, nullable=False, default=0)
    update_time = Column(TIMESTAMP, nullable=False, onupdate=datetime.datetime.utcnow)

    def __init__(self, user_id, goods_id, subscribe_status=0):
        self.user_id = user_id
        self.goods_id = goods_id
        self.subscribe_status = subscribe_status

    def __repr__(self):
        return '<Subscribe Info [user id: {0}][goods id: {1}][status: {2}]>'.format(
            self.user_id, self.goods_id, self.subscribe_status
        )
