# dupFinder.py
import os, sys, stat
import hashlib
import collections

def get_files_in_folder(parentFolder, odict, subdirs):
    for dirName, subdirs, fileList in os.walk(parentFolder):
        for filename in fileList:
            full_name = os.path.join(dirName, filename)
            if os.path.isfile(full_name):
                file_hash = hashfile(full_name)
                file_size = os.stat(full_name)[stat.ST_SIZE]
                if file_size not in odict:
                    odict[file_size] = collections.OrderedDict()
                if file_hash not in odict[file_size]:
                    odict[file_size][file_hash] = [] 
                odict[file_size][file_hash].append(full_name)
            else:
                print('directory:', full_name)
    return odict

 
def hashfile(path, blocksize = 65536):
    afile = open(path, 'rb')
    hasher = hashlib.md5()
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    afile.close()
    return hasher.hexdigest()

 
if __name__ == '__main__':
    if len(sys.argv) > 1:
        subdirs = []
        odict = collections.OrderedDict()
        folders = sys.argv[1:]
        for i in folders:
            if os.path.exists(i):
                get_files_in_folder(i, odict, subdirs)
            else:
                print('%s is not a valid path, please verify' % i)
                sys.exit()

        num_dups = 0
        for size, hashes in odict.items():
            for hsh, files in hashes.items():
                if len(files) > 1: # More than one file with the same size and same hash = duplicated file
                    sorted_list = []
                    for file in files:
                        mt = format( os.path.getmtime(file), 'f' )
                        ct = format( os.path.getctime(file), 'f' )
                        sorted_list.append(mt + '_'+ct + '_@#@_' + file)
                    # sort list of files by modified time then by creation time
                    sorted_list.sort()
                    for i in range(len(sorted_list)):
                        s = sorted_list[i].split('_@#@_')
                        fn = s[1]
                        if 0 == fn.find(".\\"):
                            fn = fn[2:]
                        if num_dups == 0:
                            print("Duplicates:")
                        if i == 0:
                            num_dups += 1
                            print()
                            print(num_dups)
                        print(fn)
    else:
        print('Usage: python findups.py folder1 folder2 folder3')
