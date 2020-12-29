import socket
import tqdm
import time
from datetime import datetime, date
import calendar
import os
import shutil
import argparse

class Transmitter():
    
    def __init__(self, host, port, backup_day, backup_timerange, backup_dir, **kwargs):
        self.host = host
        self.port = port
        self.backup_day = backup_day
        self.backup_timerange = backup_timerange
        self.backup_dir = backup_dir
        
        self.SEPARATOR = "<SEPARATOR>"
        self.BUFFER_SIZE = 4096
        
        self.files_sent = 0
        self.files_unknown = 0
        
        self.logfile = ""
        
        weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
        
        # IF ENCRYPT = TRUE THEN WE'RE GOING TO ENCRYPT EACH FILE
        
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
                if day.lower() not in weekdays:
                    print(f"\n[!] Invalid Backup Day: {day}\n")
                    exit()
        else:
            self.backup_day = weekdays
            print("\n[!] Backups will occur daily\n")
            # print(self.backup_day)
        # print("Backing up on the following days:")
        # print(self.backup_day)
                
        if backup_timerange[0] >= backup_timerange[1]:
            print("\n[!] Invalid Time Range\n")
            print("The start time must be earlier than the finish time")
            exit()            
            
        if not os.path.isdir(self.backup_dir):
            print("\n[!] Invalid backup directory\n")
            print("Path does not exist")
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
                        if day.lower() == today.lower(): #and timenow < self.backup_timerange[0]: # why was this here in the first place???
                            # print(f"{day}: Backup will commence at: {self.backup_timerange[0]}")
                            
                            
                            if self.backup_timerange[0] <= datetime.now().strftime("%H%M") < self.backup_timerange[1]:
                                print("[+] Backup window open")
                                
                                
                                try:    
                                    # add this try/except block to a separate function so that a backup can be run singly rather than on a schedule
                                    # as well, so that user has another option/mthod of backup
                                    print("[*] Beginning backup")
                                    logfiletime = datetime.now().strftime("%Y%m%d%H%M")
                                    self.logfile = f"{logfiletime}_Transmit_Log"
                                    
                                    # Begin logging the backup operation
                                    with open(self.logfile, "w") as f:
                                        f.write(f"=====BEGIN TRANSMIT OPERATION=====\n\nDTG: {logfiletime}\nDirectory: {self.backup_dir}\nServer: {self.host}:{self.port}\nSchedule: {self.backup_timerange} - {self.backup_day}\n\n")
                                    
                                    server_manifest = self.create_manifest_proposal()
                                    self.start_backup(server_manifest)
                                    backup_complete = True
                                    print("[+] Backup complete")
                                    
                                    with open(self.logfile, "a") as f:
                                        f.write("\n\n=====END TRANSMIT OPERATION=====\n")
                                    if not os.path.exists("Transmit_logs"):
                                        os.mkdir("Transmit_logs")
                                    shutil.move(self.logfile, "Transmit_logs")
                                    
                                    
                                except Exception as err:
                                    print("[!] BACKUP ERROR:")
                                    print(err)
                                    with open(self.logfile, "a") as f:
                                        f.write(f"[!] BACKUP ERROR: {err}\n")
                                        f.write("\n\n=====END TRANSMIT OPERATION=====\n")
                                    if not os.path.exists("Transmit_logs"):
                                        os.mkdir("Transmit_logs")
                                    shutil.move(self.logfile, "Transmit_logs")
                                    #recursively call self.run_scheduler again so the backup process can restart?
                                    #maybe for some errors - check what the exception/err is and decide based on that
                                    #right now it seems like it will keep looping but the script freezes because it can't duplicate the logfile
                                    # SOLUTION: time.sleep(60) at least so at least the logfile will be named differently and won't freeze the script?
                                    # that way at least it will keep trying
                                    time.sleep(61)
                                    # tried complicated methods of creating new log files each times it tries but...its just not worth it when this works
                                    
                            if timenow >= self.backup_timerange[1] and backup_complete:
                                print("Backup window closed")
                                backup_complete = False
                                    
                        # else:
                        #     print(f"{day}: No backup today")
                        
                else:
                    print("\n[!] Invalid backup time range\n")
                    print("Time range must be a tuple containing a start time and end time in 24hr format")
                    print("For example: ('1300', 1400')")
                    exit()
                        
                time.sleep(5)
            

                
            time.sleep(5)

    def create_manifest_proposal(self):
        """
        Creates a list of all the files/filepaths that are in the backup folder
        and their last modified time, as a tuple of two strings
        Receiver will then check this list against what it currently has
        and send back a confirmatory manifest, which the sender will then use
        to determine which files to send
        """
        filecount = 0
        
        if os.path.exists("client_manifest.txt"):
            with open("client_manifest.txt", "w") as f:
                f.write("")
        
        print("[*] Writing manifest")
        for item in os.walk(self.backup_dir):
            if len(item[2]) > 0:
                for file in item[2]:
                    file_namepath = item[0] + "\\" + file
                    file_modded_date =  time.ctime(os.path.getmtime(item[0] + "\\" + file))
                    # file_modded_date =  os.path.getmtime(item[0] + "\\" + file)
                    filecount += 1
                    with open("client_manifest.txt", "a") as f:
                        f.write(f"{file_namepath}{self.SEPARATOR}{file_modded_date}\n")
                        
        with open(self.logfile, "a") as f:
                f.write(f"\n[*] Files sent in client manifest: {str(filecount)}\n")
                        
        print("[*] Sending client manifest to server...")
        self.sendfile("client_manifest.txt")
        print("[+] Client manifest sent")
        
        # method 1...
        # server_manifest = self.check_server_manifest()
        # return server_manifest
        
        # method 2...less code same thing
        return self.check_server_manifest() 
                        
    def check_server_manifest(self):
        """
        Once the required file manifest is received from the server, 
        check it and use it to only send the files the server requested
        """
        
        server_manifest_filecount = 0
        
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
        
        # Count number of files in server manifest and write to log
        with open(server_manifest, "r") as sfile:
            for line in sfile.readlines():
                server_manifest_filecount += 1
        with open(self.logfile, "a") as f:
            f.write(f"\n[*] Files requested by server manifest: {str(server_manifest_filecount)}\n")
            
            
        
        return server_manifest
                        

    def sendfile(self, filename):
        """
        Creates a new socket to send each individual file
        """
        s = socket.socket()

        # print(f"[*] Connecting to: {self.host}:{self.port}")
        if "client_manifest" in filename:
            s.connect((self.host, 5002))
            print(f"[*] Connecting to: {self.host}:5002")
        else:
            s.connect((self.host,self.port))
            print(f"[*] Connecting to: {self.host}:{self.port}")
        print("[+] connected")
        
        # if "SENDCOMPLETE" not in filename and "client_manifest" not in filename:
        if "SENDCOMPLETE" not in filename:
            filesize = os.path.getsize(filename)
        else:
            filesize = 10

        s.send(f"{filename}{self.SEPARATOR}{filesize}".encode())

        if filename != "SENDCOMPLETE":
            try:
                progress = tqdm.tqdm(range(filesize), f"[*] Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
                with open(filename, "rb") as f:
                    for _ in progress:
                        try:
                            bytes_read = f.read(self.BUFFER_SIZE)
                            
                            if not bytes_read:
                                break
                            
                            s.sendall(bytes_read)
                            progress.update(len(bytes_read))
                        except:
                            print("[!] FILE SEND ERROR")
                            self.files_unknown += 1
                            break
            except:
                print("[!] FILE SEND ERROR")
                self.files_unknown += 1
                
                    
            print("[+] File sent: " + filename)
            
        s.close()
        
    def start_backup(self, server_manifest):
        """
        Starting from the backup directory, recursively goes through the folders and sends all files
        """
        
        with open(server_manifest, "r") as sfile:
            for line in sfile.readlines():
                file = line.strip()
                if "Server up to date" in file:
                    print("[!] Server is already up to date, terminating backup operations")
                    
                    with open(self.logfile, "a") as f:
                        f.write(f"\n[!] Server already up to date, terminating backup operations")
                        
                    break
                
                if os.path.exists(file):
                    print(f"[+] Located: {file}")
                    
                    try:
                        # print(file)
                        self.sendfile(file)
                        print("[+] SENT ON ATTEMPT 1\n")
                        with open(self.logfile, "a") as f:
                            f.write(f"\n[+] File sent on attempt 1: {file}")
                            
                    except:
                        for interval in range(1,60):
                            try:
                                print(f"\n[!] Connection busy, retrying in {str(interval)} seconds...\n")
                                time.sleep(interval)
                                self.sendfile(file)
                                print(f"[+] SENT ON ATTEMPT {str(interval+1)}")
                                
                                with open(self.logfile, "a") as f:
                                    f.write(f"\n[*] File sent on attempt {str(interval+1)}: {file}")
                                    
                                break
                            
                            except:
                                print("\n[!] FILE NOT SENT\n")
                                
                                with open(self.logfile, "a") as f:
                                    f.write(f"\n[!] FILE NOT SENT: {file}")
                                    
                                pass
                            
                    self.files_sent += 1
                    
                else:
                    print(f"Unable to locate: {file}")
                    self.files_unknown += 1         
                               
                    with open(self.logfile, "a") as f:
                        f.write(f"\n[!] Unable to locate: {file}")
                        
                time.sleep(0.1)
                            
            self.terminate()        

    def terminate(self):
        """
        Once the backup process is complete, let the receiver know to stop listening.
        """
        
        print("[*] File transmit complete, informing receiver")
        print(f"[*] {self.files_sent} files sent")
        print(f"[*] {self.files_unknown} requested files not located")
        time.sleep(1)
        self.sendfile('SENDCOMPLETE')
        
        print("[*] Terminate command sent")
        print(f"[-] Closing connection to: {self.host}:{self.port}")
        
        with open(self.logfile, "a") as f:
            f.write(f"\n[-] Terminate command sent to server")
            f.write(f"\n[*] {self.files_sent} files sent")
            f.write(f"\n[*] {self.files_unknown} requested files not located")
            f.write(f"\n[-] Connection closed to: {self.host}:{self.port}")
        self.files_sent = 0
        self.files_unknown = 0
    

if __name__ == '__main__':
    
    weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday','daily']
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-s", "--server", help="The IP address of the server to send files to", metavar="", type=str, required=True)
    parser.add_argument("-p", "--port", help="Port to send on - the server must be receiving on the same port", type=int, default=5001, metavar='')
    parser.add_argument("-d", "--days", help="Days to perform backup. Enter daily to backup every day.", type=str, nargs='+', choices=weekdays, metavar='', required=True)
    parser.add_argument("-t", "--timerange", help="Time (in 24hr format with no symbols) to begin and time end the backup window - ie 1300 1530", type=str, nargs=2, default = ("0200", "0400"), metavar='')
    parser.add_argument("-f", "--folder", help="Relative path of the folder (directory) you want transferred & backed up", type=str, required=True, metavar='')
    parser.add_argument("-e", "--encrypt", help="Encrypt files on transfer - sets to True if entered", default=False, action='store_true')
    
    args = parser.parse_args()
    
    # If argparse values difficult to unpack use a dictionary:
    # arg_dict = dict((k,v) for k,v in vars(args).items() if k!="message_type") 
    
    backupper = Transmitter(
        vars(args)['server'],
        vars(args)['port'],
        vars(args)['days'],
        tuple(vars(args)['timerange']),
        vars(args)['folder'],
        # **vars(args)['encrypt'], # how to give an optional kwarg in argparse

    )
    
    print("\n----------")
    print("Transmitter parameters\n")
    print(f"Backup server: {backupper.host}")
    print(f"Port: {backupper.port}")
    print(f"Backup days: {backupper.backup_day}")
    print(f"Backup time window: {backupper.backup_timerange}")
    print(f"Folder to backup: {backupper.backup_dir}")
    if vars(args)['encrypt']:
        print("Encryption: On")
    else:
        print("Encryption: Off")
    print("----------\n")
    
    run_transmitter = input("Run Transmitter now? y/n\n>>>")
    if run_transmitter == "y":
        print("Transmitter scheduler active...")
        backupper.run_scheduler()
    else:
        print("Exiting...")
        exit()

        