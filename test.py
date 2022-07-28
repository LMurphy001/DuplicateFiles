import Criteria
from utils import get_cmd_line_options, open_for_write, uprint, now_str, simple_print_dict, close_file
'''import json, os, os.path
from utils import get_cmd_line_options
from utils import open_for_write
from utils import close_file
from utils import now_str
from utils import uprint
from utils import thousands
from utils import is_junction
'''

'''def nonzerostr(label:str, val:int):
    if val != 0:
        return label +':'+str(val)+' '
    else:
        return ' '

def stat_str(stat) -> str:
    s = ''
    if stat.st_mode != 16895:
        s += nonzerostr('mode', stat.st_mode)
    #s += nonzerostr('ino', stat.st_ino)
    s += nonzerostr('dev', stat.st_dev)
    s += nonzerostr('nlink', stat.st_nlink)
    s += nonzerostr('uid', stat.st_uid)
    s += nonzerostr('gid', stat.st_gid)
    s += nonzerostr('size', stat.st_size)
    s = s.strip()
    #s = s + ' '
    #s += nonzerostr('atime', stat.st_atime)
    #s += nonzerostr('mtime', stat.st_mtime)
    #s += nonzerostr('ctime', stat.st_ctime)
    #s = s.strip()
    return s
'''

'''def recurse_dir(dirname:str, filelist:list, params, f_errorlog):
    ##### TODO: FIX CHECKING TO USE ALL LOWERCASE ########
    subdirs = []
    try:
        ls = os.scandir(dirname)
        for entry in ls:
            if entry.is_dir(follow_symlinks=False):
                if not is_junction(entry.path):
                    if entry.name in params.excl_folders or entry.path in params.excl_folders:
                        uprint('Exclude folder', entry.path, file=f_errorlog)
                        pass
                    else:
                        subdirs.append(entry.path)
            elif entry.is_file(follow_symlinks=False):
                skip = False
                if len(params.incl_files) > 0 and (not entry.name in params.incl_files):
                    skip = True
                    uprint('Filename not in files', entry.name, file=f_errorlog)
                elif len(params.excl_files) > 0 and (entry.name in params.excl_files or entry.path in params.excl_files):
                    skip = True
                    uprint('Filename', entry.path, 'is on the exclude list', file=f_errorlog)
                else:
                    part1, ext = os.path.splitext(entry.path)
                    if len(params.incl_exts) > 0 and (not ext in params.incl_exts):
                        skip = True
                        uprint('Unaccepted file ext',ext, entry.path, file=f_errorlog)
                    elif len(params.excl_exts) > 0 and ext in params.excl_exts:
                        skip = True
                        #uprint('Excluded file ext',ext, entry.path, file=f_errorlog)
                if not skip:
                    stat = entry.stat(follow_symlinks=False)
                    if stat.st_size < params.min_bytes:
                        skip = True
                        if stat.st_size > 0:
                            pass
                            #uprint('File is too small', thousands(stat.st_size), entry.path, file=f_errorlog)
                    elif params.max_bytes > 0 and stat.st_size > params.max_bytes:
                        skip = True
                        #uprint('File is too large', thousands(stat.st_size), entry.path, file=f_errorlog)
                    else:
                        filelist.append(entry.path)
        for subdir in subdirs:
            recurse_dir(subdir, filelist, params, f_errorlog)
    except Exception as e:
        uprint(now_str(), "EXCEPTION, recurse_dir:", "'" + dirname + "' ", e, file=f_errorlog)

class Params:
    def __init__(self, opts):
        self.min_bytes    = opts['min_bytes']
        self.max_bytes    = opts['max_bytes']
        self.incl_folders = set(opts['folders']) #cloth = cloth
        self.excl_folders = set(opts['exclude_folders'])
        self.incl_files   = set(opts['files'])
        self.excl_files   = set(opts['exclude_files'])
        self.incl_exts    = set(opts['extensions'])
        self.excl_exts    = set(opts['exclude_extensions'])
              
    def __str__(self):
        return f'Params(folders:{self.incl_folders}, exclude folders:{self.excl_folders}, files:{self.incl_files}, exclude files:{self.excl_files}, extensions:{self.incl_exts}, exclude extensions:{self.excl_exts})'
'''
#######################################################################################

opts = get_cmd_line_options()
f_log = open_for_write(opts['log_file'], append=True)

uprint("", file=f_log)
uprint(now_str(), 'Start', file=f_log)

f_out = open_for_write(opts['output_file'])
criteria = Criteria(opts)
countTopDir = 0
filelist = dict
folderlist = dict
for topdir in criteria.incl_folders:
    countTopDir += 1
    uprint(now_str(), countTopDir, ") topdir: '" + topdir + "'", file=f_log)
    criteria.dir_meets_criteria()

simple_print_dict(folderlist, "FOLDER LIST:", f_out)
simple_print_dict(filelist, "FILE LIST:", f_out)

uprint(now_str(), "Finished.", file=f_log)

close_file(f_out)
close_file(f_log)
