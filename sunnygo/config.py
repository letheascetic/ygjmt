# coding: utf-8

import logging


# 日志配置项
LOG_CONFIG = {
    'LOG_DIR': 'log/',
    'LOG_FILE_SIZE': 20*1024*1024,
    'LOG_FILE_BACKUP_COUNT': 5,
    'LOG_LEVER': logging.INFO,
    'LOG_FORMAT': logging.Formatter('[%(levelname)s][%(asctime)s][%(module)s][%(funcName)s][%(process)d][%(thread)d][%(message)s]')
}


# 数据库配置项
MYSQL_CONFIG_TESTING = {
    'DB_CONNECT_TYPE': 'sqlalchemy',
    'DB_CONNECT_STRING': 'mysql+pymysql://ascetic:ascetic@192.168.125.2:3306/ygjmt_db?charset=utf8mb4'
}


# IP Manager配置项
IP_MANAGER_CONFIG = {
    'VENDORS': {
        'zmhttp': {
            'enabled': True,          # 是否使用该IP供应商
            'ip_num': 5,              # 每次获取IP的数量
            'interval': 360,          # 每次获取IP的时间间隔（单位：秒）
            'ip_threshold': 0.95      # 不使用
        },
        'horocn': {
            'enabled': False,
            'ip_num': 10,
            'interval': 10,
        }
    },
    'DB_CONFIG': MYSQL_CONFIG_TESTING,   # 使用的数据库
}


# CDF北京订阅服务配置项
CDFBJ_SUBSCRIBER_CONFIG = {
    'DB_CONFIG': MYSQL_CONFIG_TESTING,   # 使用的数据库
    'SYS_USER_FILE': '管理员权限北京日上订阅用户.xlsx',
    'SYS_GOODS_FILE': '管理员权限北京日上订阅.xlsx',
    'WORKER_NUM': 15,
    'PROXY_ENABLE': True,
    'INTERVAL_ENABLE': True,
    'TIME_INTERVAL': 0.4,
    'SERVER_MAILERS': [
        {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},  # cdfbj_vx1
        {"email": 'cdf_bj_updater_2@163.com', 'code': 'SBMMBSAHCMPDUOWC'},  # cdfbj_vx2
        {"email": 'cdf_bj_updater_3@163.com', 'code': 'OAJFKDISCBDVRGJE'},  # cdfbj
        {"email": 'cdf_bj_updater_4@163.com', 'code': 'SJPLBCHBKHIIQCLF'},  # cdfbj_4
        # {"email": 'letheascetic@163.com', 'code': 'BGDAEEMWDFDGBRVQ'},
    ],
    'SYS_MAILER': {"email": '3219276656@qq.com', 'code': 'gcagfrrfnbhndejj'},
}


