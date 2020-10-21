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
    'interval': 0.1,
    'worker_num': 15,
    'goods_user_file': '海绵补货订阅通知1019.xlsx',
    'user_status_file': 'user_status.txt',
    'goods_sale_info_file': 'goods_sale_info.txt',
    'mail_senders': [
        {"email": 'buhuoupdater@163.com', 'code': 'SKJKHLBZEBRLUVDM'},
    ]
}

