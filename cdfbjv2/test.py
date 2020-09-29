# coding: utf-8

import util
import uuid
import jpype
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

    jvmPath = jpype.getDefaultJVMPath()
    jarPath = 'HttpUtil.jar'
    jpype.startJVM(jvmPath, "-Djava.class.path={0}".format(jarPath))
    HttpClientUtil = jpype.JClass('com.fizzy.sistertao.utils.HttpClientUtil')
    r = HttpClientUtil.doGet('https://mbff.yuegowu.com/goods/unLogin/spu/2c919458739b621d0173b9ae2b35338e', None, '58.218.201.122', 2458)
    logger.info(r)
    jpype.shutdownJVM()
    pass

