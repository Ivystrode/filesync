import socket

class Receiver(object):
    
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 5001
        self.BUFFER_SIZE = 1024
        
        self.connection = socket.socket()
        self.connection.bind((self.host,self.port))

    def listen(self):
        while True:
            connection, client_address = self.connection.accept()
            print("Client connected")
            
            try:
                data=connection.recv(self.BUFFER_SIZE).decode()
                print(data)
            except Exception as e:
                print("Error" + " " + e)
                
def main():
    connect = Receiver()
    connect.listen()
    
if __name__=='__main__':
    main()