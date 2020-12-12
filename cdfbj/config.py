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


ON_SALE_REMINDER_CONFIG = {
    'interval': 0.4,
    'worker_num': 2,
    'ip_pool_num': 2,
    'use_proxy': True,
    'goods_user_file': '北京日上订阅公众号粉丝0927.xlsx',
    'user_status_file': 'user_status.txt',
    'goods_sale_info_file': 'goods_sale_info.txt',
    'sys_mail_threshold': 50,
    'sys_mail_senders': [
        {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},
    ],
    'mail_senders': [
        # {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},        # cdfbj_vx1
        # {"email": 'letheascetic@163.com', 'code': 'BGDAEEMWDFDGBRVQ'},        # cdfbj_vx1
        {"email": 'cdf_bj_updater_2@163.com', 'code': 'SBMMBSAHCMPDUOWC'},	    # cdfbj_vx2
        {"email": 'cdf_bj_updater_3@163.com', 'code': 'OAJFKDISCBDVRGJE'},	    # cdfbj
        {"email": 'cdf_bj_updater_4@163.com', 'code': 'SJPLBCHBKHIIQCLF'},	    # cdfbj_4
    ]
}


AUTO_ORDER_REMINDER_CONFIG = {
    'interval': 0.1,
    'worker_num': 1,
    'use_proxy': True,
    'goods_user_file': '北京日上锁单商品信息.xlsx',
    'user_info_file': '北京日上锁单用户信息.xlsx',
    'user_status_file': 'lock_user_status.txt',
    'mail_senders': [
        {"email": 'cdf_bj_updater@163.com', 'code': 'IVLTRNOKUNHJGHUB'},        # cdfbj_vx1
        # {"email": 'letheascetic@163.com', 'code': 'BGDAEEMWDFDGBRVQ'},        # cdfbj_vx1
        # {"email": 'cdf_bj_updater_2@163.com', 'code': 'SBMMBSAHCMPDUOWC'},	    # cdfbj_vx2
        # {"email": 'cdf_bj_updater_3@163.com', 'code': 'OAJFKDISCBDVRGJE'},	    # cdfbj
    ],
    'super_users': [
     # 'wc1148728402@163.com',
    ],
    'monitor_goods_ids': [
        '2c9194587219d0ae017219dc909c03e0',
        '2c9194597219d0ad017219dc919d04b3',
        '2c919458739b621d0173b9ae2b35338e',
        '2c91c7f473bf846f0173c90408311a84',
        '2c9194597219d0ad017219dc900b036e',
        '2c919458759546e501759c6419715ba4',
        '2c91c70a74d4d8270174dc9f1f2c030f',
        '2c91c70a74d4d8270174dc9f1f25030d',
        '2c9194587219d0ae017219dc92e005b5',
        '2c919459739b63e40173b9a396614e85',
        '2c91c7f1739b651d0173b9a5ee972665', 
        '2c91c7f4756ef3620175816047e15201',
        '2c91c7f4756ef3620175816047d351ff',
        '2c91c7f1739b651d0173a03b92450b77', 
        '2c9194597219d0ad017219dc91c804d5',        
    ],
    'DB_CONFIG': MYSQL_CONFIG_TESTING,   # 使用的数据库
}
