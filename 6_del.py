def coroutine(func):
    def inner(*args, **kwargs):
        g = func(*args, **kwargs)
        g.send(None)
        return g
    return inner


class CustomException(Exception):
    pass

# читающий генератор
# читает из какого то сокета, файла и т.д.
# @coroutine
def subgen():
    while True:
        try:
            message = yield
        except StopIteration:
            # print('Exception')
            break
        else:
            print('Message', message)
    return 'Returned from subgen()'


# транслятор
@coroutine
def delegator(g):
    # while True:
    #     try:
    #         data = yield
    #         # g - объекто подгенератора, который мы передаем в делигирующий генератор
    #         g.send(data)
    #     # сохранение объекта ошибки в переменную
    #     except CustomException as e:
    #         # проброс объекта ошибки в под-генератор
    #         g.throw(e)
    result = yield from g
    print(result)
