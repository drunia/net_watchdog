#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from pytz import timezone
from PyQt5.Qt import QDialog, QTableWidgetItem, QTableWidget, QFont
from PyQt5 import uic, QtCore
from journal_db import JournalDb
from observer import Observer


PAGE_LIMIT = 100
TZ = 'Europe/Kiev'

tz = timezone(TZ)


class Journal(QDialog, Observer):
    def __init__(self, parent):
        super().__init__(parent)
        self.logger = logging.getLogger('Journal-UI')
        uic.loadUi("ui/journal.ui", self)

        # Connect to journal db
        self.journal = JournalDb()
        self.journal.attach(self)

        # Add hide/restore window option
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMaximizeButtonHint)
        self.resize(int(parent.width()*1.3), int(parent.height()*0.8))
        self.setWindowTitle(f"{parent.windowTitle()} : Журнал событий")
        self.show()

        self.tbl: QTableWidget = self.tableWidget
        self.tbl.setSelectionBehavior(QTableWidget.SelectRows)
        font: QFont = self.tbl.font()
        font.setPointSize(12)
        self.tbl.setFont(font)
        self.tbl.setColumnCount(4)
        self.tbl_columns = ['Дата время', 'Наблюдатель', 'Событие', 'Сообщение']
        self.tbl.setHorizontalHeaderLabels(self.tbl_columns)
        self.tbl.verticalScrollBar().valueChanged.connect(self.tbl_scroll)

        # Add first PAGE_LIMIT records
        self.add_table_records()

    def tbl_scroll(self, value):
        if value == self.tbl.verticalScrollBar().maximum():
            self.add_table_records()

    def add_table_records(self):
        row_offset = self.tbl.rowCount()
        data = self.journal.read_all(PAGE_LIMIT, row_offset)
        if len(data) <= 0:
            self.logger.debug('No data to view!')
            return
        self.tbl.setRowCount(row_offset + len(data))
        for row_index in range(len(data)):
            for col_index in range(len(data[row_index])-1):
                db_value = data[row_index][col_index+1]
                if col_index == self.tbl_columns.index('Дата время'):
                    db_value = tz.fromutc(datetime.fromtimestamp(int(db_value))).strftime('%c')
                tbl_item = QTableWidgetItem(str(db_value))
                tbl_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                self.tbl.setItem(row_index+row_offset, col_index, tbl_item)
        self.tbl.resizeColumnsToContents()

    def changed(self):
        """
        Journal change Listener
        """
        self.logger.debug('Update records in table...')
        self.tbl.setRowCount(0)
        self.add_table_records()

    def __del__(self):
        self.journal.detach(self)


if __name__ == "__main__":
    pass
