#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from enum import Enum
from settings import *


class WatchMethod(Enum):
    """
    PORT - Checking device by open TCP port
    ONVIF - Check by ONVIF protocol
    PING - Check by ICMP protocol
    """
    PORT = 1
    ONVIF = 2
    PING = 3


class WatchFor(Enum):
    """
    Watch when device in this mode
    """
    ONLINE = 1
    OFFLINE = 2


class WatchManager:
    watchers = []  # WatchFrame objects

    def __init__(self, main_w):
        self.main_w = main_w
        self.settings = Settings()
        self.logger = logging.getLogger("WatchManager")

    def add_watch(self, w):
        self.watchers.append(w)
        self.main_w.build_watchers_list()

    def del_watch(self, w):
        self.settings.config.remove_section(str(w.device))
        self.watchers.remove(w)
        self.main_w.vLayoutList.removeWidget(w)
        self.main_w.build_watchers_list()
        # Remove watcher (widget) from vLayoutList
        if self.main_w.vLayoutList.count() == 0:
            self.main_w.vLayoutList.addWidget(self.main_w.emptyLabel)

    def update_info(self, w):
        title = f"{str(WatchMethod(w.device.watch_method)).partition('.')[2]} {w.device.ip}"
        if w.device.watch_method == WatchMethod.PING:
            method_str = f"Использую старый добрый ping (ECHO, ICMP)"
        elif w.device.watch_method == WatchMethod.PORT:
            method_str = f"Переодически проверяю TCP порт {str(w.device.port)}"
        elif w.device.watch_method == WatchMethod.ONVIF:
            method_str = "Переодически получаю данные по ONVIF протоколу"
        else:
            method_str = f"Unknown watch method: {w.device.watch_method}"

        if w.device.watch_method == WatchMethod.ONVIF:
            if bool(w.device.online_stat):
                online_statistics = f"{method_str}\n" + \
                    f"{w.device.online_stat.Manufacturer} {w.device.online_stat.Model}\n" + \
                    f"FW ver: {w.device.online_stat.FirmwareVersion}"
            else:
                online_statistics = f"{method_str}\n"
        else:
            online_statistics = f"{method_str}\n" + \
                f"Время доступа: ~ {w.device.online_stat if bool(w.device.online_stat) else '?'} ms"
        w.update_info(title, online_statistics)
        w.update_online_status(w.device.online_stat)
        self.logger.debug(f"{w.device} online_stat (ms): {w.device.online_stat}")

    @staticmethod
    def sort_by_active(watcher):
        """
        Key function
        Sorting by online or enabled
        """
        # Online watchers, sorted by accessibility time, ONVIF top
        if bool(watcher.device.online_stat and watcher.device.watched):
            return watcher.device.online_stat+1 if str(watcher.device.online_stat).isnumeric() else 1
        # Offline watchers
        if bool(watcher.device.watched):
            return 100000
        # Disabled watchers
        return 200000


if __name__ == "__main__":
    from device import Device
    d: Device = Device(WatchMethod.ONVIF, WatchFor.ONLINE, "172.181.128.152", "viewer", "viewer123")
    print("device online:", d.is_online())
    print("dev info:\n", d._get_onvif_info())
    print("dev snapshot uri:", d.get_onvif_snapshot())
    pass
