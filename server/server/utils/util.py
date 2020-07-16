# coding: utf-8

import os
import sys
import logging
from conf.config import LOG_CONFIG
from logging.handlers import TimedRotatingFileHandler


logger = logging.getLogger(__name__)


def config_logger(prefix=None):
    root_logger = logging.getLogger()           # get root logger
    root_logger.setLevel(logging.DEBUG)         # set root logger level

    log_config = LOG_CONFIG
    log_dir = log_config.get('LOG_DIR', 'log/')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # file handler: info.log
    log_file = log_dir + prefix + '.info.log' if prefix is not None else log_dir + 'info.log'

    log_handler = TimedRotatingFileHandler(log_file, when='D', interval=1, backupCount=10, encoding='utf-8')
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(log_config.get('LOG_FORMAT'))
    root_logger.addHandler(log_handler)

    # file_handler：warn.log
    log_file = log_dir + prefix + '.warn.log' if prefix is not None else log_dir + 'warn.log'

    log_handler = TimedRotatingFileHandler(log_file, when='D', interval=1, backupCount=10, encoding='utf-8')
    log_handler.setLevel(logging.ERROR)
    log_handler.setFormatter(log_config.get('LOG_FORMAT'))
    root_logger.addHandler(log_handler)

    # stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(log_config.get('LOG_FORMAT'))
    root_logger.addHandler(stream_handler)
