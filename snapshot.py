import file_mon as fm
import update_file_content as ufc
from engine import db_util
import os
from sys import stdout

def main():
    mdb = db_util.init_db()
    cfg = fm.load_config()
    pending_files = []
    for inc in cfg["snapshot"]:
        for (root, folders, files) in os.walk(inc):
            if fm.is_exclude(root, cfg["exclude"]):
                continue
            for f in files:
                path = os.path.join(root, f)
                if fm.is_exclude(path, cfg["exclude"]):
                    continue
                pending_files.append(path)
                stdout.write("\rcollect {} files".format(len(pending_files)))
                stdout.flush()
    print('\n')
    print('indexing...')
    total = len(pending_files)
    fm.process_pending(mdb, pending_files)
    print("updating content...")
    ufc.update_content(mdb, show_log=False)
    print("snapshot include complete, total has: {} files.".format(total))

if __name__ == '__main__':
    main()
