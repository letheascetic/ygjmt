# coding: utf-8

import datetime
from flaskr.db import Base
from sqlalchemy import Column, Integer, String, BIGINT, VARCHAR, TIMESTAMP, TEXT


class Post(Base):
    __tablename__ = 'post'
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    author_id = Column(BIGINT, nullable=False, index=True)
    title = Column(VARCHAR(256), nullable=False)
    body = Column(TEXT, nullable=False)
    created = Column(TIMESTAMP, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, author_id, title, body):
        self.author_id = author_id
        self.title = title
        self.body = body

    def __repr__(self):
        return '<Post [id:{0}][title:{1}]>'.format(self.id, self.title)
