import os
import signal
import sys
import time

import magic
import zstandard

from const import Actions
from engine import db_util
from table import file_content as fc
from table import update_history as uh
import hashlib

def set_file_processed(db, file):
    info = {
        uh.COL_FILE: file,
        uh.COL_PROCESS_STATUS: 1
    }
    uh.update_history(db, info)

def is_desire_mime(mime):
    main_mime, sub_mime = mime.split('/')
    wanted = False
    if main_mime in ['text'] or sub_mime.find('officedocument') != -1:
        wanted = True
    return wanted

def read_file(path, buff_size):
    if not os.path.exists(path):
        return None
    content = None
    try:
        with open(path, 'rb') as fd:
            content = fd.read(buff_size)  # 太小了office文档识别不正确.
    except PermissionError as ex:
        pass
    return content

def is_same_content(old_conent, new_content):
    if old_conent is None:
        return False
    digest1 = hashlib.sha256(old_conent).hexdigest()
    digest2 = hashlib.sha256(new_content).hexdigest()
    return digest1 == digest2

def need_update(db, path):
    content = read_file(path, 2048)
    if not content:
        return False
    need = True
    try:
        mime = magic.from_buffer(content, mime=True)  # magic can're reco chinese file name
    except magic.magic.MagicException as ex:
        return False
    if not is_desire_mime(mime):
        set_file_processed(db, path)
        need = False
    return need

def update_content(db):
    cctx = zstandard.ZstdCompressor()
    files = uh.get_not_processed(db, action=Actions.updated, is_file=True)
    for f in files:
        path = f['path']
        if not need_update(db, path):
            continue
        content = read_file(path, -1)
        latest_content = fc.get_latest_content(db, path, None)
        new_content = cctx.compress(content)
        if is_same_content(latest_content, new_content):
            continue
        print('update file:{}'.format(path))
        file_name = os.path.split(path)[1]
        file_type = os.path.splitext(path)[1][1:]
        info = {
            fc.COL_FILE: path,
            fc.COL_TIMESTAMP: f[uh.COL_TIMESTAMP],
            fc.COL_CONTENT: new_content,
            fc.COL_FILE_NAME: file_name,
            fc.COL_FILE_TYPE: file_type,
        }
        fc.update_file_info(db, info)
        set_file_processed(db, path)
    db.commit()

def signal_handler_interupt(sig, frame):
    print('update_file_content exit(Ctrl-C).')
    sys.exit(0)

if __name__ == '__main__':
    db = db_util.init_db()
    signal.signal(signal.SIGINT, signal_handler_interupt)
    while True:
        update_content(db)
        time.sleep(300)
