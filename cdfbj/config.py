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
    'interval': 0.3,
    'worker_num': 4,
    'ip_pool_num': 6,
    'use_proxy': True,
    'auto_order_use_proxy': False,
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
     # 'wc1148728402@163.com',
    ],
    'monitor_goods_ids': [
        '2c9194587219d0ae017219dc909c03e0',
        '2c91c7f47407d82f01740b96635e03ef',
        '2c9194597219d0ad017219dc919d04b3',
        '2c919458739b621d0173b9ae2b35338e',
    ]
}
