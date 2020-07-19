# coding: utf-8

import uuid
import json
import base64
import logging
import datetime
from urllib import request


logger = logging.getLogger(__name__)
secret_key = {}


# step one: login, get token
def login(user_count, proxies):
    url = 'https://mbff.yuegowu.com/login?regId={0}'.format(uuid.uuid4())

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': None}",
               'Authorization': 'Bearer',
               'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
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

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    i = 0
    token = None
    while i < 3:
        try:
            i = i + 1
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('context', None) is not None:
                    token = content_json['context'].get('token', None)
                    if token is not None:
                        logger.info('login success, get token; [{0}].'.format(token))
                        return token
        except Exception as e:
            logger.info('login exception: [{0}].'.format(e))
    return token


# step two: add to cart
def add_to_cart(token, goods_id, num, proxies):
    url = 'https://mbff.yuegowu.com/site/purchase?regId={0}'.format(uuid.uuid4())

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }

    data = {'goodsInfoId': goods_id, 'goodsNum': num}
    data_json = json.dumps(data)

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    i = 0
    while i < 3:
        try:
            i = i + 1
            response = opener.open(req, timeout=5)
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
def sumbit_order(token, goods_id, goods_num, proxies):
    url = 'https://mbff.yuegowu.com/site/purchases?regId={0}'.format(uuid.uuid4())

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/purchase-order',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }
    data = {"goodsInfoIds": [goods_id]}
    data_json = json.dumps(data)

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    i = 0
    while i < 3:
        try:
            i = i + 1
            response = opener.open(req, timeout=5)
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
            logger.info('submit order[{0}] exception: [{1}].'.format(goods_id, e))

    logger.info('submit order[{0}] failed.'.format(goods_id))
    return False, None, None


# step four: confirm
def confirm(token, goods_id, num, marketingId, marketingLevelId, proxies):
    url = ' https://mbff.yuegowu.com/trade/confirm?regId={0}'.format(uuid.uuid4())

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
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

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='PUT')

    i = 0
    while i < 3:
        i = i + 1
        try:
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('code') == 'K-000000':
                    logger.info('confirm order[{0}][{1}] success.'.format(goods_id, num))
                    return True
        except Exception as e:
            logger.info('confirm order[{0}][{1}] exception: [{2}].'.format(goods_id, num, e))

    logger.info('confirm order[{0}][{1}] failed.'.format(goods_id, num))
    return False


# step five: commit
def commit(token, goods_id, num, proxies):
    url = ' https://mbff.yuegowu.com/trade/commit?regId={0}'.format(uuid.uuid4())

    headers = {'Host': 'mbff.yuegowu.com',
               'Connection': 'keep-alive',
               'Sec-Fetch-Mode': 'cors',
               'Origin': 'https://m.yuegowu.com',
               'distribute-channel': "{'channelType': 1, 'inviteeId': null}",
               'Authorization': 'Bearer {0}'.format(token),
               'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
               'Content-Type': 'application/json',
               'Accept': '*/*',
               'Sec-Fetch-Site': 'same-site',
               'Referer': 'https://m.yuegowu.com/order-confirm',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }

    data = {"consigneeId":"2c91c7f072be4c590173431b74fd62b5","provinceName":"浙江省","cityName":"杭州市","areaName":"余杭区","consigneeAddress":"浙江省杭州市余杭区文一西路西溪泊岸泊寓海港城1号楼","consigneeUpdateTime":None,"storeCommitInfoList":[{"storeId":123456861,"payType":0,"invoiceType":-1,"generalInvoice":{},"specialInvoice":{},"specialInvoiceAddress":False,"invoiceAddressId":"2c91c7f072be4c590173431b74fd62b5","invoiceAddressDetail":"浙江省杭州市余杭区文一西路西溪泊岸泊寓海港城1号楼","invoiceAddressUpdateTime":None,"invoiceProjectId":"","invoiceProjectName":"","invoiceProjectUpdateTime":None,"buyerRemark":"","encloses":"","deliverWay":"1"}],"commonCodeId":None,"orderSource":"WECHAT","forceCommit":False,"shareUserId":None,"flightNumber":"SU208","arriveTime":"2017-05-01 12:00:00","seatNumber":"L68","certificateType":0,"passport":"G50442696","hongkongAndMacaoPass":"","taiwanPass":""}
    data_json = json.dumps(data)

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    i = 0
    while i < 3:
        i = i + 1
        try:
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('code') == 'K-000000':
                    logger.info('commit order[{0}][{1}] success.'.format(goods_id, num))
                    return True
        except Exception as e:
            logger.info('commit order[{0}][{1}] exception: [{0}].'.format(goods_id, num, e))

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
