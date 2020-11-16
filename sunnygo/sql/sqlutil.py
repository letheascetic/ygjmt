# coding: utf-8

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)


class ISqlHelper(object):
    """interface for sql helper"""

    def __init__(self, config):
        self.config = config
        engine = create_engine(config['DB_CONNECT_STRING'], echo=False)
        session_cls = sessionmaker(bind=engine)
        self.session = session_cls()

    def add(self, row):
        try:
            self.session.add(row)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.exception('add row exception[{0}]'.format(e))
            return False
        finally:
            pass
            # self.session.close()
