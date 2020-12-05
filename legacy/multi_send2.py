# CLIENT SIDE
# SUCCESS - when sending to raspberry pi on SSG VPN

import socket
import tqdm
import time
import os

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096

# host = "192.168.0.16" # for raspberry pi
host = "10.248.220.31"
port = 5001 

def sendfile(file):
    s = socket.socket()

    print(f"[+] Connecting to: {host}:{port}")
    s.connect((host,port))
    print("[+] connected\n")
    
    filename = 'sendthis/' + file
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

# Using time.sleep is a very hacky way to achieve this, but...it works...
for file in os.listdir('sendthis'):
    try:
        print("\nSENDING FIRST TRY\n")
        sendfile(file)
    except:
        print("\nNot sent, will retry...\n")
        for interval in range(1,300):
            print(f"\n{str(interval)} second interval\n")
            try:
                print(f"\nConnection busy, retrying in {str(interval)} seconds...\n")
                time.sleep(interval)
                sendfile(file)
                break
            except:
                print("\nSENDING - PASS\n")
                pass
    time.sleep(0.5)

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