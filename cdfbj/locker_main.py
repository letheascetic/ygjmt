# coding: utf-8

import util
import json
import reader
from lock_worker import LockWorker


logger = logging.getLogger(__name__)


def get_config():
    f = open('config.txt', 'r')
    content = f.read()
    config = json.loads(content)
    return config


def worker_execute():
    config = get_config()
    goods_user_info, user_info_list = reader.load_lock_goods_user_info(None)
    locked_goods_user_info = reader.load_locked_goods_user_info(None)
    for goods_id, users in locked_goods_user_info:
        for user in users:
            if user in goods_user_info.get(goods_id, []):
                goods_user_info[goods_id].pop(goods_user_info[goods_id].index(user))

    thread_num = config['locker_thread']
    goods_per_thread = int(len(goods_user_info.keys()) / thread_num)
    workers = []

    goods_count = 0
    thread_id = 1
    goods_user_info_slice = {}
    for goods_id in goods_user_info.keys():
        goods_count = goods_count + 1
        goods_user_info_slice[goods_id] = goods_user_info[goods_id]

        if thread_id == thread_num:
            continue
        elif goods_count == goods_per_thread:
            workers.append(LockWorker(thread_id, goods_user_info_slice, user_info_list))
            goods_count = 0
            thread_id = thread_id + 1
            goods_user_info_slice = {}
    pass


if __name__ == '__main__':
    util.config_logger('locker')
    worker_execute()
    pass
