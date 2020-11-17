# coding: utf-8

import config
import logging

from utils import util
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


logger = logging.getLogger(__name__)


engine = create_engine(config.MYSQL_CONFIG_TESTING['DB_CONNECT_STRING'], echo=False)
session_cls = sessionmaker(bind=engine)


Base = declarative_base()


def init_db():
    from sql.base import IpPool, Seeker
    Base.metadata.create_all(bind=engine)
    pass


def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    logger.info("Initialized the database.")


if __name__ == "__main__":
    util.config_logger('db')
    init_db()
    pass
