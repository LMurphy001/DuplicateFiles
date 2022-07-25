import argparse
from asyncio import unix_events
import hashlib
#import gc
import json
#from operator import truediv
import os
import locale
import time # Using this for detecting elapsed time.
from pathlib import Path
# Using Path to read text file 

def thousands(value : int) -> str:
    return f'{value:n}'   

def read_file_cvt_EOL(file_path : str) -> str:
    # replace the first three types of line endings with \n
    CRLF = b'\r\n'
    LFCR = b'\n\r'
    CR = b'\r'
    LF = b'\n'

    text = Path(file_path).read_text()
    text = text.replace(CRLF, LF)
    text = text.replace(LFCR, LF)
    text = text.replace(CR, LF)
    return text

def file_get_lines(file_path : str) -> list:
    contents = read_file_cvt_EOL(file_path)
    lines = contents.split(b'\n')

    for l in lines:
        print("'" + l + "'", end=', ')
    print()

    return lines

def check_empty_set(s : str, separator : str) -> set:
    if (s.strip() == ''):
        return set()
    else:
        return set( s.lower().split(separator) ) # later comparisons expect file extensions to be lowercase

def use_hashfunc(filename : str, hashfunc : function) -> hashlib._Hash:
    hsh = hashfunc()
    # 'rb' means read, binary
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buffersize)
            if not data:
                break
            hsh.update(data)
    return hsh

def get_options() -> dict:
    options = dict()

    parser = argparse.ArgumentParser(description="Find Duplicate Files in Folders", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('FoldersFile', help='Name of file listing the folder(s) to search for duplicates. Put each foldername on its own line', default="")
    
    #parser.add_argument('OutputFile', help="Name of file where this program's output will be written.", default="" )
    
    parser.add_argument('--separator', default='|', help="Separate extensions using the separator. Enclose it in quotes if necessary")
    parser.add_argument('--min', help="Ignore files with size less than min bytes.", type=int, default=1 )

    parser.add_argument('--max', help="Ignore files with size greater than max bytes. If max bytes is 0, then the upper limit of bytes is what your computer can handle.", type=int, default=0 )

    parser.add_argument('--excl_ext', help='Exclude files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    parser.add_argument('--incl_ext', help='Include only files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    args = parser.parse_args()

    if (args.FoldersFile.strip() == ''):
        exit("Folders file name is required")
    options['FoldersFile'] = args.FoldersFile
    options.folders = file_get_lines(args.FoldersFile)

    options.excl_ext = check_empty_set(args.excl_ext, args.separator)
    options.incl_ext = check_empty_set(args.incl_ext, args.separator)

    return options

def get_filenames(folders : list, exclude_extensions : list, include_extensions : list) -> tuple:
    num_skipped_ext = 0
    num_files = 0
    are_exclusions = len(exclude_extensions) > 0
    are_inclusions = len(include_extensions) > 0

    excluded_filenames = set()
    filenames = set()
    for topdir in folders:
        print("Folder: '", topdir+"'", end=' ')
        for (root, dirs, files) in os.walk(topdir, topdown=True):
            # Ignore dirs because walk() will traverse them
            for fil in files:
                thisfile = root + '\\' + fil
                skip = False
                num_files += 1
                if are_exclusions or are_inclusions:
                    prefx, ext = os.path.splitext(thisfile)
                    ext = ext.lower()
                    if (are_exclusions) and (ext in exclude_extensions):
                        skip = True
                    if (not skip) and (are_inclusions) and (ext not in include_extensions):
                        skip = True
                if skip:
                    num_skipped_ext += 1
                    excluded_filenames.add(thisfile)
                else:
                    filenames.add(thisfile)  # filenames is a set. It will not allow duplicates
        print(thousands(num_files))
    print()

    print("\n#Total Files:", thousands(num_files), 
        "#skipped due to filename extension:", thousands(num_skipped_ext),
        "Len excluded_filenames:", thousands(len(excluded_filenames)),
        "Len filenames[]:", thousands(len(filenames)) )
    return excluded_filenames, filenames

def get_sizes(filenames : str, min : int, max : int) -> dict:
    num_too_small = 0
    num_too_big = 0
    sizeok = 0
    num_files = 0
    for fn in filenames:
        fsize = os.path.getsize(fn)
        num_files += 1
        if (fsize < min):
            num_too_small += 1
        elif (max != 0) and (fsize > max):
            num_too_big += 1
        else:
            sizeok += 1
            sizestr = str(fsize)
            if (sizestr not in sizes):
                sizes[sizestr] = []
            sizes[sizestr].append(fn)

    print("# of files:", thousands(num_files), 
        "# files too small:", thousands(num_too_small),
        "# files too big:", thousands(num_too_big), 
        '#  too small + too big:', thousands(num_too_small + num_too_big) )
    print("#files ok size:", thousands(sizeok),
        "#files excluded + size ok:", thousands(sizeok + num_too_small + num_too_big) )
    print("\n# of unique sizes:", thousands(len(sizes)), "Excluding sizes with only 1 file in them")
    
    ''' The only possible duplicates are the entries in sizes dict which have more than one filename associated with them. If there's only 1 filename, then there's no dup.'''

    singletons = 0
    multi_dict = dict()
    for sizestr, szfilenames in sizes.items():
        if (len(szfilenames) < 2): # If there's only 1 file with this length, it's a singleton
            singletons += 1
        else:
            multi_dict[sizestr] = szfilenames

    print("#Sizes with only 1 file:", thousands(singletons),
        "#Sizes with > 1 file:", thousands(len(multi_dict)),
        "Total #sizes: ", thousands(singletons + len(multi_dict)))
    return multi_dict

def compare_files(sizestr : str, szfilenames : str) -> list:
    hashes = dict()
    size = int(sizestr)

    print("\nSize:", thousands(size), "#Files:", thousands(len(szfilenames)))
    print("   ", json.dumps(szfilenames, indent=4))
    print("")

    for file in szfilenames:
        hash_val = use_hashfunc(file, hashlib.sha1)
        hash_as_hexstr = hash_val.hexdigest()
        if hash_as_hexstr not in hashes:
            hashes[hash_as_hexstr] = []
        hashes[hash_as_hexstr].append(file)

        print('   ', file, 'Sha1:', hash_as_hexstr)

    # If 2 or more files have the same hash, THEY MIGHT be identical.
    # They need to be checked byte by byte.
    # If files have different hashes, they are NOT the same file.
    for hash_str, files in hashes.items(): # For each hash value
        if len(files) > 0:
                print("   The following files have the same size and sha1 hash. They might/might not be duplicates. THEY MUST BE COMPARED BYTE BY BYTE")
                print("   ",json.dumps(files, indent=4))
            else:
                print("   The following file has same size, but different sha1. Not same file:", files[0])


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, '')
    buffersize = 8192
    opts = get_options()
    print("OPTIONS:")
    print(json.dumps(opts, indent=4))

    excluded_filenames, filenames = get_filenames(opts.folders, opts.excl_ext, opts.incl_ext)
    
    sizes = get_sizes(filenames)
    # sizes is a dict. the key is an int, the size. it is unique in the dict. 
    # the value associated with each size is an array. The array is a list of files which have this particular size
    # After we've gotten the file sizes for all files in filenames and placed them into sizes,
    # Any sizes[size] with more than one file is a possible collision
    # To determine duplicates...

    print("\nFor each size and list of files with that size:")
    for sizestr, szfilenames in sizes.items():
        print(compare_files(szfilenames))

exit()

'''
# Use sha1 and/or CRC because they are relatively fast and don't generate very long hash strings.
'''



import os
import zlib

#buffersize = 65536

#Three ways to get execution time of code:
#method 1: import time, subtract one time.time() from another
#method 2: from datetime import datetime; subtract datetime.now() from starting datetime.now()
#method 3: import timeit. Stuff code into a variable, mycode.
#   and then run timeit.timeit(setup=mysetup, stmt=mycode, number=10000))


# If two files have the same hash and the same file size,
# then open the files, buffered, and compare byte by byte to determine
# if they are actually duplicates.

# open a file with 'rb' mode = read, binary. open(filenae, 'rb', )

buffersize = 9000

def get_zlib_crc32(filename):
    with open(filename, 'rb') as afile:
        buffr = afile.read(buffersize)
        crcvalue = 0
        while len(buffr) > 0:
            crcvalue = zlib.crc32(buffr, crcvalue)
            buffr = afile.read(buffersize)
    return crcvalue

def getfilesize(filename):
    return os.path.getsize(filename)


""" def do_each_file(files):
    for file in files:
        the_val = getfilesize(file)
        print('size: ', f'{the_val:n}'.rjust(11), end="\n")

        the_val = get_zlib_crc32(file)
        print('  crc32: ', hex(the_val), end="\n")

        the_val = use_hashfunc(file, hashlib.md5)
        print("  md5: {0}".format(the_val.hexdigest()), end="\n")

        the_val = use_hashfunc(file, hashlib.sha1)
        print("  sha1: {0}".format(the_val.hexdigest()), end="\n")

        the_val = use_hashfunc(file, hashlib.sha256)
        print("  sha256: {0}".format(the_val.hexdigest()), end="\n")

        print("\n") """

def time_func(files, func):
    starttime = time.time()
    for file in files:
        use_hashfunc(file, func)
    return time.time() - starttime

def do_each_alg(files):
    elapsed = []

    # Do the same algorithm for all files, then do the next algorithm.
    starttime = time.time()
    for fidx in range(len(files)):
        get_zlib_crc32(files[fidx]) # CRC32
    elapsed.append( time.time()-starttime)
    elapsed.append(time_func(files, hashlib.md5))
    elapsed.append(time_func(files, hashlib.sha1))
    elapsed.append(time_func(files, hashlib.sha256))
    
    print("crc32\tmd5\tsha1\tsha256")
    tot = 0
    for e in elapsed:
        print ("{0:0.4f}".format(e), end="\t")
        tot += e
    print()
    for e in elapsed:
        print ("{0:0.2f}".format( (e*100)/tot), "% ", end="\t")
    print()
    print("Tot: {0:0.4f}".format(tot))
    print()


#############################################
starttime = time.time()
do_each_alg(files)
totaltime = time.time() -starttime
print("Total time, by algorithms: {0:0.4f}".format(totaltime))

starttime = time.time()
do_each_file(files)
totaltime = time.time() -starttime
print("Total time, by files: {0:0.4f}".format(totaltime))

'''
for dirName, subdirs, fileList in os.walk(parentFolder):
    for filename in filelist:
        fullname = os.path.join(dirName, filename)
        if os.path.isfile(fullname):
            filehash = hashfile(fullname)
            filesize = os.stat(fullname)[stat.ST_SIZE] """
'''
