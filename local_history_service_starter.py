import os
import signal
import subprocess
import sys
import time

def signal_handler_interupt(sig, frame):
    print('local history supervisor exit(Ctrl-C).')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler_interupt)
    path = os.path.split(__file__)[0]
    os.chdir(path)
    cmd_lst = [
        'python {}'.format(os.path.join(path, 'file_mon.py')),
        'python {}'.format(os.path.join(path, 'update_file_content.py')),
    ]
    procs = {}
    for cmd in cmd_lst:
        procs[cmd] = subprocess.Popen(cmd)
    while True:
        for (cmd, p) in procs.items():
            if p.poll() is not None:
                procs[cmd] = subprocess.Popen(cmd)
        time.sleep(10)

if __name__ == '__main__':
    main()
