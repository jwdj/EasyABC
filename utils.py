import sys
import os, os.path

def get_application_path():
    if getattr(sys, 'frozen', False):
        if sys.platform == "darwin":
            return os.path.dirname(sys.argv[0])
        else:
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

def ensure_file_name_does_not_exist(file_path):
    if not os.path.exists(file_path):
        return file_path

    i = 0
    file_exists = True
    path, file_name = os.path.split(file_path)
    name, extension = os.path.splitext(file_name)
    while file_exists:
        i += 1
        file_path = os.path.abspath(os.path.join(path, "{0}({1}){2}".format(name, i, extension)))
        file_exists = os.path.exists(file_path)
    return file_path

def generate_temp_file_name(path, ending, replace_ending=None):
    i = 0
    file_exists = True
    while file_exists:
        file_name = os.path.abspath(os.path.join(path, "temp{0:02d}{1}".format(i, ending)))
        file_exists = os.path.exists(file_name)
        if not file_exists and replace_ending is not None:
            f = os.path.abspath(os.path.join(path, "temp{0:02d}{1}".format(i, replace_ending)))
            file_exists = os.path.exists(f)
        i += 1
    return file_name