# coding: utf-8

import logging
import threading
from utils.mailer import Mailer


logger = logging.getLogger(__name__)


class SWorker(threading.Thread):

    def __init__(self, name, config, goods_id_list, message_queue):
        threading.Thread.__init__(self)
        self._running = True
        self._mailer = Mailer(config)

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            pass
