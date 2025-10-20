"""
Test cases for EOF Data section access instructions for EIP-7480.

EIP-7480 specifies instructions for accessing data stored in the dedicated
data section of the EOF format. Full specification: [EIP-7480: EOF - Data
section access instructions](https://eips.ethereum.org/EIPS/eip-7480).
Opcodes introduced: `DATALOAD` (`0xD0`), `DATALOADN` (`0xD1`), `DATASIZE`
(`0xD2`), `DATACOPY` (`0xD3`).
"""
