import argparse
import hashlib
#import gc
import json
#from operator import truediv
import os
import locale
import time # Using this for detecting elapsed time.

locale.setlocale(locale.LC_ALL, '') 


buffersize = 8192

def check_empty_set(s, separator):
    if (s.strip() == ''):
        return set()
    else:
        return set( s.lower().split(separator) )

def use_hashfunc(filename, hashfunc):
    hsh = hashfunc()
    # 'rb' means read, binary
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buffersize)
            if not data:
                break
            hsh.update(data)
    return hsh

def get_options():
    parser = argparse.ArgumentParser(description="Find Duplicate Files in Folders", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('Folders', help='Folder(s) to search for duplicates. Enclose the whole list in quotes and separate the foldernames using the separator.', default="")
    parser.add_argument('--separator', default='|', help="Separate folders and extensions using the separator. Enclose it in quotes if necessary")
    parser.add_argument('--min', help="Ignore files with size less than min bytes.", type=int, default=1 )

    parser.add_argument('--max', help="Ignore files with size greater than max bytes. If max bytes is 0, then the upper limit of bytes is what your computer can handle.", type=int, default=0 )

    parser.add_argument('--excl_ext', help='Exclude files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    parser.add_argument('--incl_ext', help='Include only files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    args = parser.parse_args()

    if (args.Folders.strip() == ''):
        exit("At least one folder is required")
    args.Folders = args.Folders.split(args.separator)

    args.excl_ext = check_empty_set(args.excl_ext, args.separator)
    args.incl_ext = check_empty_set(args.incl_ext, args.separator)

    return args

if __name__ == "__main__":
    args = get_options()
    '''options = vars(args) # turn object 'args' into a dict and print with json 
    print("You have specified the following options:")
    print( json.dumps(options, indent=4))
    print("=============================")'''

    filenames = set()
    
    are_exclusions = len(args.excl_ext) > 0
    are_inclusions = len(args.incl_ext) > 0

    print("Folders:", args.Folders)
    num_skipped_ext = 0
    for topdir in args.Folders:
        for (root, dirs, files) in os.walk(topdir, topdown=True):
            # Ignore dirs because walk() will traverse them
            for fil in files:
                thisfile = root + '\\' + fil
                skip = False
                if are_exclusions or are_inclusions:
                    pref, ext = os.path.splitext(thisfile)
                    ext = ext.lower()
                    if (are_exclusions) and (ext in args.excl_ext):
                        skip = True
                    if (not skip) and (are_inclusions) and (ext not in args.incl_ext):
                        skip = True
                if skip:
                    num_skipped_ext += 1
                    print("\nFile skipped; extension: " + thisfile + ' (ends in ' + ext + ')')
                else:
                    filenames.add(thisfile)  # filenames is a set. It will not allow duplicates

    print("Number of files skipped due to filename extension:", num_skipped_ext, "Number of files remaining:", len(filenames))

    sizes=dict()
    # sizes is a dict. the key is an int, the size. it is unique in the dict. 
    # the value associated with each size is an array. The array is a list of files which have this particular size
    # After we've gotten the file sizes for all files in filenames and placed them into sizes,
    # Any sizes[size] with more than one file is a possible collision
    # To determine duplicates...

    #print("Filenames:")
    num_too_small = 0
    num_too_big = 0
    sizeok = 0
    num_files = 0
    for fn in filenames:
        fsize = os.path.getsize(fn)
        num_files += 1
        skip = False
        if (fsize < args.min):
            num_too_small += 1
        elif (args.max != 0) and (fsize > args.max):
            num_too_big += 1
        else:
            sizeok += 1
            hxsize = hex(fsize)
            if hxsize[:2].lower() == "0x":
                hxsize = hxsize[2:]
            if (hxsize not in sizes):
                sizes[hxsize] = []
            sizes[hxsize].append(fn)

    print("# of files:", num_files, "# files too small:", num_too_small, "# files too big:", num_too_big, 
        ", Tot #files excluded due to size:", (num_too_small + num_too_big))
    print("#files with size ok:", sizeok, "#files excluded + size ok:", sizeok + num_too_small + num_too_big) 
    print("# of unique sizes:", len(sizes))
    
    ''' The only possible duplicates are the entries in sizes dict which have more than one filename associated with them. If there's only 1 filename, then there's no dup.'''

    singletons = 0
    check_if_dups = dict()
    multis = 0
    for hxsize, szfilenames in sizes.items():
        if (len(szfilenames) < 2): # If there's only 1 file with this length, it's a singleton
            singletons += 1
        else:
            check_if_dups[hxsize] = szfilenames
            multis += 1 # There are at least 2 files with this file size

    print("#sizes with only 1 file:", singletons, "#sizes with > 1 file:", multis)
    
    del sizes #not needed anymore. use check_if_dups

    #print("check_if_dups:")
    #print(json.dumps(check_if_dups, indent=4))
    #    f'{the_val:n}'.rjust(11)     f'{value:,}' # .rjust(15)  

    print("For each size and list of files with that size:")

    for hxsize, szfilenames in check_if_dups.items():
        hashes = dict()
        size = int(hxsize, 16)
        print("Size:", f'{size:,}', "#Files:", len(szfilenames))
        print("   ", json.dumps(szfilenames, indent=4))
        for file in szfilenames:
            hash_val = use_hashfunc(file, hashlib.sha1)
            if hash_val not in hashes:
                hashes[hash_val] = []
            hashes[hash_val] = file
            print('   ', file, 'Sha1:', hash_val)
        # If 2 or more files have the same hash, THEY MIGHT be identical.
        # They need to be checked byte by byte.
        # If files have different hashes, they are NOT the same file.
        for hash_val, files in hashes.items(): # For each hash value
            if len(files) > 0:
                print("   The following files have the same size and sha1 hash. They might/might not be duplicates. THEY MUST BE COMPARED BYTE BY BYTE")
                print("   ",json.dumps(files), indent=4)
            else:
                print("   The following file has same size, but different sha1. Not same file:", files[0])

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
