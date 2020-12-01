# coding: utf-8

import time
import logging
import threading
from sql.base import User
from utils.mailer import Mailer
from sql.sqlcdfbj import SqlCdfBj


logger = logging.getLogger(__name__)


class MWorker(threading.Thread):

    def __init__(self, name, config, user_id_set):
        threading.Thread.__init__(self)
        self.name = name
        self._running = True
        self._config = config
        self._sql_helper = SqlCdfBj()
        self._mailer = Mailer(config)
        self._user_id_set = user_id_set
        self._mutex = threading.Lock()
        self._mail_tasks = []

    def stop(self):
        self._running = False

    def add_user_id(self, user_id):
        self._mutex.acquire()
        self._user_id_set.add(user_id)
        self._mutex.release()

    def add_mail_tasks(self, tasks):
        self._mail_tasks.extend(tasks)

    def user_id_in_set(self, user_id):
        return user_id in self._user_id_set

    def run(self):
        while self._running:
            if len(self._mail_tasks) != 0:
                session = self._sql_helper.create_session()
                try:
                    while len(self._mail_tasks) != 0:
                        task = self._mail_tasks.pop()
                        user_id, mail_title, goods_info = task[0], task[1], task[2]
                        # if user_id != 'JingleBell200201':
                        #     continue

                        query = session.query(User).filter(User.id == user_id).filter(User.email.isnot(None))
                        user_data = query.first()
                        if not user_data:
                            continue

                        user_data.email_code = user_data.email_code.strip()
                        response = self._mailer.send_subscriber_mail(user_data, mail_title, goods_info)
                        if response['mailer'] == user_data.email:
                            if response['code'] != 0:
                                user_data.email_status = user_data.email_status + 1
                            else:
                                user_data.email_status = 0
                except Exception as e:
                    logger.exception('mailer worker exception[{0}].'.format(e))
                finally:
                    self._sql_helper.close_session(session)
            else:
                time.sleep(3)
