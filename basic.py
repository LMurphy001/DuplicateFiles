import argparse
import json
from operator import truediv
import os

def check_empty_set(s, separator):
    if (s.strip() == ''):
        return set()
    else:
        return set( s.lower().split(separator) )

def get_options():
    parser = argparse.ArgumentParser(description="Find Duplicate Files in Folders", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('Folders', help='Folder(s) to search for duplicates. Enclose the whole list in quotes and separate the foldernames using the separator.', default="")
    parser.add_argument('--separator', default='|', help="Separate folders and extensions using the separator. Enclose it in quotes if necessary")
    parser.add_argument('--min', help="Ignore files with size less than min bytes.", type=int, default=1 )

    parser.add_argument('--min', help="Ignore files with size greater than max bytes. If max bytes is 0, then there's no upper limit on file size.", type=int, default=0 )

    parser.add_argument('--excl_ext', help='Exclude files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    parser.add_argument('--incl_ext', help='Include only files with these extensions. Separate the extensions using the separator, and enclose the whole list in quotes', default="")

    args = parser.parse_args()

    if (args.Folders.strip() == ''):
        exit("At least one folder is required")
    args.Folders = args.Folders.split(args.sep)

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

    num_skipped_ext = 0
    for topdir in args.Folders:
        for (root, dirs, files) in os.walk(topdir, topdown=True):
            # Ignore dirs because walk() will traverse them
            for fil in files:
                #file = fil.lower()
                thisfile = root + '\\' + fil
                skip = False
                if are_exclusions or are_inclusions:
                    pref, ext = os.path.splitext(thisfile)
                    ext = ext.lower()
                    #print("file:(" + fil + ") pref:(" + pref + ") ext:(" + ext + ")")
                    if (are_exclusions) and (ext in args.excl_ext):
                        #print('\n***** SKIP: ext ' + ext + " is in", args.excl_ext, "." )
                        skip = True
                    if (not skip) and (are_inclusions) and (ext not in args.incl_ext):
                        #print("\n***** SKIP: ext " + ext + " is NOT in", args.incl_ext, ".")
                        skip = True
                if skip:
                    num_skipped_ext += 1
                    #print("\nFile skipped due to extension: " + thisfile + ' (' + ext + ')')
                else:
                    #print("Adding " + thisfile + " to the set", end=' ')
                    # THIS SCRIPT IS FOR WINDOWS....
                    filenames.add(thisfile)  # filenames is a set. It will not allow duplicates
                    #print(len(filenames), end = ' ')

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
    for fn in filenames:
        fsize = os.path.getsize(fn)
        skip = False
        if (fsize < args.min):
            #print("Too small: " + fn)
            num_too_small += 1
        elif (args.max != 0) and (fsize > args.max):
            #print("Too big: " + fn)
            num_too_big += 1
        else:
            sizeok += 1
            hxsize = hex(fsize)
            if hxsize[:2] == "0x":
                hxsize = hxsize[2:]
            if (hxsize not in sizes):
                sizes[hxsize] = []
            sizes[hxsize].append(fn)

    print("Num too small:", num_too_small, "Num too big:", num_too_big, ", Tot:", num_too_small + num_too_big, "Size ok:", sizeok)

    #print("SIZES:")
    #print(json.dumps(sizes, indent=4))

    ''' The only possible duplicates are the entries in sizes dict which have more than one filename associated with them. If there's only 1 filename, then there's no dup.'''

    singletons = 0
    multis = 0
    totmultis = 0
    for hxsize, szfilenames in sizes.items():
        if (len(szfilenames) < 2):
            singletons += 1
        else:
            multis += 1
            totmultis = totmultis + len(szfilenames)
    print("Singletons:",singletons,". Totmultis:", totmultis, " Multis:", multis)
exit()

# If more than one folder is to be searched:
optional_folders = []

folders = [args.folder] + optional_folders

# Ignore files with size < size_min. Default: size 0 file are ignored
size_min = 1

# If size_max <> 0, then ignore files with size > size_max
# If size_max == 0, then there is no max size for files.
size_max = 0

# If included_extensions is empty, then include all extensions
# If included_extensions is non-empty, then only examine files with extensions in the list
included_extensions = []

# If excluded_extensions is empty, then no files are excluded based on extension
# If excluded_extensions is non-empty, then do not examine file if its filename ends with one of excluded_extensions
excluded_extensions = []



exit()        
#from distutils import filelist
#import os, hashlib, stat

# Use sha1 and/or CRC because they are relatively fast and don't generate very long hash strings.
'''
Given at least 1 folder name and optionally file extensions to include/exclude and optionally file size minimum/maximum

Traverse the folders and get the file size for each file.
If it is between size min & max or if there are no size restrictions
    Put the file's full name onto a list for that file size
    If there is already exactly one file on the list for that file size, calculate the hashes for the existing file and the new file.
    If they are the same hash, add SIZE+HASH to the COLLISION list. Allow the size+hash list to contain multiple filenames.
    If they are different hashes, then the same file size has multiple child lists, one for each hash. 
At the end, examine each collision. Open the files 'rb' and compare contents. If they match, add to the DUPLICATES list
If they don't match, add to the NOT-DUPLICATES list (same size & hash but different contents)

'''

import hashlib

import locale
locale.setlocale(locale.LC_ALL, '') 

import time # Using this for detecting elapsed time.

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

def use_hashfunc(filename, hashfunc):
    hsh = hashfunc()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buffersize)
            if not data:
                break
            hsh.update(data)
    return hsh

def do_each_file(files):
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

        print("\n")

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
