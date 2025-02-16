# это сервер
# ----------
import socket
import os
import time

def main():
    server = socket.socket()
    server.bind(('', 9090))
    server.listen(1)
    conn, addr = server.accept()
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}] connected: {addr}')

    try:
        while True:
            command = conn.recv(1024).decode('utf-8')

            if 'get tasklist' in command:
                print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}] executed the command: "get tasklist"')
                conn.send(os.popen("tasklist").read().encode('utf-8'))

            if not command:
                break
    except Exception as e:
        print(e)
        input()

    conn.close()

if __name__ == "__main__":
    main()


