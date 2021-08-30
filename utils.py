import sys
import os, os.path

def get_application_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    elif __file__:
        return os.path.dirname(os.path.abspath(__file__))
    else:
        return os.getcwd()

def append_to_envpath(path):
    prepend = path + ';'
    envpath = os.environ.get('PATH', '')
    if not envpath.startswith(prepend):
        os.environ['PATH'] = prepend + envpath

def is_running_32bit():
    import struct
    bytesPerPointer = struct.calcsize("P")
    return bytesPerPointer == 4
