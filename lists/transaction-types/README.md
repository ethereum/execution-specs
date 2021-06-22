Transaction Type List
=====================

This is a list of existing, reserved and possibly future TransactionType values
for [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) transaction.

Transaction Types
-----------------

| Version | Specs or Purpose |
|---------|------------------|
| 0x00  | Reserved: to describe legacy (untyped) trancactions (see notes below) |
| 0x01  | [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930) (avaialbe in Berlin) |
| 0x02  | [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) (available in London) |
| 0x03  | Reserved: prevents collision with [EIP-3074](https://eips.ethereum.org/EIPS/eip-3074) (see notes below) |
| 0x18  | Reserved: prevent collision with [EIP-191](https://eips.ethereum.org/EIPS/eip-191) (see notes below) |


Reserved Transaction Types Motivation and History
-------------------------------------------------

Reserved types cannot be used as [EIP-2918](https://eips.ethereum.org/EIPS/eip-2718)
TransactionType values and should never be used as a TransactionType prefix.

### Type 0x00 (0)

The TransactionType 0x00 is reserved to identify transactions which
are untyped, legacy transactions. It is not prefixed, but allows
software to use a numeric value to indicate a transaction has no prefix.

This was an unintentional consequence of the internal type of 0 being
exposed in early JSON-RPC implementations, but is convenience as it
allows a canonical value to indicate a transaction is untyped.

### Type 0x03 (3)

The TransactionType 0x03 is reserved to prefix data payloads to be
signed for the `AUTHCALL` opcode.



### Type 0x19 (25)

The TransactionType 0x18 is reserved to prefix data payloads to be
signed according to [EIP-191](https://eips.ethereum.org/EIPS/eip-191).

The initial byte of `0x19` has long been used for the purpose of
marking a series of bytes to be signed, rather than a transaction.

The value 0x19 was choosen as it could not mark the beginning of a
valid RLP-encoded transaction (prior to [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718))
and represents the Bitcoin varint length of the string `"Ethereum signed Message:\n"`,
which was its original use before being extended for [EIP-191](https://eips.ethereum.org/EIPS/eip-191).
This was carried over from the similar Bitcoin prefixed messages.

For these reasons, we wish to prevent a transaction type from colliding
with the existing signed data.
