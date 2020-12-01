# CLIENT SIDE
# SUCCESS - when sending to raspberry pi on SSG VPN

import socket
import tqdm
import os

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096

# ip address or hostname of server (the receiver)
# host = "192.168.0.16" # for raspberry pi
host = "10.248.220.31"
# port
port = 5001 # pick the right port for OMV or whatever the pi ends up being on

# for testing - name of file to send
filename = "sendthis/sendmefromfolder.txt"
# get file size
filesize = os.path.getsize(filename)
# getting file path...
# the root path
root_path = os.getcwd()
print(f"Root path: {root_path}")

s = socket.socket()

# connect to the server
print(f"[+] Connecting to: {host}:{port}")
s.connect((host,port))
print("[+] connected")

# eventually the below will be in a for loop or as a function...

# send filename and filesize
s.send(f"{filename}{SEPARATOR}{filesize}".encode()) # encode function encodes it to utf-8 which we need to do
print(f"{filename}{SEPARATOR}{filesize}")

# start sending the file
progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)

with open(filename, "rb") as f:
    for _ in progress:
        # read the bytes from the file
        bytes_read = f.read(BUFFER_SIZE)
        if not bytes_read:
            # file transmitting is done!
            break
        # we use sendall to assure transmission in busy networks
        s.sendall(bytes_read)
        # update the progress bar
        progress.update(len(bytes_read))
    # close the socket
    s.close()