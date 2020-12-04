import socket
import tqdm
import time
from datetime import datetime, date
import calendar
import os

class Transmitter():
    
    def __init__(self, host, port, backup_day, backup_timerange, backup_dir):
        self.host = host
        self.port = port
        self.backup_day = backup_day
        self.backup_timerange = backup_timerange
        self.backup_dir = backup_dir
        self.SEPARATOR = "<SEPARATOR>"
        self.BUFFER_SIZE = 4096
        
        self.weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
        
        if port > 65535:
            print("\n[!] Invalid Port\n")
            exit()
            
        if type(backup_day) != list:
            print("\n[!] Invalid Day/s\n")
            print("Backup day/s must be entered as a list even if only 1 day")
            print("Enter 'daily' to backup every day in the alloted time window")
            exit()
            
        if "daily" not in self.backup_day:
            for day in self.backup_day:
                if day.lower() not in self.weekdays:
                    print(f"\n[!] Invalid Backup Day: {day}\n")
                    exit()
        else:
            self.backup_day = self.weekdays
            print("\n[!] Backups will occur daily\n")
            # print(self.backup_day)
                
        if backup_timerange[0] >= backup_timerange[1]:
            print("\n[!] Invalid Time Range\n")
            print("The start time must be earlier than the finish time")
            exit()
        
    def run_scheduler(self):    
        """
        Takes a day or list of days and a tuple containing two times that represent
        the backup time window on each backup day. Checks if the two times are valid
        before continuing.
        """
        backup_complete = False
    
        while True:
            timenow = datetime.now().strftime("%H%M")
            
            while not backup_complete:
                valid_timerange = False
                for timing in self.backup_timerange:
                    try:
                        datetime.strptime(timing, "%H%M")
                        valid_timerange = True
                    except:
                        valid_timerange = False
                        break
            
                if valid_timerange:
                    
                    date_today = datetime.now().strftime("%d-%m-%Y")
                    weekday_number = datetime.strptime(date_today, '%d-%m-%Y').weekday()
                    today = calendar.day_name[weekday_number]
                    
                    for day in self.backup_day:
                        if day.lower() == today.lower():
                            print(f"{day}: Backup today")
                            
                            if self.backup_timerange[0] <= datetime.now().strftime("%H%M") < self.backup_timerange[1]:
                                print("[+] Backup window open")
                                
                                
                                try:    
                                    # add this try/except block to a separate function so that a backup can be run singly rather than on a schedule
                                    # as well, so that user has another option/mthod of backup
                                    print("[*] Beginning backup")
                                    server_manifest = self.create_manifest_proposal()
                                    self.start_backup(server_manifest)
                                    backup_complete = True
                                    print("[+] Backup complete")
                                    
                                except Exception as err:
                                    print("[!] BACKUP ERROR:")
                                    print(err)
                                    #recursively call self.run_scheduler again so the backup process can restart?
                                    #maybe for some errors - check what the exception/err is and decide based on that
                            else:
                                print("Waiting for backup window...")
                                    
                        # else:
                        #     print(f"{day}: No backup today")
                        
                else:
                    print("\n[!] Invalid backup time range\n")
                    print("Time range must be a tuple containing a start time and end time in 24hr format")
                    print("For example: ('1300', 1400')")
                    exit()
                        
                time.sleep(5)
            
            if timenow >= self.backup_timerange[1] and backup_complete:
                print("Backup window closed")
                backup_complete = False
                
            time.sleep(5)

    def create_manifest_proposal(self):
        """
        Creates a list of all the files/filepaths that are in the backup folder
        and their last modified time, as a tuple of two strings
        Receiver will then check this list against what it currently has
        and send back a confirmatory manifest, which the sender will then use
        to determine which files to send
        """
        
        print("[*] Writing manifest")
        for item in os.walk(self.backup_dir):
            if len(item[2]) > 0:
                for file in item[2]:
                    file_namepath = item[0] + "\\" + file
                    file_modded_date =  time.ctime(os.path.getmtime(item[0] + "\\" + file))
                    # file_modded_date =  os.path.getmtime(item[0] + "\\" + file)
                    with open("proposed_manifest.txt", "a") as f:
                        f.write(f"{file_namepath}, {file_modded_date}\n")
                        
        print("[*] Sending proposed manifest to server...")
        self.sendfile("proposed_manifest.txt")
        print("[+] Proposed manifest sent")
        
        # method 1...
        # server_manifest = self.check_server_manifest()
        # return server_manifest
        
        # method 2...less code same thing
        return self.check_server_manifest() # i think this does 
                        
    def check_server_manifest(self):
        """
        Once the required file manifest is received from the server, 
        check it and use it to only send the files the server requested
        """
        
        s = socket.socket()
        s.bind(('0.0.0.0', 5002))
        s.listen(5)
        print("[*] Awaiting server manifest...")
        
        server_socket, address = s.accept()
        print(f"[+] Incoming data from {address}")
        
        received = server_socket.recv(self.BUFFER_SIZE).decode()
        path, filesize = received.split(self.SEPARATOR)
        
        filename = os.path.basename(path)
        filesize = int(filesize)
        
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f: 
            for _ in progress:
                bytes_read = server_socket.recv(self.BUFFER_SIZE)
                if not bytes_read:
                    
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))
        server_manifest = filename
        print("[+] Server manifest received")
        print(server_manifest)
        
        return server_manifest
                        

    def sendfile(self, filename):
        """
        Creates a new socket to send each individual file
        """
        s = socket.socket()

        # print(f"[*] Connecting to: {self.host}:{self.port}")
        if "proposed_manifest" in filename:
            s.connect((self.host, 5002))
            print(f"[*] Connecting to: {self.host}:5002")
        else:
            s.connect((self.host,self.port))
            print(f"[*] Connecting to: {self.host}:{self.port}")
        print("[+] connected\n")
        
        if "SENDCOMPLETE" not in filename and "proposed_manifest" not in filename:
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
        
    def start_backup(self, server_manifest):
        """
        Starting from the backup directory, recursively goes through the folders and sends all files
        """
        
        # THIS WILL HAVE TO CHANGE TO FOR FILE IN SERVER_MANIFEST!!
        with open(server_manifest, "r") as sfile:
            for line in sfile.readlines():
                file = line.strip()
                if "Server up to date" in file:
                    print("[!] Server is already up to date, terminating backup operations")
                    break
                if os.path.exists(file):
                    print("yes it exists")
                    try:
                        print(file)
                        self.sendfile(file)
                        print("[+] SENT ON ATTEMPT 1\n")
                    except:
                        for interval in range(1,60):
                            try:
                                print(f"\n[!] Connection busy, retrying in {str(interval)} seconds...\n")
                                time.sleep(interval)
                                self.sendfile(file)
                                print(f"[+] SENT ON ATTEMPT {str(interval+1)}")
                                break
                            except:
                                print("\n[!] FILE NOT SENT\n")
                                pass
                else:
                    print("Cant find it...")
                time.sleep(0.1)
                            
            self.terminate()

    def terminate(self):
        """
        Once the backup process is complete, let the receiver know to stop listening.
        """
        
        print("[*] File transmit complete, informing receiver")
        time.sleep(1)
        self.sendfile('SENDCOMPLETE')
        
        print("[*] Terminate command sent")
        print(f"[-] Closing connection to: {self.host}:{self.port}")
    

if __name__ == '__main__':
    
    rpi_backup = Transmitter("192.168.0.16", 
                         5001, 
                         ['friday', 'sunday'], 
                         ("1136", "2359"), 
                         "to_linux_sendthis")
    
    local_test = Transmitter("10.248.220.31", # does this not work because its on the same computer? try with the laptop
                         5001, 
                         ['daily'], 
                         ("1116", "1700"), 
                         "sendthis")
    
    rpi_backup.run_scheduler()

        