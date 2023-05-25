Opcodes under active consideration
----------------------------------

This list includes opcodes under active consideration for adding to the
next or subsuquent hard fork.

|  Opcode  | Name            | Description                                     | EIP                                                                          |
|:--------:|-----------------|-------------------------------------------------|------------------------------------------------------------------------------|
|   0x49   | BLOBHASH        | Returns hashes of blobs in the transaction      | [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)                          |
| ~~0x4A~~ | ~~BEACON_ROOT~~ | ~~Exposes the Beacon Chain Root~~               | [EIP-4788](https://eips.ethereum.org/EIPS/eip-4788)                          |
|   0x5C   | TLOAD           | Transient data load                             | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)                          |
|   0x5D   | TSTORE          | Transient data store                            | [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153)                          |
|   0x5E   | MCOPY           | Memory copy                                     | [EIP-5656](https://eips.ethereum.org/EIPS/eip-5656)                          |
|   0xE0   | RJUMP           | relative jump                                   | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                          |
|   0xE1   | RJUMI           | relative conditional jump                       | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                          |
|   0xE2   | RJUMV           | relative jump table                             | [EIP-4200](https://eips.ethereum.org/EIPS/eip-4200)                          |
|   0xE3   | CALLF           | EOF Subroutine Call                             | [EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)                          |
|   0xE4   | RETF            | EOF Subroutine return                           | [EIP-4750](https://eips.ethereum.org/EIPS/eip-4750)                          |
|   0xE5   | JUMPF           | EOF Function Jump                               | [EIP-6209](https://eips.ethereum.org/EIPS/eip-6209)                          |
|   0xE6   | DUPN            | Unlimited dup                                   | [EIP-663](https://eips.ethereum.org/EIPS/eip-663)                            |
|   0xE7   | SWAPN           | Unlimited swap                                  | [EIP-663](https://eips.ethereum.org/EIPS/eip-663)                            |
|   0xE8   | DATALOAD        | Loads data from EOF data section, via stack     | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xE9   | DATALOADN       | Loads data from EOF data section, via immediate | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xEA   | DATASIZE        | Size of the EOF data section                    | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xEB   | DATACOPY        | Bulk EOF data copy                              | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xEC   | CREATE3         | Create from EOF contained initcode              | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xED   | RETURNCONTRACT  | contract to be created, references EOF data     | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xF6   | PAY             | transfers value from caller to target           | [EIP-5920](https://eips.ethereum.org/EIPS/eip-5920)                          |
|   0xF7   | CREATE4         | Create from transaction contained initcode      | TBD - [mega EOF](https://notes.ethereum.org/@ipsilon/mega-eof-specification) |
|   0xF8   | CALL2           | CALL without gas and output memory              | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          ||
|   0xF9   | DELEGATECALL2   | DELEGATECALL without gas and output memory      | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          |
|   0xFB   | STATICCALL2     | STATICCALL without gas and output memory        | [EIP-7069](https://eips.ethereum.org/EIPS/eip-7069)                          |
|   0xFC   | SETCODE         | Change the code for the current contract        | [EIP-6913](https://eips.ethereum.org/EIPS/eip-6913)                          |                                                                            |
