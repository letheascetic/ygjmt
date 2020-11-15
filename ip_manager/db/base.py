# coding: utf-8

import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, VARCHAR, TEXT, INTEGER, BINARY, TIMESTAMP, SMALLINT, BIGINT, FLOAT, DATE


_Base = declarative_base()


class IpPool(_Base):
    """table for ip_pool"""

    id = Column('id', BIGINT, primary_key=True, autoincrement=True, nullable=False)
    ip = Column('ip', VARCHAR(64), index=True, nullable=False)
    port = Column('port', INTEGER, index=True, nullable=False)
    city = Column('city', VARCHAR(32), index=False, nullable=True, default=None)
    vendor = Column('vendor', VARCHAR(32), index=True, nullable=False)
    create_time = Column('create_time', TIMESTAMP, default=datetime.datetime.utcnow, index=False)
    expire_time = Column('expire_time', TIMESTAMP, nullable=False, index=True)
    failed_num = Column('failed_num', INTEGER, nullable=True, default=0)
    success_num = Column('success_num', INTEGER, nullable=True, default=0)

    def to_item(self):
        return {'id': self.id, 'ip': self.ip, 'port': self.port, 'city': self.city, 'vendor': self.vendor,
                'create_time': self.create_time, 'expire_time': self.expire_time}

    def from_item(self, item):
        row = IpPool(
            ip=item['ip'],
            port=item['port'],
            city=item['city'],
            vendor=item['vendor'],
            expire_time=item['expire_time']
        )
        return row


class Seeker(_Base):
    """table for seeker"""

    id = Column('id', VARCHAR(64), primary_key=True, nullable=False)
    tag = Column('tag', VARCHAR(64), index=False, nullable=True)
    ip = Column('ip', VARCHAR(64), index=True, nullable=False)
    register_time = Column('register_time', TIMESTAMP, default=datetime.datetime.utcnow, index=False)

    def to_item(self):
        return {'id': self.id, 'tag': self.tag, 'ip': self.ip, 'register_time': self.register_time}
