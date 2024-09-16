Opcodes under active consideration
----------------------------------

This list includes opcodes under active consideration for adding to the
next or subsequent hard fork.

|  Opcode  | Name            | Description                                     | EIP                                                                          |
|:--------:|-----------------|-------------------------------------------------|------------------------------------------------------------------------------|
|   0x49   | BLOBHASH        | Returns hashes of blobs in the transaction      | [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)                          |
| ~~0x4A~~ | ~~BEACON_ROOT~~ | ~~Exposes the Beacon Chain Root~~               | [EIP-4788](https://eips.ethereum.org/EIPS/eip-4788)                          |
|   0x5C   | TLOAD           | Transient data load                             | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)                          |
|   0x5D   | TSTORE          | Transient data store                            | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)                          |
|   0x5E   | MCOPY           | Memory copy                                     | [EIP-5656](https://eips.ethereum.org/EIPS/eip-5656)                          |
|   0xD0   | DATALOAD        | Loads data from EOF data section, via stack     | [EIP-7480](https://eips.ethereum.org/EIPS/eip-7480) |
|   0xD1   | DATALOADN       | Loads data from EOF data section, via immediate | [EIP-7480](https://eips.ethereum.org/EIPS/eip-7480) |
|   0xD2   | DATASIZE        | Size of the EOF data section                    | [EIP-7480](https://eips.ethereum.org/EIPS/eip-7480) |
|   0xD3   | DATACOPY        | Bulk EOF data copy                              | [EIP-7480](https://eips.ethereum.org/EIPS/eip-7480) |
|   0xE0   | RJUMP           | relative jump                                   | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                          |
|   0xE1   | RJUMPI          | relative conditional jump                       | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                          |
|   0xE2   | RJUMV           | relative jump table                             | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                          |
|   0xE3   | CALLF           | EOF Subroutine Call                             | [EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)                          |
|   0xE4   | RETF            | EOF Subroutine return                           | [EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)                          |
|   0xE5   | JUMPF           | EOF Function Jump                               | [EIP-6209](https://eips.ethereum.org/EIPS/eip-6209)                          |
|   0xE6   | DUPN            | Unlimited dup                                   | [EIP-663](https://eips.ethereum.org/EIPS/eip-663)                            |
|   0xE7   | SWAPN           | Unlimited swap                                  | [EIP-663](https://eips.ethereum.org/EIPS/eip-663)                            |
|   0xE8   | EXCHANGE        | Deep swap                                       | [EIP-663](https://eips.ethereum.org/EIPS/eip-663)                            |
|   0xEC   | EOFCREATE       | Create from EOF contained initcode              | [EIP-7620](https://eips.ethereum.org/EIPS/eip-7620)                          |
|   0xEE   | RETURNCONTRACT  | Contract to be created, references EOF data     | [EIP-7620](https://eips.ethereum.org/EIPS/eip-7620)                          |
|   0xEF   | -               | Reserved for EOF compatibility                  | [EIP-3540](https://eips.ethereum.org/EIPS/eip-3540)                          |
|   0xF6   | PAY             | transfers value from caller to target           | [EIP-5920](https://eips.ethereum.org/EIPS/eip-5920)                          |
|   0xF7   | RETURNDATALOAD  | Loads data returned from a call to the stack    | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          |
|   0xF8   | EXTCALL         | CALL without gas and output memory              | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          |
|   0xF9   | EXTDELEGATECALL | DELEGATECALL without gas and output memory      | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          |
|   0xFB   | EXTSTATICCALL   | STATICCALL without gas and output memory        | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          |
|   0xFC   | SETCODE         | Change the code for the current contract        | [EIP-6913](https://eips.ethereum.org/EIPS/eip-6913)                          |

Pending Opcode Table
--------------------

Full opcode table presuming all pending opcodes are adopted.

Existing Opcodes
----------------

Current up to Shanghai. Opcodes not operation in mainnet (and are either
scheduled or accepted) are in *italics*.

| Number | Name             | Execution spec category | Initial Release  | EIP                                                                            |
|--------|------------------|-------------------------|------------------|--------------------------------------------------------------------------------|
| 0x00   | STOP             | Control Flow            |                  |                                                                                |
| 0x01   | ADD              | Arithmetic              |                  |                                                                                |
| 0x02   | MUL              | Arithmetic              |                  |                                                                                |
| 0x03   | SUB              | Arithmetic              |                  |                                                                                |
| 0x04   | DIV              | Arithmetic              |                  |                                                                                |
| 0x05   | SDIV             | Arithmetic              |                  |                                                                                |
| 0x06   | MOD              | Arithmetic              |                  |                                                                                |
| 0x07   | SMOD             | Arithmetic              |                  |                                                                                |
| 0x08   | ADDMOD           | Arithmetic              |                  |                                                                                |
| 0x09   | MULMOD           | Arithmetic              |                  |                                                                                |
| 0x0A   | EXP              | Arithmetic              |                  |                                                                                |
| 0x0B   | SIGNEXTEND       | Arithmetic              |                  |                                                                                |
| 0x0C   |                  |                         |                  |                                                                                |
| 0x0D   |                  |                         |                  |                                                                                |
| 0x0E   |                  |                         |                  |                                                                                |
| 0x0F   |                  |                         |                  |                                                                                |
| 0x10   | LT               | Comparison              |                  |                                                                                |
| 0x11   | GT               | Comparison              |                  |                                                                                |
| 0x12   | SLT              | Comparison              |                  |                                                                                |
| 0x13   | SGT              | Comparison              |                  |                                                                                |
| 0x14   | EQ               | Comparison              |                  |                                                                                |
| 0x15   | ISZERO           | Comparison              |                  |                                                                                |
| 0x16   | AND              | Bitwise                 |                  |                                                                                |
| 0x17   | OR               | Bitwise                 |                  |                                                                                |
| 0x18   | XOR              | Bitwise                 |                  |                                                                                |
| 0x19   | NOT              | Bitwise                 |                  |                                                                                |
| 0x1A   | BYTE             | Bitwise                 |                  |                                                                                |
| 0x1B   | SHL              | Bitwise                 | Constantinople   | [EIP-145](https://eips.ethereum.org/EIPS/eip-145)                              |
| 0x1C   | SHR              | Bitwise                 | Constantinople   | [EIP-145](https://eips.ethereum.org/EIPS/eip-145)                              |
| 0x1D   | SAR              | Bitwise                 | Constantinople   | [EIP-145](https://eips.ethereum.org/EIPS/eip-145)                              |
| 0x1E   |                  |                         |                  |                                                                                |
| 0x1F   |                  |                         |                  |                                                                                |
| 0x20   | KECCAK           | Keccak                  |                  |                                                                                |
| 0x21   |                  |                         |                  |                                                                                |
| 0x22   |                  |                         |                  |                                                                                |
| 0x23   |                  |                         |                  |                                                                                |
| 0x24   |                  |                         |                  |                                                                                |
| 0x25   |                  |                         |                  |                                                                                |
| 0x26   |                  |                         |                  |                                                                                |
| 0x27   |                  |                         |                  |                                                                                |
| 0x28   |                  |                         |                  |                                                                                |
| 0x29   |                  |                         |                  |                                                                                |
| 0x2A   |                  |                         |                  |                                                                                |
| 0x2B   |                  |                         |                  |                                                                                |
| 0x2C   |                  |                         |                  |                                                                                |
| 0x2D   |                  |                         |                  |                                                                                |
| 0x2E   |                  |                         |                  |                                                                                |
| 0x2F   |                  |                         |                  |                                                                                |
| 0x30   | ADDRESS          | Environmental           |                  |                                                                                |
| 0x31   | BALANCE          | Environmental           |                  |                                                                                |
| 0x32   | ORIGIN           | Environmental           |                  |                                                                                |
| 0x33   | CALLER           | Environmental           |                  |                                                                                |
| 0x34   | CALLVALUE        | Environmental           |                  |                                                                                |
| 0x35   | CALLDATALOAD     | Environmental           |                  |                                                                                |
| 0x36   | CALLDATASIZE     | Environmental           |                  |                                                                                |
| 0x37   | CALLDATACOPY     | Environmental           |                  |                                                                                |
| 0x38   | CODESIZE         | Environmental           |                  |                                                                                |
| 0x39   | CODECOPY         | Environmental           |                  |                                                                                |
| 0x3A   | GASPRICE         | Environmental           |                  |                                                                                |
| 0x3B   | EXTCODESIZE      | Environmental           |                  |                                                                                |
| 0x3C   | EXTCODECOPY      | Environmental           |                  |                                                                                |
| 0x3D   | RETURNDATASIZE   | Environmental           | Byzantium        | [EIP-211](https://eips.ethereum.org/EIPS/eip-211)                              |
| 0x3E   | RETURNDATACOPY   | Environmental           | Byzantium        | [EIP-211](https://eips.ethereum.org/EIPS/eip-211)                              |
| 0x3F   | EXTCODEHASH      | Environmental           | Constantinople   | [EIP-1052](https://eips.ethereum.org/EIPS/eip-1052)                            |
| 0x40   | BLOCKHASH        | Block                   |                  |                                                                                |
| 0x41   | COINBASE         | Block                   |                  |                                                                                |
| 0x42   | TIMESTAMP        | Block                   |                  |                                                                                |
| 0x43   | NUMBER           | Block                   |                  |                                                                                |
| 0x44   | DIFFICULTY       | Block                   | Frontier->London |                                                                                |
| 0x44   | PREVRANDAO       | Block                   | Paris            | [EIP-4399](https://eips.ethereum.org/EIPS/eip-4399)                            |
| 0x45   | GASLIMIT         | Block                   |                  |                                                                                |
| 0x46   | CHAINID          | Block                   | Istanbul         | [EIP-1344](https://eips.ethereum.org/EIPS/eip-1344)                            |
| 0x47   | SELFBALANCE      | Block                   | Istanbul         | [EIP-1884](https://eips.ethereum.org/EIPS/eip-1884)                            |
| 0x48   | BASEFEE          | Block                   | London           | [EIP-3198](https://eips.ethereum.org/EIPS/eip-3198)                            |
| *0x49* | *BLOBHASH*       | *Block*                 | *Cancun*         | *[EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)*                          |
| 0x4A   |                  |                         |                  |                                                                                |
| 0x4B   |                  |                         |                  |                                                                                |
| 0x4C   |                  |                         |                  |                                                                                |
| 0x4D   |                  |                         |                  |                                                                                |
| 0x4E   |                  |                         |                  |                                                                                |
| 0x4F   |                  |                         |                  |                                                                                |
| 0x50   | POP              | Pop                     |                  |                                                                                |
| 0x51   | MLOAD            | Memory                  |                  |                                                                                |
| 0x52   | MSTORE           | Memory                  |                  |                                                                                |
| 0x53   | MSTORE8          | Memory                  |                  |                                                                                |
| 0x54   | SLOAD            | Storage                 |                  |                                                                                |
| 0x55   | SSTORE           | Storage                 |                  |                                                                                |
| 0x56   | JUMP             | Control Flow            |                  |                                                                                |
| 0x57   | JUMPI            | Control Flow            |                  |                                                                                |
| 0x58   | PC               | Control Flow            |                  |                                                                                |
| 0x59   | MSIZE            | Memory                  |                  |                                                                                |
| 0x5A   | GAS              | Control Flow            |                  |                                                                                |
| 0x5B   | JUMPDEST         | Control Flow            |                  |                                                                                |
| *0x5C* | *TLOAD*          | *Transient Storage*     | *Cancun*         | *[EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)*                          |
| *0x5D* | *TSTORE*         | *Transient Storage*     | *Cancun*         | *[EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)*                          |
| *0x5E* | *MCOPY*          | *Memory*                | *Cancun*         | *[EIP-5656](https://eips.ethereum.org/EIPS/eip-5656)*                          |
| 0x5F   | PUSH0            | Push                    | Shanghai         | [EIP-3855](https://eips.ethereum.org/EIPS/eip-3855)                            |
| 0x60   | PUSH1            | Push                    |                  |                                                                                |
| 0x61   | PUSH2            | Push                    |                  |                                                                                |
| 0x62   | PUSH3            | Push                    |                  |                                                                                |
| 0x63   | PUSH4            | Push                    |                  |                                                                                |
| 0x64   | PUSH5            | Push                    |                  |                                                                                |
| 0x65   | PUSH6            | Push                    |                  |                                                                                |
| 0x66   | PUSH7            | Push                    |                  |                                                                                |
| 0x67   | PUSH8            | Push                    |                  |                                                                                |
| 0x68   | PUSH9            | Push                    |                  |                                                                                |
| 0x69   | PUSH10           | Push                    |                  |                                                                                |
| 0x6A   | PUSH11           | Push                    |                  |                                                                                |
| 0x6B   | PUSH12           | Push                    |                  |                                                                                |
| 0x6C   | PUSH13           | Push                    |                  |                                                                                |
| 0x6D   | PUSH14           | Push                    |                  |                                                                                |
| 0x6E   | PUSH15           | Push                    |                  |                                                                                |
| 0x6F   | PUSH16           | Push                    |                  |                                                                                |
| 0x70   | PUSH17           | Push                    |                  |                                                                                |
| 0x71   | PUSH18           | Push                    |                  |                                                                                |
| 0x72   | PUSH19           | Push                    |                  |                                                                                |
| 0x73   | PUSH20           | Push                    |                  |                                                                                |
| 0x74   | PUSH21           | Push                    |                  |                                                                                |
| 0x75   | PUSH22           | Push                    |                  |                                                                                |
| 0x76   | PUSH23           | Push                    |                  |                                                                                |
| 0x77   | PUSH24           | Push                    |                  |                                                                                |
| 0x78   | PUSH25           | Push                    |                  |                                                                                |
| 0x79   | PUSH26           | Push                    |                  |                                                                                |
| 0x7A   | PUSH27           | Push                    |                  |                                                                                |
| 0x7B   | PUSH28           | Push                    |                  |                                                                                |
| 0x7C   | PUSH29           | Push                    |                  |                                                                                |
| 0x7D   | PUSH30           | Push                    |                  |                                                                                |
| 0x7E   | PUSH31           | Push                    |                  |                                                                                |
| 0x7F   | PUSH32           | Push                    |                  |                                                                                |
| 0x80   | DUP1             | Dup                     |                  |                                                                                |
| 0x81   | DUP2             | Dup                     |                  |                                                                                |
| 0x82   | DUP3             | Dup                     |                  |                                                                                |
| 0x83   | DUP4             | Dup                     |                  |                                                                                |
| 0x84   | DUP5             | Dup                     |                  |                                                                                |
| 0x85   | DUP6             | Dup                     |                  |                                                                                |
| 0x86   | DUP7             | Dup                     |                  |                                                                                |
| 0x87   | DUP8             | Dup                     |                  |                                                                                |
| 0x88   | DUP9             | Dup                     |                  |                                                                                |
| 0x89   | DUP10            | Dup                     |                  |                                                                                |
| 0x8A   | DUP11            | Dup                     |                  |                                                                                |
| 0x8B   | DUP12            | Dup                     |                  |                                                                                |
| 0x8C   | DUP13            | Dup                     |                  |                                                                                |
| 0x8D   | DUP14            | Dup                     |                  |                                                                                |
| 0x8E   | DUP15            | Dup                     |                  |                                                                                |
| 0x8F   | DUP16            | Dup                     |                  |                                                                                |
| 0x90   | SWAP1            | Swap                    |                  |                                                                                |
| 0x91   | SWAP2            | Swap                    |                  |                                                                                |
| 0x92   | SWAP3            | Swap                    |                  |                                                                                |
| 0x93   | SWAP4            | Swap                    |                  |                                                                                |
| 0x94   | SWAP5            | Swap                    |                  |                                                                                |
| 0x95   | SWAP6            | Swap                    |                  |                                                                                |
| 0x96   | SWAP7            | Swap                    |                  |                                                                                |
| 0x97   | SWAP8            | Swap                    |                  |                                                                                |
| 0x98   | SWAP9            | Swap                    |                  |                                                                                |
| 0x99   | SWAP10           | Swap                    |                  |                                                                                |
| 0x9A   | SWAP11           | Swap                    |                  |                                                                                |
| 0x9B   | SWAP12           | Swap                    |                  |                                                                                |
| 0x9C   | SWAP13           | Swap                    |                  |                                                                                |
| 0x9D   | SWAP14           | Swap                    |                  |                                                                                |
| 0x9E   | SWAP15           | Swap                    |                  |                                                                                |
| 0x9F   | SWAP16           | Swap                    |                  |                                                                                |
| 0xA0   | LOG0             | Log                     |                  |                                                                                |
| 0xA1   | LOG1             | Log                     |                  |                                                                                |
| 0xA2   | LOG2             | Log                     |                  |                                                                                |
| 0xA3   | LOG3             | Log                     |                  |                                                                                |
| 0xA4   | LOG4             | Log                     |                  |                                                                                |
| 0xA5   |                  |                         |                  |                                                                                |
| 0xA6   |                  |                         |                  |                                                                                |
| 0xA7   |                  |                         |                  |                                                                                |
| 0xA8   |                  |                         |                  |                                                                                |
| 0xA9   |                  |                         |                  |                                                                                |
| 0xAA   |                  |                         |                  |                                                                                |
| 0xAB   |                  |                         |                  |                                                                                |
| 0xAC   |                  |                         |                  |                                                                                |
| 0xAD   |                  |                         |                  |                                                                                |
| 0xAE   |                  |                         |                  |                                                                                |
| 0xAF   |                  |                         |                  |                                                                                |
| 0xB0   |                  |                         |                  |                                                                                |
| 0xB1   |                  |                         |                  |                                                                                |
| 0xB2   |                  |                         |                  |                                                                                |
| 0xB3   |                  |                         |                  |                                                                                |
| 0xB4   |                  |                         |                  |                                                                                |
| 0xB5   |                  |                         |                  |                                                                                |
| 0xB6   |                  |                         |                  |                                                                                |
| 0xB7   |                  |                         |                  |                                                                                |
| 0xB8   |                  |                         |                  |                                                                                |
| 0xB9   |                  |                         |                  |                                                                                |
| 0xBA   |                  |                         |                  |                                                                                |
| 0xBB   |                  |                         |                  |                                                                                |
| 0xBC   |                  |                         |                  |                                                                                |
| 0xBD   |                  |                         |                  |                                                                                |
| 0xBE   |                  |                         |                  |                                                                                |
| 0xBF   |                  |                         |                  |                                                                                |
| 0XC0   |                  |                         |                  |                                                                                |
| 0XC1   |                  |                         |                  |                                                                                |
| 0XC2   |                  |                         |                  |                                                                                |
| 0XC3   |                  |                         |                  |                                                                                |
| 0XC4   |                  |                         |                  |                                                                                |
| 0XC5   |                  |                         |                  |                                                                                |
| 0XC6   |                  |                         |                  |                                                                                |
| 0XC7   |                  |                         |                  |                                                                                |
| 0XC8   |                  |                         |                  |                                                                                |
| 0XC9   |                  |                         |                  |                                                                                |
| 0XCA   |                  |                         |                  |                                                                                |
| 0XCB   |                  |                         |                  |                                                                                |
| 0XCC   |                  |                         |                  |                                                                                |
| 0XCD   |                  |                         |                  |                                                                                |
| 0XCE   |                  |                         |                  |                                                                                |
| 0XCF   |                  |                         |                  |                                                                                |
| *0xD0* | *DATALOAD*       | *EOF*                   | *????*           | *[EIP-7480](https://eips.ethereum.org/EIPS/eip-7480)* |
| *0xD1* | *DATALOADN*      | *EOF*                   | *????*           | *[EIP-7480](https://eips.ethereum.org/EIPS/eip-7480)* |
| *0xD2* | *DATASIZE*       | *EOF*                   | *????*           | *[EIP-7480](https://eips.ethereum.org/EIPS/eip-7480)* |
| *0xD3* | *DATACOPY*       | *EOF*                   | *????*           | *[EIP-7480](https://eips.ethereum.org/EIPS/eip-7480)* |
| 0XD4   |                  |                         |                  |                                                                                |
| 0XD5   |                  |                         |                  |                                                                                |
| 0XD6   |                  |                         |                  |                                                                                |
| 0XD7   |                  |                         |                  |                                                                                |
| 0XD8   |                  |                         |                  |                                                                                |
| 0XD9   |                  |                         |                  |                                                                                |
| 0XDA   |                  |                         |                  |                                                                                |
| 0XDB   |                  |                         |                  |                                                                                |
| 0XDC   |                  |                         |                  |                                                                                |
| 0XDD   |                  |                         |                  |                                                                                |
| 0XDE   |                  |                         |                  |                                                                                |
| 0XDF   |                  |                         |                  |                                                                                |
| *0xE0* | *RJUMP*          | *EOF*                   | *????*           | *[EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)*                          |
| *0xE1* | *RJUMPI*         | *EOF*                   | *????*           | *[EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)*                          |
| *0xE2* | *RJUMPV*         | *EOF*                   | *????*           | *[EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)*                          |
| *0xE3* | *CALLF*          | *EOF*                   | *????*           | *[EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)*                          |
| *0xE4* | *RETF*           | *EOF*                   | *????*           | *[EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)*                          |
| *0xE5* | *JUMPF*          | *EOF*                   | *????*           | *[EIP-4750](https://eips.ethereum.org/EIPS/eip-6209)*                          |
| *0xE6* | *DUPN*           | *EOF*                   | *????*           | *[EIP-663](https://eips.ethereum.org/EIPS/eip-663)*                            |
| *0xE7* | *SWAPN*          | *EOF*                   | *????*           | *[EIP-663](https://eips.ethereum.org/EIPS/eip-663)*                            |
| *0xE8* | *EXCHANGE*       | *EOF*                   | *????*           | *[EIP-663](https://eips.ethereum.org/EIPS/eip-663)*                            |
| 0xE9   |                  |                         |                  |                                                                                |
| 0xEA   |                  |                         |                  |                                                                                |
| 0xEB   |                  |                         |                  |                                                                                |
| *0xEC* | *EOFCREATE*      | *EOF*                   | *????*           | *[EIP-7620](https://eips.ethereum.org/EIPS/eip-7620)*                          |
| 0xED   |                  |                         |                  |                                                                                |
| *0xEE* | *RETURNCONTRACT* | *EOF*                   | *????*           | *[EIP-7620](https://eips.ethereum.org/EIPS/eip-7620)*                          |
| *0xEF* | *-RESERVED-*     | *EOF*                   | *????*           | *[EIP-3540](https://eips.ethereum.org/EIPS/eip-3540)*                          |
| 0xF0   | CREATE           | System                  |                  |                                                                                |
| 0xF1   | CALL             | System                  |                  |                                                                                |
| 0xF2   | CALLCODE         | System                  |                  |                                                                                |
| 0xF3   | RETURN           | System                  |                  |                                                                                |
| 0xF4   | DELEGATECALL     | System                  | Homestead        | [EIP-7](https://eips.ethereum.org/EIPS/eip-7)                                  |
| 0xF5   | CREATE2          | System                  | Constantinople   | [EIP-1014](https://eips.ethereum.org/EIPS/eip-1014)                            |
| *0xF6* | *PAY*            | *System*                | *????*           | *[EIP-5920](https://eips.ethereum.org/EIPS/eip-5920)*                          |
| *0xF7* | *RETURNDATALOAD* | *Environmental*         | *????*           | *[EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)*                          |
| *0xF8* | *EXTCALL*        | *System*                | *????*           | *[EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)*                          |
| *0xF9* | *EXTDELEGATECALL*| *System*                | *????*           | *[EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)*                          |
| 0xFA   | STATICCALL       | System                  | Byzantium        | [EIP-214](https://eips.ethereum.org/EIPS/eip-214)                              |
| *0xFB* | *EXTSTATICCALL*  | *System*                | *????*           | *[EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)*                          |
| *0xFC* | *SETCODE*        | *System*                | *????*           | *[EIP-6913](https://eips.ethereum.org/EIPS/eip-6913)*                          |
| 0xFD   | REVERT           | System                  | Byzantium        | [EIP-140](https://eips.ethereum.org/EIPS/eip-140)                              |
| 0xFE   | INVALID/ABORT    | System                  | (unofficial)     | [EIP-141](https://eips.ethereum.org/EIPS/eip-141)                              |
| 0xFF   | SELFDESTRUCT     | System                  |                  |                                                                                |
