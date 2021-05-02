import socket
from tqdm import tqdm
import tarfile
import os
from datetime import datetime
import shutil
import ntpath
import time
import argparse
import calendar
import multiprocessing
 
class Receiver():
 
    def __init__(self, SERVER_HOST, SERVER_PORT, backup_day, backup_timerange, backup_dir):
        self.SERVER_HOST = SERVER_HOST
        self.SERVER_PORT = SERVER_PORT
 
        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"
        
        self.backup_day = backup_day
        self.backup_timerange = backup_timerange
        
        self.backup_complete = False
        
        weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
        if type(backup_day) != list:
            print("\n[!] Invalid Day/s\n")
            print("Your program must send the backup days as a list")
            print("Backup day/s must be entered as a list even if only 1 day")
            print("Enter 'daily' to backup every day in the alloted time window")
            exit()
            
        if "daily" not in self.backup_day:
            for day in self.backup_day:
                if day.lower() not in weekdays:
                    print(f"\n[!] Invalid Backup Day: {day}\n")
                    exit()
            print(self.backup_day)
        else:
            self.backup_day = weekdays
            print("\n[!] Backups will occur daily\n")
            
        if backup_timerange[0] >= backup_timerange[1]:
            print("\n[!] Invalid Time Range\n")
            print("The start time must be earlier than the finish time")
            exit()  
 
        self.files_requested = 0
        self.files_received = 0
 
        self.client_name = "N/A"
        self.sendback_address = ""
        self.sendback_port = 5002
        
        self.backup_in_progress = False
        
        self.backup_process = multiprocessing.Process(name="backup_process", target=self.start)
        self.socket_killer_process = multiprocessing.Process(name="socket_killer_process", target=self.socket_killer)
 
        self.backup_dir = backup_dir + "/"
        print(f"BACKUP DIR IS {self.backup_dir}")
        # if not os.path.exists(self.backup_dir):
        #     os.mkdirs
 
        self.logfile = ""
        
    def run_scheduler(self):
        print("[*] Receiver: Scheduler active. Awaiting backup window.")
        print(f"Address: {self.SERVER_HOST}")
        print(f"Port: {self.SERVER_PORT}")
        print(f"Day: {self.backup_day}")
        print(f"Timerange: {self.backup_timerange}")
        print(f"Target: {self.backup_dir}\n")
        
        started = False
        
        # backup_complete = False
        
        while True:
            date_today = datetime.now().strftime("%d-%m-%Y")
            weekday_number = datetime.strptime(date_today, '%d-%m-%Y').weekday()
            today = calendar.day_name[weekday_number]
            
            while not self.backup_complete and not started:
                # print("waiting for backup")
                time.sleep(1)
                # if self.backup_process.is_alive():
                #     print("OH GAWD BACKUP THREAD STILLL ALIVE")
                #     self.backup_process.terminate()
                #     print("killed...")
                # else:
                #     print("backup process dead thank god")
                for day in self.backup_day:
                    if day.lower() == today.lower():
                        # print(f"{day} - Backup commence at: {self.backup_timerange[0]}")

                        if self.backup_timerange[0] <= datetime.now().strftime("%H%M") < self.backup_timerange[1]:
                            print("[+] Backup window open")
                            # self.start() # need to be separate thread that is stopped by socket killer ??? +++++++++++++++++++++++++++++++++
                            self.backup_process.start()
                            started = True
                            # self.backup_complete = True
                            # print("[+] Backup loop complete - will start again at next window")
                            # threading.Thread(target=self.socket_killer).stop()
                            
            if self.backup_complete and datetime.now().strftime("%H%M") > self.backup_timerange[1]:
                self.backup_complete = False
                started = False
                # if self.socket_killer_thread.is_alive():
                #     self.socket_killer_thread.stop()
                print("[!] Resetting backup complete status to False")
                # self.run_scheduler()
    
    def socket_killer(self, socket):
        print(f"[*] Socket killer: Monitoring {socket}")
        while not self.backup_complete:
            if datetime.now().strftime("%H%M") > self.backup_timerange[1] and not self.backup_in_progress:
                print("[-] Backup window closed, no client connection attempts detected")
                socket.close()
                self.backup_complete = True
                break
        print(socket)
        self.run_scheduler()
        self.socket_killer_process.terminate()
        # try:
        #     self.backup_process.terminate()
        #     print("terminated")
        # except:
        #     self.backup_process.start()
        #     print("started")
        # finally:
        #     self.backup_process.join()
        #     print("joined")
        # print("[*] Listener stopper terminated")
                
            
            
            
 
    def start(self):
        
                    
        s = socket.socket()
        s.bind((self.SERVER_HOST, 5002))
        s.listen(5)
        
        print(f"[+] {socket.gethostname()}: Listening for client connections...")
        
        # start thread listener stopper+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # threading.Thread(target=self.socket_killer, args=[s]).start()
        # self.socket_killer_thread.start(args=[s])
        self.socket_killer_process = multiprocessing.Process(name = "socket_killer_process", target=self.socket_killer, args=[s]).start()
 
        try:
            client_socket, address = s.accept()
            self.sendback_address = address[0]
            timenow = datetime.now().strftime("%Y%m%d%H%M")
            self.client_name = socket.gethostbyaddr(address[0])[0]
            self.logfile = f"{timenow}_{self.client_name}_Receive_Log.txt"
            
            # print(self.sendback_address)
            # print(self.client_name)
            print(f"[+] Client {self.client_name}: {self.sendback_address} has established a connection")
            self.backup_in_progress = True
            print("[*] Awaiting client manifest...")
    
            with open(self.logfile, "w") as f:
                f.write(f"====BEGIN RECEIVE OPERATION=====\n\nDTG: {timenow}\nDirectory: {self.backup_dir}\nClient: {self.client_name} ({self.sendback_address})\n\n")
    
            received = client_socket.recv(self.BUFFER_SIZE).decode()
            print("\n\n++++++++Receiving client manifest++++++++\n")
            print(received)
            print("\n++++++++Receiving client manifest++++++++\n\n")
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
            # TO TRY AND STOP ERRNO 98 - ADDRESS ALREADY IN USE:
            print("[*] Pausing for client...")
            time.sleep(1)
            self.receive()
        except Exception as e:
            print("[!] Receiver Loop exited")
            print(e)
 
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
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
    
    weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday','daily']
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-a", "--address", help="The IP address to listen on, use 0.0.0.0 to listen on all", metavar ="", type=str, required=False, default="0.0.0.0")
    parser.add_argument("-p", "--port", help="Port to listen on - must be same as client is sending on, default 5001", metavar ="", type=int, required=False, default=5001)
    parser.add_argument("-f", "--folder", help="Target folder to backup to/sync with the client (relative path)", metavar ="", type=str, required=True)
    parser.add_argument("-d", "--days", help="Which days to carry out backup on", metavar ="", type=str, required=True, nargs="+", choices=weekdays)
    parser.add_argument("-t", "--timerange", help="Start time and end time to carry out the backup in 24h format, no symbols (allow enough time for files to upload)", required=True, type=str, nargs=2)

    args = parser.parse_args()
    
    print(args)
    print("====")

    receiver = Receiver(
        vars(args)['address'],
        vars(args)['port'],
        vars(args)['days'],
        vars(args)['timerange'],
        vars(args)['folder'],
    )
    
    print("\n----------")
    print("Receiver parameters\n")
    print(f"Receive address: {receiver.SERVER_HOST}")
    print(f"Port: {receiver.SERVER_PORT}")
    print(f"Backup days: {receiver.backup_day}")
    print(f"Backup time window: {receiver.backup_timerange}")
    print(f"Target folder: {receiver.backup_dir}")
    print("----------\n")
    
    run_receiver = input("Run Receiver now? y/n\n>>>")
    if run_receiver == "y":
        receiver.run_scheduler()
    else:
        print("Exiting...")
        exit()
    
    
    
    # backup = Receiver("0.0.0.0", 5001, '/srv/dev-disk-by-label-Data/Main/Central_repository')
    # backup.start()