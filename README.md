# Class Notes for "CPython internals: A ten-hour codewalk through the Python interpreter source code"

Class link: http://pgbovine.net/cpython-internals.htm

# Lecture 2 - Opcodes and main interpreter loop

Focusing on two files:
1. /include/opcode.h
1. /Python/ceval.c

## Opcodes

Our testing module:

```python
# test.py
x = 1
y = 2
z = x + y
print z
```

Built-in function: `compile`

```python
c = compile('test.py', 'test.py', 'exec')
# <code object <module> at 0x..., file "test.py", line 1>

c.co_code
# 'e\x00\x00j\x01\x00\x01d\x00\x00S'

[byte for byte in c.co_code]
# ['e', '\x00', '\x00', 'j', '\x01', '\x00', '\x01', 'd', '\x00', '\x00', 'S']

# ascii code for each byte
[ord(byte) for byte in c.co_code]
# [101, 0, 0, 106, 1, 0, 1, 100, 0, 0, 83]
```

Disassemble python code: `$ python -m dis test.py`
```
  1           0 LOAD_CONST               0 (1)
              3 STORE_NAME               0 (x)

  2           6 LOAD_CONST               1 (2)
              9 STORE_NAME               1 (y)

  3          12 LOAD_NAME                0 (x)
             15 LOAD_NAME                1 (y)
             18 BINARY_ADD
             19 STORE_NAME               2 (z)

  4          22 LOAD_NAME                2 (z)
             25 PRINT_ITEM
             26 PRINT_NEWLINE
             27 LOAD_CONST               2 (None)
             30 RETURN_VALUE
```
> The standard library module `dis` can be found at `/Python-2.7.8/Lib/dis.py`.

The byte code is mapped to the disassembled code, somehow, with some
optimization. The disassembler knows how to read the byte code.

The format for the disassmbled code is:
```
LINE_NUMBER -> BYTE_OFFSET OP_CODE -> INTERNAL_BOOK_KEEPING_STUFF ARGUMENT
```

Let's look at `opcode.h`
```c
#define LOAD_CONST	100	/* Index in const list */
```

> Any opcode above 90 takes an argument
```c
> #define HAVE_ARGUMENT	90	/* Opcodes from here have an argument: */
```

`x` is stored in to the 0th variable name in `3 STORE_NAME 0 (x)`

> `byteplay` is a module which lets you easily play with Python bytecode.

Python virtual machine is a "Stack Machine." When a const is loaded by 
calling `LOAD_CONST`, the
value is pushed onto the "Value Stack." When the `STORE_NAME` is called,
the last value on the Value Stack is popped and saved in the memory
associated with the variable name, `x` for example.

`LOAD_NAME` pushes whatever value the variable name is associated with
on top of the Value Stack. (Only the reference of the value is pushed.
So now the value has the Reference Counting of 2. One from the variable
name, another from the Value Stack.)

`BINARY_ADD` pops the two values from the Value Stack and pushs the
result on top of the Value Stack again. 

> `PRINT_ITEM` is a primitive operation in legacy Python (Python 2)

For completeness, the module returns a `None` value.

## Main Interpreter Loop

From `ceval.c` line 693 to line 3021, this is the main interpreter loop:

```c
PyObject *
PyEval_EvalFrameEx(PyFrameObject *f, int throwflag)
{
...
} // line 3021
```

* Everything in Python is an object, an `PyObject`.
* A `PyFrameObject` is a piece of code.

Inside the main interpreter loop:
* `PyObject **stack_pointer` is a list of pointers to the Value Stack.
It points to the Next free slot in value stack.

> `#define` is Macro in C. For example `#define LOAD_CONST 100`. This macro
means to replace every occurrence of `LOAD_CONST` with `100`.
