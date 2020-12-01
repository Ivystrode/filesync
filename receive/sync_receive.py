# SERVER SIDE

import socket
import tqdm
import os

# device's ip address
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001

#receive 4096 bytes each time
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

# create the server socket
# TCP socket
s = socket.socket()

# bind the socket to our local address
s.bind((SERVER_HOST, SERVER_PORT))

# enabling our server to accept connections
# 5 here is the number of unaccepted connections the system will allow
# before refusing new connections

s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

# accept connection if there is any
client_socket, address = s.accept()
# if below code is executed, that means sender is connected
print(f"[+] {address} connected!!")


# receive file information
# receive using client socket, not server socket
received = client_socket.recv(BUFFER_SIZE).decode()
filename, filesize = received.split(SEPARATOR)
# remove the absolute path if there is - may not have to do this for the sync but should check and figure out how to ensure we get the same folder/file tree
filename = os.path.basename(filename)
# convert to integer
filesize = int(filesize)

# start receiving the file from the socket
# and writing to the file stream
progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
with open(filename, "wb") as f: # note different read/write mode!!!
    for _ in progress:
        # read 1024 bytes from the socket (receive)
        bytes_read = client_socket.recv(BUFFER_SIZE)
        if not bytes_read:
            # nothing is received
            # file transmitting is done
            break
        # write to the file the bytes we just received
        f.write(bytes_read)
        # update progress bar
        progress.update(len(bytes_read))

    # close the client socket
    client_socket.close()
    # close the server socket
    s.close()