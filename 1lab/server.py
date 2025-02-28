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
JSON_NAME = 'data_server'


def get_action_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def reciver(s):
    package = s.recv(PACKAGE_LEN, socket.MSG_WAITALL)
    n = struct.unpack('!Q', package)[0]
    return 0 if n == 0 else s.recv(n, socket.MSG_WAITALL)


def sender(client, message):
    package = struct.pack('!Q', len(message)) + message
    sended_len = 0
    while sended_len < len(package):
        sended_len += client.send(package[sended_len:])


def converter(table):

    def create_file():
        with open(f'{JSON_NAME}.json', 'a') as f:
            f.write(json.dumps(table))

    if os.path.exists(f'{JSON_NAME}.json'):
        os.remove(f'{JSON_NAME}.json')
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

            command = reciver(conn)
            if command != 0:
                command = command.decode(FORMAT)

                if 'get tasklist' in command:
                    print(
                        f'[{get_action_time()}] executed the command: "get tasklist"')

                    if os.name == 'posix':
                        table = os.popen("ps").read()
                    else:
                        table = os.popen("tasklist").read()

                    converter(table)
                    sender(conn, table.encode(FORMAT))
                    sender(conn, b'')
                    
                # Не даёт права
                if 'kill' in command:
                    if os.name == 'posix':
                        pass
                    else:
                        pid = command.split()[1]
                        os.popen(f"taskkill /pid {pid}")
                        print(f"[{get_action_time()}] process killed: {pid}")

        conn.close()

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
