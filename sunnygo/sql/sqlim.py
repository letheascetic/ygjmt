# coding: utf-8


from sql.base import *
from db import session_cls
from sqlalchemy import func


logger = logging.getLogger(__name__)


class SqlIpManager(object):
    """sql helper for ip manager"""

    def __init__(self):
        self._session = None

    def begin_session(self):
        if self._session is not None:
            self.close_session()
        self._session = session_cls()

    def close_session(self):
        if self._session is not None:
            try:
                self._session.commit()
                self._session.close()
            except Exception as e:
                logger.info('close session exception[{0}].'.format(e))
                self._session.rollback()
            self._session = None

    def query_seeker(self, seeker_id):
        try:
            query = self._session.query(Seeker).filter(Seeker.id == seeker_id)
            seeker = query.first()
            if seeker is not None:
                seeker_info = seeker.to_item()
                logger.info('query seeker[{0}] success[{1}].'.format(seeker_id, seeker_info))
                return seeker_info
        except Exception as e:
            logger.exception('query seeker[{0}] exception[{1}]'.format(seeker_id, e))

    def update_seeker(self, seeker_info):
        try:
            query = self._session.query(Seeker).filter(Seeker.id == seeker_info['id'])
            seeker = query.first()
            if seeker is not None:
                seeker.ip = seeker_info['ip']
                seeker.register_time = seeker_info['register_time']
            else:
                seeker = Seeker(id=seeker_info['id'], ip=seeker_info['ip'],
                                register_time=seeker_info['register_time'], tag=seeker_info['tag'])
                self._session.add(seeker)
            self._session.commit()
            logger.info('update seeker[{0}] success.'.format(seeker_info))
            return True
        except Exception as e:
            logger.exception('update seeker[{0}] exception[{1}].'.format(seeker_info, e))
            self._session.rollback()
            return False

    def query_ip_activated(self, vendor, time_remaining=0, failed_threshold=20):
        try:
            expire_time = datetime.datetime.now() + datetime.timedelta(seconds=time_remaining)
            query = self._session.query(func.count('1')).filter(IpPool.vendor == vendor)\
                .filter(IpPool.expire_time >= expire_time).filter(IpPool.failed_num <= failed_threshold)
            num = query.one()[0]
            logger.info('query ip activated[{0}|{1}] success[{2}].'.format(vendor, time_remaining, num))
            return num
        except Exception as e:
            logger.exception('query ip activated[{0}|{1}] exception[{2}].'.format(vendor, time_remaining, e))

    def insert_ip_pool(self, ip_items):
        try:
            for ip_item in ip_items:
                row = IpPool.from_item(item=ip_item)
                self._session.add(row)
            self._session.commit()
            logger.info('insert ip pool[{0}] success.'.format(ip_items))
            return True
        except Exception as e:
            logger.exception('insert ip pool[{0}] exception[{1}].'.format(ip_items, e))
            self._session.rollback()
        return False

    def delete_stale_data(self, days=7):
        try:
            expire_time = datetime.datetime.now() - datetime.timedelta(days=days)
            query = self._session.query(IpPool).filter(IpPool.expire_time < expire_time)
            query.delete()
            self._session.commit()
            logger.info('delete stale data[{0}] success.'.format(days))
            return True
        except Exception as e:
            logger.exception('delete stale data[{0}] exception[{1}].'.format(days, e))
            self._session.rollback()
        return False

    def query_city_ip_rank(self, vendor, ip_threshold=0.95):
        query_sql = "select city, count(1), sum(failed_num), sum(success_num), sum(success_num)/(sum(success_num)+sum(failed_num)) as a from ip_pool where vendor = '{0}' group by city order by a desc, sum(success_num) desc"
        query_sql = query_sql.format(vendor)
        try:
            cursor = self._session.execute(query_sql)
            city_list = [city_info[0] for city_info in cursor.fetchall() if city_info[4] >= ip_threshold]
            return city_list
        except Exception as e:
            logger.exception('[{0}] query city ip rank exception[{1}].'.format(vendor, e))
            self._session.rollback()

    def query_city_ip_rank2(self, vendor, failed_threshold=20, ip_threshold=0.95):
        city_ip_rank_dict = {}
        try:
            sql = "select city, count(1) from ip_pool where vendor = '{0}' and failed_num > {1} group by city"
            sql = sql.format(vendor, failed_threshold)
            cursor = self._session.execute(sql)
            for city_info in cursor.fetchall():
                city_ip_rank_dict[city_info[0]] = {'failed': city_info[1], 'success': 0}

            sql = "select city, count(1) from ip_pool where vendor = '{0}' and failed_num <= {1} group by city"
            sql = sql.format(vendor, failed_threshold)
            cursor = self._session.execute(sql)
            for city_info in cursor.fetchall():
                if city_info[0] in city_ip_rank_dict.keys():
                    city_ip_rank_dict[city_info[0]].update({'success': city_info[1]})
                else:
                    city_ip_rank_dict[city_info[0]] = {'success': city_info[1], 'failed': 0}

            for city in city_ip_rank_dict.keys():
                city_ip_rank_dict[city]['ratio'] = city_ip_rank_dict[city]['success'] / (city_ip_rank_dict[city]['success'] + city_ip_rank_dict[city]['failed'])

            city_list = sorted(city_ip_rank_dict.items(), key=lambda x: x[1]['ratio'], reverse=True)
            city_list = [city[0] for city in city_list if city[1]['ratio'] >= ip_threshold]

            return city_list
        except Exception as e:
            logger.exception('[{0}] query city ip rank exception[{1}].'.format(vendor, e))
            self._session.rollback()
