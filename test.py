import json, os
from utils import get_cmd_line_options
from utils import open_for_write
from utils import close_file
from utils import logmsg
from utils import now_str
from utils import uprint

def is_junction(path: str) -> bool:
    try:
        return bool(os.readlink(path))
    except OSError:
        return False

def nonzerostr(label:str, val:int):
    if val != 0:
        return label +':'+str(val)+' '
    else:
        return ' '

def stat_str(stat) -> str:
    s = ''
    s += nonzerostr('mode', stat.st_mode)
    s += nonzerostr('ino', stat.st_ino)
    s += nonzerostr('dev', stat.st_dev)
    s += nonzerostr('nlink', stat.st_nlink)
    s += nonzerostr('uid', stat.st_uid)
    s += nonzerostr('gid', stat.st_gid)
    s += nonzerostr('size', stat.st_size)
    s = s.strip()
    s = s + ' '
    s += nonzerostr('atime', stat.st_atime)
    s += nonzerostr('mtime', stat.st_mtime)
    s += nonzerostr('ctime', stat.st_ctime)
    s = s.strip()
    return s

def recurse_dir(dirname:str, filelist:list, f_errorlog):
    subdirs = []
    try:
        dir_sta = os.stat(dirname, follow_symlinks=False)
        ls = os.scandir(dirname)
        for entry in ls: # each entry is type: <class 'nt.DirEntry'>
            if entry.is_dir(follow_symlinks=False):
                subdirs.append(entry.path)
                #if not is_junction(entry.path):
                #    subdirs.append(entry.path)
                #else:
                #    sta = entry.stat(follow_symlinks=False)
                #    uprint("D & J:", "'"+entry.path+"'", stat_str(sta), "\n", file=f_errorlog)
                #    if sta.st_mode != 16895:
                #        uprint("Expected mode to be 16,896", file=f_errorlog)

            elif entry.is_file(follow_symlinks=False):
                filelist.append(entry.path)

            else:
                sta = entry.stat(follow_symlinks=False)
                uprint("Not D nor F:", "'"+entry.path+"'", stat_str(sta), "\n", file=f_errorlog)

        for subdir in subdirs:
            recurse_dir(subdir, filelist, f_errorlog)

    except Exception as e:
        uprint('EXCEPTION, recurse_dir:', "'"+dirname+"'", 'stat:', stat_str(dir_sta), e, file=f_errorlog)

#######################################################################################
opts = get_cmd_line_options()
f_out = open_for_write(opts['output_file'])
f_log = open_for_write(opts['log_file'], append=True)

logmsg(f_log, 'Start:', doflush=True)
countTopDir = 0
filelist = []
for topdir in opts['folders']:
    countTopDir += 1
    logmsg(f_log, countTopDir, 'topdir:', "'"+topdir+"'")
    recurse_dir(topdir, filelist, f_log)

uprint("FILE LIST. Len:", len(filelist), file=f_out)
uprint(json.dumps(filelist, indent=2), file=f_out)
logmsg(f_log, 'Finished')

'''countwalk = 0
    for (root, dirs, files) in os.walk(topdir, topdown=True): # string, list, 
        countwalk += 1
        uprint('  ', countwalk, 'root:', root, 'Len(dirs):', len(dirs), 'Len(files):',len(files), file=f_out)
        countdirs = 0
        for dr in dirs:
            countdirs += 1
            uprint('    ', countdirs, 'dir:', dr, file=f_out)
            if countdirs > 4:
                uprint('    ', '-' * 20, file=f_out)
                break
        countfiles = 0
        for fl in files:
            countfiles += 1
            uprint('    ', countfiles, 'file:', fl, file=f_out)
            if countfiles > 4:
                uprint('    ', '_' * 20, file=f_out)
                break
        if countwalk > 9:
            uprint('  ', '*' * 40, file=f_out)
            break'''

close_file(f_out)
close_file(f_log)
