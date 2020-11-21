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
    'interval': 0.2,
    'worker_num': 4,
    'ip_pool_num': 6,
    'use_proxy': True,
    'goods_file': '管理员权限北京日上订阅.xlsx',
    'users_file': '管理员权限北京日上订阅用户.xlsx',
    'user_status_file': 'user_status.txt',
    'goods_sale_info_file': 'goods_sale_info.txt',
    'goods_stock_threshold': 50,
    'sys_mail_senders': [
        {"email": '3219276656@qq.com', 'code': 'gcagfrrfnbhndejj'},
    ],
    'mail_senders': [
        # {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},        # cdfbj_vx1
        # {"email": 'letheascetic@163.com', 'code': 'BGDAEEMWDFDGBRVQ'},        # cdfbj_vx1
        {"email": 'cdf_bj_updater_2@163.com', 'code': 'SBMMBSAHCMPDUOWC'},	    # cdfbj_vx2
        {"email": 'cdf_bj_updater_3@163.com', 'code': 'OAJFKDISCBDVRGJE'},	    # cdfbj
        {"email": 'cdf_bj_updater_4@163.com', 'code': 'SJPLBCHBKHIIQCLF'},	    # cdfbj_4
    ]
}



