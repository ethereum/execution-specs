This tests contain opcodes that has input arguments.But that arguments passed as output of another opcode. 
In this case it's Balance opcode. Each test has 2 transactions: one makes balance to return 0, another one makes balance to return 1.

This is done so evmjit or other compiler would not define opcode arguments as constant, but as a variable rather. Because evmjit encountered some bugs for this kind of scenario.


Pseudo code description:

```
foreach opcodes as opcode
{
 a = 0
 opcode (a,a, ...)

 a = 1
 opcode (a,a, ...)
}
```
