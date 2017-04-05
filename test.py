x = 1000

def foo(x):
    def bar(y):
        print x + y
    return bar

b = foo(10)
c = foo(20)