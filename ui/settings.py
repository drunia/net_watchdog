#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import QDialog, Qt, QComboBox
from PyQt5.uic import loadUi
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from settings import *


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        loadUi("ui/settings.ui", self)
        self.setWindowTitle(f"{parent.windowTitle()} : Настройки")
        self.settings = Settings()

        self.update_cb: QComboBox = self.update_cb
        # Load settings from file
        self.load_settings()

        self.show()

    def load_settings(self):
        try:
            timeout_index = (int(self.settings.read(UPDATE_TIMEOUT)) / 5)-1
        except NoOptionError:
            timeout_index = 0
        self.update_cb.setCurrentIndex(timeout_index)
        try:
            check_count_to_alarm_index = int(self.settings.read(CHECK_COUNT_TO_ALARM))-1
        except NoOptionError:
            check_count_to_alarm_index = self.check_for_trigger_cb.count()-1
        self.check_for_trigger_cb.setCurrentIndex(check_count_to_alarm_index)
        try:
            sort_by_lag_time = int(self.settings.read(SORT_BY_LAG_TIME))
        except NoOptionError:
            sort_by_lag_time = 2
        self.sort_ch.setCheckState(sort_by_lag_time)
        try:
            notify_sound = int(self.settings.read(NOTIFY_SOUND))
        except NoOptionError:
            notify_sound = 2
        self.notify_sound_ch.setCheckState(notify_sound)

    # Handle key press
    def keyPressEvent(self, evt: QKeyEvent):
        if evt.type() == evt.KeyPress and evt.key() == Qt.Key_Escape:
            # Ignore Esc key
            pass
        else:
            evt.accept()

    # Re-read settings in main_window on close SettingsDialog
    def closeEvent(self, evt: QCloseEvent):
        if evt.type() == QCloseEvent.Close:
            timeout = (self.update_cb.currentIndex()+1) * 5
            print(f"current update timeout: {timeout} seconds")
            self.settings.write(UPDATE_TIMEOUT, timeout)
            self.settings.write(CHECK_COUNT_TO_ALARM, self.check_for_trigger_cb.currentIndex()+1)
            self.settings.write(SORT_BY_LAG_TIME, self.sort_ch.checkState())
            self.settings.write(NOTIFY_SOUND, self.notify_sound_ch.checkState())
            self.settings.write_settings()
            self.parent().read_general_settings()
            evt.accept()


if __name__ == "__main__":
    pass



