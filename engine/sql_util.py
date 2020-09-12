import copy
from engine import sql_convert


def create_table(tblname, columns, primarykey):
    sql = 'CREATE TABLE IF NOT EXISTS {0} ({1}, PRIMARY KEY ({2}))'.format(
        tblname, ','.join(columns), ','.join(primarykey))
    return sql


def update(tblname, proplist, condlist):
    setlist = []
    for (k, v) in proplist.items():
        v = set_quote_sql(v)
        setlist.append('{0}={1}'.format(k, v))
    setlist = ','.join(setlist)
    condsql = []
    for cond in condlist:
        key, op, value = cond
        value = set_quote_sql(value)
        c = '{0} {1} {2}'.format(key, op, value)
        condsql.append(c)
    condsql = ' AND '.join(condsql)
    sql = 'UPDATE {0} SET {1} WHERE {2}'.format(tblname, setlist, condsql)
    return sql

def sqlite_update(tblname, proplist, condlist):
    setlist = []
    values_and_wheres = []
    for (k, v) in proplist.items():
        v = set_quote_sql(v)
        setlist.append('{0}=?'.format(k))
        values_and_wheres.append(v)
    setlist = ','.join(setlist)
    condsql = []
    for cond in condlist:
        key, op, value = cond
        value = set_quote_sql(value)
        c = '{0} {1} ?'.format(key, op)
        condsql.append(c)
        values_and_wheres.append(value)
    condsql = ' AND '.join(condsql)
    sql = 'UPDATE {0} SET {1} WHERE {2}'.format(tblname, setlist, condsql)
    return sql, values_and_wheres


def select(tblname, columns, condlist, limit, order):
    columns = ','.join(columns)
    condsql = []
    for cond in condlist:
        key, op, value = cond
        value = set_quote_sql(value)
        c = '{0} {1} {2}'.format(key, op, value)
        condsql.append(c)
    sql = 'SELECT {0} FROM {1}'.format(columns, tblname)
    if condsql:
        condsql = ' AND '.join(condsql)
        sql = '{0} WHERE {1}'.format(sql, condsql)
    if order:
        sort = order[1] and 'DESC' or 'ASC'
        sql = '{0} ORDER BY {1} {2}'.format(sql, order[0], sort)
    if limit:
        sql = '{0} LIMIT {1}'.format(sql, limit)
    return sql


def selectbatch(tblname, columns, condlist, order):
    columns = ','.join(columns)
    condColumnName, condColumnValue = condlist
    condColumnValue = list(map(lambda x:set_quote_sql(x), condColumnValue))
    condColumnValue = '{0}'.format(','.join(condColumnValue))
    sql = 'SELECT {0} FROM {1} WHERE {2} IN {3}'.format(columns, tblname, condColumnName, condColumnValue)
    if order:
        sort = order[1] and 'DESC' or ' ASC'
        sql = '{0} ORDER BY {1}'.format(sql, order[0], sort)
    return sql


def count(tableName, condList):
    condSql = []
    for cond in condList:
        key, op, value = cond
        c = '{0} {1} {2}'.format(key, op, set_quote_sql(value))
        condSql.append(c)
    condSql = ' AND '.join(condSql)
    sql = 'SELECT COUNT(*) FROM {0} WHERE {1}'.format(tableName, condSql)
    return sql


def insert(tableName, columns):
    keys = []
    values = []
    for (k, v) in columns.items():
        if v is not None:
            keys.append(k)
            values.append(set_quote_sql(v))
    keys = ','.join(keys)
    values = ','.join(values)
    sql = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(tableName, keys, values)
    return sql

def sqlite_insert(tableName, columns):
    keys = []
    holders = []
    values = []
    for (k, v) in columns.items():
        if v is not None:
            keys.append(k)
            holders.append('?')
            values.append(v)
    keys = ','.join(keys)
    holders = ','.join(holders)
    sql = 'INSERT INTO {0} ({1}) VALUES ({2})'.format(tableName, keys, holders)
    return sql, values


def insertMultiRows(tableName, columns, values):
    rows = []
    for i in range(len(values)):
        vv = values[i]
        for j in range(len(vv)):
            vv[j] = set_quote_sql(vv[j])
        oneRow = '({0})'.format(' , '.join(values[i]))
        rows.append(oneRow)
    columns = ','.join(columns)
    rows = ','.join(rows)
    sql = 'INSERT INTO {0} ({1}) VALUES {2}'.format(tableName, columns, rows)
    return sql


def insertOrUpdate(tableName, columns, primaryKey):
    updateCol = []
    columns = copy.deepcopy(columns)
    for (k, v) in columns.items():
        columns[k] = set_quote_sql(v)
        if k not in primaryKey:
            set = '{0}={1}'.format(k, columns[k])
            updateCol.append(set)
    updateCol = ','.join(updateCol)
    keys = columns.keys()
    values = list(columns.values())
    keys = ','.join(keys)
    values = ','.join(values)
    sql = 'INSERT INTO {0} ({1}) VALUES ({2}) ON DUPLICATE KEY UPDATE {3}'.format(tableName, keys, values, updateCol)
    return sql


def delete(tableName, condList):
    sql = 'DELETE FROM {0}'.format(tableName)
    if condList:
        condSql = []
        for cond in condList:
            key, op, value = cond
            c = '{0} {1} {2}'.format(key, op, set_quote_sql(value))
            condSql.append(c)
        condSql = ' AND '.join(condSql)
        sql = '{0} WHERE {1}'.format(sql, condSql)
    return sql


def add(tableName, columns, condList, getNewValue):
    setList = []
    for (k, v) in columns.items():
        set = '{0}={0}+{1}'.format(k, v)
        setList.append(set)
    setList = ','.join(setList)

    condSql = []
    for cond in condList:
        key, op, value = cond
        c = '{0} {1} {2}'.format(key, op, set_quote_sql(value))
        condSql.append(c)
    condSql = ' AND '.join(condSql)
    sql = 'UPDATE {0} SET {1} WHERE {2}'.format(tableName, setList, condSql)
    if getNewValue:
        sql = '{0};{1}'.format(sql, select(tableName, columns.keys(), condList, None, None))
    return sql


def set_quote_sql(value):
    if isinstance(value, str):
        if value != 'NULL':
            value = sql_convert.escape_item(value, 'utf-8')
    else:
        value = str(value)
    return value


def isColumnExists(tableName, column):
    sql = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{0}' AND column_name = '{1}'".format(tableName, column)
    return sql


def isCreateDatabase(sql):
    return 'create database' in sql.lower()
