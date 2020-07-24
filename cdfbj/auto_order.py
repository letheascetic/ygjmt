# coding: utf-8

import time
import uuid
import json
import base64
import logging
import datetime
from urllib import request


logger = logging.getLogger(__name__)
secret_key_info = {}


# step one: login, get token
def __login(user, proxies):
    user_name = user['email']
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

    base64_name = base64.b64encode(user['login_user'].encode('utf-8')).decode('utf-8')
    base64_password = base64.b64encode(user['login_password'].encode('utf-8')).decode('utf-8')

    data = {'customerAccount': base64_name, 'customerPassword': base64_password}
    data_json = json.dumps(data)

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    response_info = {'token': None, 'customer_id': None}

    i = 0
    while i < 2:
        try:
            i = i + 1
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('context', None) is not None:
                    token = content_json['context'].get('token', None)
                    customer_id = content_json['context'].get('customerId', None)
                    if token is not None and customer_id is not None:
                        logger.info('[{0}] login success, get token[{1}].'.format(user_name, token))
                        response_info['token'] = token
                        response_info['customer_id'] = customer_id
                        return response_info
                return None
        except Exception as e:
            logger.info('[{0}] login exception: [{1}].'.format(user_name, e))


# step two: add to cart
def __add_to_cart(token, goods_id, num, proxies):
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
    while i < 2:
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
                else:
                    return False
        except Exception as e:
            logger.info('add to cart[{0}][{1}] exception: [{2}].'.format(goods_id, num, e))

    logger.info('add to cart[{0}][{1}] failed.'.format(goods_id, num))
    return False


# step three: submit order
def __submit_order(token, goods_id, goods_num, proxies):
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

    goods_info = {}

    i = 0
    while i < 2:
        try:
            i = i + 1
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                # logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('code') == 'K-000000':
                    logger.info('submit order[{0}] success.'.format(goods_id))
                    try:
                        for info in content_json['context']['goodsInfos']:
                            if info['goodsInfoId'] == goods_id:
                                goods_info['goods_price'] = info['salePrice']
                                break

                        goodsMarketingMap = content_json['context']['goodsMarketingMap']
                        if not goodsMarketingMap:
                            return

                        goods_info['storeId'] = goodsMarketingMap[goods_id][0]['storeId']

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

                        goods_info['marketingId'] = marketingId
                        goods_info['marketingLevelId'] = marketingLevelId

                        return goods_info
                    except Exception as e:
                        logger.info('submit order[{0}] parse marketingId marketingLevelId failed: [{1}].'.format(goods_id, e))
            return None
        except Exception as e:
            logger.info('submit order[{0}] exception: [{1}].'.format(goods_id, e))

    logger.info('submit order[{0}] failed.'.format(goods_id))
    return None


# step four: confirm
def __confirm(token, goods_id, goods_num, goods_info, proxies):
    url = 'https://mbff.yuegowu.com/trade/confirm?regId={0}'.format(uuid.uuid4())

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

    marketingId = goods_info.get('marketingId', None)
    marketingLevelId = goods_info.get('marketingLevelId', None)
    price = goods_info.get('goods_price', None)
    if marketingId is None or marketingLevelId is None:
        data = {"tradeItems":[{"skuId":goods_id,"num":goods_num, "price": price}],"tradeMarketingList":[],"forceConfirm":False}
    else:
        data = {"tradeItems":[{"skuId":goods_id,"num":goods_num, "price": price}],"tradeMarketingList":[{"marketingId":marketingId,"marketingLevelId":marketingLevelId,"skuIds":[goods_id],"giftSkuIds":[]}],"forceConfirm":False}

    data_json = json.dumps(data)

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='PUT')

    i = 0
    while i < 2:
        i = i + 1
        try:
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('code') == 'K-000000':
                    logger.info('confirm order[{0}][{1}] success.'.format(goods_id, goods_num))
                    return True
                elif content_json.get('code') == 'K-999997':
                    logger.info('confirm order[{0}][{1}] success.'.format(goods_id, goods_num))
                    return True
            return False
        except Exception as e:
            logger.info('confirm order[{0}][{1}] exception: [{2}].'.format(goods_id, goods_num, e))

    logger.info('confirm order[{0}][{1}] failed.'.format(goods_id, goods_num))
    return False


def __get_list_address(token, proxies):
    url = 'https://mbff.yuegowu.com/customer/addressList?reqId={0}'.format(uuid.uuid4())
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
               'Referer': 'https://m.yuegowu.com/receive-address',
               'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'zh-CN,zh;q=0.9'
               }

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, headers=headers, method='GET')

    address_id = None

    i = 0
    while i < 2:
        i = i + 1
        try:
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('code') == 'K-000000':
                    address_id = content_json['context'][0]['deliveryAddressId']
                return address_id
        except Exception as e:
            logger.info('get address id exception: [{0}].'.format(e))
    return address_id


# step six: commit
def __commit(user, token, goods_id, goods_info, proxies, address_id):
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

    province, city, distinct, address = user['province'], user['city'], user['distinct'], user['address']
    flight, arrive_time, seat, passport = user['flight'], user['arrive_time'], user['seat'], user['passport']

    storeId = goods_info['storeId']

    # data = {"consigneeId":"2c91c7f072be4c590173431b74fd62b5","provinceName":"浙江省","cityName":"杭州市","areaName":"余杭区","consigneeAddress":"浙江省杭州市余杭区文一西路西溪泊岸泊寓海港城1号楼","consigneeUpdateTime":None,"storeCommitInfoList":[{"storeId":123456861,"payType":0,"invoiceType":-1,"generalInvoice":{},"specialInvoice":{},"specialInvoiceAddress":False,"invoiceAddressId":"2c91c7f072be4c590173431b74fd62b5","invoiceAddressDetail":"浙江省杭州市余杭区文一西路西溪泊岸泊寓海港城1号楼","invoiceAddressUpdateTime":None,"invoiceProjectId":"","invoiceProjectName":"","invoiceProjectUpdateTime":None,"buyerRemark":"","encloses":"","deliverWay":"1"}],"commonCodeId":None,"orderSource":"WECHAT","forceCommit":False,"shareUserId":None,"flightNumber":"SU208","arriveTime":"2017-05-01 12:00:00","seatNumber":"L68","certificateType":0,"passport":"G50442696","hongkongAndMacaoPass":"","taiwanPass":""}
    data = {"consigneeId": address_id, "provinceName": province, "cityName": city,
            "areaName": distinct, "consigneeAddress": address, "consigneeUpdateTime": None,
            "storeCommitInfoList": [
                {"storeId": storeId, "payType": 0, "invoiceType": -1, "generalInvoice": {}, "specialInvoice": {},
                 "specialInvoiceAddress": False, "invoiceAddressId": address_id,
                 "invoiceAddressDetail": address, "invoiceAddressUpdateTime": None,
                 "invoiceProjectId": "", "invoiceProjectName": "", "invoiceProjectUpdateTime": None, "buyerRemark": "",
                 "encloses": "", "deliverWay": "1"}], "commonCodeId": None, "orderSource": "WECHAT",
            "forceCommit": False, "shareUserId": None, "flightNumber": flight, "arriveTime": arrive_time,
            "seatNumber": seat, "certificateType": 0, "passport": passport, "hongkongAndMacaoPass": "",
            "taiwanPass": ""}
    data_json = json.dumps(data)

    handler = request.ProxyHandler(proxies)
    opener = request.build_opener(handler)
    req = request.Request(url=url, data=data_json.encode(encoding='utf-8'), headers=headers, method='POST')

    i = 0
    while i < 2:
        i = i + 1
        try:
            response = opener.open(req, timeout=5)
            if response.status == 200:
                content = response.read().decode('utf-8')
                content_json = json.loads(content)
                logger.info('get request content: [{0}].'.format(content_json))
                if content_json.get('code') == 'K-000000':
                    logger.info('commit order[{0}] success.'.format(goods_id))
                    return True
            return False
        except Exception as e:
            logger.info('commit order[{0}] exception: [{0}].'.format(goods_id, e))

    logger.info('commit order[{0}][{1}] failed.'.format(goods_id, user))
    return False


def __get_token(user, proxies):
    user_key = user['email']

    login_required = False
    if user_key in secret_key_info.keys():
        token = secret_key_info[user_key]['token']
        token_time = secret_key_info[user_key]['time']
        if token is None or (time.time() - token_time) > 3600:
            login_required = True
    else:
        login_required = True

    if login_required:
        response = __login(user, proxies)
        if response is not None:
            if user_key not in secret_key_info.keys():
                secret_key_info[user_key] = {}
            secret_key_info[user_key].update(response)
            secret_key_info[user_key]['time'] = time.time()
            return True
        else:
            return False
    return True


def __get_goods_info(token, goods_id, goods_num, proxies):
    response = __submit_order(token, goods_id, goods_num, proxies)
    return response


def __get_address_id(user, token, proxies):
    user_key = user['email']

    if secret_key_info[user_key].get('address_id', None) is None:
        address_id = __get_list_address(token, proxies)
        secret_key_info[user_key]['address_id'] = address_id

    return secret_key_info[user_key].get('address_id', None)


def lock_order(user, goods_id, proxies):
    user_key = user['email']

    if not __get_token(user, proxies):
        return False

    token = secret_key_info[user_key]['token']
    goods_num = user['goods'][goods_id]

    if not __add_to_cart(token, goods_id, goods_num, proxies):
        return False

    goods_info = __get_goods_info(token, goods_id, goods_num, proxies)
    if goods_info is None:
        return False

    if not __confirm(token, goods_id, goods_num, goods_info, proxies):
        return False

    address_id = __get_address_id(user, token, proxies)
    if address_id is None:
        return False

    if not __commit(user, token, goods_id, goods_info, proxies, address_id):
        return False

    return True


if __name__ == "__main__":
    user = {'email': 'yizhifight@163.com',
            'login_user': '15850563761',
            'login_password': 'Wc19910706',
            'province': '江苏',
            'city': '南京',
            'distinct': '秦淮 `',
            'address': '江苏省南京市秦淮区光华路鸿信清新家园22栋',
            'flight': 'SU408',
            'seat': 'L48',
            'arrive_time': '2017-05-01 12:00:00',
            'passport': 'G50442496',
            'goods': {'2c919459726fe64a01728323aca12341': 3, }
            }

    goods_id = '2c919459726fe64a01728323aca12341'

    host = '58.218.92.30'
    port = '2360'
    proxies = {
        'http': 'http://{0}:{1}'.format(host, port),
        'https': 'https://{0}:{1}'.format(host, port)
    }

    lock_order(user, goods_id, proxies)
    pass
