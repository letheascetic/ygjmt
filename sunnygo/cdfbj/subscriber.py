# coding: utf-8


import json
import time
import jpype
import reader
import random
import logging
import smtplib
import datetime
import requests
from utils import util
from sql.sqlcdfbj import SqlCdfBj

from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class Subscriber(object):

    def __init__(self, config):
        self.name = 'cdfbj_subscriber'
        self._config = config
        self._sql_helper = SqlCdfBj(config['DBCONFIG'])

        jvmPath = jpype.getDefaultJVMPath()
        jarPath = 'demo12345.jar'
        jpype.startJVM(jvmPath, "-Djava.class.path={0}".format(jarPath))
        self.http_util = jpype.JClass('com.fizzy.sistertao.utils.OkHttpUtil')

