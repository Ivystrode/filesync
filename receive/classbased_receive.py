import socket
from tqdm import tqdm
import tarfile
import os
from datetime import datetime
import shutil
import ntpath

class Receiver():
    
    def __init__(self, SERVER_HOST, SERVER_PORT, backup_dir):
        self.SERVER_HOST = SERVER_HOST
        self.SERVER_PORT = SERVER_PORT
        
        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"
        
        self.sendback_address = ""
        self.sendback_port = 5002

        self.backup_dir = backup_dir + "\\"
        print(f"BACKUP DIR IS {self.backup_dir}")
        
    def start(self):
        s = socket.socket()
        s.bind((self.SERVER_HOST, 5002))
        s.listen(5)
        
        client_socket, address = s.accept()
        self.sendback_address = address[0]
        print(self.sendback_address)
        print(f"[+] Client {address} has established a connection")
        print("[*] Awaiting proposed manifest...")
        
        received = client_socket.recv(self.BUFFER_SIZE).decode()
        path, filesize = received.split(self.SEPARATOR)
        
        filename = os.path.basename(path)
        filesize = int(filesize)
        
        if 'proposed_manifest' not in path:
            print("[!] Not a recognised manifest")
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
        
        server_manifest_file = "server_manifest.txt"
        
        with open(proposed_manifest, "r") as pfile:
            for line in pfile.readlines():
                file = tuple(line.split(", "))
                if os.path.isfile(file[0]):
                    print(f"{file[0]} is present")
                else:
                    print(f"{file[0]} is ABSENT")
                    with open(server_manifest_file, "a") as sfile:
                        sfile.write(file[0] + "\n")
        
                                    
        return server_manifest_file
        
    def send_server_manifest(self, server_manifest):
        print("[+] Sending server manifest to client")
        s = socket.socket()
        
        print(f"[*] Connecting to client: {self.sendback_address}:{self.sendback_port}")
        s.connect((self.sendback_address,self.sendback_port))
        print(f"[+] Connected to client: {self.sendback_address}")
        
        filesize = os.path.getsize(server_manifest)
        s.send(f"{server_manifest}{self.SEPARATOR}{filesize}".encode())
        
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

    def sort_file(self, path, filename):
        filename = filename.replace('\\', '/')
        destination_file = self.backup_dir + path 
        destination_file = path.replace('\\', '/')  
        destination_folder = os.getcwd() + "/" + destination_file.replace(filename, "")
        
        
        print("===")
        print(path)
        print(filename)
        print(destination_file)
        print(destination_folder)
        print("===")
        
        
        # filename = os.getcwd() + '/' + filename.replace("\\", "/")
        
        print(f"\nSorting: {filename} to: \n{destination_file}\n")
        if not os.path.exists(destination_folder):
            os.mkdir(destination_folder)
            print("folder made")
        shutil.move(filename, destination_file)
        print("Moved")
        
    def close_connection(self, client_socket, s):
        print("Terminate command received")
        client_socket.close()
        s.close()
        
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

            received = client_socket.recv(self.BUFFER_SIZE).decode()
            path, filesize = received.split(self.SEPARATOR)
            # remove the absolute path if there is - may not have to do this for the sync but should check and figure out how to ensure we get the same folder/file tree
            filename = os.path.basename(path)
            # try this to work on linux
            filename = ntpath.basename(path)
            # convert to integer
            filesize = int(filesize)
            
            if path == "SENDCOMPLETE":
                self.close_connection(client_socket, s)
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
        s.close()
            # s.shutdown(2)
        
if __name__ == '__main__':
    backup = Receiver("0.0.0.0", 5001, 'pi-sendthis')
    backup.start()
