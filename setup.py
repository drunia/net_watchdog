#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# cx_freeze faq commands: https://cx-freeze.readthedocs.io/en/latest/
# run in cmd: python.exe setup.py build_exe

from cx_Freeze import setup, Executable
import os
import sys

base = None
if sys.platform == "win32":
    base = "Win32GUI"

execs = [
    Executable("net_watchdog.py", base=base),
    Executable("net_watchdog.py", base='Console', targetName='net_watchdog_debug.exe'),
]

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))

print("PYTHON_INSTALL_DIR:", PYTHON_INSTALL_DIR)

setup(
    name="NetWatchdog",
    version="1.0.0",
    description="Watching for network devices",
    executables=execs,
    options={
        'build_exe': {
            'includes': ['ui'],
            'include_files': ['ui', 'readme.txt',
                              ('res/icons', 'res/icons'),
                              ('res/alarm.wav', 'res/alarm.wav'),
                              ('venv/Lib/site-packages/wsdl', 'lib/wsdl'),
                              ('venv/Lib/site-packages/platformdirs', 'lib/platformdirs')],
            'excludes': ['settings.ini'],
            'optimize': 2,
            'include_msvcr': True,
            'add_to_path': True
        },
    }
)

if __name__ == "__main__":

    pass
