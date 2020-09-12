from table import update_history
from table import file_content
from engine import mdb
import os

def init_db():
    os.makedirs('history_db', exist_ok=True)
    sql3cfg = {'db': 'history_db/history.db'}
    cursor = mdb.Mdb(None, sql3cfg, True)
    update_history.create_table(cursor)
    file_content.create_table(cursor)
    return cursor
