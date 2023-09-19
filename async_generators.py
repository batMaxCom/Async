import socket

from select import select

tasks = []
# словарь, на мониторинг за чтением
to_read = {}
# словарь, на мониторинг за записью
to_write = {}


def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 5000))
    server_socket.listen()

    while True:
        # read - фильтрующий признак, определяющий в какой из списков (to_read/to_write) пойдет socket
        yield ('read', server_socket)
        client_socket, addr = server_socket.accept() # read

        print("Connection from", addr)

        tasks.append(client(client_socket))


def client(client_socket):
    while True:

        yield ('read', client_socket)
        request = client_socket.recv(4096) # read

        if not request:
            break
        else:
            response = "Hello world\n".encode()

            yield ('write', client_socket)
            client_socket.send(response) # write

    client_socket.close()


def event_loop():
    # функция any принимает список каких то значений, кажое из которых должно даать либо False, либо True
    # если хоть один из них True, то any возвращает True
    # если словарь/список пустой, он интерпритируется как False
    while any([tasks, to_read, to_write]):

        # работает только в том случае, если tasks будет пустым
        while not tasks:
            ready_to_read, ready_to_write, _ = select(to_read, to_write, [])
            for sock in ready_to_read:
                tasks.append(to_read.pop(sock))
            for sock in ready_to_write:
                tasks.append(to_write.pop(sock))
        # работает, пока список tasks чем то наполнен,
        # для этого подкармливаем его циклом while not tasks
        # который отслеживает изменения в мониторинговых словарях и обеспечивает список новыми элементами
        try:
            # на первом проходе берет server и ждет событий
            task = tasks.pop(0)
            # получаем кортеж события
            reason, sock = next(task)
            # обрабатываем событие, в зависимости от его признака
            # и добавляем в один из словарей на мониторинг
            if reason == 'read':
                to_read[sock] = task
            if reason == 'write':
                to_write[sock] = task
        except StopIteration:
            print('Done')


# добавляем в событийный список сервер для его запуска и прослушивания
tasks.append(server())
event_loop()
