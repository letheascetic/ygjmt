# coding: utf-8


import json
import time
import logging
import datetime
import requests


logger = logging.getLogger(__name__)


class Horpcn(object):
    def __init__(self, config, sql_helper, vendor_name=None):
        self.vendor = vendor_name
        if vendor_name is None:
            self.vendor = 'horocn'
        self._config = config
        self._sql_helper = sql_helper
        self.vendor_initialized = False
        self._token = 'beefce6b397e3f7eecbc56f692aef9c3'
        self.update_time = None

    def init_vendor(self, ip):
        if self.ip_in_white_list(ip):
            self.vendor_initialized = True
            return self.vendor_initialized
        if self.add_to_white_list(ip):
            self.vendor_initialized = True
        logger.info('init vendor[{0}] with ip[{1}] result[{2}].'.format(self.vendor, ip, self.vendor_initialized))
        return self.vendor_initialized

    def query_white_list(self):
        try:
            url = 'https://proxyapi.horocn.com/api/ip/whitelist'
            data = {'token': self._token}
            r = requests.get(url, timeout=10, data=data)

            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] query white list response[{1}].'.format(self.vendor, content))
                if content.get('code', None) == 0:
                    return content['data']
            logger.info('[{0}] query white list failed[{1}].'.format(self.vendor, r.text))
        except Exception as e:
            logger.exception('[{0}] query white list exception[{1}].'.format(self.vendor, e))

    def ip_in_white_list(self, ip):
        white_list = self.query_white_list()
        if white_list is not None:
            if ip in white_list:
                logger.info('[{0}] ip[{1}] in white list[{1}].'.format(self.vendor, ip, white_list))
                return True
            else:
                logger.info('[{0}] ip[{1}] not in white list[{1}].'.format(self.vendor, ip, white_list))
                return False

    def add_to_white_list(self, ip):
        try:
            url = 'https://proxyapi.horocn.com/api/ip/whitelist'
            data = {'token': self._token, 'ip': ip}
            r = requests.put(url, data=data, timeout=10)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] add ip[{1}] to white list response[{2}].'.format(self.vendor, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] add ip[{1}] to white list exception[{2}].'.format(self.vendor, ip, e))

    def delete_ip_from_white_list(self, ip):
        if not self.ip_in_white_list(ip):
            return

        try:
            url = 'https://proxyapi.horocn.com/api/ip/whitelist'
            data = {'token': self._token, 'ip': ip}
            r = requests.delete(url, timeout=10, data=data)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                logger.info('[{0}] delete ip[{1}] from white list response[{2}].'.format(self.vendor, ip, content))
                return content
        except Exception as e:
            logger.exception('[{0}] delete ip[{1}] from white list exception[{2}].'.format(self.vendor, ip, e))

