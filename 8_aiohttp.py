import asyncio
from time import time

import aiohttp

# функция синхронная, так как модуль asyncio
# не предоставляет функционала для работы с записью объектов
def write_image(data):
    filename = 'file-{}.jpeg'.format(int(time() * 1000))
    # wb - запись бинарных данных
    with open(filename, 'wb') as file:
        file.write(data)


# функция(корутина), которая делает запрос на сервер
# документация aiohttp, предполагает работать в контексте сессии
async def fetch_connect(url, session):
    async with session.get(url, allow_redirects=True) as response:
        # read - возвращает бинакрые данные (например картинку)
        # так как мы работаем с асинхронными обьектами(генераторы, корутины и т.д.) используется await для вызова из событийного цикла
        data = await response.read()
        # обычно смешивать синхронный и асинхронный код плохая практика
        # так как синхронная функция в какой либо момент может стать блокирующей
        write_image(data)


async def main():
    url = 'https://url-example.com'

    # контейнер для хранения корутин, чтобы не выполнять каждую в цикле,
    # а только обернуть их классом Task и поместить в контейнер
    tasks = []
    # создать сессию (ClientSession)
    async with aiohttp.ClientSession as session:
        for i in range(10):
            # оборачиваем корутину классом Task
            task = asyncio.create_task(fetch_connect(url, session))
            tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    t0 = time()
    # запуск событийного цикла
    asyncio.run(main())
    print(time() - t0)
