# coding: utf-8

import logging


LOG_CONFIG = {
    'LOG_DIR': 'log/',
    'LOG_FILE_SIZE': 20*1024*1024,
    'LOG_FILE_BACKUP_COUNT': 5,
    'LOG_LEVER': logging.DEBUG,
    'LOG_FORMAT': logging.Formatter('[%(levelname)s][%(asctime)s][%(module)s][%(funcName)s][%(process)d][%(thread)d][%(message)s]')
}


MYSQL_CONFIG_TESTING = {
    'DB_CONNECT_TYPE': 'sqlalchemy',
    'DB_CONNECT_STRING': 'mysql+pymysql://ascetic:ascetic@127.0.0.1:3306/ygjmt_db?charset=utf8mb4'
}


MYSQL_CONFIG_PRODUCTION = {
    'DB_CONNECT_TYPE': 'sqlalchemy',
    'DB_CONNECT_STRING': 'mysql+pymysql://ygjmt:Fizzystudio#1.@101.132.173.34:3306/ygjmt_db?charset=utf8mb4'
}


IP_MANAGER_CONFIG = {
    'VENDORS': {
        'zmhttp': {
        'enabled': True,
        'ip_num': 3,
        'interval': 60,
        },
    },
    'DBCONFIG': MYSQL_CONFIG_TESTING,

}

