
def recurse_dir(dirname:str, filelist:list, params, f_errorlog):
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

