# coding: utf-8

import time
import random
import logging
from utils import reader
from sql.base import User
from utils.mailer import Mailer
from sql.sqlcdfbj import SqlCdfBj


logger = logging.getLogger(__name__)


class AutoOrder(object):
    """自助下单"""
    """
        
    """

    def __init__(self, config):
        self.name = 'cdfbj_auto_order'
        self._config = config
        self._sql_helper = SqlCdfBj()
        self._message_queue = []
        self._workers = []
        self._mailers = []
        self._mailer = Mailer(config)

    def init_sync_db(self):
        """初始化自助下单的数据库"""

        
        pass

    def execute(self, argv):
        if 'init' in argv:
            self.init_sync_db()
            return
