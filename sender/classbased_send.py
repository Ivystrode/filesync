import socket
import tqdm
import time
from datetime import datetime, date
import calendar
import os

class Transmitter():
    
    def __init__(self, host, port, backup_day, backup_timerange):
        self.host = host
        self.port = port
        self.backup_day = backup_day
        self.backup_timerange = backup_timerange
        self.SEPARATOR = "<SEPARATOR>"
        self.BUFFER_SIZE = 4096
        
        self.weekdays = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
        
        if port > 65535:
            print("\n[!] Invalid Port\n")
            exit()
            
        if type(backup_day) != list:
            print("\n[!] Invalid Day/s\n")
            print("Backup day/s must be entered as a list even if only 1 day")
            exit()
            
        for day in self.backup_day:
            if day.lower() not in self.weekdays:
                print("\n[!] Invalid Backup Day\n")
                exit()
                
            
        
    def backup_scheduler(self):    
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
                                    print("[*] Beginning backup")
                                    # self.start_backup()
                                    backup_complete = True
                                    print("[+] Backup complete")
                                    
                                except Exception as err:
                                    print("[!] BACKUP ERROR:")
                                    print(err)
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

        print(f"[*] Connecting to: {self.host}:{self.port}")
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
        print("[*] File transmit complete, informing receiver")
        time.sleep(1)
        self.sendfile('SENDCOMPLETE')
        
        print("[*] Terminate command sent")
        print(f"[-] Closing connection to: {self.host}:{self.port}")
    

if __name__ == '__main__':
    backup = Transmitter("10.248.220.31", 5001, ['thursday', 'friday'], ("1351", "1352"))
    backup.backup_scheduler()

        