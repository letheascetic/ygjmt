# coding: utf-8

import datetime
from server.db import Base
from sqlalchemy import Column, Integer, String, BIGINT, VARCHAR, TIMESTAMP


class UserInfo(Base):
    __tablename__ = 'user_info'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(64), unique=True, nullable=False)
    email = Column(VARCHAR(128), unique=True, nullable=False)
    password = Column(VARCHAR(256), nullable=False)
    user_status = Column(Integer, nullable=False, default=0, index=True)
    email_status = Column(Integer, nullable=False, default=0, index=True)
    register_time = Column(TIMESTAMP, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User [id:{0}][name:{1}]>'.format(self.id, self.name)
