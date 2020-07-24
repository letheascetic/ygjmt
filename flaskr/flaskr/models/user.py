# coding: utf-8

import datetime
from flaskr.db import Base
from sqlalchemy import Column, Integer, String, BIGINT, VARCHAR, TIMESTAMP


class User(Base):
    __tablename__ = 'user'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(64), unique=True, nullable=False)
    password = Column(VARCHAR(256), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User [id:{0}][name:{1}]>'.format(self.id, self.name)
