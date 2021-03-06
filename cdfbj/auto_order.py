# coding: utf-8

import util
import time
import uuid
import json
import jpype
import base64
import logging


jvmPath = jpype.getDefaultJVMPath()
jarPath = 'demo12345.jar'
jpype.startJVM(jvmPath, "-Djava.class.path={0}".format(jarPath))
http_util = jpype.JClass('com.fizzy.sistertao.utils.OkHttpUtil')

logger = logging.getLogger(__name__)
secret_key_info = {}
goods_lock_info = {}


# step one: login, get token
def __login(user, proxyHost, proxyPort):
    user_name = user['email']
    url = 'https://mbff.yuegowu.com/login?regId={0}'.format(uuid.uuid4())

    response_info = {'token': None, 'customer_id': None}

    if not proxyHost:
        proxyHost = ''

    i = 0
    while i < 2:
        try:
            i = i + 1
            
            base64_name = base64.b64encode(user['login_user'].encode('utf-8')).decode('utf-8')
            base64_password = base64.b64encode(user['login_password'].encode('utf-8')).decode('utf-8')

            data = {'customerAccount': base64_name, 'customerPassword': base64_password}
            data_json = json.dumps(data)
    
            response = http_util.login(url, data_json, proxyHost, proxyPort)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
                    if content_json.get('context', None) is not None:
                        token = content_json['context'].get('token', None)
                        customer_id = content_json['context'].get('customerId', None)
                        if token is not None and customer_id is not None:
                            logger.info('[{0}] login success, get token[{1}].'.format(user_name, token))
                            response_info['token'] = token
                            response_info['customer_id'] = customer_id
                            return response_info
                except Exception as err:
                    logger.info('[{0}] login exception: [{1}].'.format(user, err))
                return None
        except Exception as e:
            logger.info('[{0}] login exception: [{1}].'.format(user, e))


# step two query cart & update goods lock info(discount info)
def __query_cart(token, goods_id, host, port):
    url = 'https://mbff.yuegowu.com/site/purchases?regId={0}'.format(uuid.uuid4())
    if not host:
        host = ''

    data = {"goodsInfoIds": []}
    data_json = json.dumps(data)

    cart_status = {}

    i = 0
    while i < 2:
        try:
            i = i + 1
            response = http_util.queryCart(url, token, data_json, host, port)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
                    if content_json.get('code') == 'K-000000':
                        for info in content_json['context']['goodsInfos']:
                            cart_status[info['goodsInfoId']] = info['buyCount']
                            logger.info('query cart info success, goods[{0}] num in cart: [{1}].'.format(info['goodsInfoId'], info['buyCount']))

                            goods_info = {}
                            goods_info['storeId'] = info['storeId']
                            goods_info['marketPrice'] = info['marketPrice']
                            if info['goodsInfoId'] in goods_lock_info.keys():
                                goods_lock_info[info['goodsInfoId']].update(goods_info)
                            else:
                                goods_lock_info[info['goodsInfoId']] = goods_info

                        if goods_id not in cart_status.keys():
                            cart_status[goods_id] = 0
                            logger.info('query cart info success, but no goods[{0}] in cart: [{1}].'.format(goods_id, 0))

                        goodsMarketingMap = content_json['context']['goodsMarketingMap']
                        if goodsMarketingMap is None:
                            logger.info('query cart info, no discount info in response[{0}].'.format(str(response)))
                            return cart_status

                        # 将折扣信息更新到goods lock info
                        for discount_goods_id in content_json['context']['goodsMarketingMap'].keys():
                            discount_info_list = content_json['context']['goodsMarketingMap'][discount_goods_id][0]['fullDiscountLevelList']
                            goods_lock_info[discount_goods_id]['discount'] = discount_info_list

                        logger.info('current goods lock info: [{0}].'.format(goods_lock_info))
                        return cart_status
                    else:
                        logger.info('query goods[{0}] cart info return code: [{1}].'.format(goods_id, content_json.get('code')))
                        return None
                except Exception as e:
                    logger.info('query cart[{0}] exception: [{1}].'.format(goods_id, e))
        except Exception as e:
            logger.info('query cart[{0}] exception: [{1}].'.format(goods_id, e))

    logger.info('query cart[{0}] failed.'.format(goods_id))
    return None


def __delete_goods_in_cart(token, goods_id, host, port):
    url = 'https://mbff.yuegowu.com/site/purchase?regId={0}'.format(uuid.uuid4())
    if not host:
        host = ''

    data = {"goodsInfoIds": [goods_id]}
    data_json = json.dumps(data)

    i = 0
    while i < 2:
        try:
            i = i + 1
            response = http_util.deleteGoods(url, token, data_json, host, port)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
                    if content_json.get('code') == 'K-000000':
                        logger.info('delete goods in cart[{0}] success.'.format(goods_id))
                        return True
                    else:
                        return False
                except Exception as e:
                    logger.info('delete goods in cart[{0}] exception: [{1}].'.format(goods_id, e))
        except Exception as e:
            logger.info('delete goods in cart[{0}] exception: [{1}].'.format(goods_id, e))

    logger.info('delete goods[{0}] failed.'.format(goods_id))
    return False


# step two: add to cart
def __add_to_cart(token, goods_id, num, host, port):
    url = 'https://mbff.yuegowu.com/site/purchase?regId={0}'.format(uuid.uuid4())
    if not host:
        host = ''

    data = {'goodsInfoId': goods_id, 'goodsNum': num}
    data_json = json.dumps(data)

    i = 0
    while i < 2:
        try:
            i = i + 1
            response = http_util.addToCart(url, token, data_json, host, port)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
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
        except Exception as e:
            logger.info('add to cart[{0}][{1}] exception: [{2}].'.format(goods_id, num, e))

    logger.info('add to cart[{0}][{1}] failed.'.format(goods_id, num))
    return False


# step three: submit order
def __submit_order(token, goods_id, goods_num, host, port):
    url = 'https://mbff.yuegowu.com/site/purchases?regId={0}'.format(uuid.uuid4())
    if not host:
        host = ''

    data = {"goodsInfoIds": [goods_id]}
    data_json = json.dumps(data)

    goods_info = {}

    i = 0
    while i < 2:
        try:
            i = i + 1
            response = http_util.submitOrder(url, token, data_json, host, port)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
                    if content_json.get('code') == 'K-000000':
                        logger.info('submit order[{0}] success.'.format(goods_id))
                        try:
                            goods_info['marketPrice'] = content_json['context']['tradePrice']

                            goodsMarketingMap = content_json['context']['goodsMarketingMap']
                            if not goodsMarketingMap:
                                logger.info('[{0}] no discount info in response content[{1}].'.format(goods_id, str(response)))
                                goods_info['storeId'] = 123456861
                                if goods_id not in goods_lock_info.keys() and i == 1:
                                    continue
                            else:
                                goods_info['storeId'] = goodsMarketingMap[goods_id][0]['storeId']
                                discount_info_list = content_json['context']['goodsMarketingMap'][goods_id][0]['fullDiscountLevelList']
                                goods_info['discount'] = discount_info_list

                            if goods_id not in goods_lock_info.keys():
                                goods_lock_info[goods_id] = goods_info
                            else:
                                goods_lock_info[goods_id].update(goods_info)

                            logger.info('submit order[{0}] discount info: [{1}].'.format(goods_id, goods_info))
                            return goods_info
                        except Exception as e:
                            logger.info('submit order[{0}] failed: [{1}][{2}].'.format(goods_id, str(response), e))
                except Exception as e:
                    logger.info('submit order[{0}] exception: [{1}].'.format(goods_id, e))
        except Exception as e:
            logger.info('submit order[{0}] exception: [{1}].'.format(goods_id, e))

    logger.info('submit order[{0}] failed.'.format(goods_id))
    return None


# step four: confirm
def __confirm(token, goods_id, goods_num, goods_info, host, port):
    url = 'https://mbff.yuegowu.com/trade/confirm?regId={0}'.format(uuid.uuid4())
    if not host:
        host = ''

    discount_info = goods_info['discount']
    if discount_info is not None:
        marketingId = discount_info.get('marketingId', None)
        marketingLevelId = discount_info.get('discountLevelId', None)
    else:
        marketingId = None
        marketingLevelId = None
    price = goods_info.get('goods_price', None)

    if marketingId is None or marketingLevelId is None:
        tradePrice = price * goods_num
        # data = {"tradeItems": [{"skuId": "2c9194597219d0ad017219dc903b0396", "num": 1}], "tradeMarketingList": [],"forceConfirm": False, "tradePrice": tradePrice}
        data = {"tradeItems": [{"skuId": goods_id, "num": goods_num}], "tradeMarketingList": [], "forceConfirm": False, "tradePrice": tradePrice}
    else:
        tradePrice = price * goods_num * discount_info['discount']
        # data = {"tradeItems":[{"skuId":goods_id,"num":goods_num, "price": price}],"tradeMarketingList":[{"marketingId":marketingId,"marketingLevelId":marketingLevelId,"skuIds":[goods_id],"giftSkuIds":[]}],"forceConfirm":False}
        data = {"tradeItems":[{"skuId":goods_id,"num":goods_num}],"tradeMarketingList":[{"marketingId":marketingId,"marketingLevelId":marketingLevelId,"skuIds":[goods_id],"giftSkuIds":[]}],"forceConfirm":False,"tradePrice":tradePrice}
        # {"tradeItems":[{"skuId":"2c9194597219d0ad017219dc903b0396","num":6}],"tradeMarketingList":[{"marketingId":715,"marketingLevelId":1647,"skuIds":["2c9194597219d0ad017219dc903b0396"],"giftSkuIds":[]}],"forceConfirm":false,"tradePrice":2049.6}

    data_json = json.dumps(data)

    i = 0
    while i < 2:
        i = i + 1
        try:
            response = http_util.confirm(url, token, data_json, host, port)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
                    if content_json.get('code') == 'K-000000':
                        logger.info('confirm order[{0}][{1}] success.'.format(goods_id, goods_num))
                        return True
                    elif content_json.get('code') == 'K-999997':
                        logger.info('confirm order[{0}][{1}] success.'.format(goods_id, goods_num))
                        return True
                except Exception as e:
                    logger.info('confirm order[{0}][{1}] exception: [{2}].'.format(goods_id, goods_num, e))
            return False
        except Exception as e:
            logger.info('confirm order[{0}][{1}] exception: [{2}].'.format(goods_id, goods_num, e))

    logger.info('confirm order[{0}][{1}] failed.'.format(goods_id, goods_num))
    return False


def __get_list_address(token, host, port):
    url = 'https://mbff.yuegowu.com/customer/addressList?reqId={0}'.format(uuid.uuid4())

    if not host:
        host = ''

    address_id = None

    i = 0
    while i < 2:
        i = i + 1
        try:
            response = http_util.getListAddress(url, token, host, port)
            if response:
                try:
                    content_json = json.loads(str(response))
                    logger.info('get request content: [{0}].'.format(content_json))
                    if content_json.get('code') == 'K-000000':
                        address_id = content_json['context'][0]['deliveryAddressId']
                    return address_id
                except Exception as e:
                    logger.info('get address id exception: [{0}].'.format(e))
        except Exception as e:
            logger.info('get address id exception: [{0}].'.format(e))
    return address_id


# step six: commit
def __commit(user, token, goods_id, goods_info, host, port, address_id):
    url = ' https://mbff.yuegowu.com/trade/commit?regId={0}'.format(uuid.uuid4())

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
                 "encloses": "", "deliverWay": "1"}], "commonCodeId": None, "orderSource": "LITTLEPROGRAM",
            "forceCommit": False, "shareUserId": None, "flightNumber": flight, "arriveTime": arrive_time,
            "seatNumber": seat, "certificateType": 0, "passport": passport, "hongkongAndMacaoPass": "",
            "taiwanPass": "", "taiwanPassName":""}
    data_json = json.dumps(data)

    i = 0
    while i < 2:
        i = i + 1
        try:
            response = http_util.commit(url, token, data_json, host, port)
            if response:
                try:
                    logger.info('get request content: [{0}].'.format(str(response)))
                    content_json = json.loads(str(response))
                    if content_json.get('code') == 'K-000000':
                        logger.info('commit order[{0}] success.'.format(goods_id))
                        return True
                except Exception as e:
                    logger.info('commit order[{0}] exception: [{0}].'.format(goods_id, e))
            return False
        except Exception as e:
            logger.info('commit order[{0}] exception: [{0}].'.format(goods_id, e))

    logger.info('commit order[{0}][{1}] failed.'.format(goods_id, user))
    return False


def __get_token(user, proxyHost, proxyPort):
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
        response = __login(user, proxyHost, proxyPort)
        if response is not None:
            if user_key not in secret_key_info.keys():
                secret_key_info[user_key] = {}
            secret_key_info[user_key].update(response)
            secret_key_info[user_key]['time'] = time.time()
            return True
        else:
            return False
    return True


def __get_goods_info(user, token, goods_id, goods_num, host, port, goods_discount):
    # response = __submit_order(token, goods_id, goods_num, host, port)
    # return response

    goods_info = {}

    if goods_id not in goods_lock_info.keys():
        logger.info('goods[{0}] not in goods_lock_info[{1}], query cart.'.format(goods_id, goods_lock_info))
        __query_cart(token, goods_id, host, port)
        if goods_id not in goods_lock_info.keys():
            logger.info('goods[{0}] not in goods_lock_info[{1}], submit order.'.format(goods_id, goods_lock_info))
            __submit_order(token, goods_id, goods_num, host, port)
        # __submit_order(token, goods_id, goods_num, host, port)
        # __query_cart_info(user, token, goods_id, host, port)

    if goods_id in goods_lock_info.keys():
        goods_info['storeId'] = goods_lock_info[goods_id]['storeId']
        goods_info['goods_price'] = goods_lock_info[goods_id]['marketPrice']
        if goods_lock_info[goods_id].get('discount', None) is None and goods_discount:
            logger.info('goods[{0}] no discount info[{1}] but actually has discount now[{2}], submit order to get discount.'.format(
                goods_id, goods_lock_info[goods_id], goods_discount))
            __submit_order(token, goods_id, goods_num, host, port)
            # __query_cart(token, goods_id, host, port)
        else:
            logger.info('goods[{0}] discount info[{1}] discount desc[{2}].'.format(goods_id, goods_lock_info[goods_id], goods_discount))

        discount_info_list = goods_lock_info[goods_id].get('discount', [])
        selected_discount_info = None
        for discount_info in discount_info_list:
            if discount_info['fullCount'] == goods_num:
                selected_discount_info = discount_info
                break
            elif discount_info['fullCount'] < goods_num:
                if selected_discount_info is None or \
                        discount_info['fullCount'] > selected_discount_info['fullCount']:
                    selected_discount_info = discount_info

        if selected_discount_info is not None:
            goods_info['discount'] = selected_discount_info
            logger.info('goods[{0}] find matching info in goods lock info[{1}].'.format(goods_id, goods_info))
        else:
            goods_info['discount'] = None
            logger.info('goods[{0}] no matching discount info in goods lock info[{1}].'.format(goods_id, discount_info_list))
            if goods_id == '2c91c7f473bf846f0173e1c610e73c18' or goods_id == '2c91c7f473bf846f0173e1c610e23c16':
                selected_discount_info = {'discountLevelId': 4751, 'marketingId': 2015, 'fullAmount': None, 'fullCount': 3, 'discount': 0.68}
                goods_info['discount'] = selected_discount_info
                logger.info('goods[{0}] use default discount info:[{1}].'.format(goods_id, selected_discount_info))
        return goods_info

    logger.info('goods[{0}] not in goods lock info[{1}].'.format(goods_id, goods_lock_info))
    return None


def __get_address_id(user, token, host, port):
    user_key = user['email']

    if user_key not in secret_key_info.keys() or secret_key_info[user_key].get('address_id', None) is None:
        address_id = __get_list_address(token, host, port)
        if address_id is None:
            address_id = '2c91c7f07358a7b5017367f563472b90'
        secret_key_info[user_key]['address_id'] = address_id

    return secret_key_info[user_key].get('address_id', None)


def __query_cart_info(user, token, goods_id, host, port):
    user_key = user['email']
    if user_key not in secret_key_info.keys() or secret_key_info[user_key].get(goods_id, None) is None:
        cart_status = __query_cart(token, goods_id, host, port)
        if cart_status is not None:
            secret_key_info[user_key][goods_id] = cart_status[goods_id]

    return secret_key_info[user_key].get(goods_id, None)


def __update_cart_info(user, token, goods_id, host, port):
    user_key = user['email']
    cart_status = __query_cart(token, goods_id, host, port)
    if cart_status is not None:
        secret_key_info[user_key][goods_id] = cart_status[goods_id]


def lock_order(user, goods_id, host, port, goods_discount):
    user_key = user['email']

    # 第一步，获取token
    if not __get_token(user, host, port):
        return False

    token = secret_key_info[user_key]['token']
    goods_num = user['goods'][goods_id][0]

    # 第二步，查询购物车中数量
    num_in_cart = __query_cart_info(user, token, goods_id, host, port)
    if num_in_cart is None:
        return False
    if num_in_cart > goods_num:
        # 第三步，从购物车删除
        if not __delete_goods_in_cart(token, goods_id, host, port):
            return False
        else:
            num_in_cart = 0
            secret_key_info[user_key][goods_id] = num_in_cart

    # 第三步，添加到购物车
    num_to_add = goods_num - num_in_cart
    if num_to_add != 0:
        if not __add_to_cart(token, goods_id, num_to_add, host, port):
            return False
    secret_key_info[user_key][goods_id] = goods_num

    # 第四步，确定要购买的东西
    goods_info = __get_goods_info(user, token, goods_id, goods_num, host, port, goods_discount)
    if goods_info is None:
        return False

    # 第五步，下单
    if not __confirm(token, goods_id, goods_num, goods_info, host, port):
        return False

    # 第六步，获取地址
    address_id = __get_address_id(user, token, host, port)
    if address_id is None:
        return False

    # 第七步，提交订单
    if not __commit(user, token, goods_id, goods_info, host, port, address_id):
        return False

    secret_key_info[user_key][goods_id] = 0
    return True


def add_cart(user, goods_id, host, port, stock, goods_discount):
    user_key = user['email']

    if not __get_token(user, host, port):
        return False

    token = secret_key_info[user_key]['token']
    goods_num = user['goods'][goods_id][0]

    num_in_cart = __query_cart_info(user, token, goods_id, host, port)
    if num_in_cart is None:
        return False
    if num_in_cart > goods_num:
        if not __delete_goods_in_cart(token, goods_id, host, port):
            return False
        else:
            num_in_cart = 0
            secret_key_info[user_key][goods_id] = num_in_cart

    num_to_add = goods_num - num_in_cart
    if num_to_add == 0:
        return True
    if num_to_add > stock:
        num_to_add = stock

    if not __add_to_cart(token, goods_id, num_to_add, host, port):
        return False
    secret_key_info[user_key][goods_id] = num_in_cart + num_to_add

    if goods_discount is not None and (goods_id not in goods_lock_info.keys() or goods_lock_info[goods_id].get('discount', None) is None):
        __submit_order(token, goods_id, goods_num, host, port)
        # __get_goods_info(user, token, goods_id, goods_num, host, port, check_discount=True)

    return True


def init_user_info(user, host, port):
    user_key = user['email']

    if not __get_token(user, host, port):
        return
    token = secret_key_info[user_key]['token']

    __get_address_id(user, token, host, port)

    for goods_id in user['goods'].keys():
        __update_cart_info(user, token, goods_id, host, port)

    # save_goods_lock_info()


def load_goods_lock_info():
    filename = 'goods_lock_info.txt'
    try:
        f = open(filename, 'r')
        content = f.read()
        if not content.strip():
            content = '{}'
    except:
        content = '{}'
    goods_lock_info = json.loads(content)
    logger.info('goods lock info dict: ------------------------------------------------------------------')
    logger.info(goods_lock_info)
    logger.info('---------------------------------------------------------------------------------')


def save_goods_lock_info():
    filename = 'goods_lock_info.txt'
    try:
        content = json.dumps(goods_lock_info)
        f = open(filename, 'w', encoding='utf-8')
        f.write(content)
        f.close()
    except Exception as e:
        logger.exception('save goods lock info to [{0}] exception: [{1}].'.format(filename, e))


if __name__ == "__main__":
    util.config_logger('auto_order')

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
            'goods': {'2c91c7f473bf846f0173c904062f19d0': [3, 2]}
            }

    goods_id = '2c91c7f473bf846f0173c904062f19d0'

    host = '110.90.175.241'
    port = 4235

    host = None

    # init_user_info(user, host, port)
    load_goods_lock_info()
    lock_order(user, goods_id, host, port)
    save_goods_lock_info()
    pass
