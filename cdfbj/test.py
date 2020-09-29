# coding: utf-8

import util
import uuid
import logging
import requests


logger = logging.getLogger(__name__)


def get(goods_id):
    url = 'https://mbff.yuegowu.com/goods/unLogin/spu/{0}'.format(goods_id)
    # url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}?regId={1}".format(goods_id, uuid.uuid4())

    # headers = {'Host': 'mbff.yuegowu.com', 'Referer': 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id),
    #           'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 MicroMessenger/7.0.13(0x17000d2a) NetType/WIFI Language/zh_CN',
    #           'Content-Type': 'application/json'}

    # r = requests.get(url, headers=headers)

    r = requests.get(url, headers={'Host': 'mbff.yuegowu.com'})

    logger.info('get response: [{0}][{1}].'.format(r.status_code, r.text))


if __name__ == '__main__':
    util.config_logger('test')
    get(goods_id='2c919458739b621d0173b9ae2b35338e')
    pass

