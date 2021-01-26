"""
 *  @@@@@@@@@@@@@@   TheYoungWolf Productions   @@@@@@@@@@@@@@
 *
 *  Copyright (C) 2020 File System Simulation
 *
 * Licensed under the Apache License, Version 1.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License from the author
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""
import os
import sys
import math
import llist
from llist import dllist, dllistnode  # Using Double Linked List Library
from threading import Lock, Thread
from socket import *
# from _thread import *
import pickle


# ******************* Global Variables ********************

gl_inputfile = ""
gl_inputdir = ""
gl_disksize = 0
gl_blocksize = 0
gl_totalblock = 0
gl_filecount = 0
gl_dircount = 0
gl_fragmentation = 0
gl_freespace = 0


# ******************** All definitons **********************


# Node definition of Disk Linked List
class nodeDiskLL:
    def __init__(self):
        self.status = "FREE"
        self.begin = 0
        self.end = 0
        # self.next = None


# Disk = nodeDiskLL()
Disk = dllist()


# Node definition of File node in tree
class nodeFile:
    def __init__(self):
        self.filename = ""
        self.fullname = ""
        self.path = ""
        self.fileSize = 0
        self.fileInfoList = None


# Node definition of Directory node in tree
class nodeDir:
    def __init__(self):
        self.parentDir = None
        self.fullname = ""
        self.name = ""
        self.path = ""
        self.dirDLList = None
        self.fileDLList = None


# Creating a root node
root = None


# ************* Main program helper functions ***************
# dirORls(<dir node>) -> Prints out the items in a directory #DONE
# printout(<dir node>) -> Prints meta info about files in a directory #DONE
# chdir(<parentDir node>, <dir name>) -> Change Directory #DONE
# mkdir(<parentDir node>, <dir name>) -> Creates a new directory #DONE
# rmdir(<parentDir node>, <dir name>) -> Removes a directory #DONE
# mkfile(<parentDir node>, <file name>, <file size>) -> Creates a new file #DONE
# rmfile(<parentDir node>, <file name>) -> Removes a file #DONE
# remove(<parentDir node>, <file name>, <file size>) -> Remove bytes from file #DONE
# append(<parentDir node>, <file name>, <file size>) -> Append bytes to a file #DONE


# Prints out the items in a directory
def dirORls(node):
    # print('in dirORls')
    reply = ""
    for i in range(node.dirDLList.size):
        reply += node.dirDLList[i].name + "\n"
    for j in range(node.fileDLList.size):
        reply += node.fileDLList[j].filename + "\n"
    return reply


# Print meta info about files in a directory
def printout(node):
    reply = ''
    l = node.fileDLList
    for each in range(len(l)):
        currentChild = l[each]
        reply += ("-------------------------------------------------------------\n")
        reply += ("1. File name: " + currentChild.filename + '\n')
        reply += ("2. Full name: " + currentChild.fullname + '\n')
        reply += ("3. File path: " + currentChild.path+"/\n")
        reply += ("4. File size: " + str(currentChild.fileSize)+" bytes\n")
        reply += printFileLL(currentChild.fileInfoList, currentChild.fileSize)
        reply += ("-------------------------------------------------------------\n")
    return reply


# Change directory
def chdir(dir, name):
    l = dir.dirDLList
    if(l.first != None):
        for i in range(len(l)):
            currentChild = l[i]
            if(currentChild.name in name):
                return currentChild
        return None
    return None


# Creates a new directory if it doesn't exist.
def mkdir(node, name):
    global gl_dircount
    new = nodeDir()
    # Concat final full name of directory
    fullname = node.fullname + name
    # Creates a new directory if and only if it doesnt already exist
    if (node.fullname != fullname):
        new = initDir(node, fullname)
        node.dirDLList.append(new)
        gl_dircount += 1
    file = open(gl_inputdir, "a")
    file.write(fullname+"\n")
    file.flush()
    file.close()


# Removes a directory
def rmdir(node, name):
    reply = ''
    i = 0
    # if there is no directory to remove
    if node.dirDLList == None:
        return reply
    # Child directories
    dirList = node.dirDLList
    # Traverse over child directories to find directory to delete.
    for i in range(node.dirDLList.size):
        cd = dirList[i]
        if cd.name == name:
            # Inorder to remove a directory, it cannot have subdirectories
            if (cd.dirDLList.first != None):
                reply += ("Failed to remove directory because it has subdirectories!\n")
                return reply
            else:
                dirList.remove(dirList.nodeat(i))
                # Update the dir_list.txt file
                fullname = cd.fullname
                # print(fullname+str(len(fullname)))
                file = open(gl_inputdir, "r")
                lines = file.readlines()
                file.close()
                file2 = open(gl_inputdir, "w")
                for line in lines:
                    if str(line.strip("\n")+"/") != fullname:
                        # print(line.strip("\n") + " " + fullname)
                        file2.write(line)
                        file2.flush()
                file2.close()
                return reply


# Creates a file
def mkfile(node, name, size):
    reply = ''
    global gl_filecount
    if(size > gl_freespace):
        reply += ("Not enough freespace, current freespace: " +
                  str(gl_freespace)+" bytes\n")
        return reply
    fullname = ""
    f = nodeFile()
    f.fileSize = size
    # Concat into final fullname
    fullname += node.fullname
    fullname += name
    # Assign to node variables.
    f.fullname = fullname
    f.filename = name
    f.path = node.path
    # Create a linked list for this file
    f.fileInfoList = dllist()
    createFileLL(f, f.fileSize)
    # The parent node should have this file in its files DLL
    node.fileDLList.append(f)
    gl_filecount += 1
    onFileAdd(size)
    # Write new file to file_list.txt
    file = open(gl_inputfile, "a")
    file.write(str(size)+" "+fullname+"\n")
    file.close()
    return reply


# Removes a file
def rmfile(node, name):
    reply = ''
    global gl_freespace, gl_fragmentation
    # First check whether this node(dir) has any files in it
    # If not, return
    if(node.fileDLList == None):
        reply += ("No such file in this directory\n")
        return reply
    # We traverse the list and find the file node to be deleted from DLL.
    for i in range(node.fileDLList.size):
        currentChild = node.fileDLList[i]
        # Once found, free up disk space, reduce fragmentation
        # Free up that files own Linked List
        # Lastly remove the file from the node(dir) DLL of all files
        if(currentChild.filename == name):
            fullname = currentChild.fullname
            onFileRemove(currentChild.fileSize)
            # gl_freespace += currentChild.fileSize
            # gl_fragmentation -= countFragmentation(currentChild.fileSize)
            freeFileLL(currentChild.fileInfoList)
            node.fileDLList.remove(node.fileDLList.nodeat(i))
            # Update the file_list.txt file.
            file = open(gl_inputfile, "r")
            lines = file.readlines()
            file.close()
            file2 = open(gl_inputfile, "w")
            for line in lines:
                each = line.split()
                if each[1].strip("\n") != fullname:
                    file2.write(line)
                    file2.flush()
            file2.close()
            return reply


# Remove file data aka reduce file size
def remove(node, name, size):
    reply = ''
    global gl_blocksize
    x = 0
    # No files in the directory
    if node.fileDLList.first == None:
        return
    if size <= 0:
        return reply
    # Access nodes Files DLL
    filelist = node.fileDLList
    # Iterate over every file
    for i in range(node.fileDLList.size):
        cf = filelist[i]
        if cf.filename == name:
            onFileRemove(cf.fileSize)
            x = cf.fileSize - size
            if(x < 0):
                reply += ("Cannot remove more bytes than total file size\n")
                return reply
            cf.fileSize = x
            f = open(gl_inputfile, "r")
            lines = f.readlines()
            f.close()
            f2 = open(gl_inputfile, "w")
            for line in lines:
                each = line.split()
                if(each[1].strip("\n") != cf.fullname):
                    f2.write(line)
                else:
                    f2.write(str(x)+" "+each[1]+"\n")
                    f2.flush()
                    # filesize = cf.fileSize
            f2.close()
            onFileAdd(cf.fileSize)
            if (x == 0):
                freeFileLL(cf.fileInfoList)
                cf.fileInfoList = None
                cf.fileSize = 0
                return reply
            else:
                freeFileLL(cf.fileInfoList)
                cf.fileInfoList = None
                createFileLL(cf, x)
            # if x < gl_blocksize:
            #     return
            # while x > gl_blocksize:
            #     x -= gl_blocksize
            #     if(temp == None):
            #         temp = cf.fileInfoList
            #     temp = temp.next
            # freeFileLL(temp.next)
            # temp.next = None
            return reply


# Add file data aka increase file size
def append(root, name, size):
    reply = ''
    global gl_blocksize, gl_freespace
    new = 0
    # No files in the directory
    if(size > gl_freespace):
        reply += ("Not enough freespace\n")
        return reply
    if root.fileDLList.first == None:
        return reply
    if size <= 0:
        return reply
    # Access nodes files DLL
    filelist = root.fileDLList
    # Iterate over every file
    for i in range(root.fileDLList.size):
        cf = filelist[i]
        if cf.filename == name:
            onFileRemove(cf.fileSize)
            cf.fileSize = cf.fileSize + size
            new = cf.fileSize
            f = open(gl_inputfile, "r")
            lines = f.readlines()
            f.close()
            f2 = open(gl_inputfile, "w")
            for line in lines:
                each = line.split()
                if(each[1].strip("\n") != cf.fullname):
                    f2.write(line)
                else:
                    f2.write(str(new)+" "+each[1]+"\n")
                    # filesize = cf.fileSize
            f2.flush()
            f2.close()
            onFileAdd(new)
            if cf.fileInfoList == None:
                createFileLL(cf, new)
                return reply
            else:
                freeFileLL(cf.fileInfoList)
                cf.fileInfoList = None
                createFileLL(cf, new)
            # while new > gl_blocksize:
            #     new -= gl_blocksize
            #     if cf.fileInfoList.next == None:
            #         cf.fileInfoList = cf.fileInfoList.next
            #     else:
            #         cf.fileInfoList.next = createFileLL(new)
            return reply


# ********************** Input checks **********************
# inputCheck(<No. of args>, <args list>) -> Checks Input arguments #DONE
# inputError(arg) -> Displays Appropriate error #DONE (NOT USED THO)
# paramCheck(str, i) -> Helper function to inputCheck #DONE
# inputFiles() -> Prints the names of input files we'll run our script on #DONE
# readFile(argc) -> Opens the readme file #DONE (NOT USED THO)


# Check if there are 4 args. If yes, then checks their correctness
# If not, it displays the relavent error
def inputCheck(argc, argv):
    r = 1
    if(argc < 4):
        if(argv[1] != "?" or argv[1] != "help"):
            r = inputError(0)
        else:
            r = inputError(4-argc)
    elif(argc > 4):
        r = inputError(argc)
    else:
        for i in range(1, 4):
            r = paramCheck(argv[i], i)
            if(r != 1):
                return r
    return r


# Used to display various messages depending upon user entry
def inputError(arg):
    if(arg == 0):
        print("Please read the README.txt")
    elif(arg < 4):
        print("Some parameters missing\nSeek help using command ./FileSystem ? or ./FileSystem help")
    else:
        print("Too many arguments passed\nSeek help using command ./FileSystem ? or ./FileSystem help")
    return 0


# Check Parameters
def paramCheck(str, i):
    r = 1
    size = 0
    # Ignore the zeroth parameter
    # CASE 1: Validating the first parameter
    if(i == 1):
        size = len(str)
        if(size > 20):
            print("First parameter out of boundary")
            r = 0
        else:
            for k in range(size):
                if(str[k] == "."):
                    print("First parameter wrong form")
                    r = 0
            if(r == 1):
                global gl_inputfile
                gl_inputfile += "file_"+str+".txt"
                global gl_inputdir
                gl_inputdir += "dir_"+str+".txt"
    # CASE 2: Validating the second parameter
    elif(i == 2):
        val = eval(str)
        k = 1
        for j in range(31):
            if(val == k):
                global gl_disksize
                gl_disksize = val
                return r
            k *= 2
        print("Second parameter is invalid")
        r = 0
    # CASE 3: Validating the third parameter
    elif(i == 3):
        val = eval(str)
        k = 1
        for j in range(11):
            if(val == k):
                global gl_blocksize
                gl_blocksize = val
                return r
            k *= 2
        print("Third parameter is invalid")
        r = 0
    return r


# Display Input files
def inputFiles():
    print("Input file is "+gl_inputfile)
    print("Input directory is "+gl_inputdir)


# Prints the helper document on terminal
def readFile(argc):
    f = open(argc, "r")
    if(f == None):
        print("Cannot open help document")
        exit(1)
    print(f.read())

# ************************** Tree ***************************
# initDir(<parent Dir>, <dir name>) -> Initializes a directory node #DONE
# initFile(<file name>, <file size>) -> Initializes a file node #DONE
# findDir(<parent Dir>, <dir name>) -> Searches for a directory #DONE
# createTree() -> Runs the next two functions (Modularity :P) #DONE
# initDirDLL() -> Initializes Child dir list of every directory node #DONE
# initFileDLL() -> Initializes Child files list of every directory node #DONE
# printTree(<dir node>, <tab for spaces>) -> Prints tree to visualize #DONE


# Initializes a directory node
def initDir(parent, name):
    dir = nodeDir()
    dir.parentDir = parent
    # Put absolute path given by name parameter into fullname variable
    dir.fullname = name
    # print(dir.fullname[2] == "\n")
    # Put / symbol after the fullname except on root directory
    if(parent != None):
        dir.fullname += "/"
    dir.dirDLList = dllist()
    dir.fileDLList = dllist()
    # rfind finds the last occuring / and reutrns its index
    i = name.rfind("/")
    if(i != -1):
        # Put everything before the last / in path variable
        for j in range(i):
            dir.path += name[j]
        # Put everything after the last / in name variable
        for k in range(i+1, len(name)):
            dir.name += name[k]
    return dir


# Initializes a file node
def initFile(name, size=0):
    global gl_freespace
    if (size > gl_freespace):
        print("Not enough memory space!\n")
        return
    newFile = nodeFile()
    newFile.fullname = name
    # newFile.fullname[len(newFile.filename)] = "\0"
    i = name.rfind("/")
    if(i != -1):
        # Put everything before the last / in path variable
        for j in range(i):
            newFile.path += name[j]
        # Put everything after the last / in filename variable
        for k in range(i+1, len(name)):
            newFile.filename += name[k]
    newFile.fileSize = size
    createFileLL(newFile, size)
    return newFile


# Finds the directory of path given as 2nd argument
def findDir(dir, name):
    if(dir.fullname in name):
        if(dir.dirDLList.size == 0):
            return dir
        else:
            i = 0
            childList = dir.dirDLList
            currentChild = childList[i]
            while(currentChild.fullname not in name and i < childList.size):
                currentChild = childList[i]
                i += 1
            if(currentChild.fullname in name):
                return findDir(currentChild, name)
            else:
                return dir
    return None


# Create a tree structure
def createTree():
    initDirDLL()
    initFileDLL()


# Yet to comment
def initDirDLL():
    global root, gl_dircount
    file = open(gl_inputdir, "r")
    file.flush()
    if(file == None):
        print("Cannot open dir_file")
        exit(1)
    temp = file.read().splitlines()
    for each in temp:
        if(root == None):
            root = initDir(root, each)
            gl_dircount += 1
        else:
            current = findDir(root, each)
            if(current.fullname != each):
                new = initDir(current, each)
                current.dirDLList.append(new)
                gl_dircount += 1
    file.flush()
    file.close()


def initFileDLL():
    global gl_filecount, root
    # Input file has entries as follows
    # (size) (name)
    # 2048 ./1A/2B/meema.txt
    f = open(gl_inputfile, "r")
    f.flush()
    if(f == None):
        print("Cannot open dir_file")
        exit(1)
    # For each line in in inputfile
    temp = f.read().splitlines()
    for each in temp:
        # Ex/ [int fSize, string fName]
        arraySplit = each.split()
        # initFile function instantiates a nodeFile instance
        new = initFile(arraySplit[1], eval(arraySplit[0]))
        # Re-calculating total space
        onFileAdd(new.fileSize)
        if(root == None):
            print("Can't find the root folder")
        else:
            current = root
            current = findDir(current, new.fullname)
            current.fileDLList.append(new)
            gl_filecount += 1
    f.flush()
    f.close()


# Print Tree recursively
def printTree(node, tab):
    reply = ''
    # Do nothing if current node is None
    if(node == None):
        return reply
    # Create whitespace for display purpose
    for i in range(tab):
        reply += (".....")
    # Print node name infront of the whitespace
    reply += (node.name + '\n')
    # Return if the current node has no more child directories
    if(node.dirDLList == None):
        return reply
    dirChild = node.dirDLList
    # Recursively go into directory depth
    for j in range(node.dirDLList.size):
        reply += printTree(dirChild[j], tab+1)
    # Return if a directory has no files in it
    if(node.fileDLList == None):
        return reply
    fileChild = node.fileDLList
    # Print all files in the directory
    for k in range(node.fileDLList.size):
        for l in range(tab):
            reply += (".....")
        reply += (fileChild[k].filename + '\n')
    return reply


# ******************** File Linked List *********************
# createFileLL(<file node>, <file size>) -> Returns a file storage info list
# printFileLL(<File info list>, <file size>) -> Prints the file storage info
# freeFileLL(<File info list>) -> Clears file info list and occupied space in disk
# countFragmentation(<File size>) -> Returns the leftover space in block
# onFileAdd(<file size>) -> Recalculates global freespace and global fragmentation
# onFileRemove(<file size>) -> Recalculates global freespace and global fragmentation


# Returns LL specifying all memory locations of file blocks.
def createFileLL(node, fSize):
    global gl_blocksize
    node.fileInfoList = dllist()
    # t_file = nodeFileLL()
    # current = nodeFileLL()
    blocks = 1
    i = 0
    if fSize > 0:
        # Obtain number of blocks needed to store file info.
        blocks = math.floor(fSize/gl_blocksize)
        # Add extra block if file needs more room
        if fSize != (blocks * gl_blocksize):
            blocks += 1
    else:
        return
    for i in range(blocks):
        # find offset of every block according to disk.
        # new = nodeFileLL()
        pma = requestDiskSpace() * gl_blocksize
        node.fileInfoList.append(pma)
    # for i in range(blocks):
    #     # find offset of every block according to disk.
    #     new.pma = requestDiskSpace() * gl_blocksize
    #     new.next = None
    #     if i == 0:  # First node in LL.
    #         t_file = new
    #         current = new
    #     else:  # All subsequent nodes
    #         current.next = new
    #         current = current.next
    # return t_file


# Visits every node and prints its PMA value
# along with the size every node is taking in memory
def printFileLL(LL, fSize):
    reply = ''
    i = 1
    reply += ("\nFile stored in " + str(LL.size)+" piece(s):\n\n")
    for value in LL:
        reply += ("\t"+str(i)+". Memory location: " + str(value) + '- ')
        i += 1
        if fSize > gl_blocksize:
            reply += ("Used memory: " + str(gl_blocksize) +
                      "/"+str(gl_blocksize)+" bytes\n")
            # Decrease size every iteration by block size.
            fSize -= gl_blocksize
        else:
            # Print the value of used size within a block.
            reply += ("Used memory: " + str(fSize) +
                      "/"+str(gl_blocksize)+" bytes\n")
    return reply
    # break
    # while(LL != None):
    #     print("\t"+str(i)+". Memory location: " + str(LL.pma), end=" - ")
    #     i += 1
    #     if fSize > gl_blocksize:
    #         print("Used memory: " + str(gl_blocksize) +
    #               "/"+str(gl_blocksize)+" bytes")
    #         # Decrease size every iteration by block size.
    #         fSize -= gl_blocksize
    #     else:
    #         # Print the value of used size within a block.
    #         print("Used memory: " + str(fSize)+"/"+str(gl_blocksize)+" bytes")
    #         break
    #     LL = LL.next


# Frees up used blocks in disk
def freeFileLL(LL):
    global gl_blocksize
    if(LL == None or len(LL) == 0):
        return
    for value in LL:
        freeOccupiedDiskSpace(value/gl_blocksize)
    # while(LL != None):
    #     freeOccupiedDiskSpace(LL.pma/gl_blocksize)
    #     LL = LL.next


# Returns the leftover space in last block
def countFragmentation(fSize):
    global gl_blocksize
    i = fSize
    if(i == 0):
        return 0
    while(i > gl_blocksize):
        i -= gl_blocksize
    return gl_blocksize - i


# Recalculates global freespace and global fragmentation
def onFileAdd(fSize):
    global gl_freespace, gl_fragmentation
    gl_freespace -= fSize
    gl_fragmentation += countFragmentation(fSize)


# Recalculates global freespace and global fragmentation
def onFileRemove(fSize):
    global gl_freespace, gl_fragmentation, gl_blocksize
    gl_freespace += fSize
    gl_fragmentation -= countFragmentation(fSize)


# ******************** Disk Linked List *********************
# initDisk() -> Initializes Disk using arguments given when running script
# printDisk() -> Prints the status of Disk
# requestDiskSpace() -> Finds free block and returns its block number
# updateDisk() -> Ensures we have at most 2 nodes in Disk Linked List
# freeOccupiedDiskSpace(<starting address>) -> Frees used space

def initDisk():
    global gl_freespace, gl_fragmentation, gl_totalblock, gl_disksize, Disk
    # Find the number of blocks in disk
    gl_totalblock = gl_disksize/gl_blocksize
    node = nodeDiskLL()
    # Disk is empty aka free
    node.status = "FREE"
    node.begin = 0
    # Disk blocks 0 to max-1 are all free
    node.end = gl_totalblock - 1
    # Only one node
    Disk.append(node)
    gl_fragmentation = 0
    # All space is free
    gl_freespace = gl_totalblock*gl_blocksize


def printDisk():
    global Disk
    reply = ''
    # Traverse through Disk and print block number that are used and free
    # Note: There will only be 2 nodes to traverse because remember, we ensure
    # that using the updateDisk function
    for i in range(len(Disk)):
        if(Disk[i].status == "FREE"):
            reply += "Free blocks from " + \
                str(Disk[i].begin) + " to " + str(Disk[i].end) + '\n'
        else:
            reply += "Used blocks from " + \
                str(Disk[i].end) + " to " + str(Disk[i].begin) + '\n'
    reply += "Fragmentation: " + str(gl_fragmentation) + " bytes" + '\n'
    reply += "Free Disk Space: " + str(gl_freespace) + " bytes" + '\n'
    return reply


# Returns the block number of the first vacant block found.
def requestDiskSpace():
    global Disk
    temp = nodeDiskLL()
    current = Disk
    i = 0
    # Iterate till an empty space is found
    for i in range(current.size):
        # FREE space found
        # If more than one contigious block is free
        # Isolate the first free block and return its block number
        if(current[i].status == "FREE"):
            if(current[i].begin != current[i].end):
                temp.status = "USED"
                temp.begin = current[i].begin
                temp.end = current[i].begin
                current[i].begin += 1
                current.appendleft(temp)
            else:  # Only single block is free, use it.
                current[i].status = "USED"
    # 2 nodes at all times
    updateDisk()
    return temp.begin


# Updates disk such that we have only 2 nodes(with status USED and FREE)
def updateDisk():
    global Disk
    # Run Disksize - 1 to prevent index out of bounds
    for i in range(Disk.size - 1):
        nextChildBlock = Disk[i+1]
        childBlock = Disk[i]
        # If both statuses same, merge the blocks together
        if(childBlock.status == nextChildBlock.status):
            childBlock.end = nextChildBlock.end
            Disk.remove(Disk.nodeat(i+1))
            updateDisk()
            # Important to break, or else it will
            # go out of bound on its way back from recursion
            break


# Frees up the used blocks depending on starting address
def freeOccupiedDiskSpace(start):
    global Disk
    current = Disk
    # Create a free block node
    new = nodeDiskLL()
    new.status = "FREE"
    new.begin = start
    new.end = start
    for i in range(Disk.size):
        # If current node is before or after start address
        if(current[i].begin <= start and current[i].end >= start):
            # Begin address matches start address
            if(current[i].begin == start):
                current.insert(new, current[i])
                current[i].begin += 1
                updateDisk()
                break
            # End address matches start address
            elif(current[i].end == start):
                current[i].end -= 1
                current.insert(new, current[i+1])
                updateDisk()
                break
            else:  # start address is somewhere in between begin and end
                temp = nodeDiskLL()
                temp.status = "USED"
                temp.begin = current[i].begin
                temp.end = start - 1
                current.insert(temp, current[i])
                current.insert(new, current[i])
                current.begin = start + 1
                updateDisk()
                break


def main(argc, argv):
    # If terminal command not found, return Error.
    if (os.getcwd() == None):
        print("Virtual Memory Exhausted!")
        exit(1)
    n = 0

    # Check input arguments to ensure it conforms.
    x = inputCheck(argc, argv)
    if (x == 0):
        exit(1)

    # Create server socket at 127.0.0.1 and port 95.
    ServerSideSocket = socket(AF_INET, SOCK_STREAM)
    ServerSideSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    host = '127.0.0.1'
    # host = '192.356.31.3'
    port = 21018

    # This is the ID to uniquely identify a client.
    ThreadCount = 0

    # Instantiate Lock
    mutex = Lock()

    # An array to store input thread
    threadsArr = []
    # An array to simply keep track of active threads
    runningThreads = []
    # A DYNAMIC* array holding all data of connected users.
    # Dynamic: Everytime a user connects or disconnects, array auto resizes.
    users = []

    # Instantiate the file system on server.
    inputFiles()
    initDisk()
    createTree()
    #
    print("\n-------- FileSystem status --------")
    print(printDisk())
    print("-----------------------------------\n")

    # Bind server and start listening to incoming connections.
    try:
        ServerSideSocket.bind((host, port))
    except socket.error as e:
        print('Here ' + str(e))
    print('Socket is listening..\n')
    ServerSideSocket.listen(5)

    # This function is not used because we don't want to wait
    # for every other thread to complete before exiting from one thread.
    # It is still mentioned so it can directly be used in future (if needed)
    def joinThreads():
        # Join threads
        for i in range(len(threadsArr)):
            print(i)
            threadsArr[i].join()

    # This function is responsible for accessing the filesystem
    # Mutex is acquired before every "core" function
    # in order to maintain mutual exclusion for thread synchronization.
    # The current directory and filesystem response is returned
    def run(str, current):
        vect = str.split()
        # if (vect[0] == "exit"):
        #     exit()
        if ((vect[0] == "dir") or (vect[0] == "ls")):
            mutex.acquire()
            reply = dirORls(current)
            mutex.release()
            return current, reply
        elif (vect[0] == "printdisk"):
            mutex.acquire()
            reply = printDisk()
            mutex.release()
            return current, reply
        elif (vect[0] == "cd"):
            reply = ''
            if (vect[1] == ".."):
                mutex.acquire()
                current = current.parentDir
                mutex.release()
                return current, reply
            else:
                mutex.acquire()
                temp = chdir(current, vect[1])
                if (temp != None):
                    current = temp
                else:
                    reply += (vect[1]+": No such file or directory\n")
                mutex.release()
                return current, reply
        elif (vect[0] == "printfiles"):
            reply = ''
            mutex.acquire()
            reply = printout(current)
            mutex.release()
            return current, reply
        elif (vect[0] == "printtree"):
            reply = ''
            mutex.acquire()
            reply += printTree(current, 0)
            mutex.release()
            return current, reply
        elif (vect[0] == "mkdir"):
            reply = ''
            mutex.acquire()
            if (len(vect) != 2):
                reply += ("Wrong input, use 'mkdir <directory name>'\n")
            mkdir(current, vect[1])
            mutex.release()
            return current, reply
        elif (vect[0] == "rmdir"):
            reply = ''
            mutex.acquire()
            if (len(vect) != 2):
                reply += ("Wrong input, use 'rmdir <directory name>'\n")
            reply += rmdir(current, vect[1])
            mutex.release()
            return current, reply
        elif (vect[0] == "create"):
            reply = ''
            mutex.acquire()
            if (len(vect) != 3):
                reply += ("Wrong input, use 'create <file name> <file size>'\n")
            reply += mkfile(current, vect[1], eval(vect[2]))
            mutex.release()
            return current, reply
        elif (vect[0] == "removefile"):
            reply = ''
            mutex.acquire()
            if (len(vect) != 2):
                reply += ("Wrong input, use 'removefile <file name>'\n")
            reply += rmfile(current, vect[1])
            mutex.release()
            return current, reply
        elif (vect[0] == "removebytes"):
            reply = ''
            mutex.acquire()
            if (len(vect) != 3):
                reply += ("Wrong input, use 'removebytes <file name> <No. of bytes>'\n")
            reply += remove(current, vect[1], eval(vect[2]))
            mutex.release()
            return current, reply
        elif (vect[0] == "appendbytes"):
            reply = ''
            mutex.acquire()
            if (len(vect) != 3):
                reply += ("Wrong input, use 'appendbytes <file name> <No. of bytes>'\n")
            reply += append(current, vect[1], eval(vect[2]))
            mutex.release()
            return current, reply
        else:
            reply = ''
            reply += (vect[0]+": No such command, try again.\n")
            return current, reply

    # This is the function run by each thread individually.
    def multi_threaded_client(connection, tNum, user):
        try:
            # Every thread starts at root directory
            current = root
            # Loop unitl client keeps requesting filesystem access
            while True:
                # Client request received and decoded
                data = connection.recv(2048)
                clientReq = data.decode('utf-8')
                # This if block is run either when client wants to exit
                # or when client has exhausted its access limit(=5).
                # Note: No access cost on wrong commands or exit command.
                # So if a client sends a wrong/misspelled command, they
                # will not lose an access count.
                if ((not data) or clientReq == 'exit' or user['accessCount'] > 4):
                    if(clientReq == 'exit' or user['accessCount'] > 4):
                        if(user['accessCount'] > 4):
                            print('EXCEEDED MAX ACCESS ALLOWANCE BY ' +
                                  user['username'])
                            # Server initiating close, so it informs client.
                            responseArray = ['exit', current.fullname]
                            data_string = pickle.dumps(responseArray)
                            connection.sendall(data_string)
                        runningThreads[tNum] = False
                        # Important to acquire mutex when removing a user from
                        # global users array. We don't want multiple users to
                        # leave users array at the same time as it may result in
                        # nasty index out of bound errors.
                        mutex.acquire()
                        for i in range(len(users)):
                            if(users[i]['threadNum'] == tNum):
                                print(
                                    'User ' + users[i]['username'] + ' with Thread number ' + str(tNum) + ' exiting.\n')
                                users.pop(i)
                                break
                        mutex.release()
                        # If no guests to entertain, server shuts down
                        # until manually restarted.
                        if not any(runningThreads):
                            print(
                                'Shutting down server as no more clients to entertain. Thank you.\n')
                            # joinThreads()
                            os._exit(0)
                    break
                # User request is run on filesystem and the response
                # bundled with users' current directory is sent back to the client.
                current, response = run(clientReq, current)
                if (not (response.endswith('try again.\n'))):
                    user['accessCount'] = user['accessCount'] + 1
                responseArray = [response, current.fullname]
                data_string = pickle.dumps(responseArray)
                connection.sendall(data_string)
            connection.close()
        except (Exception, Exception) as e:
            raise Exception('Raising from multithreaded')

    # A loop run by master thread awaiting client connections
    while True:
        try:
            # Letting client know server is up and initiating connection
            # when client sends its username.
            Client, address = ServerSideSocket.accept()
            Client.send(str.encode('Server is working:'))
            data = Client.recv(2048)
            username = data.decode('utf-8')
            # Log which new user connected with its meta data
            print('Connected to: ' + address[0] + ':' +
                  str(address[1]) + ' with username ' + username)
            print('Thread Number: ' + str(ThreadCount) + '\n')
            # Dict to store new user meta data and make it a part of
            # global allUsers array
            newUser = {
                'username': username,
                'ipAddress': address[0],
                'portNumber': address[1],
                'accessCount': 0,
                'threadNum': ThreadCount
            }
            users.append(newUser)
            # Thread appended to allThreads array.
            # Every threads target is function they run individually
            # Parameters passed are client conn, thread number of cient and
            # CURRENT index of client in users array(IMP because index is
            # subject to change every time a client exits)
            threadsArr.append(Thread(
                target=multi_threaded_client, args=(Client, ThreadCount, users[users.index(newUser)])))
            runningThreads.append(True)
            # Thread starts right away.
            threadsArr[ThreadCount].start()
            # Global thread count incremented
            ThreadCount += 1
        except (Exception, Exception) as e:
            # exit()
            print('Exception in while')
            print(e)
            break
    ServerSideSocket.close()
    return 0


# Driver code
if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
