# это сервер
# ----------
import socket
import os
import time

def converter(table):
    table_text = str(table)
    rows = list()
    for item in table_text.split('\n'):
        rows.append(item.split())
    json_table = {'procesess':dict()}
    for i in range(len(rows[0])):
        pass

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
                if os.name == 'posix':
                    table = os.popen("ps").read()
                    converter(table)
                    conn.send(table.encode('utf-8'))
                else:
                    table = os.popen("tasklist").read()
                    converter(table)
                    conn.send(table.encode('utf-8'))

            if not command:
                break
            
        conn.close()
    except Exception as e:
        print(e)
        input()


if __name__ == "__main__":
    main()


