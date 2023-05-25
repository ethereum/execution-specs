Existing Opcodes
----------------

Current up to Shanghai

| Number | Name           | Execution spec category | Initial Release  | EIP                                                 |
|--------|----------------|-------------------------|------------------|-----------------------------------------------------|
| 0x00   | STOP           | Control Flow            |                  |                                                     |
| 0x01   | ADD            | Arithmetic              |                  |                                                     |
| 0x02   | MUL            | Arithmetic              |                  |                                                     |
| 0x03   | SUB            | Arithmetic              |                  |                                                     |
| 0x04   | DIV            | Arithmetic              |                  |                                                     |
| 0x05   | SDIV           | Arithmetic              |                  |                                                     |
| 0x06   | MOD            | Arithmetic              |                  |                                                     |
| 0x07   | SMOD           | Arithmetic              |                  |                                                     |
| 0x08   | ADDMOD         | Arithmetic              |                  |                                                     |
| 0x09   | MULMOD         | Arithmetic              |                  |                                                     |
| 0x0A   | EXP            | Arithmetic              |                  |                                                     |
| 0x0B   | SIGNEXTEND     | Arithmetic              |                  |                                                     |
| 0x10   | LT             | Comparison              |                  |                                                     |
| 0x11   | GT             | Comparison              |                  |                                                     |
| 0x12   | SLT            | Comparison              |                  |                                                     |
| 0x13   | SGT            | Comparison              |                  |                                                     |
| 0x14   | EQ             | Comparison              |                  |                                                     |
| 0x15   | ISZERO         | Comparison              |                  |                                                     |
| 0x16   | AND            | Bitwise                 |                  |                                                     |
| 0x17   | OR             | Bitwise                 |                  |                                                     |
| 0x18   | XOR            | Bitwise                 |                  |                                                     |
| 0x19   | NOT            | Bitwise                 |                  |                                                     |
| 0x1A   | BYTE           | Bitwise                 |                  |                                                     |
| 0x1B   | SHL            | Bitwise                 | Constantinople   | [EIP-145](https://eips.ethereum.org/EIPS/eip-145)   |
| 0x1C   | SHR            | Bitwise                 | Constantinople   | [EIP-145](https://eips.ethereum.org/EIPS/eip-145)   |
| 0x1D   | SAR            | Bitwise                 | Constantinople   | [EIP-145](https://eips.ethereum.org/EIPS/eip-145)   |
| 0x20   | KECCAK         | Keccak                  |                  |                                                     |
| 0x30   | ADDRESS        | Environmental           |                  |                                                     |
| 0x31   | BALANCE        | Environmental           |                  |                                                     |
| 0x32   | ORIGIN         | Environmental           |                  |                                                     |
| 0x33   | CALLER         | Environmental           |                  |                                                     |
| 0x34   | CALLVALUE      | Environmental           |                  |                                                     |
| 0x35   | CALLDATALOAD   | Environmental           |                  |                                                     |
| 0x36   | CALLDATASIZE   | Environmental           |                  |                                                     |
| 0x37   | CALLDATACOPY   | Environmental           |                  |                                                     |
| 0x38   | CODESIZE       | Environmental           |                  |                                                     |
| 0x39   | CODECOPY       | Environmental           |                  |                                                     |
| 0x3A   | GASPRICE       | Environmental           |                  |                                                     |
| 0x3B   | EXTCODESIZE    | Environmental           |                  |                                                     |
| 0x3C   | EXTCODECOPY    | Environmental           |                  |                                                     |
| 0x3D   | RETURNDATASIZE | Environmental           | Byzantium        | [EIP-211](https://eips.ethereum.org/EIPS/eip-211)   |
| 0x3E   | RETURNDATACOPY | Environmental           | Byzantium        | [EIP-211](https://eips.ethereum.org/EIPS/eip-211)   |
| 0x3F   | EXTCODEHASH    | Environmental           | Constantinople   | [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052) |
| 0x40   | BLOCKHASH      | Block                   |                  |                                                     |
| 0x41   | COINBASE       | Block                   |                  |                                                     |
| 0x42   | TIMESTAMP      | Block                   |                  |                                                     |
| 0x43   | NUMBER         | Block                   |                  |                                                     |
| 0x44   | DIFFICULTY     | Block                   | Frontier->London |                                                     |
| 0x44   | PREVRANDAO     | Block                   | Paris            | [EIP-4399](https://eips.ethereum.org/EIPS/eip-4399) |
| 0x45   | GASLIMIT       | Block                   |                  |                                                     |
| 0x46   | CHAINID        | Block                   | Istanbul         | [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344) |
| 0x47   | SELFBALANCE    | Block                   | Istanbul         | [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884) |
| 0x48   | BASEFEE        | Block                   | London           | [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198) |
| 0x50   | POP            | Pop                     |                  |                                                     |
| 0x51   | MLOAD          | Memory                  |                  |                                                     |
| 0x52   | MSTORE         | Memory                  |                  |                                                     |
| 0x53   | MSTORE8        | Memory                  |                  |                                                     |
| 0x54   | SLOAD          | Storage                 |                  |                                                     |
| 0x55   | SSTORE         | Storage                 |                  |                                                     |
| 0x56   | JUMP           | Control Flow            |                  |                                                     |
| 0x57   | JUMPI          | Control Flow            |                  |                                                     |
| 0x58   | PC             | Control Flow            |                  |                                                     |
| 0x59   | MSIZE          | Memory                  |                  |                                                     |
| 0x5A   | GAS            | Control Flow            |                  |                                                     |
| 0x5B   | JUMPDEST       | Control Flow            |                  |                                                     |
| 0x5F   | PUSH0          | Push                    | Shanghai         | [EIP-3855](https://eips.ethereum.org/EIPS/eip-3855) |
| 0x60   | PUSH1          | Push                    |                  |                                                     |
| 0x61   | PUSH2          | Push                    |                  |                                                     |
| 0x62   | PUSH3          | Push                    |                  |                                                     |
| 0x63   | PUSH4          | Push                    |                  |                                                     |
| 0x64   | PUSH5          | Push                    |                  |                                                     |
| 0x65   | PUSH6          | Push                    |                  |                                                     |
| 0x66   | PUSH7          | Push                    |                  |                                                     |
| 0x67   | PUSH8          | Push                    |                  |                                                     |
| 0x68   | PUSH9          | Push                    |                  |                                                     |
| 0x69   | PUSH10         | Push                    |                  |                                                     |
| 0x6A   | PUSH11         | Push                    |                  |                                                     |
| 0x6B   | PUSH12         | Push                    |                  |                                                     |
| 0x6C   | PUSH13         | Push                    |                  |                                                     |
| 0x6D   | PUSH14         | Push                    |                  |                                                     |
| 0x6E   | PUSH15         | Push                    |                  |                                                     |
| 0x6F   | PUSH16         | Push                    |                  |                                                     |
| 0x70   | PUSH17         | Push                    |                  |                                                     |
| 0x71   | PUSH18         | Push                    |                  |                                                     |
| 0x72   | PUSH19         | Push                    |                  |                                                     |
| 0x73   | PUSH20         | Push                    |                  |                                                     |
| 0x74   | PUSH21         | Push                    |                  |                                                     |
| 0x75   | PUSH22         | Push                    |                  |                                                     |
| 0x76   | PUSH23         | Push                    |                  |                                                     |
| 0x77   | PUSH24         | Push                    |                  |                                                     |
| 0x78   | PUSH25         | Push                    |                  |                                                     |
| 0x79   | PUSH26         | Push                    |                  |                                                     |
| 0x7A   | PUSH27         | Push                    |                  |                                                     |
| 0x7B   | PUSH28         | Push                    |                  |                                                     |
| 0x7C   | PUSH29         | Push                    |                  |                                                     |
| 0x7D   | PUSH30         | Push                    |                  |                                                     |
| 0x7E   | PUSH31         | Push                    |                  |                                                     |
| 0x7F   | PUSH32         | Push                    |                  |                                                     |
| 0x80   | DUP1           | Dup                     |                  |                                                     |
| 0x81   | DUP2           | Dup                     |                  |                                                     |
| 0x82   | DUP3           | Dup                     |                  |                                                     |
| 0x83   | DUP4           | Dup                     |                  |                                                     |
| 0x84   | DUP5           | Dup                     |                  |                                                     |
| 0x85   | DUP6           | Dup                     |                  |                                                     |
| 0x86   | DUP7           | Dup                     |                  |                                                     |
| 0x87   | DUP8           | Dup                     |                  |                                                     |
| 0x88   | DUP9           | Dup                     |                  |                                                     |
| 0x89   | DUP10          | Dup                     |                  |                                                     |
| 0x8A   | DUP11          | Dup                     |                  |                                                     |
| 0x8B   | DUP12          | Dup                     |                  |                                                     |
| 0x8C   | DUP13          | Dup                     |                  |                                                     |
| 0x8D   | DUP14          | Dup                     |                  |                                                     |
| 0x8E   | DUP15          | Dup                     |                  |                                                     |
| 0x8F   | DUP16          | Dup                     |                  |                                                     |
| 0x90   | SWAP1          | Swap                    |                  |                                                     |
| 0x91   | SWAP2          | Swap                    |                  |                                                     |
| 0x92   | SWAP3          | Swap                    |                  |                                                     |
| 0x93   | SWAP4          | Swap                    |                  |                                                     |
| 0x94   | SWAP5          | Swap                    |                  |                                                     |
| 0x95   | SWAP6          | Swap                    |                  |                                                     |
| 0x96   | SWAP7          | Swap                    |                  |                                                     |
| 0x97   | SWAP8          | Swap                    |                  |                                                     |
| 0x98   | SWAP9          | Swap                    |                  |                                                     |
| 0x99   | SWAP10         | Swap                    |                  |                                                     |
| 0x9A   | SWAP11         | Swap                    |                  |                                                     |
| 0x9B   | SWAP12         | Swap                    |                  |                                                     |
| 0x9C   | SWAP13         | Swap                    |                  |                                                     |
| 0x9D   | SWAP14         | Swap                    |                  |                                                     |
| 0x9E   | SWAP15         | Swap                    |                  |                                                     |
| 0x9F   | SWAP16         | Swap                    |                  |                                                     |
| 0xA0   | LOG0           | Log                     |                  |                                                     |
| 0xA1   | LOG1           | Log                     |                  |                                                     |
| 0xA2   | LOG2           | Log                     |                  |                                                     |
| 0xA3   | LOG3           | Log                     |                  |                                                     |
| 0xA4   | LOG4           | Log                     |                  |                                                     |
| 0xF0   | CREATE         | System                  |                  |                                                     |
| 0xF1   | CALL           | System                  |                  |                                                     |
| 0xF2   | CALLCODE       | System                  |                  |                                                     |
| 0xF3   | RETURN         | System                  |                  |                                                     |
| 0xF4   | DELEGATECALL   | System                  | Homestead        | [EIP-7](https://eips.ethereum.org/EIPS/eip-7)       |
| 0xF5   | CREATE2        | System                  | Constantinople   | [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014) |
| 0xFA   | STATICCALL     | System                  | Byzantium        | [EIP-214](https://eips.ethereum.org/EIPS/eip-214)   |
| 0xFD   | REVERT         | System                  | Byzantium        | [EIP-140](https://eips.ethereum.org/EIPS/eip-140)   |
| 0xFE   | INVALID/ABORT  | System                  | (unofficial)     | [EIP-141](https://eips.ethereum.org/EIPS/eip-141)   |
| 0xFF   | SELFDESTRUCT   | System                  |                  |                                                     |
