from socket import *
import sys

class Server():
    """A routing table engine server

    Handles update and query messages
    """

    def __init__(self, server_addr):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('', server_port))
        server_socket.listen(1)

        self.connection = None
        self.socket = server_socket

        self.router_table = {"0.0.0.0/0": ("A", 100)}

    def run(self):
        while True:
            self.connection, address = self.socket.accept()
            self.handle_request()
            self.connection.close()

    def handle_request(self):
        """Takes request message and checks for errors before sending"""
        byte_data = self.connection.recv(8192)
        msg_data = byte_data.decode()

        request_msg = msg_data.split("\r\n")

        if request_msg[0] == "UPDATE":
            for i in range(1, len(request_msg)-2):
                self.update_cmd(request_msg[i])

        if request_msg[0] == "QUERY":
            if len(request_msg) > 3:
                self.query_cmd(request_msg[1])
            else:
                response_msg = "RESULT" + "\r\n" + "END" + "\r\n"
                self.connection.send(response_msg.encode())

    def update_cmd(self, line):
        """Updates the routing table with new CIDR-netmasks"""

        line_items = line.split(" ")
        self.router_table[line_items[1]] = (line_items[0], int(line_items[2]))

        response_msg = "ACK" + "\r\n" + "END" + "\r\n"
        self.connection.send(response_msg.encode())

    def query_cmd(self, ip_query):
        """Finds the correct subnet to return"""
        subnet = "0.0.0.0/0"
        cost = 100
        prefix = 0
        # Sets subnet to the one with lowest cost that covers the same range
        # If same cost, prefer the longest prefix
        for key, val in self.router_table.items():
            subnet_list = key.rsplit("/", 1)
            addr_octets = subnet_list[0].split(".")
            cidr_prefix = int(subnet_list[1]) // 8

            query_octets = ip_query.split(".")

            query_matches = True
            for i in range(0, cidr_prefix):
                if addr_octets[i] != query_octets[i]:
                    query_matches = False
                    break

            if query_matches and key != "0.0.0.0/0":
                if val[1] < cost or val[1] == cost and cidr_prefix > prefix:
                    cost = val[1]
                    prefix = cidr_prefix
                    subnet = key

        body = ip_query + " " + \
                self.router_table[subnet][0] + " " + \
                str(self.router_table[subnet][1]) + "\r\n"
        response_msg = "RESULT" + "\r\n" + body + "END" + "\r\n"
        self.connection.send(response_msg.encode())


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        sys.exit("Error: Invalid number of arguments supplied.\n"
                 "Usage: python router-table.py [port]")
    else:
        server_port = int(sys.argv[1])

    print("Server listening on port {}... ".format(server_port))
    routingServer = Server(('', server_port))
    routingServer.run()
