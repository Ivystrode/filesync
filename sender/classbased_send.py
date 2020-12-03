import socket
import tqdm
import time
from datetime import datetime, date
import calendar
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

def backup_scheduler(backup_day, backup_time):    
    """
    Takes a day or list of days and a tuple containing two times that represent
    the backup time window on each backup day. Checks if the two times are valid
    before continuing.
    """
    
    valid_timerange = False
    for time in backup_time:
        try:
            datetime.strptime(time, "%H%M")
            valid_timerange = True
        except:
            print("Invalid backup time range")
            valid_timerange = False
            break
    
    
    if valid_timerange:
        
        date_today = datetime.now().strftime("%d-%m-%Y")
        weekday_number = datetime.strptime(date_today, '%d-%m-%Y').weekday()
        today = calendar.day_name[weekday_number]
        
        # print(today)
        # print(backup_time[0])
        # print(backup_time[1])
        # print(datetime.now().strftime("%H%M"))
        
        if today.lower() == backup_day.lower():
            print("Its backup day...")
            if datetime.now().strftime("%H%M") < backup_time[1] >= backup_time[0]:
                print("It's backup time boys!")
                return True
        else:
            print("No backup right now")
            return False
    else:
        print("Invalid backup time range")
        return False
    

if __name__ == '__main__':
    backup_complete = False
    start_time = "1030"
    finish_time = "1255"
    
    while True:
        timenow = datetime.now().strftime("%H%M")
        
        while not backup_complete:
            if backup_scheduler('thursday', (start_time, finish_time)):
                try:    
                    print("Backup time!!")
                    backup = Transmitter("10.248.220.31", 5001)
                    backup.start_backup()
                    backup_complete = True
                    print("Backup complete")
                    
                except Exception as err:
                    print("BACKUP ERROR:")
                    print(err)
                    
            else:
                print("Not scheduled to do a backup at thsi moment")
                
            time.sleep(1)
            
        if timenow >= finish_time and backup_complete:
            print("Backup window over")
            print("Waiting for next window")
            backup_complete = False
            
        time.sleep(1)
        