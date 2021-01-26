# Simulation of File System!

This repo is a simulation of File System in Python Language

TO RUN SCRIPTS:

1) Open Linux Terminal
2) cd into the filesystem directory
3) use 'pip3 install llist' to install llist module(need to be done only once)
4) run SERVER using, python3 filesystemwolf.py list 65536 32
 	<python3> <serverProgramName.py> <listName> <Disk Size> <Sector/Block Size>
5) In another terminal, run CLIENT using python3 fileSysClient.py
	<python3> <serverProgramName.py>
	Note: You can run multiple clients

Commands:

1) dir or ls - Displays all contents of current directory
2) printdisk - Prints storage status
3) cd .. - To move back a direcotry
4) cd <directory name> - Move forward into a directory
5) printfiles - Displays info on all files in current directory(also shows their memory mapping details)
6) mkdir <directory name> - Creates a new directory and updates the filesystem
7) rmdir <directory name> - Removes a directory and updates the filesystem
8) create <file name> <file size>- Creates a new file of given size and updates the filesystem
9) removefile <file name> - Removes the file from the directory and updates the filesystem
10) appendbytes <file_name> <No. of bytes> - Appends the given bytes to the given file
11) removebytes <file_name> <No. of bytes> - Removes the given bytes from a file.
12) printtree - Prints the structure of filesystem
13) exit - To quit the program