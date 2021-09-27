#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, Qt, QTimer, QRect, QSize
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5 import uic, QtCore
from PyQt5.QtGui import QFont, QIcon, QResizeEvent, QShowEvent
from watch_manager import *
from ui.list_item import WatchFrame
from device import Device
from ui.add_dev_dialog import AddDevDialog
from ui.journal import Journal
from ui.settings import SettingsDialog


class MainWin(QMainWindow):
    WM: WatchManager

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("MainWin")
        # Update Thread
        self.update_thread = UpdateDevicesThread(self)
        self.update_thread.updateSignal.connect(self._update_watcher)
        self.update_thread.finished.connect(self.build_watchers_list)

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

        # Create update timer
        self.timer = QTimer(self)
        self.timer.setInterval(5*1000)
        self.timer.timeout.connect(self.update_watcher_list)
        self.timer.start()

        # Settings
        self.settings = Settings()
        self.WM = WatchManager(self)

        if len(self.settings.watchers) > 0:
            self.load_config()
        else:
            self.vLayoutList.addWidget(self.emptyLabel)

    def read_general_settings(self):
        try:
            timeout = int(self.settings.read(UPDATE_TIMEOUT))
        except NoOptionError:
            timeout = 5
            self.settings.write(UPDATE_TIMEOUT, timeout)
        self.timer.setInterval(timeout*1000)
        self.logger.info("General settings readed")

    def showEvent(self, evt: QShowEvent):
        """Set geometry on showEvent"""
        try:
            # x = self.settings.read(MAIN_WINDOW_X)
            # y = self.settings.read(MAIN_WINDOW_Y)
            w = self.settings.read(MAIN_WINDOW_WIDTH)
            h = self.settings.read(MAIN_WINDOW_HEIGHT)
            # self.setGeometry(int(x), int(y), int(w), int(h))
            self.resize(int(w), int(h))
        except NoOptionError:
            pass

    def open_journal(self):
        Journal(self)

    def open_settings(self):
        SettingsDialog(self)

    def update_watcher_list(self):
        """
        Update watchers list in other thread
        """
        self.update_thread.start()

    def add_dev_btn_click(self):
        AddDevDialog(self.add_dev, parent=self).show()

    def add_dev(self, dev):
        print(f"Add watcher: {dev}")
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
        self.settings.write(MAIN_WINDOW_X, str(self.pos().x()))
        self.settings.write(MAIN_WINDOW_Y, str(self.pos().y()))
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
        self.WM.watchers.sort(key=self.WM.sort_by_active)
        for wf, index in zip(self.WM.watchers, range(0, len(self.WM.watchers))):
            if index < self.vLayoutList.count() and self.vLayoutList.itemAt(index).widget() is not wf:
                tmp_widget = self.vLayoutList.itemAt(index).widget()
                self.vLayoutList.removeWidget(tmp_widget)
                self.vLayoutList.insertWidget(index, wf)
                self.vLayoutList.addWidget(tmp_widget)
            elif index >= self.vLayoutList.count():
                self.vLayoutList.addWidget(wf)

    def load_config(self):
        for watcher in self.settings.watchers:
            watcher_conf = self.settings.read_watcher_conf(watcher)
            wf = WatchFrame(Device(*watcher_conf), self.WM)
            self.WM.watchers.append(wf)
        self.update_watcher_list()
        self.read_general_settings()

    # Save settings on close main window
    def closeEvent(self, evt):
        self.save_config()
        evt.accept()
        print("Settings saved.")

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
    updateSignal = QtCore.pyqtSignal(object)

    def __init__(self, main_w: MainWin):
        super().__init__()
        self.logger = logging.getLogger("UpdateDevicesThread")
        self.main_w: MainWin = main_w

    def run(self):
        self.logger.debug("started")
        for w in self.main_w.WM.watchers:
            if w.enabled:
                w.loading_lb.setVisible(True)
                online_stat = w.device.is_online()
                self.logger.debug(f"{w.device} online_stat (ms): {online_stat}")
                self.updateSignal.emit(w)
                w.loading_lb.setVisible(False)
        self.logger.debug("finished")


if __name__ == "__main__":
    pass



