import socket
from tqdm import tqdm
import tarfile
import os
from datetime import datetime
import shutil
import ntpath
import time
 
class Receiver():
 
    def __init__(self, SERVER_HOST, SERVER_PORT, backup_dir):
        self.SERVER_HOST = SERVER_HOST
        self.SERVER_PORT = SERVER_PORT
 
        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"
 
        self.files_requested = 0
        self.files_received = 0
 
        self.sendback_address = ""
        self.sendback_port = 5002
 
        self.backup_dir = backup_dir + "\\"
        print(f"BACKUP DIR IS {self.backup_dir}")
        # if not os.path.exists(self.backup_dir):
        #     os.mkdirs
 
        self.logfile = ""
 
    def start(self):
        s = socket.socket()
        s.bind((self.SERVER_HOST, 5002))
        s.listen(5)
 
 
        timenow = datetime.now().strftime("%Y%m%d%H%M")
        self.logfile = f"{timenow}_Receive_Log.txt"
 
        client_socket, address = s.accept()
        self.sendback_address = address[0]
        print(self.sendback_address)
        print(f"[+] Client {address} has established a connection")
        print("[*] Awaiting proposed manifest...")
 
        with open(self.logfile, "w") as f:
            f.write(f"====BEGIN RECEIVE OPERATION=====\n\nDTG: {timenow}\nDirectory: {self.backup_dir}\nClient: {self.sendback_address}\n\n")
 
        received = client_socket.recv(self.BUFFER_SIZE).decode()
        path, filesize = received.split(self.SEPARATOR)
 
        filename = os.path.basename(path)
        filesize = int(filesize)
 
        if 'proposed_manifest' not in path:
            print("[!] Not a recognised manifest")
            with open(self.logfile, "a") as f:
                f.write("[!] Invalid client manifest")
            exit()
 
        else:
            progress = tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
            with open(filename, "wb") as f: 
                for _ in progress:
                    bytes_read = client_socket.recv(self.BUFFER_SIZE)
                    if not bytes_read:
 
                        break
                    f.write(bytes_read)
                    progress.update(len(bytes_read))
            proposed_manifest = filename
            print(f"[+] Proposed manifest received: {proposed_manifest}")
 
        server_manifest = self.check_proposed_manifest(proposed_manifest)
        self.send_server_manifest(server_manifest)
        client_socket.close()
        s.close()
        self.receive()
 
    def check_proposed_manifest(self, proposed_manifest):
        print(f"[*] Checking proposed manifest: {proposed_manifest}...")
 
        proposed_manifest_filecount = 0
 
        server_manifest_file = "server_manifest.txt" # eventually give this a dated name
 
        with open(server_manifest_file, "w") as s: # I think I should remove this so that the below works...
            s.write("")
 
        # for some reason this writes each file to the manifest several times
        # or at least the sender sends the file several times
        # why does it do this?
        with open(proposed_manifest, "r") as pfile:
            for line in pfile.readlines():
                file = tuple(line.split(", "))
                file_name = file[0].replace("\\", "/")
                proposed_manifest_filecount += 1
                if os.path.exists(file_name):
                    print(f"{file_name} is present")
                    pass
                else:
                    print(f"Adding: {file_name} to server manifest")
                    self.files_requested += 1
                    with open(server_manifest_file, "a") as sfile:
                        sfile.write(file_name + "\n")
                        time.sleep(0.1)
 
        if not os.path.exists(server_manifest_file):
            print("[-] No files required")
            print("[*] Inform client that server is up to date")
            with open(server_manifest_file, "w") as sfile:
                sfile.write("Server up to date\n")
            with open(self.logfile, "a") as f:
                f.write(f"\n[!] All client files already present")
 
        else:
            with open(self.logfile, "a") as f:
                f.write(f"Client manifest files: {str(proposed_manifest_filecount)}\n")
                f.write(f"Server manifest files: {str(self.files_requested)}\n\n")
 
 
        return server_manifest_file
 
    def send_server_manifest(self, server_manifest):
        print("[+] Sending server manifest to client")
        s = socket.socket()
 
        print(f"[*] Connecting to client: {self.sendback_address}:{self.sendback_port}")
        s.connect((self.sendback_address,self.sendback_port))
        print(f"[+] Connected to client: {self.sendback_address}")
 
        filesize = os.path.getsize(server_manifest)
        s.send(f"{server_manifest}{self.SEPARATOR}{filesize}".encode())
        time.sleep(1)
 
        progress = tqdm(range(filesize), f"\n[*] Sending {server_manifest}", unit="B", unit_scale=True, unit_divisor=1024)
 
        with open(server_manifest, "rb") as f:
            for _ in progress:
                bytes_read = f.read(self.BUFFER_SIZE)
 
                if not bytes_read:
                    break
 
                s.sendall(bytes_read)
                progress.update(len(bytes_read))
            print(f"\n[+] Server manifest sent to client {self.sendback_address}")
        s.close()
        with open(self.logfile, "a") as f:
            f.write(f"[+] Server manifest sent to {self.sendback_address}\n")
 
    def sort_file(self, path, filename):
        filename = filename.replace('\\', '/')
        destination_file = self.backup_dir + path 
        destination_file = path.replace('\\', '/')  
        destination_folder = os.getcwd() + "/" + destination_file.replace(filename, "")
 
 
        print(f"\nSorting: {filename} to: \n{destination_file}\n")
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            print("folder made")
        shutil.move(filename, destination_file)
        self.files_received += 1
        print("Moved")
 
    def close_connection(self, client_socket, s, address, *args):
 
        if args:
            print("[!] RETRYING CONNECTION")
            with open(self.logfile, "a") as f:
                f.write(f"[!] RETRYING CONNECTION TO: {address}\n")
            client_socket.close()
            s.close()
 
        if not args: # the arg will be saying that there was an error, so if none terminate connection         
            client_socket.close()
            s.close()            
            print(f"[-] Terminate command received from client: {address}")
            print(f"[-] Connection to {address} closed")
            print(f"[-] {self.files_requested} files requested")
            print(f"[-] {self.files_received} files received")
 
            with open(self.logfile, "a") as f:            
                f.write(f"[-] Terminate command received from client: {address}\n")
                f.write(f"[-] Connection to {address} closed\n")
                f.write(f"[-] {self.files_requested} files requested\n")
                f.write(f"[-] {self.files_received} files received\n")
                f.write(f"\n\n=====END OF RECEIVE OPERATION=====")
            if not os.path.exists("Receive_logs"):
                os.mkdir("Receive_logs")
            shutil.move(self.logfile, "Receive_logs")
 
 
    def receive(self):
        print("[+] Standing by to receive files...")
        # while True:
        print(self.SERVER_HOST)
        print(self.SERVER_PORT)
        s = socket.socket()
        s.bind((self.SERVER_HOST, self.SERVER_PORT))
        s.listen(5)
        print(f"[*] Listening as {self.SERVER_HOST}:{self.SERVER_PORT}")
        while True:
            client_socket, address = s.accept()
            print(f"[+] {address} connected!!")
 
            try:
                received = client_socket.recv(self.BUFFER_SIZE).decode()
            except:
                received = client_socket.recv(self.BUFFER_SIZE).decode("iso-8859-1")
 
            try:
                path, filesize = received.split(self.SEPARATOR)
                # remove the absolute path if there is - may not have to do this for the sync but should check and figure out how to ensure we get the same folder/file tree
                filename = os.path.basename(path)
                # try this to work on linux
                filename = ntpath.basename(path)
                # convert to integer
                filesize = int(filesize)
 
                if path == "SENDCOMPLETE":
                    self.close_connection(client_socket, s, address)
                    break
 
                else:
                    progress = tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
                    with open(filename, "wb") as f: 
                        for _ in progress:
                            bytes_read = client_socket.recv(self.BUFFER_SIZE)
                            if not bytes_read:
 
                                break
                            f.write(bytes_read)
                            progress.update(len(bytes_read))
 
                    self.sort_file(path, filename)
 
                    with open(self.logfile, "a") as f:
                        f.write(f"[+] File received: {filename}\n")
            except:
                time.sleep(5)
                print("[!] FILE RECEIVE ERROR - RETRYING")
                with open(self.logfile, "a") as f:
                    f.write(f"[!] FILE RECEIVE ERROR: {filename}\n")
                time.sleep(5)
                self.close_connection(client_socket, s, address, "File receive error")
                self.receive()
                break
        s.close()
 
if __name__ == '__main__':
    backup = Receiver("0.0.0.0", 5001, 'File_Root')
    backup.start()