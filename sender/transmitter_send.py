import socket

class Transmitter(object):
    
    def __init__(self, host, port, BUFFER_SIZE):
        self.host = "10.248.220.31"
        self.port = 5001
        self.BUFFER_SIZE = 1024
    
    def connect(self):
        connection = socket.socket()
        print("[-] Connecting...")
        connection.connect((self.host,self.port))
        print("[+] Connected")
        return connection
    
    def send(self, command):
        connection = self.connect()
        recv_data = ""
        data = True
        
        print("Sending: " + command)
        connection.sendall(command)

        while data:
            data = connection.recv(self.BUFFER_SIZE)
            
        connection.close()
        return recv_data
    
def main():
    connect = Transmitter()
    print(connect.send("STATUS"))
    print(connect.send("MEASURE"))

if __name__=='__main__':
    main()