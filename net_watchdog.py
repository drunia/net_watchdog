#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import locale

APP_NAME = "NetWatcher"
APP_VER = "1.0.0"

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, 'ru')

    parser = argparse.ArgumentParser(description=f"{APP_NAME} {APP_VER}")
    parser.add_argument("--loglevel", "-l", default="INFO", help="Set the log level (DEBUG, INFO, WARNING, ...)")
    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    file_handler = logging.FileHandler('NetWatchdog.log', mode='w')
    stdout_handler = logging.StreamHandler()
    logging.basicConfig(format="%(filename)s:%(lineno)d: %(levelname)s %(asctime)s (%(name)s): %(message)s",
                        level=numeric_level, datefmt="%d-%b-%Y %H:%M:%S", handlers=[stdout_handler, file_handler])

    logger = logging.getLogger(__name__)
    logger.info(f"Start {APP_NAME} {APP_VER}")

    from ui import main_win
    from PyQt5.QtWidgets import QApplication, QStyleFactory

    app = QApplication(sys.argv)
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
    main_w = main_win.MainWin()
    main_w.show()
    app_ret_code = app.exec()

    # Clear tmp dir
    tmp_dir = os.path.join(os.curdir, "tmp")
    if os.path.exists(tmp_dir):
        for file in os.listdir(tmp_dir):
            del_file = os.path.join(tmp_dir, file)
            if os.access(del_file, os.W_OK):
                logger.info(f"Delete temp file: {del_file}")
                os.remove(del_file)
    sys.exit(app_ret_code)
