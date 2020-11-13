# coding: utf-8


import logging
import threading


logger = logging.getLogger(__name__)


class Manager(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.config = config

    def run(self):
        pass
