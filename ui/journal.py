#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import QDialog, QTableWidgetItem, QTableWidget
from PyQt5 import uic, QtCore


class Journal(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi("ui/journal.ui", self)

        # Add hide/restore window option
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMaximizeButtonHint)
        self.resize(parent.width()*1.3, parent.height()*1.5)
        self.setWindowTitle(f"{parent.windowTitle()} : Журнал событий")
        self.show()

        self.build_table()

    def build_table(self):
        tbl: QTableWidget = self.tableWidget
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setColumnCount(5)
        tbl.setRowCount(500)
        tbl.setHorizontalHeaderLabels(["datetime", "event", "message", "header4", "header5"])

        for row in range(tbl.rowCount()):
            for col in range(tbl.columnCount()):
                tbl_item = QTableWidgetItem("item")
                tbl_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                tbl.setItem(row, col, tbl_item)

        # tbl.resizeRowsToContents()
        # tbl.resizeColumnsToContents()


if __name__ == "__main__":
    pass



