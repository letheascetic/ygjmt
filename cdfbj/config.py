# coding: utf-8

import logging


LOG_CONFIG = {
    'LOG_DIR': 'log/',
    'LOG_FILE_SIZE': 20*1024*1024,
    'LOG_FILE_BACKUP_COUNT': 5,
    'LOG_LEVER': logging.DEBUG,
    'LOG_FORMAT': logging.Formatter('[%(levelname)s][%(asctime)s][%(module)s][%(funcName)s][%(process)d][%(thread)d][%(message)s]')
}


ON_SALE_REMINDER_CONFIG = {
    'interval': 1,
    'worker_num': 1,
    'goods_user_file': '北京日上补货订阅0712.xlsx',
    'user_status_file': 'user_status.txt',
    'mail_senders': [
        {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},
    ]
}


AUTO_ORDER_REMINDER_CONFIG = {
    'interval': 1,
    'worker_num': 1,
    'goods_user_file': '北京日上补货订阅0712.xlsx',
    'user_status_file': 'user_status.txt',
    'mail_senders': [
        {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},
    ]
}
