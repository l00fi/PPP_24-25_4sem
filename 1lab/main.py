# main.py будет клиентом, который обращается к server.py
#-------------------------------------------------------
import socket
import os
import readline
import json
import struct

NAME = 'localhost'
PORT = 9090
FORMAT = 'utf-8'
PACKAGE_LEN = 8
COMMANDS = {
    "get tasklist": "Выводит список процессов исполняемых на сервере",
    "exit": "Прерывает соединение с сервером",
    "cls": "Очистить консоль"
}

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

def completer(inp, state):
    options = [command for command in COMMANDS if command.startswith(inp)]
    return options[state] if state < len(options) else None

def client_command_input(client_socket):
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    message = input(f'{NAME}~ ')

    if message == 'help':

        for command in COMMANDS:
            print(f"{command} | {COMMANDS[command]}")
        return 'inner command'
    
    elif message == 'exit':

        return False
    
    elif message == 'cls':

        if os.name == 'posix':
            os.system('clear')
        else:    
            os.system('cls')
        return 'inner command'
    
    elif message == 'get tasklist':
        
        sender(client_socket, message)
        # client_socket.send(message.encode(FORMAT))
        return 'outter command'
    
    else:
        print("Error! Command does not exist")

def main():
    client = socket.socket()
    client.connect((NAME, PORT))

    try:
        while True:
            client_status = client_command_input(client)
            while client_status != 'recived' and client_status is not False:
                if client_status == 'outter command':
                    data = reciver(client)
                    if data == 0:
                        client_status = 'recived'
                    with open('data_client.json', 'a') as f:
                        f.write(json.dumps(data))
                    print(data)
            if client_status == False:
                break
        client.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()

