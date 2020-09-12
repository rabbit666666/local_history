import os
import signal
import sys
import time
import json

import win32con
import win32file

from engine import db_util
from engine import path_util as pu
from table import update_history as uh

from viewer.kmp import strrmatch

def is_exclude(file, exclude):
    need_execlude = False
    for ex_file in exclude:
        if strrmatch(file, ex_file):
            need_execlude = True
            break
    return need_execlude

def listen(path_to_watch, db, exclude):
    assert os.path.isabs(path_to_watch), 'file path must absolute, but give: {}'.format(path_to_watch)
    FILE_LIST_DIRECTORY = 0x0001
    hDir = win32file.CreateFile(path_to_watch,
                                FILE_LIST_DIRECTORY,
                                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                                None,
                                win32con.OPEN_EXISTING,
                                win32con.FILE_FLAG_BACKUP_SEMANTICS,
                                None
                                )
    while True:
        results = win32file.ReadDirectoryChangesW(
            hDir,
            4096,
            True,
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
            win32con.FILE_NOTIFY_CHANGE_SIZE |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
            win32con.FILE_NOTIFY_CHANGE_SECURITY,
            None,
            None
        )
        for action, file in results:
            full_filename = os.path.normpath(os.path.join(path_to_watch, file))
            if is_exclude(full_filename, exclude):
                continue
            print('{} has changed'.format(full_filename))
            is_file = os.path.isfile(full_filename) and 1 or 0
            info = {
                uh.COL_FILE: full_filename,
                uh.COL_ACTION: action,
                uh.COL_TIMESTAMP: int(time.time()),
                uh.COL_PROCESS_STATUS: 0,
                uh.COL_IS_FILE: is_file,
            }
            uh.update_history(db, info)
        db.commit()

def signal_handler_interupt(sig, frame):
    print('listen file change exit(Ctrl-C).')
    sys.exit(0)

def load_config():
    with open('app_cfg.json', 'r') as fd:
        cfg = json.loads(fd.read())
    exclude = cfg['exclude']
    for i, info in enumerate(exclude):
        path = pu.norm_path(info['text'])
        if info['need_wildcard']:
            path = '*{}*'.format(path)
        exclude[i] = path
    return cfg

if __name__ == '__main__':
    db = db_util.init_db()
    cwd = os.getcwd()
    signal.signal(signal.SIGINT, signal_handler_interupt)
    cfg = load_config()
    listen_path = pu.norm_path(cfg['include'][0])
    listen(listen_path, db, cfg['exclude'])
