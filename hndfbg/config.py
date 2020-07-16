# coding: utf-8

import logging


LOG_CONFIG = {
    'LOG_DIR': 'log/',
    'LOG_FILE_SIZE': 20*1024*1024,
    'LOG_FILE_BACKUP_COUNT': 5,
    'LOG_LEVER': logging.DEBUG,
    'LOG_FORMAT': logging.Formatter('[%(levelname)s][%(asctime)s][%(module)s][%(funcName)s][%(process)d][%(thread)d][%(message)s]')
}

