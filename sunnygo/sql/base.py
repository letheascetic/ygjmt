# coding: utf-8

import logging
import datetime
from ip_manager.db import Base
from sqlalchemy import Column, VARCHAR, INTEGER, TIMESTAMP, BIGINT, FLOAT


logger = logging.getLogger(__name__)


class IpPool(Base):
    """table for ip_pool"""
    __tablename__ = 'ip_pool'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True, nullable=False)
    ip = Column('ip', VARCHAR(64), index=True, nullable=False)
    port = Column('port', INTEGER, index=True, nullable=False)
    city = Column('city', VARCHAR(32), index=False, nullable=True, default=None)
    vendor = Column('vendor', VARCHAR(32), index=True, nullable=False)
    create_time = Column('create_time', TIMESTAMP, default=datetime.datetime.now, index=False)
    expire_time = Column('expire_time', TIMESTAMP, nullable=False, index=True)
    failed_num = Column('failed_num', INTEGER, nullable=True, default=0)
    success_num = Column('success_num', INTEGER, nullable=True, default=0)

    def to_item(self):
        return {'id': self.id, 'ip': self.ip, 'port': self.port, 'city': self.city, 'vendor': self.vendor,
                'create_time': self.create_time, 'expire_time': self.expire_time}

    @staticmethod
    def from_item(item):
        row = IpPool(
            ip=item['ip'],
            port=item['port'],
            city=item['city'],
            vendor=item['vendor'],
            create_time=item['create_time'],
            expire_time=item['expire_time']
        )
        return row


class Seeker(Base):
    """table for seeker"""
    __tablename__ = 'seeker'

    id = Column('id', VARCHAR(64), primary_key=True, nullable=False)
    tag = Column('tag', VARCHAR(64), index=False, nullable=True)
    ip = Column('ip', VARCHAR(64), index=True, nullable=False)
    register_time = Column('register_time', TIMESTAMP, default=datetime.datetime.now, index=False)

    def to_item(self):
        return {'id': self.id, 'tag': self.tag, 'ip': self.ip, 'register_time': self.register_time}


class CdfBjGoodsInfo(Base):
    """table for cdfbj_goods_info, 用于表述各产品的信息，包括名称、链接、价格、库存、折扣、状态等"""
    __tablename__ = 'cdfbj_goods_info'

    goods_id = Column('goods_id', VARCHAR(64), primary_key=True, nullable=False)    # 商品id
    goods_name = Column('goods_name', VARCHAR(256), nullable=False)                 # 商品名
    goods_url = Column('goods_url', VARCHAR(1024), nullable=False)                  # 商品链接
    goods_status = Column('goods_status', VARCHAR(64), nullable=False, index=True)  # 商品状态[在售、下架、缺货]
    goods_num = Column('goods_num', INTEGER, nullable=True, default=0)              # 商品库存
    goods_price = Column('goods_price', FLOAT, nullable=True, default=None)         # 商品售价
    goods_discount = Column('goods_discount', VARCHAR(128), nullable=True, default=None)    # 商品折扣
    update_time = Column('update_time', TIMESTAMP, nullable=False, onupdate=datetime.datetime.now, default=datetime.datetime.now)

    def __repr__(self):
        return '<CdfBj Goods Info [{0}][{1}][{2}][{3}][{4}][{5}]>'.format(self.goods_id, self.goods_name,
                                                                          self.goods_status, self.goods_num,
                                                                          self.goods_price, self.goods_discount)


class CdfBjSubscriberInfo(Base):
    """table for cdfbj_subscriber_info, 用于表述各产品的订阅信息，包括订阅者id、补货提醒开关、补货提醒阈值、补货提醒状态、折扣提醒开关等"""
    __tablename__ = 'cdfbj_subscriber_info'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True, nullable=False)     # 主id
    goods_id = Column('goods_id', VARCHAR(64), index=True, nullable=False)              # 订阅的商品
    user_id = Column('user_id', VARCHAR(64), index=True, nullable=False)                # 订阅该商品的用户id
    # login_name = Column('login_name', VARCHAR(64), nullable=True, default=None)         # 订阅该商品的用户使用的北京cdf账号
    replenishment_switch = Column('replenishment_switch', INTEGER, default=1)           # 补货提醒开关[0:不提醒]
    replenishment_threshold = Column('replenishment_threshold', INTEGER, default=50)    # 补货提醒阈值[默认50]
    replenishment_flag = Column('replenishment_flag', INTEGER, default=0)       # 商品数量①下降到阈值以下或②超过阈值且还没提醒，这两者情况下置0[0表示需要提醒，1表示已经提醒]
    discount_switch = Column('discount_switch', INTEGER, default=1)                     # 折扣提醒开关[0:不提醒]
    update_time = Column('update_time', TIMESTAMP, nullable=False, onupdate=datetime.datetime.now, default=datetime.datetime.now)

    def __repr__(self):
        return '<CdfBj Subscriber Info [goods_id:{0}][user_id:{1}][{2}:{3}:{4}][{5}]>'\
            .format(self.goods_id, self.user_id, self.replenishment_switch, self.replenishment_threshold,
                    self.replenishment_flag, self.discount_switch)

    def update(self, item):
        replenishment_switch_updated = False

        if item.get('replenishment_switch', None) and item['replenishment_switch'] != self.replenishment_switch:
            replenishment_switch_updated = True
            self.replenishment_switch = item['replenishment_switch']

        if item.get('replenishment_threshold', None) and item['replenishment_threshold'] != self.replenishment_threshold:
            self.replenishment_threshold = item['replenishment_threshold']

        # 补货提醒开关被更新，无条件更新replenishment_flag为0[需要提醒]状态
        if replenishment_switch_updated:
            self.replenishment_flag = 0

        if item.get('discount_switch', None) and item['discount_switch'] != self.discount_switch:
            self.discount_switch = item['discount_switch']

    @staticmethod
    def from_item(item):
        return CdfBjSubscriberInfo(
            goods_id=item['goods_id'],
            user_id=item['user_id'],
            replenishment_switch=item.get('replenishment_switch', 1),
            replenishment_threshold=item.get('replenishment_threshold', 50),
            replenishment_flag=item.get('replenishment_flag', 1),
            discount_switch=item.get('discount_switch', 1)
        )


class CdfBjUserInfo(Base):
    """table for cdfbj_user_info, 用于表述各用户在cdfbj的信息，包括用户id、cdfbj登录名、cdfbj登录密码、状态等"""
    __tablename__ = 'cdfbj_user_info'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(VARCHAR(64), index=True, nullable=False)                           # 对应的用户id
    login_name = Column(VARCHAR(64), index=True, nullable=False)                        # 北京cdf登录名
    login_passwd = Column(VARCHAR(64), index=False, nullable=False)                     # 北京cdf登录密码
    status = Column(INTEGER, index=False, nullable=False, default=0)                    # 账户当前状态[0:正常, 1:密码错误, 2:没有额度 3:其他]
    update_time = Column('update_time', TIMESTAMP, nullable=False, onupdate=datetime.datetime.now, default=datetime.datetime.now)


class User(Base):
    """table for user, 用于表述各用户的信息，包括用户id、昵称、邮箱、邮箱授权码、邮箱状态、密码、注册时间等"""
    __tablename__ = 'user'

    id = Column(VARCHAR(64), primary_key=True, nullable=False)                      # 用户id，唯一
    name = Column(VARCHAR(128), unique=True, nullable=False)                        # 昵称
    email = Column(VARCHAR(128), index=True, nullable=True, default=None)           # 邮箱
    email_code = Column(VARCHAR(64), index=False, nullable=True, default=None)      # 邮箱授权码
    email_status = Column(INTEGER, default=0)                                       # 邮箱是否可用[0:正常 1:授权码有误]
    password = Column(VARCHAR(256), nullable=False)                                 # 登录密码
    register_time = Column(TIMESTAMP, nullable=False, default=datetime.datetime.now)    # 注册时间

    def __repr__(self):
        return '<User [id:{0}][name:{1}][email:{2}]>'.format(self.id, self.name, self.email)

    def update(self, item):
        if not item['name'] and item['name'] != self.name:            # 更新昵称
            self.name = item['name']

        email_updated, email_code_updated = False, False

        if not item['email'] and item['email'] != self.email:         # 更新email
            email_updated = True
            self.email = item['email']

        # 如果邮箱被更新，则授权码无条件被更新，否则只在授权码不一致时更新
        if email_updated or (not item['email_code'] and item['email_code'] != self.email_code):
            email_code_updated = True
            self.email_code = item['email_code']

        # 如果邮箱被更新或授权码被更新，则无条件更新
        if email_updated or email_code_updated:
            self.email_status = 0

    @staticmethod
    def from_item(item):
        return User(
            id=item['user_id'],
            name=item['name'],
            email=item['email'],
            email_code=item['email_code'],
            password=item['user_id'],       # 使用user_id作为密码
        )
