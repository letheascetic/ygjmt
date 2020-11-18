# coding: utf-8


from utils import util
from cdfbj.subscriber import Subscriber


if __name__ == '__main__':
    util.config_logger('cdfbj_subscriber')

    import config
    reminder = Subscriber(config.CDFBJ_SUBSCRIBER_CONFIG)
    reminder.execute()
    pass
