# CLIENT SIDE
# SUCCESS - when sending to raspberry pi on SSG VPN

import socket
import tqdm
import os

        


SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096

# host = "192.168.0.16" # for raspberry pi
host = "10.248.220.31"
# port
port = 5001 

# for testing - name of file to send

# print(f"Root path: {root_path}")

s = socket.socket()

print(f"[+] Connecting to: {host}:{port}")
s.connect((host,port))
print("[+] connected")
s.send("77".encode(encoding="ISO-8859-1"))

for file in os.listdir('sendthis'):
    filename = 'sendthis/' + file
    filesize = os.path.getsize(filename)
    # root_path = os.getcwd()

    s.send(f"{filename}{SEPARATOR}{filesize}".encode())
    print(f"{filename}{SEPARATOR}{filesize}")

    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "rb") as f:
        for _ in progress:
            bytes_read = f.read(BUFFER_SIZE)
            
            if not bytes_read:
                break
            
            s.sendall(bytes_read)
            progress.update(len(bytes_read))
        print("File sent: " + filename)
            
# s.send("FINISHSEND".encode())
s.close()