# A simple test client
import sys
from socket import *

server_name = "localhost"
server_port = 12000

def run_client(server_port):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_name, server_port))
    
    sentence = "GET /primes-small.txt HTTP/1.0\r\nHost: something.edu\r\n" + \
    "Connection: close\r\nUser-agent: Mozilla\r\n" + \
    "2 3 5 7 11"

    print(sentence)
    client_socket.send(sentence.encode())
    
    response = client_socket.recv(2048)
    print("From Server: " + response.decode())
    
    client_socket.close()

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("Error: Invalid number of arguments entered. Must only have port number.")
        exit(0)
    else:
        server_port = int(sys.argv[1])

    run_client(server_port)
