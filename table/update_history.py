from engine import sql_util as sqlutil

tbl_name = 'update_history'

COL_FILE = 'path'
COL_ACTION = 'action'  # 1: "Created", 2: "Deleted", 3: "Updated", 4: "Renamed from something", 5: "Renamed to something"
COL_TIMESTAMP = 'timestamp'
COL_IS_FILE = 'is_file'
COL_PROCESS_STATUS = 'status'  # 处理状态: 0:未处理, 1:已处理

PRIMARY_KEY = [COL_FILE]

def create_table(mdb):
    columns = [
        COL_FILE + " VARCHAR(32767) NOT NULL",  # windows max path length
    ]
    sql = sqlutil.create_table(tbl_name, columns, PRIMARY_KEY)
    mdb.execute(sql)
    add_cols = [
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_ACTION + " TINYINT(2) DEFAULT NULL",
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_TIMESTAMP + " INT(11) DEFAULT NULL",
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_IS_FILE + " TINYINT(2) DEFAULT 0",
        "ALTER TABLE " + tbl_name + " ADD COLUMN " + COL_PROCESS_STATUS + " TINYINT(2) DEFAULT 0",
    ]
    for sql in add_cols:
        mdb.execute(sql)
    return True

def get_not_processed(mdb, action=None, is_file=None):
    where = [(COL_PROCESS_STATUS, '=', 0)]
    if action:
        where.append((COL_ACTION, '=', action))
    if is_file is not None:
        where.append((COL_IS_FILE, '=', is_file and 1 or 0))
    columns = [COL_FILE, COL_ACTION, COL_TIMESTAMP]
    sql = sqlutil.select(tbl_name, columns, where, None, None)
    mdb.execute(sql)
    files = mdb.fetchall()
    new_files = []
    for f in files:
        new_files.append(dict(zip(columns, f)))
    return new_files

def update_history(mdb, history):
    file = history[COL_FILE]
    sql = sqlutil.select(tbl_name, [COL_FILE], [(COL_FILE, '=', file)], None, None)
    mdb.execute(sql)
    rst = mdb.fetchone()
    if rst:
        sql = sqlutil.update(tbl_name, history, [(COL_FILE, '=', file)])
    else:
        sql = sqlutil.insert(tbl_name, history)
    mdb.execute(sql)
