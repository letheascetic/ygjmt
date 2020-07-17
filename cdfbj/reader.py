# coding: utf-8

import logging
from openpyxl import load_workbook


logger = logging.getLogger(__name__)


def load_goods_user_info(filename):
    workbook = load_workbook(filename)
    sheets = workbook.get_sheet_names()
    booksheet = workbook.get_sheet_by_name(sheets[0])

    rows = booksheet.rows
    # columns = booksheet.columns

    content = {}
    i = 1
    for row in rows:
        i = i+1
        email = booksheet.cell(row=i, column=3).value
        if email is None or email.strip().isspace() or '@' not in email:
            continue
        email = email.strip()
        goods_ids = []
        if email in content.keys():     # 同一个人过去的数据
            # goods_ids = content[email]
            continue

        urls = [booksheet.cell(row=i, column=j).value for j in range(4, 10)]
        urls = [url for url in urls if url and url.strip()]
        for url in urls:
            try:
                url = [u for u in url.split(' ') if 'goods-detail' in u]
                for u in url:
                    goods_id = u.split('goods-detail/')[-1].split('/')[0]
                    if goods_id not in goods_ids:
                        goods_ids.append(goods_id)
            except Exception as e:
                logger.exception('parse[{0}] url[{1}] exception: [{2}].'.format(email, url, e))
        content[email] = goods_ids

    # logger.debug('---------------------------------------------------------------------------------')
    # i = 0
    # for email in content.keys():
    #     i = i + 1
    #     logger.debug('[{0}] [{1}]: [{2}].'.format(i, email, content[email]))
    # logger.debug('---------------------------------------------------------------------------------')

    goods_user_dict = {}
    for user, goods_ids in content.items():
        for goods_id in goods_ids:
            if goods_id not in goods_user_dict.keys():
                goods_user_dict[goods_id] = set()
            goods_user_dict[goods_id].add(user)

    # logger.debug('---------------------------------------------------------------------------------')
    # i = 0
    # for goods_id in goods_user_dict.keys():
    #     i = i + 1
    #     logger.debug('[{0}] [{1}]: [{2}].'.format(i, goods_id, goods_user_dict[goods_id]))
    # logger.debug('---------------------------------------------------------------------------------')

    return goods_user_dict


def load_goods_user_info_v2(filename):
    goods_user_info = load_goods_user_info(filename)
    user_info_dict = {}
    for goods_id, users in goods_user_info.items():
        for user in users:
            if user not in user_info_dict.keys():
                user_info_dict[user] = {}
                user_info_dict[user]['email'] = user
                user_info_dict[user]['password'] = None
                user_info_dict[user]['goods'] = {}
            user_info_dict[user]['goods'][goods_id] = 1
    logger.info('goods user info: ----------------------------------------------------------------')
    logger.info(goods_user_info)
    logger.info('---------------------------------------------------------------------------------')
    logger.info('user info dict: ------------------------------------------------------------------')
    logger.info(user_info_dict)
    logger.info('---------------------------------------------------------------------------------')
    return goods_user_info, user_info_dict


def load_lock_goods_user_info(filename):
    goods_user_info = {
        '2c9194587219d0ae017219dc973a08e0': ['15850563761', '15850563806'],
        '2c9194597219d0ad017219dc95fb081f': ['15850563761'],
        '2c9194597219d0ad017219dc9297057b': ['15850563806']
    }

    user_info_list = {
        '15850563761': {
            'password': 'Wc19910706', 'email': 'wc1148728402@163.com',
            'goods': {
                '2c9194587219d0ae017219dc973a08e0': 2,
                '2c9194597219d0ad017219dc95fb081f': 3
            }
        },
        '15850563806': {
            'password': 'Wc19910706', 'email': 'wc1148728402@163.com',
            'goods': {
                '2c9194587219d0ae017219dc973a08e0': 2,
                '2c9194597219d0ad017219dc9297057b': 3
            }
        }
    }

    return goods_user_info, user_info_list


def load_locked_goods_user_info(filename):
    return {}
