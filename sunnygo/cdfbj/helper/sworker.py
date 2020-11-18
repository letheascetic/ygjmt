# coding: utf-8


import time
import random
import logging
import threading
from utils.mailer import Mailer
from utils.ip_util import IpUtil
from sqlalchemy import or_, and_
from sql.sqlcdfbj import SqlCdfBj
from utils.http_util import HttpUtil
from sql.base import CdfBjGoodsInfo, CdfBjSubscriberInfo, User


logger = logging.getLogger(__name__)


class SWorker(threading.Thread):

    def __init__(self, name, config, goods_id_list):
        threading.Thread.__init__(self)
        self.name = name
        self._running = True
        self._config = config
        self._sql_helper = SqlCdfBj()
        self._http_util = HttpUtil(config)
        self._ip_util = IpUtil(config, self._sql_helper)
        self._mailer = Mailer(config)
        self._goods_id_list = goods_id_list                 # 负责查询的产品id
        self._update_time = None
        self._mutex = threading.Lock()

    def stop(self):
        self._running = False

    def update_goods_id_list(self, goods_id_list):
        self._mutex.acquire()
        self._goods_id_list = goods_id_list
        self._mutex.release()

    def __get_goods_info(self, goods_id):
        """获取产品详情"""

        ip_item = None

        # 确认是否使用IP代理，若使用则获取一个IP Proxy
        if self._config.get('PROXY_ENABLE', True):
            ip_item = self._ip_util.get_proxy()
            if not ip_item:
                return None
            host, port = ip_item['ip'], ip_item['port']
        else:
            host, port = '', -1

        # 获取产品详情
        goods_info = self._http_util.cdfbj_get_goods_info(goods_id, host, port)

        # 如果使用IP代理，则记录访问结果
        if self._config.get('PROXY_ENABLE', True):
            self._ip_util.feedback(ip_item, goods_info)

        return goods_info

    def __check_goods_info(self, goods_id, goods_info):
        with self._sql_helper.session_cls() as session:
            try:
                subscriber_user_id_list = [set(), set()]

                # 查询该商品在db中的数据
                goods_data = session.query(CdfBjGoodsInfo).filter(CdfBjGoodsInfo.goods_id == goods_id).first()
                new_goods_item = CdfBjGoodsInfo.parse(goods_id, goods_info)

                # 新订阅的商品，添加该新订阅的商品到CdfBjGoodsInfo
                if goods_data is None:
                    logger.info('new subscribe goods info[{0}], insert into db.'.format(goods_info))
                    session.add(CdfBjGoodsInfo.from_item(new_goods_item))
                # 原有的商品，则更新该商品在db中的数据
                else:
                    goods_data.update(new_goods_item)
                session.commit()

                # 查询订阅了该商品的用户，更新这些用户的相关状态，并确定其中要发邮件的用户
                query = session.query(CdfBjSubscriberInfo).filter(CdfBjSubscriberInfo.goods_id == goods_id)\
                    .filter(or_(CdfBjSubscriberInfo.replenishment_switch == 1, CdfBjSubscriberInfo.discount_switch == 1))

                # 如果该产品目前下架了，则不需要查询补货提醒或折扣变动提醒
                # !!!是否需要将关注该商品用户的补货通知标志位[replenishment_flag]统一复位？
                if new_goods_item['goods_status'] == '下架':
                    for subscriber_data in query.all():
                        subscriber_data.replenishment_flag = 0
                    return subscriber_user_id_list

                # 如果该产品没有下架，则需要查询补货提醒或折扣变动提醒
                for subscriber_data in query.all():
                    # 补货提醒是开启的
                    if subscriber_data.replenishment_switch:
                        # 产品库存大于等于补货提醒阈值且没有通知过，则将该用户添加到补货提醒邮件发送队列
                        if new_goods_item['goods_num'] >= subscriber_data.replenishment_threshold and not subscriber_data.replenishment_flag:
                            subscriber_user_id_list[0].add(subscriber_data.user_id)
                            subscriber_data.replenishment_flag = 1      # !!!是否需要提前将通知标志位置位？或根据发送邮件结果来置位？
                        # 产品库存小于补货提醒阈值且已经通知过了，则将通知标志位复位
                        elif new_goods_item['goods_num'] < subscriber_data.replenishment_threshold and subscriber_data.replenishment_flag:
                            subscriber_data.replenishment_flag = 0
                    # 折扣提醒是开启的
                    if subscriber_data.discount_switch:
                        # 折扣有变动：价格变动或折扣变动，则将该用户添加到折扣提醒邮件发送队列
                        if goods_data.goods_discount != new_goods_item['goods_discount'] or goods_data.goods_price != new_goods_item['goods_price']:
                            subscriber_user_id_list[1].add(subscriber_data.user_id)

                session.commit()
                return subscriber_user_id_list
            except Exception as e:
                logger.info('check goods info[{0}] exception[{1}].'.format(goods_info, e))

    def __mail_subscribers(self, goods_id, goods_info, subscriber_user_id_list):
        user_id_both = subscriber_user_id_list[0].intersection(subscriber_user_id_list[1])
        user_id_replenishment = subscriber_user_id_list[0] - subscriber_user_id_list[1]
        user_id_discount = subscriber_user_id_list[1] - subscriber_user_id_list[0]

        user_id_list = list(subscriber_user_id_list[0].union(subscriber_user_id_list[1]))
        if not user_id_list:
            return

        with self._sql_helper.session_cls() as session:
            try:
                query = session.query(User).filter(User.id.in_(user_id_list)).filter(User.email)
                user_all_list = random.shuffle([user for user in query.all()])

                for user_data in user_all_list:
                    if user_data.id in user_id_both:
                        mail_title = '{0} 折扣和补货提醒'.format(goods_info['title'])
                    elif user_data.id in user_id_replenishment:
                        mail_title = '{0} 补货提醒'.format(goods_info['title'])
                    else:
                        mail_title = '{0} 折扣提醒'.format(goods_info['title'])

                self._mailer.send_subscriber_mail(user_data, mail_title, goods_info)

            except Exception as e:
                logger.exception('goods[{0}] mail subscribers[{1}] exception[{2}].'.format(
                    goods_info, subscriber_user_id_list, e))
        pass

    def run(self):
        i = 0
        while self._running:
            i = i + 1
            logger.info('thread[{0}], start [{1}] times........................'.format(self.name, i))

            # 得到goods_id_list的拷贝
            self._mutex.acquire()
            goods_id_list = self._goods_id_list.copy()
            self._mutex.release()

            # 对于每个
            for goods_id in goods_id_list:
                # 获取产品详情
                goods_info = self.__get_goods_info(goods_id)
                if goods_info is None:
                    continue

                # 获取要发送邮件的用户
                subscriber_user_id_list = self.__check_goods_info(goods_id, goods_info)
                if subscriber_user_id_list is None:
                    continue

                # 发送邮件
                self.__mail_subscribers(goods_id, goods_info, subscriber_user_id_list)
                if self._config.get('INTERVAL_ENABLE', True):
                    time.sleep(random.random() * self._config.get('TIME_INTERVAL', 0.5) * 2)