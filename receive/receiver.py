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
 
        self.client_name = "N/A"
        self.sendback_address = ""
        self.sendback_port = 5002
 
        self.backup_dir = backup_dir + "/"
        print(f"BACKUP DIR IS {self.backup_dir}")
        # if not os.path.exists(self.backup_dir):
        #     os.mkdirs
 
        self.logfile = ""
 
    def start(self):
        s = socket.socket()
        s.bind((self.SERVER_HOST, 5002))
        s.listen(5)
 
 
        timenow = datetime.now().strftime("%Y%m%d%H%M")
 
        client_socket, address = s.accept()
        self.sendback_address = address[0]
        self.client_name = socket.gethostbyaddr(address[0])[0]
        self.logfile = f"{timenow}_{self.client_name}_Receive_Log.txt"
        
        # print(self.sendback_address)
        # print(self.client_name)
        print(f"[+] Client {self.client_name}: {self.sendback_address} has established a connection")
        print("[*] Awaiting client manifest...")
 
        with open(self.logfile, "w") as f:
            f.write(f"====BEGIN RECEIVE OPERATION=====\n\nDTG: {timenow}\nDirectory: {self.backup_dir}\nClient: {self.client_name} ({self.sendback_address})\n\n")
 
        received = client_socket.recv(self.BUFFER_SIZE).decode()
        print(received)
        path, filesize = received.split(self.SEPARATOR)
 
        filename = os.path.basename(path)
        filesize = int(filesize)
 
        if 'client_manifest' not in path:
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
            client_manifest = filename
            print(f"[+] Client manifest received: {client_manifest}")
 
        server_manifest = self.check_client_manifest(client_manifest)
        self.send_server_manifest(server_manifest)
        client_socket.close()
        s.close()
        self.receive()
 
    def check_client_manifest(self, client_manifest):
        print(f"[*] Checking client manifest: {client_manifest}...")
 
        client_manifest_filecount = 0
 
        server_manifest_file = "server_manifest.txt" 
 
        with open(server_manifest_file, "w") as s: # I think I should remove this so that the below works...
            s.write("")
 
        with open(client_manifest, "r") as pfile:
            for line in tqdm(pfile.readlines()):
                file = tuple(line.split(f"{self.SEPARATOR}"))
                file_name = file[0].replace("\\", "/")
                file_mtime = file[1]
                client_manifest_filecount += 1
                
                if self.check_file_needed(file_name, file_mtime) == True:
                    print(f"Adding: {file_name} to server manifest\n")
                    self.files_requested += 1
                    with open(server_manifest_file, "a") as sfile:
                        sfile.write(file_name + "\n")
                        time.sleep(0.1)
                else:
                    print(f"{file_name} is not needed\n")
                    pass
                
                # if os.path.exists(self.backup_dir + file_name): # try changing to isfile to fix above?
                #     # print(f"{file_name} is present")
                #     pass
                # else:
                #     # print(f"Adding: {file_name} to server manifest")
                #     self.files_requested += 1
                #     with open(server_manifest_file, "a") as sfile:
                #         sfile.write(file_name + "\n")
                #         time.sleep(0.1)
 
        if not os.path.exists(server_manifest_file):
            print("[-] No files required")
            print("[*] Inform client that server is up to date")
            with open(server_manifest_file, "w") as sfile:
                sfile.write("Server up to date\n")
            with open(self.logfile, "a") as f:
                f.write(f"\n[!] All client files already present")
 
        else:
            with open(self.logfile, "a") as f:
                f.write(f"Client manifest files: {str(client_manifest_filecount)}\n")
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
            print(f"\n[+] Server manifest sent to {self.client_name} ({self.sendback_address})")
        s.close()
        with open(self.logfile, "a") as f:
            f.write(f"[+] Server manifest sent to {self.client_name}\n")
 
    def sort_file(self, path, filename):
        filename = filename.replace('\\', '/')
        destination_file = self.backup_dir + path.replace('\\','/') 
        
        print(f"Sorting: {filename} to: \n{destination_file}")
        # self.check_file(path, filename, destination_file)
        
        if not os.path.exists(destination_file.replace(filename, "")):
            print("making dir")
            os.makedirs(destination_file.replace(filename, ""))
            # need to check for actual file as well? ::
        # if not os.path.exists(destination_file):
        #     os.makedirs(destination_file.replace(filename, ""))
            # and then move the below 2 lines into this tab
        print("moving file")
        shutil.move(filename, destination_file)
        self.files_received += 1
        
    def check_file_needed(self, client_file, client_file_mtime):
        destination_file = self.backup_dir + client_file        
        have_file = False
        have_latest_version = False
        
        print("\n-+-+-+-+-+-+-\nChecking existence of: " + str(destination_file))
        print("With client file: " + str(client_file))
        
        if os.path.exists(destination_file):
            have_file = True
            print("MATCH: " + str(destination_file) + " ---> " + str(client_file))
            print("Checking modified times...")
            
            server_file_mtime = os.path.getmtime(destination_file)
            
            print("Server file mtime: " + str(server_file_mtime))
            print("Client file mtime: " + str(client_file_mtime))
            
            if server_file_mtime < float(client_file_mtime):
                print("Server's version is out of date, we need this file")
                return True
            else:
                print("Server's version is the same version (same last modified date)")
                return False
            
        else:
            print("File not found - get it from the client")
            have_file = False            
            return True 
       
    # Function to check modified time: 
    # def more_recently_modified(f1, f2):
    #     f1_mtime = os.path.getmtime(f1)
    #     f2_mtime = os.path.getmtime(f2)
        
    #     if f1_mtime > f2_mtime:
    #         print(f1 + " was more recently modified")
    #     else:
    #         print(f2 + " was more recently modified")

 
    def close_connection(self, client_socket, s, address, *args):
 
        if args:
            print("[!] RETRYING CONNECTION")
            with open(self.logfile, "a") as f:
                f.write(f"[!] RETRYING CONNECTION TO: {self.client_name} ({self.sendback_address})\n")
            client_socket.close()
            s.close()
 
        if not args: # the arg will be saying that there was an error, so if none terminate connection         
            client_socket.close()
            s.close()            
            print(f"[-] Terminate command received from client: {self.client_name}")
            print(f"[-] Connection to {self.client_name} closed")
            print(f"[-] {self.files_requested} files requested") # minus 1 to account for the blank line at EOF?
            print(f"[-] {self.files_received} files received")
 
            with open(self.logfile, "a") as f:            
                f.write(f"[-] Terminate command received from {self.client_name}\n")
                f.write(f"[-] Connection to {self.client_name} closed\n")
                f.write(f"[-] {self.files_requested} files requested\n")
                f.write(f"[-] {self.files_received} files received\n")
                f.write(f"\n\n=====END OF RECEIVE OPERATION=====\n")
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
            print(f"\n[+] Incoming data from {self.client_name} - {address}")
 
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
            except Exception as e:
                time.sleep(5)
                print("[!] FILE RECEIVE ERROR - RETRYING")
                print(e)
                with open(self.logfile, "a") as f:
                    f.write(f"[!] FILE RECEIVE ERROR: {filename}\n")
                time.sleep(5)
                self.close_connection(client_socket, s, address, "File receive error")
                self.receive()
                break
        s.close()
 
if __name__ == '__main__':
    backup = Receiver("0.0.0.0", 5001, '/srv/dev-disk-by-label-Data/Main/Central_repository')
    backup.start()