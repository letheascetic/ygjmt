# coding: utf-8

from utils import util
from ip_manager.ip_manager import IpManager


if __name__ == "__main__":
    util.config_logger('ip manager')

    import config
    manager = IpManager(config.IP_MANAGER_CONFIG)
    manager.execute()
    pass
