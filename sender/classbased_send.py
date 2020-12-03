import socket
import tqdm
import time
from datetime import datetime
import os

class Transmitter():
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.SEPARATOR = "<SEPARATOR>"
        self.BUFFER_SIZE = 4096

    def create_manifest_proposal(self):
        """
        Creates a list of all the files/filepaths that are in the backup folder
        and their last modified time, as a tuple of two strings
        Receiver will then check this list against what it currently has
        and send back a confirmatory manifest, which the sender will then use
        to determine which files to send
        """
        
        for item in os.walk('sendthis'):
            if len(item[2]) > 0:
                for file in item[2]:
                    file_namepath = item[0] + "\\" + file
                    file_modded_date =  time.ctime(os.path.getmtime(item[0] + "\\" + file))
                    with open("proposed_manifest.txt", "a") as f:
                        f.write(f"('{file_namepath}', '{file_modded_date}')\n")
                        

    def sendfile(self, filename):
        """
        Creates a new socket to send each individual file
        """
        s = socket.socket()

        print(f"[-] Connecting to: {self.host}:{self.port}")
        s.connect((self.host,self.port))
        print("[+] connected\n")
        
        if filename != "SENDCOMPLETE":
            filesize = os.path.getsize(filename)
        else:
            filesize = 10

        s.send(f"{filename}{self.SEPARATOR}{filesize}".encode())

        if filename != "SENDCOMPLETE":
            progress = tqdm.tqdm(range(filesize), f"\nSending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
            with open(filename, "rb") as f:
                for _ in progress:
                    bytes_read = f.read(self.BUFFER_SIZE)
                    
                    if not bytes_read:
                        break
                    
                    s.sendall(bytes_read)
                    progress.update(len(bytes_read))
                    
            print("\nFile sent: " + filename)
        s.close()
        
    def start_backup(self):
        for item in os.walk('sendthis'):
            if len(item[2]) > 0: # there are files in this directory!
                for file in item[2]:
                    file_namepath = item[0] + "\\" + file
                    try:
                        print(file_namepath)
                        self.sendfile(file_namepath)
                        print("[+] SENT ON ATTEMPT 1\n")
                    except:
                        for interval in range(1,300):
                            try:
                                print(f"\n[!] Connection busy, retrying in {str(interval)} seconds...\n")
                                time.sleep(interval)
                                self.sendfile(file_namepath)
                                print(f"[+] SENT ON ATTEMPT {str(interval+1)}")
                                break
                            except:
                                print("\n[!] FILE NOT SENT\n")
                                pass
        self.terminate()

    def terminate(self):
        print("[-] File transmit complete, informing receiver")
        time.sleep(1)
        self.sendfile('SENDCOMPLETE')
        
        print("[-] Terminate command sent")
        print(f"[-] Closing connection to: {self.host}:{self.port}")


if __name__ == '__main__':
    try:    
        backup = Transmitter("10.248.220.31", 5001)
        backup.start_backup()
    except Exception as err:
        print("BACKUP ERROR:")
        print(err)