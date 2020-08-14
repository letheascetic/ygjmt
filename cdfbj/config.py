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
    'interval': 0.25,
    'worker_num': 3,
    'ip_pool_num': 3,
    'use_proxy': True,
    'goods_user_file': '北京日上订阅公众号粉丝0814.xlsx',
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
    ]
}


AUTO_ORDER_REMINDER_CONFIG = {
    'interval': 0.25,
    'worker_num': 2,
    'ip_pool_num': 2,
    'use_proxy': True,
    'goods_user_file': '北京日上锁单商品信息.xlsx',
    'user_info_file': '北京日上锁单用户信息.xlsx',
    'user_status_file': 'lock_user_status.txt',
    'mail_senders': [
        {"email": 'cdf_bj_updater@163.com', 'code': 'ZYMXQVJTZRVBEJMS'},        # cdfbj_vx1
        # {"email": 'letheascetic@163.com', 'code': 'BGDAEEMWDFDGBRVQ'},        # cdfbj_vx1
        # {"email": 'cdf_bj_updater_2@163.com', 'code': 'SBMMBSAHCMPDUOWC'},	    # cdfbj_vx2
        # {"email": 'cdf_bj_updater_3@163.com', 'code': 'OAJFKDISCBDVRGJE'},	    # cdfbj
    ],
    'super_users': [
        'fch960301@163.com',
        'yizhifight@163.com',
        '502544609@qq.com',
        'hjj_duiyi@163.com',
        'liukaixia136@163.com',
        '334220735@qq.com',
        'yj975005962@163.com',
        '87845698@qq.com',
        'cdf_bj_updater@163.com',
        'letheascetic@163.com',
        '475453260@qq.com',
        '346857309@qq.com',
        '846119389@qq.com',
        '1054518030@qq.com'
    ]
}
