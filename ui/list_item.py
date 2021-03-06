#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import logging
import requests
import settings
import os
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QMovie, QFont
from PyQt5.QtWidgets import QFrame, QMessageBox
from requests.auth import HTTPBasicAuth


class WatchFrame(QFrame):
    device = None
    import watch_manager

    def __init__(self, device, w_manager):
        super().__init__()
        self.enabled = False
        self.triggered = False
        self.device = device
        self.WM = w_manager
        self.logger = logging.getLogger("WatchFrame")
        self.blinked = False
        # UI
        self.base_stylesheet = """
            QFrame {
                background-color: rgb(206, 220, 224); 
                border: 2px outset rgb(190, 190, 190);
                border-radius: 10px;
                margin: 2px;
            }
            QLabel {
                border: inherit; border-radius: 5px;
                color : rgb(0, 0, 0);
            }
            QPushButton {border-radius: 8px; }
        """
        self.disable_stylesheet = """
            QFrame {
                background-color: rgb(200, 200, 200);
            } 
            QLabel {
                border: inherit; border-radius: 5px;
                color : rgb(120, 120, 120);
            }
        """
        uic.loadUi('ui/list_item.ui', self)
        self.setStyleSheet(self.base_stylesheet)
        self.cam_preview_lb.setStyleSheet("border: 0px solid rgb(210, 210, 210)")
        self.del_btn.setIcon(QIcon(QPixmap('./res/icons/delete.png')))

        # graphic res
        self.btn_on_pixmap: QPixmap = QPixmap("./res/icons/switch-on.png")
        self.btn_off_pixmap: QPixmap = QPixmap("./res/icons/switch-off.png")
        self.online_pixmap = QPixmap("./res/icons/web.png")
        self.online_pixmap_disabled = QPixmap("./res/icons/weboff.png")
        self.offline_pixmap = QPixmap("./res/icons/alert.png")
        self.offline_pixmap_disabled = QPixmap("./res/icons/alertoff.png")

        self.loading_movie = QMovie("./res/icons/loading.gif")
        self.loading_movie.start()
        self.loading_lb.setAttribute(Qt.WA_NoSystemBackground)
        self.loading_lb.setMovie(self.loading_movie)
        self.loading_lb.setVisible(False)

        # Disable / Enable watcher button click handler
        self.on_off_btn.clicked.connect(lambda: self.enable(not self.enabled, True))

        # Delete watcher button click handler
        self.del_btn.clicked.connect(self.close_watcher)

        # Trigger timer
        self.blinkTimer = QTimer(self)
        self.blinkTimer.setInterval(1000)
        self.blinkTimer.timeout.connect(self.timerEvent)

        # Enable watcher
        self.enable(self.device.watched)
        self.WM.update_info(self)

    def timerEvent(self):
        font: QFont = self.device_status_lb.font()
        if self.device.trigger_count >= int(self.WM.settings.read(settings.CHECK_COUNT_TO_ALARM)):
            self.blinked = not self.blinked
            font.setBold(self.blinked)
        else:
            font.setBold(False)
        if not self.enabled:
            self.blinkTimer.stop()
            font.setBold(False)
        self.device_status_lb.setFont(font)

    # Close/delete this watcher
    def close_watcher(self):
        ret = QMessageBox.question(self.parent(), "???????????????? ??????????????????????",
                                   f"?????????????? ?????????????????????? ???? {self.device.ip} ?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.No:
            return
        self.WM.del_watch(self)
        self.close()
        self.logger.debug(f"Watcher {self.device} removed.")

    def update_cam_preview(self, url, auth_data):
        """
            :param url - HTTP URL
            :param auth_data - list [user, password]
            :return QPixmap
        """
        tmp_dir = os.path.join(os.path.curdir, "tmp")
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        pic = os.path.join(tmp_dir, f"preview_{self.device.ip}_.png")
        res = None
        try:
            res = requests.get(url, auth=HTTPBasicAuth(*auth_data), stream=True)
        except Exception as e:
            self.logger.error(e)
        pic_size = 0
        if res is not None and res.status_code == 200:
            with open(pic, "wb") as f:
                shutil.copyfileobj(res.raw, f)
            pic_size = os.stat(pic).st_size
            self.logger.debug(f"Watcher [{self.device_title_lb.text()}] " +
                             f"update_cam_preview(): Snapshot downloaded OK, size: {pic_size//1024} Kb")
        else:
            if os.path.exists(pic):
                os.remove(pic)
        if pic_size > 0:
            pic_path = pic
            pic = QPixmap(pic)
            # resizing for tooltip
            pic = pic.scaled(self.cam_preview_lb.width()*6, self.cam_preview_lb.height()*6,
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # save resized
            pic.save(pic_path)
            self.cam_preview_lb.setToolTip("<img src='" + pic_path + "'></img>")
            # resizing for cam_preview_lb
            pic = pic.scaled(self.cam_preview_lb.width(), self.cam_preview_lb.height(),
                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pic = QPixmap("./res/icons/no-image.png")
        self.cam_preview_lb.setPixmap(pic)
        return pic

    def update_online_status(self, online):
        if not online:
            if self.enabled:
                self.cam_preview_lb.setPixmap(self.offline_pixmap)
                self.device_status_lb.setStyleSheet("QLabel { color : rgb(255, 0, 0); }")
                self.device_status_lb.setText("???? ?? ????????")
            else:
                self.cam_preview_lb.setPixmap(self.online_pixmap_disabled)
            self.cam_preview_lb.setToolTip(None)
        else:
            # online
            if self.enabled:
                # if method ONVIF - set preview from update_cam_preview()
                if self.device.watch_method == self.watch_manager.WatchMethod.ONVIF:
                    self.update_cam_preview(self.device.get_onvif_snapshot(), (self.device.user, self.device.password))
                else:
                    self.cam_preview_lb.setPixmap(self.online_pixmap)
                self.device_status_lb.setStyleSheet("QLabel { color : rgb(0, 161, 13); }")
                self.device_status_lb.setText("?? ????????")
            else:
                self.cam_preview_lb.setPixmap(self.online_pixmap_disabled)

    def enable(self, enabled: bool, switch_enable: bool = False):
        self.logger.debug(
            f"Watcher [{self.device_title_lb.text()}] enable(): enabled={enabled}, switch_enable={switch_enable}")
        if enabled:
            self.on_off_btn.setIcon(QIcon(self.btn_on_pixmap))
            self.setStyleSheet(self.base_stylesheet)
            if not self.enabled and switch_enable:
                self.device.watched = True
            self.blinkTimer.start()
        else:
            self.on_off_btn.setIcon(QIcon(self.btn_off_pixmap))
            self.device_status_lb.setText("?????????????????????? ????????????????")
            self.setStyleSheet(self.base_stylesheet + self.disable_stylesheet)
            self.device_status_lb.setStyleSheet("QLabel { color : rgb(120, 120, 120); }")
            self.cam_preview_lb.setToolTip(None)
            self.device.online_stat = 0

        self.device.watched = enabled
        self.device.trigger_count = 0
        self.enabled = enabled
        self.WM.update_info(self)

    def update_info(self, title, info):
        self.device_title_lb.setText(title)
        self.device_info_lb.setText(info)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import os

    os.chdir("../")
    app = QApplication([])
    win = WatchFrame()
    win.show()
    app.exec_()
    pass
