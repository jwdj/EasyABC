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

def search_files(dir, ext):
    return [os.path.join(dp, f) for dp, dn, filenames in os.walk(dir) for f in filenames if os.path.splitext(f)[1] in ext]

def read_entire_file(path):
    f = open(path, 'rb') # read in binary to avoid problem with EOL characters
    result = f.read()
    f.close()
    return result

def read_text_if_file_exists(filepath):
    ''' reads the contents of the given file if it exists, otherwise returns the empty string '''
    if filepath and os.path.exists(filepath):
        return read_entire_file(filepath)
    else:
        return ''
