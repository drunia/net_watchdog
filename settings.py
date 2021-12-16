#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from configparser import *
import logging
from os.path import exists

GENERAL_SECTION = "General"
SETTINGS_FILE = "./settings.ini"

# Settings window
UPDATE_TIMEOUT = "update_timeout"
CHECK_COUNT_TO_ALARM = "check_count_to_alarm"
SORT_BY_LAG_TIME = "sort_by_lag_time"
NOTIFY_SOUND = "notify_sound"

# Main window
MAIN_WINDOW_WIDTH = "main_win_w"
MAIN_WINDOW_HEIGHT = "main_win_h"
MAIN_WINDOW_X = "main_win_x"
MAIN_WINDOW_Y = "main_win_y"


class Settings:
    """
    :return settings object
    """
    def __init__(self, file=SETTINGS_FILE):
        """
        :param file: Optional - settings file
        """
        self.logger = logging.getLogger('Settings')
        self.file = file
        self.config = ConfigParser()
        self.sections = []
        self.watchers = []

        if not exists(SETTINGS_FILE):
            self.write_default_settings()
        self.read_settings()

    # Singleton
    def __new__(cls, *args):
        if not hasattr(cls, "instance"):
            cls.instance = super(Settings, cls).__new__(cls)
        return cls.instance

    def read_settings(self):
        """
        Read config from file
        :return: None
        """
        try:
            with open(self.file, "r") as f:
                    self.config.read_file(f)
            self.sections = self.config.sections()
            self.watchers = list(
                filter(lambda item: str(item).startswith("WatchMethod."), self.config.sections())
            )
        except FileNotFoundError:
            self.logger.error("File:", SETTINGS_FILE, "not found, write settings first!", file=sys.stderr)

    def write(self, key, value):
        """
        :param key: String key
        :param value: String value
        """
        if not self.config.has_section(GENERAL_SECTION):
            self.config.add_section(GENERAL_SECTION)
        self.config[GENERAL_SECTION][key] = str(value)
        self.sections = self.config.sections()

    def read(self, key):
        return self.config.get(GENERAL_SECTION, key)

    def write_watcher(self, watcher):
        """
        :param watcher: WatchFrame object
        :param values_dict: Watcher values (dict)
        """
        watcher_config = {
            "watch_method": str(watcher.device.watch_method.value),
            "watch_for": str(watcher.device.watch_for.value),
            "ip": watcher.device.ip,
            "user": watcher.device.user,
            "password": watcher.device.password,
            "port": str(watcher.device.port),
            "watched": str(watcher.device.watched)
        }
        self.config[watcher.device] = watcher_config
        self.watchers = list(
            filter(lambda item: str(item).startswith("WatchMethod."), self.config.sections())
        )

    def read_watcher_conf(self, watcher_section):
        """
        :param watcher_section: Name of watcher section in settings file
        :return: watcher configuration list()
        """
        return dict(self.config[watcher_section]).values()

    def write_settings(self):
        """
        Write settings to file
        """
        with open(self.file, "w") as f:
            self.config.write(f)
        self.logger.info(f'Settings write to {self.file}')

    def write_default_settings(self):
        """ Init default settings"""
        self.logger.info('Write default settings...')
        self.write(UPDATE_TIMEOUT, '5')
        self.write(CHECK_COUNT_TO_ALARM, '2')
        self.write(SORT_BY_LAG_TIME, '2')
        self.write(NOTIFY_SOUND, '2')
        self.write_settings()


if __name__ == "__main__":
    s = Settings()
    s.write_settings()
    print("Sections:", s.sections)




