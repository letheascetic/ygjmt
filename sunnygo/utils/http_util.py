# coding: utf-8

import time
import json
import uuid
import jpype
import logging
import threading


logger = logging.getLogger(__name__)


class HttpUtil(object):
    def __init__(self, config):
        self.name = 'http_util'
        self._config = config
        self._mutex = threading.Lock()

        jvm_path = jpype.getDefaultJVMPath()
        jar_path = 'demo12345.jar'
        jpype.startJVM(jvm_path, "-Djava.class.path={0}".format(jar_path))
        self._http_util = jpype.JClass('com.fizzy.sistertao.utils.OkHttpUtil')

        self._http_statistics = {'total': 0, 'success': 0, 'failed': 0, 'total_time_span': 0.0,
                                 'success_time_span': 0.0, 'total_avg_time': 0.0, 'success_avg_time': 0.0}

    def cdfbj_get_goods_info(self, goods_id, host=None, port=None):
        """获取cdf北京产品详情，成功则返回goods_info(dict)，失败则返回None"""

        goods_info = {'title': None, 'url': None, 'status': None, 'stock': None, 'price': None, 'discount': None}
        url = "https://mbff.yuegowu.com/goods/unLogin/spu/{0}?regId={1}".format(goods_id, uuid.uuid4())
        goods_info['url'] = 'https://m.yuegowu.com/goods-detail/{0}'.format(goods_id)
        start = time.time()
        try:

            response = self._http_util.getGoodsInfo(url, host, port)
            content = json.loads(str(response))         # 如果返回的是html，在这一步会发生exception

            code = content.get('code', None)
            # 商品已下架
            if code == 'K-030007':
                goods_info['status'] = '下架'
                goods_info['stock'] = 0
            # 商品缺货或在售
            elif code == 'K-000000':
                context = content.get('context', None)
                info = context['goodsInfos'][0]
                goods_info['stock'] = info['stock']
                goods_info['title'] = info['goodsInfoName']
                if goods_info['stock'] > 0:
                    goods_info['status'] = '在售'
                else:
                    goods_info['status'] = '缺货'
                goods_info['price'] = info['salePrice']
                if len(info['marketingLabels']) > 0:
                    goods_info['discount'] = info['marketingLabels'][0]['marketingDesc']
            elif 'K-' in code:
                logger.info('cdfbj get goods info[{0}] return unknown response code[{1}].'.format(goods_info['url'], content))
                goods_info = None
            else:
                logger.info('cdfbj get goods info[{0}] with ip proxy[{1}:{2}] failed[{3}].'.format(url, host, port, content))
                goods_info = None
        except Exception as e:
            logger.exception('cdfbj get goods info[{0}] with ip proxy[{1}:{2}] exception[{3}].'.format(url, host, port, e))
            goods_info = None

        self.__reocrd(goods_info, time.time() - start)

        return goods_info

    def __reocrd(self, goods_info, time_span):
        """统计http请求情况"""

        self._mutex.acquire()
        self._http_statistics['total'] = self._http_statistics['total'] + 1
        self._http_statistics['total_time_span'] = self._http_statistics['total_time_span'] + time_span
        self._http_statistics['total_avg_time'] = self._http_statistics['total_time_span'] / self._http_statistics['total']

        if goods_info:
            self._http_statistics['success_time_span'] = self._http_statistics['success_time_span'] + time_span
            self._http_statistics['success_avg_time'] = self._http_statistics['success_time_span'] / self._http_statistics['success']
        else:
            self._http_statistics['failed'] = self._http_statistics['failed'] + 1
        self._mutex.release()
