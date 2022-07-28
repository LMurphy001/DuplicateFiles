import os
from typing import TextIO
from utils import list_to_lower, now_str, uprint, is_junction

class Criteria:
    def __init__(self, opts:dict):
        self.min_bytes     = opts['min_bytes']
        self.max_bytes     = opts['max_bytes']
        self.has_max_bytes = self.max_bytes > 0

        self.incl_folders     = set(list_to_lower(opts['folders']))
        self.excl_folders     = set(list_to_lower(opts['exclude_folders']))
        self.has_folders      = len(self.incl_folders) > 0
        self.has_excl_folders = len(self.excl_folders) > 0

        self.incl_files         = set(list_to_lower(opts['files']))
        self.excl_files         = set(list_to_lower(opts['exclude_files']))
        self.has_filenames      = len(self.incl_files) > 0
        self.has_excl_filenames = len(self.excl_files) > 0

        self.incl_exts      = set(list_to_lower(opts['extensions']))
        self.excl_exts      = set(list_to_lower(opts['exclude_extensions']))
        self.has_extensions = len(self.incl_exts) > 0
        self.has_excl_ext   = len(self.excl_exts) > 0

    def __repr__(self):
        r = 'Criteria('
        r += f'min_bytes={self.min_bytes}, max_bytes={self.max_bytes}, has_max_bytes={self.has_max_bytes}'

        r += f',\n incl_folders={self.incl_folders},\n excl_folders={self.excl_folders}'
        r += f',\n has_folders={self.has_folders}, has_excl_folders={self.has_excl_folders}'

        r += f',\n incl_files={self.incl_files},\n excl_files={self.excl_files}'
        r += f',\n has_filenames={self.has_filenames}, has_excl_filenames={self.has_excl_filenames}'

        r += f',\n incl_exts={self.incl_exts},\n excl_exts={self.excl_exts}'
        r += f',\n has_extensions={self.has_extensions}, has_excl_ext={self.has_excl_ext}'
        r += f')'
        return r

    def folder_meets_req(self, lowername:str, lowerpath:str, f_errorlog:TextIO)->dict:
        try:
            if (lowername in self.excl_folders) or (lowerpath in self.excl_folders):
                return {'met':False,'reason':'excl_folder'}
        except Exception as e:
            uprint(now_str(), "EXCEPTION, folder_meets_req:", "'" + lowerpath + "' ", e, file=f_errorlog)
            return {'met':False, 'reason':'Exception'}
        return {'met':True,'reason':'met'}

    def file_meets_req(self, lowername:str, lowerpath:str, stat:os.stat_result, f_errorlog:TextIO)->dict:
        try:
            if self.has_filenames and (not lowername in self.incl_files):
                return {'met':False, 'reason':'filename'}
            if self.has_excl_filename:
                if (lowername in self.excl_files) or (lowerpath in self.excl_files):
                    return {'met':False, 'reason':'fn_excl'}

            #stat = entry.stat(follow_symlinks=False)
            stsz = stat.st_size
            if stsz < self.min_bytes:
                if stsz == 0:
                    return {'met':False, 'reason':'empty_file'}
                else:
                    return {'met':False, 'reason':'too_small'}
            if self.has_max_bytes and stsz > self.max_bytes:
                return {'met':False, 'reason':'too_big'}

            part1, ext = os.path.splitext(lowerpath)
            lowerext = ext.lower()
            if self.has_extensions and (not lowerext in self.incl_exts):
                    return {'met':False, 'reason':'extension'}
            if self.has_excl_ext and (lowerext in self.excl_exts):
                return {'met':False, 'reason':'ext_excl'}

        except Exception as e:
            uprint(now_str(), "EXCEPTION, file_meets_req:", "'" + lowerpath + "' ", e, file=f_errorlog)
            return {'met':False, 'reason':'Exception'}
        return {'met':True, 'reason':'met'}

    def dir_meets_criteria(self, dirname:str, filelist:dict, folderlist:dict, f_errorlog:TextIO):
        subdirs = []
        try:
            ls = os.scandir(dirname)
            for entry in ls:
                lowerpath = entry.path.lower()
                lowername = entry.name.lower()
                if entry.is_dir(follow_symlinks=False):
                    if is_junction(entry.path):
                        if 'junction' not in folderlist:
                            folderlist['junction']=[]
                        folderlist['junction'].append(entry.path)
                    else:
                        met_res = self.folder_meets_req(lowername, lowerpath, f_errorlog)
                        reason = met_res['reason']
                        if not reason in folderlist:
                            folderlist[reason]=[]
                        folderlist[reason].append(entry.path)
                        if met_res['met']:
                            subdirs.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    met_res = self.file_meets_req(lowername, lowerpath,
                        entry.stat(follow_symlinks=False), f_errorlog)
                    reason = met_res['reason']
                    if not met_res['reason'] in filelist:
                        filelist[reason]=[]
                    filelist[reason].append(entry.path)
            for subdir in subdirs:
                self.dir_meets_criteria(subdir, filelist, f_errorlog)
        except Exception as e:
            uprint(now_str(), "EXCEPTION, dir_meets_criteria:", "'" + dirname + "' ", e, file=f_errorlog)

