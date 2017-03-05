# Class Notes for "CPython internals: A ten-hour codewalk through the Python interpreter source code"

Class link: http://pgbovine.net/cpython-internals.htm

# Lecture 1 - Interpreter and Source Code Overview

```
source code   |                (C)Python                   |       output
              |                                            |
  test.py     --->  compiler -> [bytecode] -> interpreter  ---> 'Hello World!'
                                    ^                                ^
                                    |                                |
                                    |                                |
                                    ----------------------------------
                                        This is more interesting
```

## Python sourcecode tree

Main subdirectories:
1. `Include/` - all the .h files
1. `Objects/` - all the .c files representing python objects
1. `Python/` - the main runtime

Other subdirectories:
1. `Modules/` - built-in modules implemented in C
1. `Libs/` - standard libraries implemented in Python

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

The format for the disassembled code is:
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

Line 964, Infinite loop to go through the byte code:
```c
    for (;;) {
        ...
```

Line 1078, extract opcode:
```c
        /* Extract opcode and argument */

        opcode = NEXTOP();
        oparg = 0;   /* allows oparg to be stored in a register because
            it doesn't have to be remembered across a full loop */
```

Line 1112, GIANT switch case:
```c
        switch (opcode) {
            ...
```

Line 2959, breaking out of the main loop:
```c
        if (why != WHY_NOT)
            break;
        READ_TIMESTAMP(loop1);

    } /* main loop */
```

Line 3020, return retval
```c
    return retval;
}
```

# Lecture 3 - Frames, function calls, and scope

```python
# test.py

x = 10

def foo(x):
    y = x * 2
    return bar(y)

def bar(x):
    y = x / 2
    return y

z = foo(x)
```

`python -m dis test.py`

```
  1           0 LOAD_CONST               0 (10)
              3 STORE_NAME               0 (x)

  3           6 LOAD_CONST               1 (<code object foo at 0x1004b1eb0, file "test.py", line 3>)
              9 MAKE_FUNCTION            0
             12 STORE_NAME               1 (foo)

  7          15 LOAD_CONST               2 (<code object bar at 0x1004b1f30, file "test.py", line 7>)
             18 MAKE_FUNCTION            0
             21 STORE_NAME               2 (bar)

 11          24 LOAD_NAME                1 (foo)
             27 LOAD_NAME                0 (x)
             30 CALL_FUNCTION            1
             33 STORE_NAME               3 (z)
             36 LOAD_CONST               3 (None)
             39 RETURN_VALUE
```

All Python codes are precompiled but not bounded until runtime.
A __code object__ is immutable, is just a blob of codes inside
the function definition. Besides a __code object__, a __function object__
also contains a pointer to its environment, or __closure__.

```
# import dis
# import test
# dis.dis(test.foo)
  4           0 LOAD_FAST                0 (x)
              3 LOAD_CONST               1 (2)
              6 BINARY_MULTIPLY
              7 STORE_FAST               1 (y)

  5          10 LOAD_GLOBAL              0 (bar)
             13 LOAD_FAST                1 (y)
             16 CALL_FUNCTION            1
             19 RETURN_VALUE
# dis.dis(test.bar)
  8           0 LOAD_FAST                0 (x)
              3 LOAD_CONST               1 (2)
              6 BINARY_DIVIDE
              7 STORE_FAST               1 (y)

  9          10 LOAD_FAST                1 (y)
             13 RETURN_VALUE
```

Or just call `dis.dis(test)`

```
# dis.dis(test)
Disassembly of bar:
  8           0 LOAD_FAST                0 (x)
              3 LOAD_CONST               1 (2)
              6 BINARY_DIVIDE
              7 STORE_FAST               1 (y)

  9          10 LOAD_FAST                1 (y)
             13 RETURN_VALUE

Disassembly of foo:
  4           0 LOAD_FAST                0 (x)
              3 LOAD_CONST               1 (2)
              6 BINARY_MULTIPLY
              7 STORE_FAST               1 (y)

  5          10 LOAD_GLOBAL              0 (bar)
             13 LOAD_FAST                1 (y)
             16 CALL_FUNCTION            1
             19 RETURN_VALUE
```

In `/Include/code.h`

```c
/* Bytecode object */
typedef struct {
    PyObject_HEAD
    int co_argcount;		/* #arguments, except *args */
    int co_nlocals;		/* #local variables */
    int co_stacksize;		/* #entries needed for evaluation stack */
    int co_flags;		/* CO_..., see below */
    PyObject *co_code;		/* instruction opcodes */
    PyObject *co_consts;	/* list (constants used) */
    PyObject *co_names;		/* list of strings (names used) */
    PyObject *co_varnames;	/* tuple of strings (local variable names) */
    PyObject *co_freevars;	/* tuple of strings (free variable names) */
    PyObject *co_cellvars;      /* tuple of strings (cell variable names) */
    /* The rest doesn't count for hash/cmp */
    PyObject *co_filename;	/* string (where it was loaded from) */
    PyObject *co_name;		/* string (name, for reference) */
    int co_firstlineno;		/* first source line number */
    PyObject *co_lnotab;	/* string (encoding addr<->lineno mapping) See
				   Objects/lnotab_notes.txt for details. */
    void *co_zombieframe;     /* for optimization only (see frameobject.c) */
    PyObject *co_weakreflist;   /* to support weakrefs to code objects */
} PyCodeObject;
```

And `/Include/frameobject.h`

```c
typedef struct _frame {
    PyObject_VAR_HEAD
    struct _frame *f_back;	/* previous frame, or NULL */
    PyCodeObject *f_code;	/* code segment */
    PyObject *f_builtins;	/* builtin symbol table (PyDictObject) */
    PyObject *f_globals;	/* global symbol table (PyDictObject) */
    PyObject *f_locals;		/* local symbol table (any mapping) */
    PyObject **f_valuestack;	/* points after the last local */
    /* Next free slot in f_valuestack.  Frame creation sets to f_valuestack.
       Frame evaluation usually NULLs it, but a frame that yields sets it
       to the current stack top. */
    PyObject **f_stacktop;
    PyObject *f_trace;		/* Trace function */

    /* If an exception is raised in this frame, the next three are used to
     * record the exception info (if any) originally in the thread state.  See
     * comments before set_exc_info() -- it's not obvious.
     * Invariant:  if _type is NULL, then so are _value and _traceback.
     * Desired invariant:  all three are NULL, or all three are non-NULL.  That
     * one isn't currently true, but "should be".
     */
    PyObject *f_exc_type, *f_exc_value, *f_exc_traceback;

    PyThreadState *f_tstate;
    int f_lasti;		/* Last instruction if called */
    /* Call PyFrame_GetLineNumber() instead of reading this field
       directly.  As of 2.3 f_lineno is only valid when tracing is
       active (i.e. when f_trace is set).  At other times we use
       PyCode_Addr2Line to calculate the line from the current
       bytecode index. */
    int f_lineno;		/* Current line number */
    int f_iblock;		/* index in f_blockstack */
    PyTryBlock f_blockstack[CO_MAXBLOCKS]; /* for try and loop blocks */
    PyObject *f_localsplus[1];	/* locals+stack, dynamically sized */
} PyFrameObject;
```

### Frame vs. function vs. code vs. bytecode

* __bytecode__ is a bunch of 1s and 0s
* A __code__ contains bytecode and also variable informations
* A __function__ contains a code and a pointer to its environment
* A __frame__ also contains a code and a pointer to its environment
* A __frame__ represents a code __at run time__

# What does `CALL_FUNCTION` opcode do

In `ceval.c`

```c
        case CALL_FUNCTION:
        {
            PyObject **sp;
            PCALL(PCALL_ALL);
            sp = stack_pointer;
#ifdef WITH_TSC
            x = call_function(&sp, oparg, &intr0, &intr1);
#else
            x = call_function(&sp, oparg);
#endif
            stack_pointer = sp;
            PUSH(x);
            if (x != NULL)
                continue;
            break;
        }
```

The `call_function` function:

```c
static PyObject *
call_function(PyObject ***pp_stack, int oparg
#ifdef WITH_TSC
                , uint64* pintr0, uint64* pintr1
#endif
                )
{
    ...
    /* Always dispatch PyCFunction first, because these are
       presumed to be the most frequent callable object.
    */
    if (PyCFunction_Check(func) && nk == 0) {
        ...
    } else {
        ...
        if (PyFunction_Check(func))
            x = fast_function(func, pp_stack, n, na, nk);
        else
            x = do_call(func, pp_stack, na, nk);
        ...
    }
    ...
    return x;
}
```

In `fast_function` function

```c
static PyObject *
fast_function(PyObject *func, PyObject ***pp_stack, int n, int na, int nk)
{
    ...
    if (argdefs == NULL && co->co_argcount == n && nk==0 &&
        co->co_flags == (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE)) {
        PyFrameObject *f;
        PyObject *retval = NULL;
        PyThreadState *tstate = PyThreadState_GET();
        PyObject **fastlocals, **stack;
        int i;

        PCALL(PCALL_FASTER_FUNCTION);
        assert(globals != NULL);
        /* XXX Perhaps we should create a specialized
           PyFrame_New() that doesn't take locals, but does
           take builtins without sanity checking them.
        */
        assert(tstate != NULL);
        f = PyFrame_New(tstate, co, globals, NULL);
        if (f == NULL)
            return NULL;

        fastlocals = f->f_localsplus;
        stack = (*pp_stack) - n;

        for (i = 0; i < n; i++) {
            Py_INCREF(*stack);
            fastlocals[i] = *stack++;
        }
        retval = PyEval_EvalFrameEx(f,0);
        ++tstate->recursion_depth;
        Py_DECREF(f);
        --tstate->recursion_depth;
        return retval;
    }
    ...
}
```
