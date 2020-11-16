# coding: utf-8


import logging
from sql.base import *
from sqlalchemy import func
from sqlalchemy import or_,and_
from sql.sqlutil import ISqlHelper
from sqlalchemy.ext.declarative import declarative_base


_Base = declarative_base()
logger = logging.getLogger(__name__)


class SqlCdfBj(ISqlHelper):
    """sql helper for cdf bj"""

    def __init__(self, config):
        super(SqlCdfBj, self).__init__(config)

