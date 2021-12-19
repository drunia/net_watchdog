#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sqlite3
from logging import Logger

DB_VERSION = 1


class JournalDb:

    # Singleton
    def __new__(cls, *args):
        if not hasattr(cls, 'instance'):
            cls.instance = super(JournalDb, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if hasattr(self, 'db_path'):
            return
        self.logger = logging.getLogger('Journal-DB')
        self.db_path = './res/journal.db'
        self.logger.info('Open journal db...')
        try:
            self.db = sqlite3.connect(self.db_path)
            self.upgrade_db()
        except sqlite3.Error as e:
            self.logger.error(e)

    def upgrade_db(self, version=DB_VERSION):
        """
        Provides upgrade database when schema has changed
        """
        self.logger.info(f'Upgrade db to version {version} ...')
        db_ver = self._get_db_ver()
        if db_ver < version:
            if db_ver == 0:
                # Create new db
                self.logger.info('Create new db...')
                self._create_db()
            # if db_ver == 1:
                # [ code ] to update to ver 2
                # ...
        else:
            self.logger.info(f'Update not needed, exiting...')

    def _get_db_ver(self):
        ver = 0
        cursor = self.db.cursor()
        try:
            sql = 'SELECT version FROM version;'
            cursor.execute(sql)
            ver = int(cursor.fetchone()[0])
        except sqlite3.Error as e:
            self.logger.error(e)
        else:
            self.logger.info(f'Journal db version: {ver}')
        cursor.close()
        return ver

    def _create_db(self):
        """
        Creates new database
        """
        cursor = self.db.cursor()
        try:
            sql = 'CREATE TABLE version (version INTEGER);'
            cursor.execute(sql)
            sql = 'INSERT INTO version VALUES ("1");'
            cursor.execute(sql)
            sql = 'CREATE TABLE journal (id INTEGER PRIMARY KEY, timestamp INTEGER, event TEXT, msg TEXT);'
            cursor.execute(sql)
            self.db.commit()
        except sqlite3.Error as e:
            self.logger.error(e)
        else:
            self.logger.info('Database created!')
        cursor.close()

    def read_all(self, limit=0, offset=0):
        """
        Select journal records from db
        return 2d array (list/tuple)
        """
        cursor = self.db.cursor()
        rows = [[]]
        try:
            if limit == 0:
                sql = 'SELECT * FROM journal;'
            else:
                sql = f'SELECT * FROM journal LIMIT {limit} OFFSET {offset};'
            cursor.execute(sql)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.error(e)
        else:
            self.logger.info(f'Readed {len(rows)} records')
        cursor.close()
        return rows

    def add_record(self, timestamp, event, msg):
        """
        Add new row to db
        """
        cursor = self.db.cursor()
        try:
            sql = f'INSERT INTO journal (timestamp, event, msg) VALUES ("{timestamp}", "{event}", "{msg}");'
            cursor.execute(sql)
        except sqlite3.Error as e:
            self.logger.error(e)
        else:
            self.db.commit()
        cursor.close()

    def __del__(self):
        if self.db is not None:
            self.logger.info('Closing db.')
            self.db.close()


if __name__ == "__main__":
    logging.basicConfig(format="%(filename)s:%(lineno)d: %(levelname)s %(asctime)s (%(name)s): %(message)s",
                        level=1, datefmt="%d-%b-%Y %H:%M:%S")
    journal = JournalDb()
    for i in [1, 2, 3]:
        journal.add_record(i, "12", "smwdj")
    tbl = journal.read_all()
    for row in tbl:
        print(row)
    pass



