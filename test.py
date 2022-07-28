import json, os
from utils import get_cmd_line_options
from utils import open_for_write
from utils import close_file
from utils import now_str
from utils import uprint
from utils import thousands
from utils import is_junction

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

def recurse_dir(dirname:str, filelist:list, f_errorlog):
    subdirs = []
    try:
        ls = os.scandir(dirname)
        for entry in ls:
            if entry.is_dir(follow_symlinks=False):
                if not is_junction(entry.path):
                    subdirs.append(entry.path)
            elif entry.is_file(follow_symlinks=False):
                filelist.append(entry.path)
        for subdir in subdirs:
            recurse_dir(subdir, filelist, f_errorlog)
    except Exception as e:
        uprint(now_str(), "EXCEPTION, recurse_dir:", "'" + dirname + "' ", e, file=f_errorlog)

#######################################################################################
opts = get_cmd_line_options()
f_out = open_for_write(opts['output_file'])
f_log = open_for_write(opts['log_file'], append=True)

uprint("", file=f_log)
uprint(now_str(), 'Start', file=f_log)
countTopDir = 0
filelist = []
for topdir in opts['folders']:
    countTopDir += 1
    uprint(now_str(), countTopDir, ") topdir: '" + topdir + "'", file=f_log)
    recurse_dir(topdir, filelist, f_log)

uprint("FILE LIST. Len:", thousands(len(filelist)), file=f_out)
uprint(json.dumps(filelist, indent=2), file=f_out)
uprint(now_str(), "Finished.", file=f_log)


close_file(f_out)
close_file(f_log)
