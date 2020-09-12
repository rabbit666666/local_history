import os

def norm_path(path):
    drive, sub_path = os.path.splitdrive(path)
    drive = drive.upper()
    new_path = os.path.normpath(os.path.join(drive, sub_path))
    return new_path

def unquote_path(path):
    return path.replace('\\\\', '\\')
