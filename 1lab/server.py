# это сервер
# ----------
import socket
import os
import time
import json
import struct

PORT = 9090
FORMAT = 'utf-8'
PACKAGE_LEN = 8

def get_action_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def reciver(client_socket):
    package = client_socket.recv(PACKAGE_LEN)
    # print(package)
    n = struct.unpack('!Q', package)[0]
    return 0 if n == 0 else package

def sender(client, message):
    message = message.encode(FORMAT)
    package = struct.pack('!Q', len(message)) + message
    sended_len = 0
    while sended_len < len(package):
        sended_len += client.send(package[sended_len:])


def converter(table):

    def create_file():
        with open('data_server.json', 'a') as f:
            f.write(json.dumps(table))
    
    if os.path.exists('data_server.json'):
        os.remove('data_server.json')
        create_file()
    else:
        create_file()


def main():
    server = socket.socket()
    server.bind(('', PORT))
    server.listen(1)

    conn, addr = server.accept()
    print(f'[{get_action_time()}] connected: {addr}')

    try:

        while True:

            command = reciver(server) # conn.recv(PACKAGE_LEN).decode(FORMAT)

            if 'get tasklist' in command:
                print(f'[{get_action_time()}] executed the command: "get tasklist"')

                if os.name == 'posix':
                    table = os.popen("ps").read()
                else:
                    table = os.popen("tasklist").read()

                converter(table)
                sender(conn, table)

            if not command:
                break
            
        conn.close()

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()


