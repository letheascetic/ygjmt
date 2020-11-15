# coding: utf-8

import datetime
from flaskr.db import Base
from sqlalchemy import Column, Integer, String, BIGINT, VARCHAR, TIMESTAMP



class IpPool(Base):
    __tablename__ = 'ip_pool'
    id = Column(BIGINT, primary_key=True, autoincrement=True, nullable=False)
    host = Column(VARCHAR(32), index=True, nullable=False)
    port = Column(Integer, index=True, nullable=False)
