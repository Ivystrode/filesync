# SERVER SIDE

import socket
from tqdm import tqdm
import tarfile
import os
from datetime import datetime
import shutil

# device's ip address
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001

#receive 4096 bytes each time
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

# create the server socket
# TCP socket
s = socket.socket()

# bind the socket to our local address
s.bind((SERVER_HOST, SERVER_PORT))

# set the primary backup directory
# backup_dir = os.getcwd()
# backup_dir = backup_dir + "\\"
# print(f"BACKUP DIR IS {backup_dir}")

# decompress the received archive
def decompress(tar_file, path, members=None):
    """Extracts tar file and puts the members to path. If members is none all
    members will be extracted"""
    tar = tarfile.open(tar_file, mode="r:gz")
    if members is None:
        members = tar.getmembers()
    
    progress = tqdm(members)
    for member in progress:
        tar.extract(member, path=path)
        progress.set_description(f"Extracting{member}")
        # or use tar.extractall(members=members, path=path)
    
    #close the file
    tar.close()

# enabling our server to accept connections
# 5 here is the number of unaccepted connections the system will allow
# before refusing new connections
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

# accept connection if there is any
client_socket, address = s.accept()
# if below code is executed, that means sender is connected
print(f"[+] {address} connected!!")


# receive file information
# receive using client socket, not server socket
received = client_socket.recv(BUFFER_SIZE).decode()
path, filesize = received.split(SEPARATOR)
# remove the absolute path if there is - may not have to do this for the sync but should check and figure out how to ensure we get the same folder/file tree
filename = os.path.basename(path)
# convert to integer
filesize = int(filesize)

# start receiving the file from the socket
# and writing to the file stream
progress = tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
with open(filename, "wb") as f: # note different read/write mode!!!
    for _ in progress:
        # read 1024 bytes from the socket (receive)
        bytes_read = client_socket.recv(BUFFER_SIZE)
        if not bytes_read:
            # nothing is received
            # file transmitting is done
            
            break
        # write to the file the bytes we just received
        f.write(bytes_read)
        # update progress bar
        progress.update(len(bytes_read))
        

backup_date = datetime.now().strftime("%Y_%m_%d")
backup_name = f"{backup_date}_backup"

# extract archive contents into dated backup folder
decompress(f"{filename}", backup_name)
# delete archive
os.remove(filename)

# close the client socket
client_socket.close()
# close the server socket
s.close()