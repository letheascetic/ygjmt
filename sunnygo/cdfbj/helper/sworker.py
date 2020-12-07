# coding: utf-8


import time
import random
import logging
import threading
from utils.mailer import Mailer
from sqlalchemy import or_, and_
from utils.ip_util import IpUtil
from sql.sqlcdfbj import SqlCdfBj
from utils.http_util import HttpUtil
from sql.base import CdfBjGoodsInfo, CdfBjSubscriberInfo, User


logger = logging.getLogger(__name__)


class SWorker(threading.Thread):

    def __init__(self, name, config, goods_id_list, message_queue):
        threading.Thread.__init__(self)
        self.name = name
        self._running = True
        self._config = config
        self._sql_helper = SqlCdfBj()
        self._http_util = HttpUtil(config)
        self._mailer = Mailer(config)
        self._goods_id_list = goods_id_list                 # 负责查询的产品id
        self._update_time = time.time()
        self._ip_util = IpUtil(config)
        self._mutex = threading.Lock()
        self._message_queue = message_queue

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
                time.sleep(5)
                return None
            host, port = ip_item['ip'], ip_item['port']
        else:
            host, port = '', -1

        # 获取产品详情
        goods_info = self._http_util.cdfbj_get_goods_info(goods_id, host, port)
        if goods_info is not None:
            logger.info('cdfbj get goods info with ip proxy[{0}:{1}] response[{2}].'.format(host, port, goods_info))

        # 如果使用IP代理，则记录访问结果
        if self._config.get('PROXY_ENABLE', True):
            self._ip_util.feedback(ip_item, goods_info)

        return goods_info

    def __check_goods_info(self, goods_id, goods_info):
        session = self._sql_helper.create_session()
        try:
            subscriber_user_id_list = [set(), set()]

            # 查询该商品在db中的数据
            goods_data = session.query(CdfBjGoodsInfo).filter(CdfBjGoodsInfo.goods_id == goods_id).first()
            new_goods_item = CdfBjGoodsInfo.parse(goods_id, goods_info)

            # 新订阅的商品，添加该新订阅的商品到CdfBjGoodsInfo，并直接返回
            if goods_data is None:
                logger.info('new subscribe goods info[{0}], insert into db.'.format(goods_info))
                session.add(CdfBjGoodsInfo.from_item(new_goods_item))
                return subscriber_user_id_list
            # 原有的商品，则更新该商品在db中的数据
            else:
                old_goods_item = goods_data.to_item()
                goods_data.update(new_goods_item)
                session.commit()

            # 查询订阅了该商品的用户，更新这些用户的相关状态，并确定其中要发邮件的用户
            query = session.query(CdfBjSubscriberInfo).filter(CdfBjSubscriberInfo.goods_id == goods_id)\
                .filter(or_(CdfBjSubscriberInfo.replenishment_switch == 1, CdfBjSubscriberInfo.discount_switch == 1))

            # 如果该产品目前下架了，则不需要查询补货提醒或折扣变动提醒
            # !!!是否需要将关注该商品用户的补货通知标志位[replenishment_flag]统一复位？
            if new_goods_item['goods_status'] == '下架' or new_goods_item['goods_status'] == '不存在':
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
                    if old_goods_item['goods_discount'] != new_goods_item['goods_discount'] or old_goods_item['goods_price'] != new_goods_item['goods_price']:
                        if new_goods_item['goods_discount'] is not None:    # 折扣变动且当前有折扣的情况下才会通知
                            subscriber_user_id_list[1].add(subscriber_data.user_id)

            session.commit()

            if subscriber_user_id_list[0] or subscriber_user_id_list[1]:
                logger.info('goods info change from [{0}] to [{1}], need to mail.'.format(old_goods_item, new_goods_item))

            return subscriber_user_id_list
        except Exception as e:
            logger.info('check goods info[{0}] exception[{1}].'.format(goods_info, e))
            session.rollback()
        finally:
            self._sql_helper.close_session(session)

    # def __mail_subscribers(self, goods_info, subscriber_user_id_list):
    #     user_id_both = subscriber_user_id_list[0].intersection(subscriber_user_id_list[1])
    #     user_id_replenishment = subscriber_user_id_list[0] - subscriber_user_id_list[1]
    #     user_id_discount = subscriber_user_id_list[1] - subscriber_user_id_list[0]
    #
    #     user_id_list = list(subscriber_user_id_list[0].union(subscriber_user_id_list[1]))
    #     if not user_id_list:
    #         return
    #
    #     logger.info('goods[{0}] send mail to users[{1}].'.format(goods_info, subscriber_user_id_list))
    #
    #     if user_id_both or user_id_discount:
    #         mail_title = '折扣/价格变动 {0}'.format(goods_info['title'])
    #     else:
    #         mail_title = '补货提醒 {0}'.format(goods_info['title'])
    #     self._mailer.send_sys_subscriber_mail(mail_title, goods_info, user_id_list)
    #
    #     session = self._sql_helper.create_session()
    #     try:
    #         query = session.query(User).filter(User.id.in_(user_id_list)).filter(User.email.isnot(None))
    #         user_all_list = [user for user in query.all()]
    #         random.shuffle(user_all_list)
    #
    #         for user_data in user_all_list:
    #             if user_data.id in user_id_both:
    #                 mail_title = '折扣/价格变动 {0}'.format(goods_info['title'])
    #             elif user_data.id in user_id_replenishment:
    #                 mail_title = '补货提醒 {0}'.format(goods_info['title'])
    #             else:
    #                 mail_title = '折扣/价格变动 {0}'.format(goods_info['title'])
    #
    #             response = self._mailer.send_subscriber_mail(user_data, mail_title, goods_info)
    #             if response['code'] != 0:
    #                 user_data.email_status = 1
    #
    #     except Exception as e:
    #         logger.exception('goods[{0}] mail subscribers[{1}] exception[{2}].'.format(
    #             goods_info, subscriber_user_id_list, e))
    #         session.rollback()
    #     finally:
    #         self._sql_helper.close_session(session)

    def run(self):
        i = 0
        while self._running:
            i = i + 1
            logger.info('thread[{0}], start [{1}] times........................'.format(self.name, i))

            # 得到goods_id_list的拷贝
            self._mutex.acquire()
            goods_id_list = self._goods_id_list.copy()
            self._mutex.release()

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
                self._message_queue.append([goods_info, subscriber_user_id_list])
                # self.__mail_subscribers(goods_info, subscriber_user_id_list)

                if self._config.get('INTERVAL_ENABLE', True):
                    time.sleep(random.random() * self._config.get('TIME_INTERVAL', 0.5) * 2)

            if (time.time() - self._update_time) > 600:
                self._update_time = time.time()
                self._http_util.log()
