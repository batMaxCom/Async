
"""
Генераторы
"""


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
    # берем первый элемент списка в переменную task и удаляем его
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
