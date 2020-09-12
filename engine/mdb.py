import sqlite3

import pymysql
import pymysql.cursors

class Mdb:
    def __init__(self, mysqlConfig, sqliteConfig, useSqliteRead, autoCommit = False):
        self.mysqlConn = None
        self.mysqlCursor = None
        self.sqliteConn = None
        self.sqliteCursor = None
        self.mysqlConfig = mysqlConfig
        self.sqliteConfig = sqliteConfig
        if mysqlConfig:
            self.mysqlConn = pymysql.connect(host=mysqlConfig['host'],
                                             user=mysqlConfig['user'],
                                             passwd=mysqlConfig['passwd'],
                                             port=mysqlConfig['port'],
                                             charset='utf8')
            self.mysqlConn.autocommit(autoCommit)
            self.mysqlCursor = self.mysqlConn.cursor()
            self.mysqlCursor.execute('CREATE DATABASE IF NOT EXISTS {0};'.format(mysqlConfig['db']))
            self.mysqlCursor.execute('USE {0}'.format(mysqlConfig['db']))
            #self.mysqlConn.set_charset('utf8')
            self.mysqlCursor.execute('SET NAMES utf8;')
            self.mysqlCursor.execute('SET CHARACTER SET utf8;')
            self.mysqlCursor.execute('SET character_set_connection=utf8;')

        if sqliteConfig:
            self.sqliteConn = sqlite3.connect(sqliteConfig['db'])
            self.sqliteCursor = self.sqliteConn.cursor()
            # if autoCommit:
            #     self.sqliteConn.isolation_level = None # todo: for test
        self.sqliteConfig = sqliteConfig
        self.useSqliteRead = useSqliteRead

    def clone(self):
        obj = Mdb(None, self.sqliteConfig, True)
        return obj

    def getSqliteConfig(self):
        return self.sqliteConfig

    def getMysqlConfig(self):
        return self.mysqlConfig

    def execute(self, sql):
        if not self.mysqlCursor:
            self._executeSqlite(sql)
        elif self._isReadSql(sql):
            if self.useSqliteRead:
                self._executeSqlite(sql)
            else:
                self._executeMysql(sql)
        else:
            if self.sqliteCursor:
                self._executeSqlite(sql)
            self._executeMysql(sql)

    def _executeSqlite(self, sql):
        try:
            res = self.sqliteCursor.execute(sql)
            return res
        except sqlite3.OperationalError as ex:
            if ex.args[0].find('duplicate column') == -1:
                raise ex

    def _executeMysql(self, sql):
        if not self.mysqlCursor:
            return
        try:
            self.mysqlCursor.execute(sql)
        except pymysql.err.Error as ex:
            if ex.args[1].find('Duplicate column') == -1:
                raise ex

    def fetchone(self):
        if self.useSqliteRead:
            res = self.sqliteCursor.fetchone()
        else:
            res = self.mysqlCursor.fetchone()
        return res

    def fetchall(self):
        if self.useSqliteRead:
            res = self.sqliteCursor.fetchall()
        else:
            res = self.mysqlCursor.fetchall()
        return res

    def commit(self):
        if self.sqliteConn:
            self.sqliteConn.commit()
        if self.mysqlConn:
            self.mysqlConn.commit()

    def close(self):
        if self.mysqlConn:
            self.mysqlCursor.close()
            self.mysqlConn.close()
        self.sqliteCursor.close()
        self.sqliteConn.close()

    def _isReadSql(self, sql):
        return sql.upper().find('SELECT ') != -1
