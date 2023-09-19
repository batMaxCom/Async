import socket
from select import select

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('localhost', 5000))
server_socket.listen()

to_monitor = []


# создание клиентского сокета
def accept_connect(server_socket):
    client_socket, addr = server_socket.accept()
    print("Connection from", addr)
    to_monitor.append(client_socket)


def send_message(client_socket):
    request = client_socket.recv(4096)

    if not request:
        response = "Hello world\n".encode()
        client_socket.send(response)
    else:
        server_socket.close()


# событийный цикл
def event_loop():
    while True:
        # select делает выборку на предмет того, готов ли обьект для чтения/записи или нет
        ready_to_read, _, _ = select(to_monitor, [], [])

        for sock in ready_to_read:
            # если это серверный сокет, то передаем функцию на подключение
            if sock is server_socket:
                accept_connect(sock)
            #  если это клиентский сокет, то передаем функцию на отправку сообщения
            else:
                send_message(sock)


if __name__ == '__main__':
    to_monitor.append(server_socket)
    event_loop()
