from utils import get_cmd_line_options, open_for_write, uprint, now_str, simple_print_dict, close_file
from Criteria import Criteria

opts = get_cmd_line_options()
f_log=open_for_write(opts['log_file'], append=True)
f_out=open_for_write(opts['output_file'])

crit = Criteria(opts)
countTopDir = 0
filelist = dict()
folderlist = dict()
for topdir in crit.incl_folders:
    countTopDir += 1
    uprint(now_str(), countTopDir, ") topdir: '" + topdir + "'", file=f_log)
    crit.dir_meets_criteria(topdir, filelist, folderlist, f_log)

simple_print_dict(folderlist, "FOLDER LIST:", f_out)
simple_print_dict(filelist, "FILE LIST:", f_out)

uprint(now_str(), "Finished.", file=f_log)

close_file(f_out)
close_file(f_log)
