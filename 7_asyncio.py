import asyncio


async def print_nums():
    num = 1
    while True:
        print(num)
        num += 1
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
    # генератор, событийный цикл, куда поочередно помещаются корутины
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    asyncio.run(main())
