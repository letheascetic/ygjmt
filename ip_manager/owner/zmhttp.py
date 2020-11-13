# coding: utf-8

import json
import logging
import requests


logger = logging.getLogger(__name__)


class ZmHttp(object):
    def __init__(self, config):
        self.owner_tag = '芝麻Http'
        self.config = config

    def query_white_list(self):
        try:
            url = 'http://wapi.http.cnapi.cc/index/index/white_list?neek=158245&appkey=237d0703818d39a61a4153c2dd8b3aff'
            r = requests.get(url, timeout=10)

            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] query white list response[{1}].'.format(self.owner_tag, content))
                if content.get('code', None) == 0:
                    white_list = [ip_info['mark_ip'] for ip_info in content['data']['lists']]
                    return white_list

            logger.info('[{0}] query white list failed[{1}].'.format(self.owner_tag, r.text))
        except Exception as e:
            logger.exception('[{0}] query white list exception[{1}].'.format(self.owner_tag, e))

    def ip_in_white_list(self, ip):
        white_list = self.query_white_list()
        if white_list is not None:
            if ip in white_list:
                logger.info('[{0}] ip[{1}] in white list[{1}].'.format(self.owner_tag, ip, white_list))
                return True
            else:
                logger.info('[{0}] ip[{1}] not in white list[{1}].'.format(self.owner_tag, ip, white_list))
                return False

    def add_to_white_list(self, ip):
        try:
            url = 'http://wapi.http.cnapi.cc/index/index/save_white?neek=158245&appkey=237d0703818d39a61a4153c2dd8b3aff&white={ip}'.format(ip=ip)
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] add ip[{1}] to white list response[{2}].'.format(self.owner_tag, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] add ip[{1}] to white list exception[{2}].'.format(self.owner_tag, ip, e))

    def delete_ip_from_white_list(self, ip):
        if not self.ip_in_white_list():
            return

        try:
            url = 'http://wapi.http.cnapi.cc/index/index/del_white?neek=158245&appkey=237d0703818d39a61a4153c2dd8b3aff&white={ip}'.format(ip=ip)
            r = requests.get(url, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] delete ip[{1}] from white list response[{2}].'.format(self.owner_tag, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] delete ip[{1}] from white list exception[{2}].'.format(self.owner_tag, ip, e))

