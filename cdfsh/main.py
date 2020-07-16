# coding: utf-8

import time
import collector
import reader
from worker import Worker


def execute():
    config = collector.get_config()
    i = 1
    while 1:
        try:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            print('[{0}], start [{1}] times........................................................................'.format(current_time, i))
            # interval = config['interval']
            # time.sleep(random.random() * interval * 2)
            collector.execute()
            i = i + 1
        except Exception as e:
            print('execute failed; [{0}].'.format(e))
    pass


def worker_execute():
    goods_user_info = reader.load_goods_user_info('id_user.xlsx')
    config = collector.get_config()
    thread_num = config['thread']
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
            workers.append(Worker(thread_id, goods_user_info_slice))
            goods_count = 0
            thread_id = thread_id + 1
            goods_user_info_slice = {}

    workers.append(Worker(thread_id, goods_user_info_slice))

    for worker in workers:
        print('[{0}] [{1}].'.format(worker.id, len(worker.goods_user_info.keys())))

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    pass


if __name__ == '__main__':
    worker_execute()
    pass

