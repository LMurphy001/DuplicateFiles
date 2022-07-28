import argparse
import hashlib
import json
import os
import sys
import locale
from time import time # Using time for detecting elapsed time.
from pathlib import Path # Using Path to read text file 


def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def thousands(value : int) -> str:
    return f'{value:n}'

def timex(end_time, st_time):
    return "{0:0.4f}".format(end_time - st_time)

def read_file_convert_EOL(file_path : str) -> str:
    # replace the first three types of line endings with \n
    CRLF = "\r\n" # b'\r\n'
    LFCR = "\n\r" # b'\n\r'
    CR   = "\r"   # b'\r'
    LF   = "\n"   # b'\n'

    text = Path(file_path).read_text()
    text = text.replace(CRLF, LF)
    text = text.replace(LFCR, LF)
    text = text.replace(CR, LF)
    return text

def file_get_lines(file_path : str) -> list:
    contents = read_file_convert_EOL(file_path)
    return contents.strip().split('\n')  # b'\n')
    
def check_empty_set(s : str, separator : str) -> set:
    if (s.strip() == ''):
        return set()
    else:
        return set( s.lower().split(separator) ) # later comparisons expect file extensions to be lowercase

def use_hashfunc(filename : str, hashfunc, buffersize : int = 4096):
    ''' use_hashfunc() provides ability to hash very large files without adding memory crush for very large file'''
    hsh = hashfunc()
    # 'rb' means read, binary
    try:
        f = open(filename, 'rb')
    except Exception as e:
        uprint(filename, e)
        return 0

    while True:
        try:
            data = f.read(buffersize)
            if not data:
                break
            hsh.update(data)
        except Exception as e:
            uprint(filename, e)
            return 0
    f.close()
    return hsh

def get_options() -> dict:
    options = dict()

    parser = argparse.ArgumentParser(description="Find Duplicate Files in Folders", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('FoldersFile', help='Name of file listing the folder(s) to search for duplicates. Put each foldername on its own line', default="")
    
    parser.add_argument('OutputFile', help="Name of file where this program's output will be written.", default="" )
    
    parser.add_argument('--separator', default='|', help="Separate extensions using the separator. Start each extension with a period (.) Enclose it in quotes if necessary")
    parser.add_argument('--min', help="Ignore files with size less than min bytes.", type=int, default=1 )

    parser.add_argument('--max', help="Ignore files with size greater than max bytes. If max bytes is 0, then the upper limit of bytes is what your computer can handle.", type=int, default=0 )

    parser.add_argument('--excl_ext', help='Exclude files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    parser.add_argument('--incl_ext', help='Include only files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    parser.add_argument('--ExcludeFoldersFile', help="Name of file listing folder(s) to ignore", default="")
    args = parser.parse_args()

    if (args.FoldersFile.strip() == ''):
        exit("Folders file name is required")
    options['FoldersFile'] = args.FoldersFile
    options['folders'] = file_get_lines(args.FoldersFile)

    options['ExcludeFoldersFile'] = args.ExcludeFoldersFile
    options['exclude_folders'] = file_get_lines(args.ExcludeFoldersFile)

    options['excl_ext'] = check_empty_set(args.excl_ext, args.separator)
    options['incl_ext'] = check_empty_set(args.incl_ext, args.separator)
    options['min'] = args.min
    options['max'] = args.max

    return options

def get_filenames(folders : list, exclude_extensions : list, include_extensions : list) -> tuple:
    uprint("\nGETTING FILENAMES...")
    are_exclusions = len(exclude_extensions) > 0
    are_inclusions = len(include_extensions) > 0
    excluded_filenames = list()
    filenames = set()
    grand_tot = 0

    for topdir in folders:
        uprint(topdir + " folder: ", end='')
        tot = 0
        for (root, dirs, files) in os.walk(topdir, topdown=True):
            # Ignore dirs because walk() will traverse them
            for fil in files:
                thisfile = root + '\\' + fil
                skip = False
                tot += 1
                grand_tot += 1
                if are_exclusions or are_inclusions:
                    prefx, ext = os.path.splitext(thisfile)
                    uprint(os.path.basename(thisfile))
                    ext = ext.lower()
                    if (are_exclusions) and (ext in exclude_extensions):
                        uprint("Excluding (excl)", thisfile)
                        skip = True
                    if (not skip) and (are_inclusions) and (ext not in include_extensions):
                        uprint("Excluding (incl)", thisfile)
                        skip = True
                if skip:
                    excluded_filenames.append(thisfile)
                else:
                    filenames.add(thisfile)  # filenames is a set. It will not allow duplicates
        uprint(thousands(tot))
    uprint("Grand total:", thousands(grand_tot))
    uprint('# excluded due to file extension: ' + thousands(len(excluded_filenames)))
    uprint('# files: ' + thousands(len(filenames)) )
    return excluded_filenames, filenames

def get_sizes(filenames : str, min : int, max : int) -> tuple:
    uprint("\nGETTING SIZES...")
    num_too_small = 0
    num_too_big = 0
    num_ok = 0
    total_files = 0
    sizes = dict()
    exclude = list()

    for fn in filenames:
        fsize = os.path.getsize(fn)
        total_files += 1
        if (fsize < min):
            num_too_small += 1
            exclude.append(fn)
        elif (max != 0) and (fsize > max):
            num_too_big += 1
            exclude.append(fn)
        else:
            num_ok += 1
            sizestr = str(fsize)
            if (sizestr not in sizes):
                sizes[sizestr] = []
            sizes[sizestr].append(fn)

    uprint("# of files:", thousands(total_files))
    uprint("# files too small: " + thousands(num_too_small))
    uprint("# files too big: " + thousands(num_too_big) )
    uprint("# too small + too big: " + thousands(num_too_small + num_too_big) )

    uprint("# files ok size: " + thousands(num_ok))
    uprint("# excluded + num ok:" + thousands(num_ok + num_too_big + num_too_small) )

    uprint("\n# of unique sizes: " + thousands(len(sizes)) )
    uprint("Excluding sizes with only 1 file in them...")
    
    ''' The only possible duplicates are the entries in sizes dict which have more than one filename associated with them. If there's only 1 filename, then there's no dup.'''

    singletons = 0
    multi_dict = dict()
    for sizestr, szfilenames in sizes.items():
        if (len(szfilenames) < 2): # If there's only 1 file with this length, it's a singleton
            singletons += 1
            exclude.append(szfilenames[0])
        else:
            multi_dict[sizestr] = szfilenames

    uprint("#Sizes with only 1 file: " + thousands(singletons))
    uprint("#Sizes with    > 1 file: " + thousands(len(multi_dict)) )
    uprint("Check: Total #sizes: " + thousands(singletons + len(multi_dict)))
    return exclude, multi_dict

def compare_files(szfilenames : list, sizestr : str) -> tuple:
    uprint("\nCOMPARE FILES. Size:", thousands(int(sizestr)), "# Files:", thousands(len(szfilenames)) )
    ''' Return a list of lists. Each list holds the file names which were found to be identical'''
    hashes = dict()
    unis = []
    dups = dict()
    errors = []
    for file in szfilenames:
        hash_val = use_hashfunc(file, hashlib.sha1)
        if (hash_val == 0):
            errors.append(file)
            continue
        
        hash_as_hexstr = hash_val.hexdigest()
        if not (hash_as_hexstr in hashes):
            hashes[hash_as_hexstr] = []
        hashes[hash_as_hexstr].append(file)
    # If 2 or more files have the same hash, THEY MIGHT be identical, i.e.
    # They need to be checked byte by byte.
    # If files have different hashes, they are NOT the same file.
    for hash_as_hexstr, files in hashes.items(): # For each hash value
        if len(files) < 2:
            unis.append(files[0])
        else:
            dups[sizestr+'_'+hash_as_hexstr] = files
    return dups, unis, errors

def comp_file_bytes(fn1 : str, fn2 : str) -> bool:
    pass
# If two files have the same hash and the same file size,
# then open the files, buffered, and compare byte by byte to determine
# if they are actually duplicates. 'rb'

class Student:
    def __init__(self, roll_no, name, batch):
        self.roll_no = roll_no
        self.name = name
        self.batch = batch
  
##############################################################################################
if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, '')

    dc = dict()
    dc['min'] = 1
    dc['max'] = 0
    dc['output_file'] = '..\\basic.txt'

    dc['folders'] = ['o:', 'e:', 'c:\\users']
    dc['exclude_folders'] = ['o:\\github\\duplicatefiles\\.git', 'e:\\fakedir']

    dc['files'] = []
    dc['exclude_files'] = ['key','expand']

    dc['extension'] = []
    dc['exclude_ext'] = ['.obj', '.ssh']

    dc['Json-Config-File-Help'] = {
        "min" : "Ignore files with size less than 'min' bytes. Default = 1",
        "max" : "Ignore files with size greater than 'max' bytes. If max bytes is 0, then it is ignored. Default: 0" 
        }


    print(json.dumps(dc,indent=2))
    
    
    #f = open('data.json', 'r', encoding='utf-8')
  
# returns JSON object as 
# a dictionary
    #data = json.load(f)

    exit()
    
    t0 = time()

    opts = get_options()
    t1 = time()
    uprint("Get options, elapsed:", timex(t1,t0))
    uprint()

    excluded = []
    errlist = []

    uprint("OPTIONS:")
    for name, option in opts.items():
        uprint(name+": ", end='')
        if isinstance(option, list):
            uprint(json.dumps(option, indent=2))
        else:
            uprint(option)
    uprint('-' * 70)

    excluded_files, filenames = get_filenames(opts['folders'], opts['excl_ext'], opts['incl_ext'])
    excluded = excluded + excluded_files
    t2 = time()
    uprint("Get filenames, elapsed:", timex(t2,t1))
    uprint()

    excluded_sizes, sizes = get_sizes(filenames, opts['min'], opts['max'])
    excluded = excluded + excluded_sizes
    t3 = time()
    uprint("Get sizes, elapsed:", timex(t3,t2))
    uprint()

    # sizes is a dict. the key is an int, the size. it is unique in the dict. 
    # the value associated with each size is an array. The array is a list of files which have this particular size
    # After we've gotten the file sizes for all files in filenames and placed them into sizes,
    # Any sizes[size] with more than one file is a possible collision
    # To determine duplicates...

    uprint("\nCOMPARING FILES FOR EACH SAME-SIZE FILE-LIST")
    uprint("\nFor each size and list of files with that size:")
    for sizestr, szfilenames in sizes.items():
        dups, unis, errors = compare_files(szfilenames, sizestr)
        errlist = errlist + errors
        excluded = excluded + unis
        # Dups is a dict, unis is a list, errors is a list
        for dkey, dval in dups.items():
            uprint(dkey)
            for v in dval:
                uprint(' ', v)
    t4 = time()
    uprint("Compare files, elapsed:", timex(t4,t3))
    uprint()

    t5 = time()
    uprint("TOTAL TIME:", timex(t5,t0))

    #uprint("Duplicates (Maybe):")
    #uprint(duplicates)

    #uprint("Errors:")
    #uprint(errors)

    uprint("EXCLUDED:")
    uprint(excluded)
#Three ways to get execution time of code:
#method 1: import time, subtract one time.time() from another
#method 2: from datetime import datetime; subtract datetime.now() from starting datetime.now()
#method 3: import timeit. Stuff code into a variable, mycode.
#   and then run timeit.timeit(setup=mysetup, stmt=mycode, number=10000))
