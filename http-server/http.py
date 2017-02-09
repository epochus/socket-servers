from socket import *
import sys
from time import gmtime, strftime, strptime
import os.path


class Server():
    """A basic web server using sockets.

    Only supports the HTTP GET method requests in
    the form of HTML, text, or JPEG
    """

    def __init__(self, server_addr):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('', server_port))
        server_socket.listen(1)

        self.connection = None
        self.socket = server_socket

    def run(self):
        while True:
            self.connection, address = self.socket.accept()
            self._handle_request()
            self.connection.close()

    def _handle_request(self):
        """Takes request message and checks for errors before sending"""
        status = 200
        byte_data = self.connection.recv(8192)
        msg_data = byte_data.decode()
        if ("\r\n\r\n" not in msg_data):
            status = 400
        request_msg = msg_data.split("\r\n")

        # Checking for invalid requests
        modified_date = None
        has_host = False
        content_type = ""
        for i in range(len(request_msg)):
            if (request_msg[i].lower().startswith("if-modified-since: ")):
                modified_date = request_msg[i].split(":", 1)[1].strip()
            if (request_msg[i].lower().startswith("host: ")):
                has_host = True
            if (request_msg[i].lower().startswith("content-type: ")):
                content_type = request_msg[i].split(" ")[1]
        if (has_host is False):
            status = 400

        print("Content type:", content_type)

        # Error checking request line
        request_line = request_msg[0].split(" ")
        if (len(request_line) != 3):
            status = 400
        if (request_line[0] not in ["HEAD", "GET", "POST"]):
            status = 501
        if (request_line[2] != "HTTP/1.1"):
            status = 505

        file_ext = os.path.splitext(request_line[1])[1]
        filename = request_line[1][1:]
        content = ""

        if request_line[0] == "GET":
            (media_type, mode) = self._media_type(file_ext)
            if media_type:
                try:
                    inputfile = open(filename, mode)
                    content = inputfile.read()
                except OSError:
                    status = 404
                    filename = None
            else:
                status = 415
                filename = None
        if request_line[0] == "POST":
            if content_type not in ["application/x-www-form-urlencoded",
                    "multipart/form-data", "application/json"]:
                status = 415
                filename = None
            else:
                filename = request_line[1][1:]
                media_type = content_type
                content = ""


        request_info = [status, filename, media_type, modified_date]
        self._send_response(request_info, content)

    def _media_type(self, file_ext):
        media_types = {
                ".txt": ("text/plain", "r"),
                ".html": ("text/html", "r"),
                ".htm": ("text/html", "r"),
                ".jpeg": ("image/jpeg", "rb"),
                ".jpg": ("image/jpeg", "rb"),
                ".ico": ("image/png", "rb")
        }

        return media_types.get(file_ext, None)

    def _is_valid_date(self, timeStr):
        """Checks for invalid date format and a date later than current time"""

        date = None
        try:
            date = strptime(timeStr, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            try:
                date = strptime(timeStr)
            except ValueError:
                try:
                    date = strptime(timeStr, "%A, %d-%b-%y %H:%M:%S %Z")
                except ValueError:
                    date = None

        if (date is None or date > gmtime()):
            return False
        else:
            return True

    def _status_msg(self, status):
        """A dictionary mapping of status code to phrase"""

        phrase = {
            200: "OK",
            304: "Not Modified",
            404: "Not Found",
            415: "Unsupported Media Type",
            501: "Not Implemented",
            505: "HTTP Version Not Supported",
        }
        return phrase.get(status, "Bad Request")

    def _send_response(self, info, content):
        """Creates a response message to send

        Uses the status, filename, media type, and if-modified-since
        date to generate the appropriate response
        """

        connection_header = "Connection: close\r\n"
        date_time_now = strftime("%a, %d %b %Y %H:%M:%S " + "GMT", gmtime())
        date_header = "Date: " + date_time_now + "\r\n"
        server_header = "Server: Comet/1.0\r\n"

        # Check if object has been modified
        modified = False
        if (info[3] is not None):
            if (info[0] != 200):
                is_modified = True
            elif (self._is_valid_date(info[3]) is False):
                is_modified = True
                info[0] = 400
            if (modified is False):
                info[0] = 304
                content = ""

        status_line = "HTTP/1.1" + " " + str(info[0]) + " " + \
                self._status_msg(info[0]) + "\r\n"

        # Send for not modified
        if (info[0] == 304):
            response_msg = status_line + date_header + \
                    server_header + "\r\n"
            self.connection.sendall(response_msg.encode())
            return None

        # Send for error status codes
        if (info[0] != 200):
            content = ""
            response_msg = status_line + connection_header + \
                    date_header + server_header + \
                    "Last-Modified: \r\n" + "Content-Length: \r\n" + \
                    "Content-Type: \r\n" + "\r\n"
            if (info[0] == 505):
                content = "<!DOCTYPE html>\n<html>\n<head>\n" + \
                        "<title>505 HTTP Version Not Supported</title>\n" + \
                        "</head>\n<body>\nHTTP/1.1 Request Not Found\n" + \
                        "</body>\n<html>"

            self.connection.sendall((response_msg + content).encode())
            return None

        date_time_mod = strftime("%a, %d %b %Y %H:%M%S " + "GMT",
                gmtime(os.path.getmtime(info[1])))
        last_modified_header = "Last-Modified: " + date_time_mod + "\r\n"
        content_length_header = "Content-Length: " + \
            str(os.path.getsize(info[1])) + "\r\n"

        content_type_header = "Content-Type: " + info[2] + "\r\n"

        header_lines = connection_header + date_header + \
                server_header + last_modified_header + content_length_header + \
                content_type_header

        # Encode content with response message if content is not an image
        response_msg = status_line + header_lines + "\r\n"
        if (info[2] == "image/jpeg"):
            self.connection.sendall(response_msg.encode() + content)
        else:
            self.connection.sendall((response_msg + content).encode())


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        sys.exit("Error: Invalid number of arguments supplied.\n"
                 "Usage: python http.py [port]")
    else:
        server_port = int(sys.argv[1])

    print("Server listening on port {}... ".format(server_port))
    httpServer = Server(('', server_port))
    httpServer.run()
