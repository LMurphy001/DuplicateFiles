import locale
import os # os.readlink
from datetime import datetime
from sys import stderr, stdout
from argparse import ArgumentParser
from json import loads

# Todo: add options to the config file for file encoding. File/folder names and contents.
# For now, fudging utf-8 and utf-16. Not sure if it covers the bases.

def thousands(value : int) -> str:
    return f'{value:n}'

def timex(end_time, st_time):
    return "{0:0.4f}".format(end_time - st_time)

def now_str() -> str:
    locale.setlocale(locale.LC_ALL, '')
    dt = datetime.now()
    s = dt.strftime('%Y/%m/%d %H:%M:%S')
    s = s + dt.strftime('.%f')[:4]
    return s

def uprint(*objects, sep=' ', end='\n', file=stdout):
    enc = file.encoding
    if enc == 'UTF-8' or enc == 'UTF-16':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def is_junction(path: str) -> bool:
    try:
        return bool(os.readlink(path))
    except OSError: # non-link paths will land here.
        return False

def read_text_file(filename : str, r_enc = "UTF-8") -> str:
    ''' Read a whole UTF-8 file and return its contents. Not suitable for large or binary files. '''
    try:
        f = open(filename, mode='rt', encoding=r_enc)
        txt = f.read()
        f.close()
    except Exception as e:
        uprint(filename, e, stderr)
        return ''
    return txt

def open_for_write(filename : str, append=False, w_enc="UTF-8"):
    o_mode = 't' # text, not binary
    if append:
        o_mode = 'a' + o_mode # writing, append to end of file if it exists
    else:
        o_mode = 'w' + o_mode # writing, truncate file first
    try:
        f = open(filename, mode=o_mode, encoding=w_enc)
    except Exception as e:
        uprint("Unable to write",filename, "Mode:",o_mode,"Encoding:", w_enc, e, stderr)
    return f

def close_file(f):
    f.close()

def get_cmd_line_options() -> dict:

    def get_options_filename() -> str:
        parser = ArgumentParser(description="Find Duplicate Files in Folders")
        parser.add_argument('Options_filename', help="Name of .json file with the script's options. See the example in config.json file", default="")
        args = parser.parse_args()
        if (args.Options_filename.strip() == ''):
            exit("Required: Options_filename")
        return args.Options_filename.strip()

    options_filename = get_options_filename()
    readtxt = read_text_file(options_filename)
    try:
        dictionary = loads(readtxt)
    except Exception as e:
        uprint('EXCEPTION: Badly formatted json in', options_filename,"\n", e, stderr)
    return dictionary

def hash_large_file(filename : str, hashfunc, errorlog, buffersize : int = 4096):
    ''' hash very large file. Buffers. Easier on computer's memory (RAM). '''
    hsh = hashfunc()
    # 'rb' means read, binary
    try:
        f = open(filename, 'rb')
    except Exception as e:
        uprint('hash_large_file, open()', filename, e, file=errorlog)
        return 0

    while True:
        try:
            data = f.read(buffersize)
            if not data:
                break
            hsh.update(data)
        except Exception as e:
            uprint('hash_large_file, read() or hash update()', filename, e, file=errorlog)
            return 0
    f.close()
    return hsh

def simple_print_dict(adict:dict, label:str, outfile):
    uprint(label, file=outfile)
    for key, val in adict.items():
        uprint(' ', key, ' = [', file=outfile)
        for name in val:
            uprint('   ', name, file=outfile)
    uprint(']', file=outfile)
    uprint(file=outfile)

def list_to_lower(list:list)->list:
    res = list
    for item in list:
        res.append(str(item).lower())
    return res
