import socket
import tqdm
import time
import os

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096

# host = "192.168.0.16" # for raspberry pi if on vpn
host = "10.248.220.31"
port = 5001 

def create_manifest_proposal():
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

def sendfile(filename):
    """
    Creates a new socket to send each individual file
    """
    s = socket.socket()

    print(f"[+] Connecting to: {host}:{port}")
    s.connect((host,port))
    print("[+] connected\n")
    
    # filename = 'sendthis/' + file
    filesize = os.path.getsize(filename)

    s.send(f"{filename}{SEPARATOR}{filesize}".encode())
    print(f"{filename}{SEPARATOR}{filesize}")

    progress = tqdm.tqdm(range(filesize), f"\nSending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        for _ in progress:
            bytes_read = f.read(BUFFER_SIZE)
            
            if not bytes_read:
                break
            
            s.sendall(bytes_read)
            progress.update(len(bytes_read))
            
    print("\nFile sent: " + filename)
    s.close()
    
# create_manifest_proposal() just making sure it worked. it does
    
for item in os.walk('sendthis'):
    if len(item[2]) > 0: # there are files in this directory!
        for file in item[2]:
            file_namepath = item[0] + "\\" + file
            try:
                print("\nSENDING FIRST TRY\n")
                sendfile(file_namepath)
            except:
                print("\nNot sent, will retry...\n")
                for interval in range(1,300):
                    print(f"\n{str(interval)} second interval\n")
                    try:
                        print(f"\nConnection busy, retrying in {str(interval)} seconds...\n")
                        time.sleep(interval)
                        sendfile(file_namepath)
                        break
                    except:
                        print("\nSENDING - PASS\n")
                        pass
            time.sleep(0.5)

# Sending files complete, operation over - tell the receiver we're done and close
print("File transmit complete")
s = socket.socket()
print(f"[+] Closing connection to: {host}:{port}")
s.connect((host,port))
print("[+] connected\n")

filename = 'SENDCOMPLETE'
filesize = 10

s.send(f"{filename}{SEPARATOR}{filesize}".encode())
print("Sent terminate command and closing connection")
s.close()