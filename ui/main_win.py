#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, Qt, QTimer, QRect, QSize
from PyQt5.QtWidgets import QMainWindow, QLabel, QMessageBox
from PyQt5 import uic
from PyQt5.QtGui import QFont, QIcon, QResizeEvent, QShowEvent

from settings import *
from watch_manager import *
from ui.list_item import WatchFrame
from device import Device
from ui.add_dev_dialog import AddDevDialog
from ui.journal import Journal
from ui.settings import SettingsDialog
from playsound import playsound
from os.path import abspath
import platform

if platform.system().lower() == 'windows':
    import winsound


class MainWin(QMainWindow):
    WM: WatchManager

    def __init__(self):
        super().__init__()

        # Settings
        self.settings = Settings()

        self.logger = logging.getLogger("MainWin")
        self.update_threads_pool = []

        # PlaySound Thread
        self.playsound_thread = PlayAudioThread()
        self.notify_sound = False

        uic.loadUi('ui/main_win.ui', self)

        self.setWindowIcon(QIcon("./res/icons/radar.png"))
        self.add_dev_btn.setIcon(QIcon("./res/icons/+.png"))
        self.open_journal_btn.setIcon(QIcon("./res/icons/paste.png"))
        self.open_settings_btn.setIcon(QIcon("./res/icons/config.png"))

        self.emptyLabel = QLabel()
        self.emptyLabel.setTextFormat(Qt.RichText)
        self.emptyLabel.setFont(QFont('Arial', 16))
        self.emptyLabel.setFixedSize(int(self.size().width() / 1.4), int(self.size().height() / 1.2))
        self.emptyLabel.setText(
            '<img src="./res/icons/+.png" align=top width=64> Добавьте устройство для отслеживания</img>'
        )

        self.setStyleSheet(
            """
            QToolButton {border: 1px outset rgb(150, 150, 150); border-radius: 5px;}
            """
        )

        # Buttons handlers
        self.add_dev_btn.clicked.connect(self.add_dev_btn_click)
        self.open_journal_btn.clicked.connect(self.open_journal)
        self.open_settings_btn.clicked.connect(self.open_settings)

        # Create WatchManager
        self.WM = WatchManager(self)

        # Create update timer
        self.timer = QTimer(self)
        # Set default interval
        self.timer.setInterval(5*1000)
        self.timer.timeout.connect(self.update_watcher_list)
        self.timer.start()

        if len(self.settings.watchers) == 0:
            self.vLayoutList.addWidget(self.emptyLabel)

        self.load_config()

        self.update_watcher_list()
        # To display disabled watchers
        self.build_watchers_list()

    def read_general_settings(self):
        try:
            timeout = int(self.settings.read(UPDATE_TIMEOUT))
        except NoOptionError or ValueError:
            timeout = 5
            self.settings.write(UPDATE_TIMEOUT, timeout)
        self.timer.stop()
        self.timer.setInterval(timeout*1000)
        self.timer.start()

        try:
            self.notify_sound = bool(int(self.settings.read('notify_sound')))
        except NoOptionError or ValueError:
            self.notify_sound = True
            
        self.logger.debug("General settings readed")

    def showEvent(self, evt: QShowEvent):
        """Set geometry on showEvent"""
        try:
            x = self.settings.read(MAIN_WINDOW_X)
            y = self.settings.read(MAIN_WINDOW_Y)
            w = self.settings.read(MAIN_WINDOW_WIDTH)
            h = self.settings.read(MAIN_WINDOW_HEIGHT)
            self.setGeometry(int(x), int(y), int(w), int(h))
            self.resize(int(w), int(h))
        except Exception as e:
            self.logger.error(e)

    def open_journal(self):
        Journal(self)

    def open_settings(self):
        SettingsDialog(self)

    def update_watcher_list(self):
        """
        Update watchers list in different threads
        """
        if len(self.update_threads_pool) > 0:
            self.logger.debug('Threads still working, wait ...')
            return
        for w in self.WM.watchers:
            if w.enabled:
                update_thread = UpdateDevicesThread(w)
                update_thread.finished.connect(self.update_thread_finished)
                self.update_threads_pool.append(update_thread)
                update_thread.start()
            else:
                w.device.trigger_count = 0

    # Invoked when thread is finished
    def update_thread_finished(self):
        for thread in self.update_threads_pool:
            if thread.isFinished():
                self.update_threads_pool.remove(thread)
                self.logger.debug(f'Thread {thread.objectName()} finished and removed')
        if len(self.update_threads_pool) == 0:
            self.build_watchers_list()

    def add_dev_btn_click(self):
        AddDevDialog(self.add_dev, parent=self).show()

    def add_dev(self, dev):
        self.logger.debug(f"Add watcher: {dev}")
        # Check if watcher already exists
        for w in self.WM.watchers:
            if str(w.device) == str(dev):
                QMessageBox.warning(self, 'Добавить наблюдатель',
                                    'Такой наблюдатель уже в списке!')
                return
        # Remove emptyLabel from watchers list
        if self.vLayoutList.count() == 1 and type(self.vLayoutList.itemAt(0).widget()) is QLabel:
            self.vLayoutList.removeWidget(self.vLayoutList.itemAt(0).widget())
        wf = WatchFrame(dev, self.WM)
        self.WM.add_watch(wf)
        self.vLayoutList.addWidget(wf)
        self.update_watcher_list()

    def save_config(self):
        for w in self.WM.watchers:
            self.settings.write_watcher(w)
        self.settings.write(MAIN_WINDOW_X, str(self.geometry().x()))
        self.settings.write(MAIN_WINDOW_Y, str(self.geometry().y()))
        self.settings.write(MAIN_WINDOW_HEIGHT, str(self.height()))
        self.settings.write(MAIN_WINDOW_WIDTH, str(self.width()))
        self.settings.write_settings()

    def _update_watcher(self, w):
        """
        Invoke from UpdateDevThread
        :param w: update watcher state
        """
        self.logger.debug(f"Update watcher: {w.device}")
        self.WM.update_info(w)

    def build_watchers_list(self):
        if self.settings.read(SORT_BY_LAG_TIME) != '0':
            self.WM.watchers.sort(key=WatchManager.sort_by_active)
        for wf, index in zip(self.WM.watchers, range(0, len(self.WM.watchers))):
            self._update_watcher(wf)
            if index < self.vLayoutList.count() and self.vLayoutList.itemAt(index).widget() is not wf:
                tmp_widget = self.vLayoutList.itemAt(index).widget()
                self.vLayoutList.removeWidget(tmp_widget)
                self.vLayoutList.insertWidget(index, wf)
                self.vLayoutList.addWidget(tmp_widget)
            elif index >= self.vLayoutList.count():
                self.vLayoutList.addWidget(wf)
        # Initialize ALARM by trigger count
        triggers = int(self.settings.read('check_count_to_alarm'))
        if not isinstance(triggers, int):
            triggers = 1
            self.settings.write('check_count_to_alarm', str(triggers))
        alarm = False
        for w in self.WM.watchers:
            if w.device.trigger_count >= triggers:
                self.logger.debug(f"{w.device_title_lb.text()} - TRIGGER ALARM ({w.device.trigger_count})")
                alarm = True
        # Play alarm
        if alarm and self.notify_sound:
            self.playsound_thread.start()

    def load_config(self):
        for watcher in self.settings.watchers:
            watcher_conf = self.settings.read_watcher_conf(watcher)
            wf = WatchFrame(Device(*watcher_conf), self.WM)
            self.WM.watchers.append(wf)
        self.read_general_settings()

    # Save settings on close main window
    def closeEvent(self, evt):
        try:
            self.save_config()
        except Exception as e:
            print(e.with_traceback())
        evt.accept()

    def resizeEvent(self, evt: QResizeEvent):
        size = QSize(self.scrollArea.width(), self.size().height()-20)
        self.scrollArea.resize(size)
        rect: QRect = self.settings_frame.geometry()
        self.settings_frame.setGeometry(rect.x(), self.geometry().height() - rect.height(),
                                        rect.width(), rect.height())


class UpdateDevicesThread(QThread):
    """
    Used for network requests
    """

    def __init__(self, w: WatchFrame):
        super().__init__()
        self.w = w
        self.setObjectName('QThread-' + str(w.device))
        self.logger = logging.getLogger(self.objectName())

    def run(self):
        self.logger.debug("update started")
        if self.w.enabled:
            self.w.loading_lb.setVisible(True)
            online_stat = self.w.device.is_online()
            self.logger.debug(f"online_stat (ms): {online_stat}")
            self.w.loading_lb.setVisible(False)
        else:
            self.w.device.trigger_count = 0
        self.logger.debug("update finished")


class PlayAudioThread(QThread):
    """
    Used for play audio
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("PlayAudioThread")

    def run(self):
        snd_path = abspath('./res/alarm.wav')
        self.logger.debug(f"Play started {snd_path}")
        try:
            if platform.system().lower() == 'windows':
                winsound.PlaySound(snd_path, winsound.SND_FILENAME)
            else:
                playsound(snd_path)
        except Exception as e:
            self.logger.error(e)
        self.logger.debug(f"Play finished")
        

if __name__ == "__main__":
    pass
