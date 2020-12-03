# WORKS WITH ALL VERSIONS OF MULTI_SEND


import socket
from tqdm import tqdm
import tarfile
import os
from datetime import datetime
import shutil

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001

#receive 4096 bytes each time
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

backup_dir = os.getcwd()
backup_dir = backup_dir + "\\"
print(f"BACKUP DIR IS {backup_dir}")

def sort_file(path, filename):
    destination_file = backup_dir + path.replace('/', '\\')  
    destination_folder = destination_file.replace(filename, "")
    filename = os.getcwd() + '\\' + filename
    
    print(f"\nSorting: {filename} to: \n{destination_file}\n")
    if not os.path.exists(destination_folder):
        os.mkdir(destination_folder)
        print("folder made")
    shutil.move(filename, destination_file)
    print("Moved")
    
def close_connection(client_socket, s):
    print("Terminate command received")
    client_socket.close()
    s.close()
    

while True:
    s = socket.socket()
    s.bind((SERVER_HOST, SERVER_PORT))
    s.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

    client_socket, address = s.accept()
    print(f"[+] {address} connected!!")

    received = client_socket.recv(BUFFER_SIZE).decode()
    path, filesize = received.split(SEPARATOR)
    # remove the absolute path if there is - may not have to do this for the sync but should check and figure out how to ensure we get the same folder/file tree
    filename = os.path.basename(path)
    # convert to integer
    filesize = int(filesize)
    
    if path == "SENDCOMPLETE":
        close_connection(client_socket, s)
        break
    
    else:
        progress = tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f: 
            for _ in progress:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))

        sort_file(path, filename)
        
