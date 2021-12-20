#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sqlite3
from logging import Logger
from observer import Observer, Observable

DB_VERSION = 1


class JournalDb(Observable):

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
        self.observers = []
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
            sql = 'CREATE TABLE journal (id INTEGER PRIMARY KEY, ' \
                  'timestamp INTEGER, watcher TEXT, event TEXT, msg TEXT);'
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
                sql = 'SELECT * FROM journal ORDER BY id DESC;'
            else:
                sql = f'SELECT * FROM journal ORDER BY id DESC LIMIT {limit} OFFSET {offset} ;'
            cursor.execute(sql)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.error(e)
        else:
            self.logger.info(f'Readed {len(rows)} records')
        cursor.close()
        return rows

    def add_record(self, timestamp, watcher, event, msg):
        """
        Add new row to db
        """
        cursor = self.db.cursor()
        try:
            sql = f"INSERT INTO journal (timestamp, watcher, event, msg)" \
                f" VALUES ('{timestamp}', '{str(watcher)}', '{event}', '{msg}');"
            cursor.execute(sql)
        except sqlite3.Error as e:
            self.logger.error(e)
        else:
            self.db.commit()
            self.notify_observers()
        cursor.close()

    def attach(self, observer: Observer):
        """
        Add journal changes listener
        """
        self.observers.append(observer)

    def detach(self, observable: Observable):
        """
        Remove journal changes listener
        """
        self.observers.remove(observable)

    def notify_observers(self):
        """
        Notify observers about journal changes
        """
        for observer in self.observers:
            observer.changed()

    def __del__(self):
        if self.db is not None:
            self.logger.info('Closing db.')
            self.db.close()


if __name__ == "__main__":
    from datetime import datetime
    journal = JournalDb()
    for i in range(200):
        journal.add_record(datetime.utcnow().timestamp(), "PING@127.0.0.1", 'Онлайн', 'Утсройство появилось в сети')
    pass





