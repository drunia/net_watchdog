#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from enum import Enum
from settings import *
from ui.list_item import WatchFrame
from journal_db import JournalDb
from datetime import datetime


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
        self.logger = logging.getLogger("WatchManager")
        self.settings = Settings()
        self.journal = JournalDb()

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

    def update_info(self, w: WatchFrame):
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

        # Write in journal watcher changed status
        dev_triggered = (w.device.trigger_count > int(Settings().read(CHECK_COUNT_TO_ALARM)))
        if (w.triggered ^ dev_triggered) and w.enabled:
            w.triggered = not w.triggered
            self.logger.info('Watcher online status changed, write to journal...')
            event_timestamp = datetime.utcnow().timestamp()
            online_status = 'Онлайн' if bool(w.device.online_stat) else 'Оффлайн'
            msg = 'Устройство появилось онлайн' if bool(w.device.online_stat) else 'Устройство ушло в оффлайн'
            self.journal.add_record(event_timestamp, str(w.device), online_status, msg)
        self.logger.debug(f"{w.device} online_stat (ms): {w.device.online_stat}")

    @staticmethod
    def sort_by_active(watcher):
        """
        Key function
        Sorting by online or enabled
        """
        # Online watchers, sorted by accessibility time, ONVIF top
        if bool(watcher.device.online_stat and watcher.device.watched):
            if watcher.device.watch_method == WatchMethod.ONVIF:
                return -1
            else:
                return int(watcher.device.online_stat) if str(watcher.device.online_stat).isnumeric() else 10000
        # Offline watchers
        if bool(watcher.device.watched):
            return 100000 if watcher.device.trigger_count < int(Settings().read(CHECK_COUNT_TO_ALARM)) else -2
        # Disabled watchers
        return 200000


if __name__ == "__main__":
    from device import Device
    d: Device = Device(WatchMethod.ONVIF, WatchFor.ONLINE, "172.181.128.152", "viewer", "viewer123")
    print("device online:", d.is_online())
    print("dev info:\n", d._get_onvif_info())
    print("dev snapshot uri:", d.get_onvif_snapshot())
    pass
