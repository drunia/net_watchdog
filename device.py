#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import logging
import time

from onvif import ONVIFCamera, ONVIFError
from ping3 import ping
from contextlib import closing
from watch_manager import WatchMethod, WatchFor
from datetime import datetime
import threading

class Device:
    def __init__(self, method, watch_for, ip: str, user: str = "none",
                 password: str = "none", port: int = 0, watched=True):
        self.watch_method = method if type(method) is WatchMethod else WatchMethod(int(method))
        self.watch_for = watch_for if type(watch_for) is WatchFor else WatchFor(int(watch_for))
        self.ip = ip
        self.user = user
        self.password = password
        self.port = int(port)
        self.watched = watched if type(watched) is bool else True if watched == "True" else False
        self.online_stat = None
        self.onvif_device = None
        self.onvif_snapshot_uri = None
        self.trigger_count = 0
        self.logger = logging.getLogger("Device")

    def get_config(self):
        """
        :return: dict {} (Config of watcher)
        """
        return {
            "watch_method": str(self.watch_method.value),
            "watch_for": str(self.watch_for.value),
            "ip": self.ip,
            "user": self.user,
            "password": self.password,
            "port": str(self.port),
            "watched": str(self.watched)
        }

    def is_online(self):
        """
        Check online device status
        :return:
            WatchMethod.PING and WatchMethod.PORT - delay ms
            WatchMethod.ONVIF - ONVIF info
            All method write statistics to self.online_stat
        """
        # errors in time measurement in ms
        measurement_error = 2
        self.online_stat = None
        if not self.watched:
            return ""
        if self.watch_method == WatchMethod.ONVIF:
            try:
                self.online_stat = self._get_onvif_info()
            except ONVIFError as e:
                print(e)
        elif self.watch_method == WatchMethod.PORT:
            port_res = self._port_is_open()
            if isinstance(port_res, (int, float)):
                port_res += 1
            if not bool(port_res):
                self.online_stat = ""
            else:
                port_res -= measurement_error
                self.online_stat = round(port_res) if port_res > 1 else 0
        elif self.watch_method == WatchMethod.PING:
            ping_res = ping(self.ip, timeout=3, unit="ms")
            if isinstance(ping_res, (int, float)):
                ping_res += 1
            if not bool(ping_res):
                self.online_stat = ""
            else:
                ping_res -= measurement_error
                self.online_stat = round(ping_res) if ping_res > 1 else 0
        # Update trigger count 
        if bool(self.online_stat):
            self.trigger_count = 0
        else:
            self.trigger_count += 1
        print('time=', time.time(), 'self.online_stat=', self.online_stat, 'thread=', threading.current_thread().name)
        return self.online_stat

    def get_onvif_snapshot(self):
        try:
            if self.onvif_device is None:
                self.onvif_device: ONVIFCamera = ONVIFCamera(self.ip, self.port, self.user, self.password)
                self.onvif_snapshot_uri = None
            if self.onvif_snapshot_uri is None:
                media = self.onvif_device.create_media_service(True)
                token = media.GetProfiles()[0]["token"]
                self.onvif_snapshot_uri = media.GetSnapshotUri(token)["Uri"]
            return self.onvif_snapshot_uri
        except ONVIFError:
            self.onvif_device = None
            self.onvif_snapshot_uri = None
            return None

    def _get_onvif_info(self):
        """
        Get ONVIF info about device
        :return: dict()
        Example:
        {
            'Manufacturer': 'HIKVISION',
            'Model': 'DS-2CD2420F-IW',
            'FirmwareVersion': 'V5.4.81 build 180203',
            'SerialNumber': 'DS-2CD2420F-IW20190908AAWRD58372373',
            'HardwareId': '2'
        }
        """
        try:
            if self.onvif_device is None:
                self.onvif_device: ONVIFCamera = ONVIFCamera(self.ip, self.port, self.user, self.password)
            return self.onvif_device.devicemgmt.GetDeviceInformation()
        except ONVIFError:
            self.onvif_device = None
            return None

    def _port_is_open(self):
        """
        Check state port and return connect delay
        :return: int - connect delay in ms or None
        """
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(3)  # seconds
            start = datetime.timestamp(datetime.now())
            connected = sock.connect_ex((self.ip, self.port)) == 0
            stop = datetime.timestamp(datetime.now())
            delay = None
            if connected:
                delay = round((stop - start) * 1000)
            return delay

    def __str__(self):
        return f"{self.watch_method}@{self.ip}"


if __name__ == "__main__":
    pass
