# coding: utf-8

import time
import util
import json
import base64
import logging
import datetime
import requests
import smtplib
import random
from urllib import request
from email.utils import formataddr
from email.header import Header
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)
secret_key = {}


# step one: login, get token
def login(user_count):
    url = 'https://mbff.yuegowu.com/login'

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': None}",
               'Authorization': 'Bearer',
               'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/user-center',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }

    base64_name = base64.b64encode(user_count['name'].encode('utf-8')).decode('utf-8')
    base64_password = base64.b64encode(user_count['password'].encode('utf-8')).decode('utf-8')

    data = {'customerAccount': base64_name, 'customerPassword': base64_password}
    data_json = json.dumps(data)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    token = None
    try:
        response = request.urlopen(req)
        if response.status == 200:
            content = response.read().decode('utf-8')
            content_json = json.loads(content)
            logger.info('get request content: [{0}].'.format(content_json))
            if content_json.get('context', None) is not None:
                token = content_json['context'].get('token', None)
                if token is not None:
                    logger.info('login success, get token; [{0}].'.format(token))
    except Exception as e:
        logger.exception('login exception: [{0}].'.format(e))

    return token


# step two: add to cart
def add_to_cart(token, goods_id, num):
    url = 'https://mbff.yuegowu.com/site/purchase'

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }

    data = {'goodsInfoId': goods_id, 'goodsNum': num}
    data_json = json.dumps(data)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')
    try:
        response = request.urlopen(req)
        if response.status == 200:
            content = response.read().decode('utf-8')
            content_json = json.loads(content)
            logger.info('get request content: [{0}].'.format(content_json))
            if content_json.get('code') == 'K-000000':
                logger.info('add to cart[{0}][{1}] success.'.format(goods_id, num))
                return True
            elif content_json.get('code') == 'K-050215':
                logger.info('goods already in cart[{0}][{1}].'.format(goods_id, num))
                return True
    except Exception as e:
        logger.info('add to cart[{0}][{1}] exception: [{2}].'.format(goods_id, num, e))

    logger.info('add to cart[{0}][{1}] failed.'.format(goods_id, num))
    return False


# step three: submit order
def sumbit_order(token, goods_id, goods_num):
    url = 'https://mbff.yuegowu.com/site/purchases'

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/purchase-order',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }
    data = {"goodsInfoIds": [goods_id]}
    data_json = json.dumps(data)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')
    try:
        response = request.urlopen(req)
        if response.status == 200:
            content = response.read().decode('utf-8')
            content_json = json.loads(content)
            logger.info('get request content: [{0}].'.format(content_json))
            if content_json.get('code') == 'K-000000':
                logger.info('submit order[{0}] success.'.format(goods_id))
                try:
                    goodsMarketingMap = content_json['context']['goodsMarketingMap']
                    if not goodsMarketingMap:
                        return True, None, None

                    discount_info_list = content_json['context']['goodsMarketingMap'][goods_id][0]['fullDiscountLevelList']
                    selected_discount_info = None

                    for discount_info in discount_info_list:
                        if discount_info['fullCount'] == goods_num:
                            selected_discount_info = discount_info
                            break
                        elif discount_info['fullCount'] < goods_num:
                            if selected_discount_info is None or \
                                    discount_info['fullCount'] > selected_discount_info['fullCount']:
                                selected_discount_info = discount_info

                    logger.info('submit order[{0}] select discount info: [{1}].'.format(goods_id, selected_discount_info))
                    if selected_discount_info is not None:
                        marketingId = selected_discount_info.get('marketingId', None)
                        marketingLevelId = selected_discount_info.get('discountLevelId', None)
                    else:
                        marketingId = None
                        marketingLevelId = None
                    logger.info('submit order[{0}] parse marketingId[{1}] marketingLevelId[{2}] success.'.format(
                        goods_id, marketingId, marketingLevelId))
                    return True, marketingId, marketingLevelId
                except Exception as e:
                    logger.info('submit order[{0}] parse marketingId marketingLevelId failed: [{1}].'.format(goods_id, e))
                    return True, None, None
    except Exception as e:
        logger.exception('submit order[{0}] exception: [{1}].'.format(goods_id, e))

    logger.info('submit order[{0}] failed.'.format(goods_id))
    return False, None, None


# step four: confirm
def confirm(token, goods_id, num, marketingId, marketingLevelId):
    url = ' https://mbff.yuegowu.com/trade/confirm'

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/purchase-order',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }

    if marketingId is None or marketingLevelId is None:
        data = {"tradeItems":[{"skuId":goods_id,"num":num}],"tradeMarketingList":[],"forceConfirm":False}
    else:
        data = {"tradeItems":[{"skuId":goods_id,"num":num}],"tradeMarketingList":[{"marketingId":marketingId,"marketingLevelId":marketingLevelId,"skuIds":[goods_id],"giftSkuIds":[]}],"forceConfirm":False}

    data_json = json.dumps(data)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='PUT')
    try:
        response = request.urlopen(req)
        if response.status == 200:
            content = response.read().decode('utf-8')
            content_json = json.loads(content)
            logger.info('get request content: [{0}].'.format(content_json))
            if content_json.get('code') == 'K-000000':
                logger.info('confirm order[{0}][{1}] success.'.format(goods_id, num))
                return True
    except Exception as e:
        logger.exception('confirm order[{0}][{1}] exception: [{2}].'.format(goods_id, num, e))

    logger.info('confirm order[{0}][{1}] failed.'.format(goods_id, num))
    return False


# step five: commit
def commit(token, goods_id, num):
    url = ' https://mbff.yuegowu.com/trade/commit'

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/order-confirm',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }
    data = {"consigneeId":"2c91c7f072be4c590173431b74fd62b5","provinceName":"浙江省","cityName":"杭州市","areaName":"余杭区","consigneeAddress":"浙江省杭州市余杭区文一西路西溪泊岸泊寓海港城1号楼","consigneeUpdateTime":None,"storeCommitInfoList":[{"storeId":123456861,"payType":0,"invoiceType":-1,"generalInvoice":{},"specialInvoice":{},"specialInvoiceAddress":False,"invoiceAddressId":"2c91c7f072be4c590173431b74fd62b5","invoiceAddressDetail":"浙江省杭州市余杭区文一西路西溪泊岸泊寓海港城1号楼","invoiceAddressUpdateTime":None,"invoiceProjectId":"","invoiceProjectName":"","invoiceProjectUpdateTime":None,"buyerRemark":"","encloses":"","deliverWay":"1"}],"commonCodeId":None,"orderSource":"WECHAT","forceCommit":False,"shareUserId":None,"flightNumber":"SU208","arriveTime":"2017-05-01 12:00:00","seatNumber":"L68","certificateType":0,"passport":"G50442696","hongkongAndMacaoPass":"","taiwanPass":""}
    data_json = json.dumps(data)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')
    try:
        response = request.urlopen(req)
        if response.status == 200:
            content = response.read().decode('utf-8')
            content_json = json.loads(content)
            logger.info('get request content: [{0}].'.format(content_json))
            if content_json.get('code') == 'K-000000':
                logger.info('commit order[{0}][{1}] success.'.format(goods_id, num))
                return True
    except Exception as e:
        logger.exception('commit order[{0}][{1}] exception: [{0}].'.format(goods_id, num, e))

    logger.info('commit order[{0}][{1}] failed.'.format(goods_id, num))
    return False


def lock_order(user_count, goods_id, num):
    if secret_key.get(user_count['name'], None) is None:
        secret_key['name'] = {'token': None, 'time': None}

    token = secret_key['name'].get('token', None)

    if token is None:
        token = login(user_count)
    elif (datetime.datetime.now() - secret_key['name'].get('time')).total_seconds() > 3600:
        token = login(user_count)

    if token is None:
        return False
    else:
        secret_key['name']['token'] = token
        secret_key['name']['time'] = datetime.datetime.now()

    if not add_to_cart(token, goods_id, num):
        return False

    status, marketingId, marketingLevelId = sumbit_order(token, goods_id, num)
    if not status:
        return False

    if not confirm(token, goods_id, num, marketingId, marketingLevelId):
        return False

    if not commit(token, goods_id, num):
        return False

    return True


def get_goods_info(goods_id):
    try:
        url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}".format(goods_id)
        header = {'Host': 'mbff.yuegowu.com', 'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
                  'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Mobile Safari/537.36',
                  'Content-Type': 'application/json'}

        r = requests.get(url, timeout=10, headers=header)
        if r.status_code == requests.codes.ok:
            content = json.loads(r.text)
            context = content['context']
            if context is None:
                status = '下架'
                return None, None, None, None
            else:
                info = context['goodsInfos'][0]
                stock = info['stock']
                title = info['goodsInfoName']
                if stock > 0:
                    status = '在售'
                else:
                    status = '缺货'
                return title, header['Referer'], stock, status
        else:
            logger.info('request url[{0}] failed with return code: [{1}].'.format(url, r.status_code))
            return None, None, None, None
    except Exception as e:
        logger.exception('get goods info[{0}] failed: [{1}].'.format(goods_id, e))
    return None, None, None, None


def send_mail(info, users):
    goods_title = info['title']
    content = '{0} 锁单成功了,请尽快支付.'.format(goods_title)

    from_addr = 'cdf_bj_updater@163.com'
    code = 'ZYMXQVJTZRVBEJMS'
    smtp_server = 'smtp.163.com'  # 固定写死
    smtp_port = 465  # 固定端口

    users = list(users)
    random.shuffle(users)

    for user in users:
        to_addrs = [user, ]
        i = 0
        while i < 5:
            try:
                # 配置服务器
                stmp = smtplib.SMTP_SSL(smtp_server, smtp_port)
                stmp.login(from_addr, code)
                # 组装发送内容
                message = MIMEText(content, 'plain')  # 发送的内容
                message['From'] = formataddr(["阳光姐妹淘鸭", from_addr])
                message['To'] = ','.join(to_addrs)        # 收件人
                subject = '{0}: 锁单成功了-{1}'.format('cdf北京', goods_title)
                message['Subject'] = Header(subject)  # 邮件标题
                stmp.sendmail(from_addr, to_addrs, message.as_string())
                break
            except Exception as e:
                i = i + 1
                logger.exception('send lock order mail[{0}][{1}] failed; [{2}].'.format(info, to_addrs, e))
                time.sleep(2)


def execute():
    user_count = {'name': '15850563761', 'password': 'Wc19910706', 'email': 'wc1148728402@163.com'}
    lock_goods_list = [
        {'goods_id': '2c9194587219d0ae017219dc973a08e0', 'goods_num': 2},
        {'goods_id': '2c9194597219d0ad017219dc95fb081f', 'goods_num': 3},
        # {'goods_id': '2c9194597219d0ad017219dc91ec04ef', 'goods_num': 7},
        {'goods_id': '2c9194597219d0ad017219dc9297057b', 'goods_num': 3},
        {'goods_id': '2c9194587219d0ae017219dc88af000e', 'goods_num': 2},
        {'goods_id': '2c9194587219d0ae017219dc92ce05a5', 'goods_num': 5},
    ]
    locked_goods_list = []

    while True:
        logger.info('[{0}] has [{1}] goods to lock.'.format(user_count['name'], len(lock_goods_list)))
        if len(lock_goods_list) == 0:
            time.sleep(60)

        for lock_goods in lock_goods_list:
            goods_id = lock_goods['goods_id']
            goods_num = lock_goods['goods_num']

            try:
                title, url, stock, status = get_goods_info(goods_id)
                goods_info = {'title': title, 'url': url, 'status': status, '库存': stock}
                if url is not None and status == '在售':
                    logger.info('goods on sale: [{0}].'.format(goods_info))
                    if stock < goods_num:
                        continue

                    logger.info('[{0}] try to lock order[{1}].'.format(user_count['name'], goods_info))
                    if lock_order(user_count, goods_id, goods_num):
                        logger.info('[{0}] lock order [{1}][{2}] success.'.format(user_count['name'], goods_id, goods_num))
                        locked_goods_list.append(lock_goods)
                        lock_goods_list.remove(lock_goods)
                        logger.info('send mail to [{0}].'.format(user_count['email']))
                        send_mail(goods_info, [user_count['email']])
                    else:
                        logger.info('[{0}] lock order [{1}][{2}] failed.'.format(user_count['name'], goods_id, goods_num))

                    logger.info('[{0}] currently locked order [{1}].'.format(user_count['name'], locked_goods_list))

            except Exception as e:
                logger.exception('[{0}] lock order [{1}][{2}] exception: [{3}].'.format(
                    user_count['name'], goods_id, goods_num, e))

        time.sleep(1)


if __name__ == '__main__':
    util.config_logger('lock_order')
    execute()
    pass

