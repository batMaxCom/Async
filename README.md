# Асинхронное программирование (корпоративная многозадачность)

В однопоточном запуске программы можно столкнутся с таким понятием как блокирующие операции.

Предположим, создается некоторый сокет, принимающий запросы от клиентов.

```python
import socket  
  
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
server_socket.bind(('localhost', 5000))  
server_socket.listen()  
  
def accept_connect(server_socket):  
    while True:  
        client_socket, addr = server_socket.accept()  
        print("Connection from", addr)  
        send_message(client_socket)  
  
def send_message(client_socket):  
    while True:  
        request = client_socket.recv(4096)  
  
        if not request:  
            break  
 else:  
            response = "Hello world\n".encode()  
            client_socket.send(response)  
    server_socket.close()  
  
if __name__ == '__main__':  
    accept_connect(server_socket)
```

В данном случае сокет блокирующей операцией при запуске будет .accept(), так как она ждет подключения со стороны клиента.

При подключении клиента это уже будет .recv(4096).

И пока клиент думает что бы ему написать и не выйдет из сессии, подключение со стороны второго, третьего и т.д. клиента не возможно, пока выполняется код для первого, так как он стоит на блокирующей операции.

## Передача контроля выполнения

### Событийный цикл (event loop)
Файловый дескриптор - своего рода номер исполняемого файла в системе. Любой процесс, устройство и т.д. в системе позиционируется как файл. Файловый дескриптор служит как его идентификатор в системе.

Сокет - это тоже файл.

`select` - системная функция, необходимая для мониторинга изменений состояния файловых дескрипторов. Соответственно, в нее также можно передать сокет.

Он принимает на вход 3 списка для отслеживания:
-  на чтение
- на запись
- на получение ошибок

Таким образом создается `контроль за выполнением событий (event loop)`.
Функции выведены в отдельные методы  и будут вызываться только при изменении состояния сокета.

```python
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
```
## Callback
```python
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
 # events - событие, которое нас интересует (EVENT_READ - встроенное события отслеживающее чтение) # data - любые связанные данные (например сессия)  selector.register(fileobj=server_socket, events=selectors.EVENT_READ, data=accept_connect)  
  
  
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
 # select - возвращает объекто из 2 кортежей (key, events) # key - обьект класса SelectorsKey имеющий все те же свойства, что и у регистрации (fileobj, events, data)  events = selector.select()  
        for key, _ in events:  
            # определяем метод при изменении дескрипторного файла в callback  
  callback = key.data  
            # исполняем, передавая сокет(клиентский или серверный, в зависимости от дескрипторного файла)  
  callback(key.fileobj)  
  
  
if __name__ == '__main__':  
    server()  
    event_loop()
```
## Генераторы и событийный цикл построенный по принципу Round Robin(карусель)

Генераторы - это функции. Есть ложное представление, что это списки, кортежи и т.д.

Функция генератор отдает не только свое значение, которое она сгенерировала, но и контроль выполнения программы и отдает его в то место, откуда была вызвана функция `next()`.

### Цикл Round Robin (пример с бассейном)
Предположим что существует пустой бассейн на вашем участке и заполненный водой на соседнем.

Необходимо перелить воду из чужого в наш. Для этого были приглашены люди, выстроены в очередь и розданы ведра.

Суть цикла **Round Robin (карусель)** в том, что первый зачерпнувший воду идет и выливает ее в пустой бассейн, а затем становится в конец очереди.
Очередь смещается, и вот уже первый человек идет в конец, а второй - становится первым и так до конца, пока бассейн не заполнится.

```python
def gen1(s):  
    for i in s:  
        yield i  
  
def gen2(n):  
    for i in range(n):  
        yield n  
          
g1 = gen1('string')  
g2 = gen2(6)  
  
tasks = [g1, g2]  
  
while tasks:  
    # берем первый элемент списка в task и удаляем его  
  task = tasks.pop(0)  
      
    try:  
        # производим итерацию к следующему элементу генератора  
  i = next(task)  
        print(i)  
        # возвращаем элемент списка в его конец  
  tasks.append(task)  
    # вызываем исключение, чтобы генератор не прерывался при окончании итерации генератора  
  except StopIteration:  
        pass
```

### Преобразование функций в генераторы
```python
import socket  
  
from select import select  
  
tasks = []  
to_read = {}  
to_write = {}  
  
  
def server():  
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
    server_socket.bind(('localhost', 5000))  
    server_socket.listen()  
  
    while True:  
  
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
 # если хоть один из них True, то any возвращает True # если словарь/список пустой, он интерпритируется как False  while any([tasks, to_read, to_write]):  
  
        # работает только в том случае, если tasks будет пустым  
  while not tasks:  
            ready_to_read, ready_to_write, _ = select(to_read, to_write, [])  
            for sock in ready_to_read:  
                tasks.append(to_read.pop(sock))  
            for sock in ready_to_write:  
                tasks.append(to_write.pop(sock))  
  
        try:  
            task = tasks.pop(0)  
  
            reason, sock = next(task)  
  
            if reason == 'read':  
                to_read[sock] = task  
            if reason == 'write':  
                to_write[sock] = task  
        except StopIteration:  
            print('Done')  
  
  
tasks.append(server())  
event_loop()
```

Генераторы возвращают кортежи, в которых:
1) Фильтрующий признак (read/write) 
2) Socket, фильтрующий признак которого определяет куда он пойдет (в какой из списков)
 
 #### Описать процесс для понимания

## Корутины и yield from

Корутины (coroutines), или сопрограммы — это блоки кода, которые работают асинхронно, то есть по очереди. В нужный момент исполнение такого блока приостанавливается с сохранением всех его свойств, чтобы запустился другой код. Когда управление возвращается к первому блоку, он продолжает работу. В результате программа выполняет несколько функций одновременно.

Корутины, по своей сути - генераторы, которые в процессе работы могут принимать извне какие либо данные. Делается с помощью метода `send()`
```python
def subgen():  
    message = yield  
	print(message)
```
После объявления генератора `subgen()` требуется его первичная инициализация. Для этого передается объект `None`. Это обязательное действие и оно предписано документацией.

При передачи любого другого значения в `message` выдаст ошибку, что в методе `send()` нельзя передавать ничего кроме `None`.

```python
>>> i = subgen()
>>> i.send(None)
```
Также можно посмотреть состояние генератора на данный момент
```python
from inspect import getgeneratorstate

getgeneratorstate(i)
>>> 'GET_CREATED' # новосозданный

i.send(None)
getgeneratorstate(i)
>>> 'GET_SUSPENDED' # приостановлен
```
После  передачи в методе `send()` тип `None` управление сместилось до следующего `yield`, точно так же как при работе с функцией `next()`.

```python
i.send('Hello') 
>>> Hello
>>> Traceback (most recent call last):
	File "<stdin>", line 1, in <module>
	StopIteration
```
`yield` принял сообщение `Hello` и передал его в `message` и после этого он был выведен в консоль(`print`)

### Логика
Сначала `yield` может отдавать нам какое то значение. 
Пример:
```python
def s():
	x = 'HI'  
    message = yield x  
    print(message)  
    yield 'Nice'

i = subgen()
i.send(None)
>>> HI
```
На самом деле, если ничего не объявить после yield, он неявно отдает нам `None`, но он не отображается в консоли.
Далее принимая какое то значение, он передает его в переменную `message`.
```python
i.send("Hello")
>>> Hello
```
Свое рода, операции в генераторе выполняются уголком:
1) все что идет до `yield`
2) сам все что находится после знака `=`
3) все остальное
```python
def s():
	x = 'HI'#1  
			     yield x #2  
    message # 3
    print(message)  
    yield 'Nice'
```

Для того, чтобы не инициализировать каждый раз генератор через `send(None)`, модно прописать инициализирующий декоратор

```python
def coroutine(func):  
    def inner(*args, **kwargs):  
        g = func(*args, **kwargs)  
        g.send(None)  
	    return g
    return inner
```


### Возвращаемое значение

Добавим возвращаемое значение 
```python
@coroutine  
def average():  
 count = 0  
 summ = 0  
 average = None  
  
 while True:  
        try:  
            ...
        except StopIteration:  
            ...  
            break  
...

  return average
```
В генератор можно забрасывать не только значения, которые будут обработаны, но и исключения (хоть стандартное, хоть кастомное). Делается с помощью метода `throw()`

```python
i.throw(StopIteration)
```
Также пробросить исключение можно в интерактивном режиме.

```python
g = average()
g.send(5)
>>> 5
g.send(6)
>>> 5.5
try:  
    g.throw()
except StopIteration as e:  
    print("Average", e.value)
>>> Average 5.5
```
В таком случае, пробрасывается исключение в функцию и сразу же оно обрабатывается. А функция `return` можно извлечь с помощью атрибута `exception.value`

## Делегирующий генератор и под-генератор

Делегирующий генератор - это тот генератор, который вызывает какой либо другой генератор, а вызываемый генератор называется под-генератор.

Такая конструкция необходима, когда требуется разбить один генератор на несколько.

Аналогично, когда мы из одних функций вызываем другие, однако нюанс в том

### Пример:
Существует читающий генератор (`subgen`), который читает из какого то сокета, файла и т.д.  
Есть транслятор (`delegator`). Транслирует значения из под-генератора.

```python
def subgen():  
    for i in 'string':  
        yield i  
  
def delegator(g):  
    for i in g:  
        yield i
```

Вызывающий код (`caller`)
```python
>>> sg = subgen()
>>> g = delegator(sg)
>>> g.next()
s
>>> g.next()
t
>>> g.next()
r
...
```
### Превращение генератора в `корутины`
Задача - из вызывающего кода передавать на обработку данные в под-генератор через делегирующий генератор.

```python
@coroutine  
def subgen():  
    while True:  
        try:  
            message = yield  
		 except:  
            pass  
		 else:  
            print('Message', message)  
  
@coroutine  
def delegator(g):  
    while True:  
        try:  
            data = yield  
			# g - объекто подгенератора, который мы передаем в делигирующий генератор  
			g.send(data)  
        except:  
            pass
```
В делегирующем генераторе перехватываем отсылаемые с помощью `send()` значения и передали их в под-генератор.
### Обработчик ошибок
Случается ситуация, когда, например, передается неверный формат данных. 
Цель теперь заключается в том, чтобы передать объект исключения в под-генератор.

Алгоритм:
- перехватываем исключение в делегирующем генераторе 
- сохраняем его в переменную
- перебрасываем с помощью throw() в под-генератор
```python
@coroutine  
def subgen():  
    while True:  
        try:  
            message = yield  
		 except CustomException:  
            print('Exception')  
        else:  
            print('Message', message)  
  
@coroutine  
def delegator(g):  
    while True:  
        try:  
            data = yield  
			g.send(data)  
		except CustomException as e:  
			g.throw(e)
```
Все это довольно объемный код. Его можно сократить используя конструкцию `yield from`.

### yield from (спецификация PEP 380) await - в других языках
`yield from` -  по спецификации уже располагает инициализацию под-генератора. 
Поэтому `@coroutine` в под-генераторе можно убрать. И генераторы будут выполнять те же функции.
```python
def subgen():  
    while True:  
        try:  
            message = yield  
		except CustomException:  
            print('Exception')  
        else:  
            print('Message', message)  
            
@coroutine  
def delegator(g):  
	yield from g
```
Тогда встает вопрос `зачем нужен делегирующий генератор, если все действия выполняются на стороне под-генератора?`


```python
def subgen():  
    while True:  
        try:  
            message = yield  
		except StopIteration:  
            print('Exception')  
        else:  
            print('Message', message)  
    return 'Returned from subgen()'  
  
def delegator(g):  
	result = yield from g  
    print(result)
```
Делегирующий генератор может обрабатывать возвращаемое значение из под-генератора.
```python
>>> s = subgen()           
>>> g = delegator(s)       
>>> g.throw(StopIteration)
Returned from subgen()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
StopIteration
```
Как пример среднего значения:

Делегирующий генератор мог не возвращать нам среднее значение каждый раз при добавлении нового, а накапливать и выдать только тогда, когда под-генератор закончил свою работу.
Так как делегирующий генератор сохраняет значение в переменную, его можно было бы обработать дополнительно при желании.

`yield from` не только заменяет цикл в делегирующем генераторе, который перебирает под-генератор она берет на себя:
- передачу данных в генератор
- передачу исключений
- получает с помощью `return` результат и обрабатывает его.

## Asyncio

Главный элемент любой асинхронной программы это событийный цикл (Event Loop), который является менеджером/планировщиком задач, который реагирует на какие либо внешние события.

`Asyncio` - модуль для создания событийных циклов.

В `Asyncio` корутины оборачиваются в объект класса `Task`, который является подклассов класса `Future`, который является своего рода заглушкой. У всех функций блокирующая природа, то есть контроль выполнения потоком программы никуда не перейдет пока функция не выдаст какой либо результат. Асинхронные функции используют класс-обертку Task, который и представляет собой результат ее работы.

Например:
Делаем запрос на сервер, а сервер никогда не отвечает сразу.
И пока функция не получит ответ от сервера она блокирует любые другие операции.
Асинхронная же функция выдает эту самую заглушку, чтобы можно было выполнять любое другое действие, пока сервер собирает данные, формирует и отдает ответ. 

Поскольку экземпляры класса Task это объекты их можно помещать в очередь на выполнение, опрашивать на предмет того, выполнилась ли связанная с этим объектом Task корутина или нет, был получен результат или исключение и т.д.

Принцип работы:
Событийный цикл берет из очереди первую задачу Task, у ассоциированной с этим классом корутиной вызывается метод `step()` и корутина выполняет свой код. Если корутина вызывает какую либо блокирующую функцию, то контроль возвращается в событийный цикл. Затем он берет следующую задачу из очереди и так далее по кругу. Она доходит до первого элемента очереди и она возобновляет работу с того момента, где закончила работу в прошлый раз.

Действия:
1) Оборачиваем функции в экземпляр класса Task
2) Добавляем их в очередь на выполнение
3) Запускаем событийный цикл
4) Ожидаем результата и закрываем событийный цикл

Asyncio берет на себя функцию создания событийного цикла, поэтому приписывать его вручную не требуется. Тоже самое касается создания корутин, помещения в очередь и т.д.

```python
import asyncio  
  
  
async def print_nums():  
    num = 1  
  while True:  
        print(num)  
        num += 1
  # await заменяет yield from
  await asyncio.sleep(1)  
  
  
async def print_time():  
    count = 0  
  while True:  
        if count % 3 == 0:  
            print("{} seconds have pass".format(count))  
        count += 1  
  await asyncio.sleep(1)  
  
  
async def main():  
    # оборачиваем корутины в объект класса Task  
  task1 = asyncio.create_task(print_nums())  
  task2 = asyncio.create_task(print_time())  
  # генератор, событийный цикл, куда поочередно помещаются корутины (очередь задач)
  await asyncio.gather(task1, task2)  
  
  
if __name__ == "__main__":
	# запуск событийного цикла  
    asyncio.run(main())
```

### Асинхронный код, на примере скачивания картинок

Asyncio предоставляет API для работы с протоколами TCP и  UDP, но для работы с HTTP api у него нет. 
Для этого существует библиотека `aiohttp`
```bash
pip install aiohttp
```
С ее помощью взаимодействуем с ресурсом.
Документация `aiohttp`, предполагает работать в контексте сессии.
```python
import asyncio  
from time import time  
import aiohttp  

async def fetch_connect(url, session):  
    async with session.get(url, allow_redirects=True) as response:  
      write_image(data)  
```
Где `write_image()` - синхронная функция записи картинки (бинарных данных) в файл
Обычно смешивать синхронный и асинхронный код плохая практика, так как синхронная функция в какой либо момент может стать блокирующей.
```python
def write_image(data):  
    filename = 'file-{}.jpeg'.format(int(time() * 1000))  
	with open(filename, 'wb') as file:  
	      file.write(data)  
```
Для работы определяем вызывающий код.

Создаем контейнер для хранения корутин (`tasks`), чтобы не выполнять каждую операцию поочередно в цикле.

Цикл необходим только для того, чтобы  обернуть их классом Task и поместить их в контейнер.

`create_task` - оборачиваем корутину классом Task.
`gather()` - помещаем контейнер с корутинами в событийный цикл
`asyncio.run()` - запускаем событийный цикл

```python
async def main():  
    url = 'https://url-example.com' 
    async with aiohttp.ClientSession as session:  
        for i in range(10):  
			task = asyncio.create_task(fetch_connect(url, session))  
	        tasks.append(task) 
	    await asyncio.gather(*tasks)  
  
  
if __name__ == "__main__":  
    t0 = time()  
    asyncio.run(main())  
    print(time() - t0)
```
