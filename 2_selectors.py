import socket
# более совершенный модуль select
import selectors


selector = selectors.DefaultSelector()


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 5000))
    server_socket.listen()
    # fileobj - файл, имеющий дескриптовый номер для отслеживания
    # events - событие, которое нас интересует (EVENT_READ - встроенное события отслеживающее чтение)
    # data - любые связанные данные (например сессия)
    selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=accept_connect)


# создание клиентского сокета
def accept_connect(server_socket):
    client_socket, addr = server_socket.accept()
    print("Connection from", addr)
    selector.register(fileobj=client_socket, events=selectors.EVENT_READ, data=send_message)


def send_message(client_socket):
    request = client_socket.recv(4096)

    if request:
        response = "Hello world\n".encode()
        client_socket.send(response)
    else:
        # перед закрытие сокета необходимо отслеживаемый файл снять с регистрации
        selector.unregister(client_socket)
        client_socket.close()


def event_loop():
    while True:
        # делаем выборку объектов, готовых для чтения или записи
        # select - возвращает объекто из 2 кортежей (key, events)
        # key - обьект класса SelectorsKey имеющий все те же свойства, что и у регистрации (fileobj, events, data)
        events = selector.select()
        for key, _ in events:
            # определяем метод при изменении дескрипторного файла в callback
            callback = key.data
            # исполняем, передавая сокет(клиентский или серверный, в зависимости от дескрипторного файла)
            callback(key.fileobj)


if __name__ == '__main__':
    server()
    event_loop()
