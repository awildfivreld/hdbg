def f(x):
    return x*3

f(3)


def g(x, y):
    return x*f(y)


print(g(3, 4))