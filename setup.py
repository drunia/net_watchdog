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
    Executable("net_watchdog.py", base=base)
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
            'excludes': ['settings.ini'],
            'include_files': ['ui', 'res'],
            'bin_excludes': ['res/journal.db']
        },
    }
)

if __name__ == "__main__":

    pass
