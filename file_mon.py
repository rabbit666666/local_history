import json
import time
from functools import reduce
import codecs

import watchdog.observers.winapi as winapi
from const import Actions
from engine import db_util
from engine import path_util as pu
from table import update_history as uh
from viewer.kmp import strrmatch
from watchdog.events import *
from watchdog.observers import Observer

winapi.WATCHDOG_FILE_NOTIFY_FLAGS = reduce(
    lambda x, y: x | y, [
        winapi.FILE_NOTIFY_CHANGE_LAST_WRITE,
    ])

def is_exclude(file, exclude):
    need_execlude = False
    for ex_file in exclude:
        if strrmatch(file, ex_file):
            need_execlude = True
            break
    return need_execlude

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, exclude_lst, pending_modify_files):
        FileSystemEventHandler.__init__(self)
        self.exclude_lst = exclude_lst
        self.pending_modify_files = pending_modify_files

    def on_modified(self, event):  # 文件修改
        if event.is_directory:
            return
        if is_exclude(event.src_path, self.exclude_lst):
            return
        if event.src_path not in pending_modify:
            print('{} has changed'.format(event.src_path))
            pending_modify.append(event.src_path)

def load_config():
    with codecs.open('app_cfg.json', 'r', encoding='utf8') as fd:
        cfg = json.loads(fd.read())
    exclude = cfg['exclude']
    for i, info in enumerate(exclude):
        path = pu.norm_path(info['text'])
        if info['need_wildcard']:
            path = '*{}*'.format(path)
        exclude[i] = path
    for i, dir in enumerate(cfg["include"]):
        cfg["include"][i] = pu.norm_path(dir)
    for i, dir in enumerate(cfg["snapshot"]):
        cfg["snapshot"][i] = pu.norm_path(dir)
    return cfg

def process_pending(mdb, pending_modify):
    for f in pending_modify:
        info = {
            uh.COL_FILE: f,
            uh.COL_ACTION: Actions.updated,
            uh.COL_TIMESTAMP: int(time.time()),
            uh.COL_PROCESS_STATUS: 0,
            uh.COL_IS_FILE: 1,
        }
        uh.update_history(mdb, info)
    if pending_modify:
        mdb.commit()
    pending_modify.clear()

if __name__ == '__main__':
    if not os.path.exists('app_cfg.json'):
        print('please change app_cfg.json.sample to app_cfg.json, and setup it.')
        exit(0)
    mdb = db_util.init_db()
    cwd = os.getcwd()
    cfg = load_config()
    pending_modify = []
    event_handler = FileEventHandler(cfg["exclude"], pending_modify)

    observer = Observer()
    for inc in cfg["include"]:
        observer.schedule(event_handler, inc, True)
    observer.start()

    try:
        while True:
            process_pending(mdb, pending_modify)
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print('file mon stoped.')
