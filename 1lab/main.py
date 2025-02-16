# main.py будет клиентом, который обращается к server.py
#-------------------------------------------------------
import socket
import os
import readline

NAME = 'localhost'
COMMANDS = {
    "get tasklist": "Выводит список процессов исполняемых на сервере",
    "exit": "Прерывает соединение с сервером",
    "cls": "Очистить консоль"
}

def print_info(text=''):
    print(f'{NAME}~ ', end=text)

# def completer(inp, state):
#     _, _, inp = inp.partition("~ ")
#     options = [command for command in COMMANDS if command.startswith(inp)]
#     return options[state] if state < len(options) else None

def client_command_input(client_socket):
    # readline.set_completer(completer)
    # readline.parse_and_bind("tab: complete")

    print_info()
    message = input()

    if message == 'help':
        for command in COMMANDS:
            print(f"{command} | {COMMANDS[command]}")
        return 'inner command'
    elif message == 'exit':
        return False
    elif message == 'cls':
        os.system('cls')
        return 'inner command'
    else:
        client_socket.send(message.encode('utf-8'))
        return 'outter command'

def main():
    client = socket.socket()
    client.connect((NAME, 9090))

    try:
        client_status = True
        while client_status is not False:
            client_status = client_command_input(client_socket=client)
            if client_status == 'outter command':
                data = client.recv(1024)
                print(data.decode('utf-8'))
    except Exception as e:
        print(e)
        input()

    client.close()

if __name__ == "__main__":
    main()

