from engine import sql_util as sqlutil
from engine import path_util as pu

tbl_name = 'file_content'

COL_FILE = 'file'
COL_TIMESTAMP = 'timestamp'
COL_FILE_NAME = 'filen_name'
COL_FILE_TYPE = 'file_type'
COL_CONTENT = 'content'  # 处理状态: 0:未处理, 1:已处理

PRIMARY_KEY = [COL_FILE, COL_TIMESTAMP]

def create_table(mdb):
    columns = [
        COL_FILE + " TEXT NOT NULL",  # windows max path length
        COL_TIMESTAMP + " INT(11) NOT NULL",
    ]
    sql = sqlutil.create_table(tbl_name, columns, PRIMARY_KEY)
    mdb.execute(sql)
    add_cols = [
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_FILE_NAME + " VARCHAR(256) DEFAULT NULL",
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_FILE_TYPE + " VARCHAR(32) DEFAULT NULL",
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_CONTENT + " BLOB",
    ]
    for sql in add_cols:
        mdb.execute(sql)
    return True

def update_file_info(mdb, file_info):
    where = [
        (COL_FILE, '=', file_info[COL_FILE]),
        (COL_TIMESTAMP, '=', file_info[COL_TIMESTAMP])
    ]
    sql = sqlutil.select(tbl_name, [COL_FILE], where, None, None)
    mdb.execute(sql)
    rst = mdb.fetchone()
    if rst:
        assert False
        sql, values_and_where = sqlutil.sqlite_update(tbl_name, file_info, where)
        mdb.sqliteConn.execute(sql, values_and_where)
    else:
        sql, values = sqlutil.sqlite_insert(tbl_name, file_info)
        mdb.sqliteConn.execute(sql, values)

def get_file_content(mdb, file, time):
    where = [
        (COL_FILE, '=', file),
        (COL_TIMESTAMP, '=', time),
    ]
    sql = sqlutil.select(tbl_name, [COL_CONTENT], where, None, None)
    mdb.execute(sql)
    rst = mdb.fetchone()
    return rst[0]

def get_latest_content(mdb, file, time):
    where = [
        (COL_FILE, '=', file),
    ]
    if time:
        where.append((COL_TIMESTAMP, '<=', time))
    sql = sqlutil.select(tbl_name, [COL_CONTENT], where, 1, (COL_TIMESTAMP, 'DESC'))
    mdb.execute(sql)
    rst = mdb.fetchone()
    if rst:
        return rst[0]
    return None

def get_file_update_time(mdb, file):
    where = [
        (COL_FILE, '=', file),
    ]
    sql = sqlutil.select(tbl_name, [COL_TIMESTAMP], where, None, None)
    mdb.execute(sql)
    times = mdb.fetchall()
    new_times = []
    for f in times:
        new_times.append(f[0])
    return new_times

def get_file_names(mdb, date_from, date_to):
    if date_from and date_to:
        sql = 'SELECT DISTINCT {} FROM {} WHERE {}>={} AND {}<={}'.format(
            COL_FILE, tbl_name, COL_TIMESTAMP, date_from, COL_TIMESTAMP, date_to)
    elif date_from:
        sql = 'SELECT DISTINCT {} FROM {} WHERE {}>={}'.format(
            COL_FILE, tbl_name, COL_TIMESTAMP, date_from)
    elif date_to:
        sql = 'SELECT DISTINCT {} FROM {} WHERE {}<={}'.format(
            COL_FILE, tbl_name, COL_TIMESTAMP, date_to)
    else:
        sql = 'SELECT DISTINCT {} FROM {}'.format(COL_FILE, tbl_name)
    mdb.execute(sql)
    files = mdb.fetchall()
    new_files = []
    for f in files:
        new_files.append(f[0])
    return new_files

def get_file_datetimes(mdb, files):
    if files:
        sql = 'SELECT DISTINCT {dt} FROM {table} WHERE {file} IN ({cond})'.format(
            dt=COL_TIMESTAMP, table=tbl_name, file=COL_FILE, cond=','.join(files))
    else:
        sql = 'SELECT DISTINCT {dt} FROM {table}'.format(
            dt=COL_TIMESTAMP, table=tbl_name)
    print(sql)
    mdb.execute(sql)
    dt_lst = mdb.fetchall()
    new_dt = []
    for f in dt_lst:
        new_dt.append(f[0])
    new_dt.sort(reverse=True)
    return new_dt