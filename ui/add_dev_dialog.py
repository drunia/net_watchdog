#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import QDialog, QApplication, QStackedWidget, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi
from watch_manager import WatchFor, WatchMethod
from device import Device
import re
import socket
import logging


class AddDevDialog(QDialog):
    def __init__(self, add_dev_callback, parent):
        super().__init__(parent)
        loadUi("ui/add_dev_dialog.ui", self)

        self.logger = logging.getLogger("AddDevDialog")
        self.add_dev_callback = add_dev_callback
        self.setModal(True)
        self.setWindowTitle(f"{parent.windowTitle()} : Добавить наблюдатель")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.port_edit: QLineEdit = self.stackedWidget.widget(0).findChild(QLineEdit, "portEdit")
        self.login_edit: QLineEdit = self.stackedWidget.widget(1).findChild(QLineEdit, "loginEdit")
        self.pass_edit: QLineEdit = self.stackedWidget.widget(1).findChild(QLineEdit, "passEdit")

        # Hide optional panel (port/auth)
        self.stackedWidget: QStackedWidget
        self.stackedWidget.resize(self.stackedWidget.minimumSize())

        # Add QCombobox Item Change handler
        self.comboBox.currentIndexChanged.connect(self.cb_index_changed)

        # Add addButton click handler
        self.addButton.clicked.connect(self.add_btn_click)

    def show(self):
        super().show()
        # Fill ip automatically
        ip = socket.gethostbyname(socket.gethostname())
        self.ipEdit.setText(ip)

    def cb_index_changed(self, index: int):
        if index > 0:
            self.stackedWidget.resize(self.stackedWidget.maximumSize())
            if index == 1:
                self.stackedWidget.setCurrentIndex(0)
            elif index == 2:
                self.stackedWidget.setCurrentIndex(1)
        else:
            self.stackedWidget.resize(self.stackedWidget.minimumSize())

    def device(self):
        cb_index = self.comboBox.currentIndex()
        w_cb_index = self.watchStateCb.currentIndex()
        watch_for = WatchFor.ONLINE if w_cb_index == 0 else WatchFor.OFFLINE

        return {
            0: Device(WatchMethod.PING, watch_for, self.ipEdit.text()),
            1: Device(WatchMethod.PORT, watch_for, ip=self.ipEdit.text(), port=int(self.port_edit.text())),
            2: Device(WatchMethod.ONVIF, watch_for, ip=self.ipEdit.text(), user=self.login_edit.text(),
                      password=self.pass_edit.text())
        }.get(cb_index)

    # Add button handler
    def add_btn_click(self):
        # Check fields
        ip: str = self.ipEdit.text()
        port: str = self.port_edit.text()
        user: str = self.login_edit.text()
        pwd: str = self.pass_edit.text()

        self.logger.info(f"add fields: {ip}, {port}, {user}, {pwd}")

        success = (
            bool(re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", ip)) and
            bool(re.match("[0-9]+", port)) and (len(user.strip()) > 1) and (len(pwd.strip()) > 1)
        )

        if not success:
            QMessageBox.critical(
                self, "Ошибка заполнения", "Некоторые поля заполнены неверно, проверьте!", QMessageBox.Ok)
            return

        # Invoke callback function to add device
        self.add_dev_callback(self.device())
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    d = AddDevDialog()
    d.show()
    print(d.device())
    app.exec()
    pass



