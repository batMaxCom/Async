# принимает какую либо функцию
def coroutine(func):
    # инициализация этой функции
    # принимает позиционные аргументы и именнованные
    def inner(*args, **kwargs):
        g = func(*args, **kwargs)
        g.send(None)
        # возвращает инициализированный объект генератора
        return g
    # возвращает, уже инициализированную функцию
    return inner


def s():
    message = yield 'HI'
    print(message)

@coroutine
def average():
    count = 0
    summ = 0
    average = None

    while True:
        try:
            # 1 - возвращает значение average (изначально None)
            # 2 - принимает значение из send()
            # 3 - проходит цикл и возвращается к yield, где уже возвращает новое, высчитанное значение average
            x = yield average
        except StopIteration:
            print('Done')
            break
        else:
            # увеличение количества, после каждого цикла итерации
            count += 1
            # увеличение суммы на новое число
            summ += x
            # round - округлять число с плавающей точкой до той цифры после запятой,
            # которая указана вторым аргументом
            average = round(summ/count, 2)
    # после выхода из блока while контроль передается функции и она возвращает конечное значение
    # получить его можно только с помощью вызова исключения и извленеия из него атрибута - exception.value
    return average