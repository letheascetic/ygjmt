# coding: utf-8

import logging


LOG_CONFIG = {
    'LOG_DIR': 'log/',
    'LOG_FILE_SIZE': 20*1024*1024,
    'LOG_FILE_BACKUP_COUNT': 5,
    'LOG_LEVER': logging.DEBUG,
    'LOG_FORMAT': logging.Formatter('[%(levelname)s][%(asctime)s][%(module)s][%(funcName)s][%(process)d][%(thread)d][%(message)s]')
}


# 数据库配置项
MYSQL_CONFIG_TESTING = {
    'DB_CONNECT_TYPE': 'sqlalchemy',
    'DB_CONNECT_STRING': 'mysql+pymysql://ascetic:ascetic@127.0.0.1:3306/ygjmt_db?charset=utf8mb4'
}


# IP Manager配置项
IP_MANAGER_CONFIG = {
    'VENDORS': {
        'zmhttp': {
            'enabled': True,       # 是否使用该IP供应商
            'ip_num': 1,            # 每次获取IP的数量
            'interval': 360,        # 每次获取IP的时间间隔（单位：秒）
        },
        'horocn': {
            'enabled': True,
            'ip_num': 10,
            'interval': 10,
        }
    },
    'DBCONFIG': MYSQL_CONFIG_TESTING,   # 使用的数据库
}


# CDF北京订阅服务配置项
CDFBJ_SUBSCRIBER_CONFIG = {
    'DBCONFIG': MYSQL_CONFIG_TESTING,   # 使用的数据库
    'SYS_USER_FILE': '管理员权限北京日上订阅用户.xlsx',
    'SYS_GOODS_FILE': '管理员权限北京日上订阅.xlsx',
    'WORKER_NUM': 10,
    'PROXY_ENABLE': True
}


