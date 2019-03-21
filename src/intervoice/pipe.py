import socket
import sys

while True:
    # Create a UDS socket
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = "/tmp/intervoice/sock"
    print("connecting to {}".format(server_address))
    try:
        sock.connect(server_address)
    except socket.error as msg:
        print(msg)
        sys.exit(1)

    try:

        # Send data
        message = sys.stdin.buffer.readline()
        print("sending {!r}".format(message))
        sock.sendall(message)

    finally:
        print("closing socket")
        sock.close()
