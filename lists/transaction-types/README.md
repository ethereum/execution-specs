Transaction Type List
=====================

This is a list of existing, reserved and tentative
[EIP-2718](https://eips.ethereum.org/EIPS/eip-2718) TransactionTypes.

Transaction Types
-----------------

| Version Byte | Specs or Purpose |
|--------------|------------------|
| 0x00  | Reserved: indicates legacy (untyped) trancactions *(see notes below)* |
| 0x01  | [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930) *(available in Berlin)* |
| 0x02  | [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) *(available in London)* |
| 0x03  | Reserved: prevents collision with [EIP-3074](https://eips.ethereum.org/EIPS/eip-3074) *(see notes below)* |
| 0x18  | Reserved: prevents collision with [EIP-191](https://eips.ethereum.org/EIPS/eip-191) *(see notes below)* |
| 0x80 - 0xff  | Invalid; collides with the initial byte of valid RLP encoded transactions |


Reserved Transaction Types Motivation and History
-------------------------------------------------

Reserved version bytes cannot be used as an [EIP-2718](https://eips.ethereum.org/EIPS/eip-2718)
TransactionType and should never be used as a typed transaction prefix.

We disallow prefixing with reserved bytes to prevent encoded transactions from
colliding with data that may otherwise be signed to prevent unintentionally
authorizing unintended transactions.


### Type 0x00 (0)

The TransactionType `0x00` is reserved to identify transactions which
are untyped legacy transactions. It is not prefixed, but allows
software to use a numeric enum value to indicate a legacy transaction.

This was an unintentional consequence of the internal type of 0 being
exposed in early JSON-RPC implementations, but is convenient as a
canonical value to use within APIs or databases.


### Type 0x19 (25)

The TransactionType `0x19` is reserved to prefix data payloads to be
signed according to [EIP-191](https://eips.ethereum.org/EIPS/eip-191).

The initial byte of `0x19` has long been used for the purpose of
prefixing a series of bytes to be signed, rather than a transaction
since a valid RLP-encoded transaction could not begin with it (prior to 
[EIP-2718](https://eips.ethereum.org/EIPS/eip-2718)) and represents the
Bitcoin varint length of the string `"Ethereum signed Message:\n"`.

It was carried over from the technique Bitcon used to sign personal messages
(which uses `"\18Bitcoin signed message:\n"`) but was extended with
[EIP-191](https://eips.ethereum.org/EIPS/eip-191), which effectively
retconned signed personal messages into a scheme that is extensible,
allowing new types of data and structures to be safely signed with
the same prefix byte.


Tentative Transaction Types
---------------------------

Proposed TransactionTypes to reserve or for upcoming purposes, but
still subject to change.


### Type 0x03 (3)

The TransactionType `0x03` is reserved to prefix data payload operand
to be signed for the [EIP-3074](https://eips.ethereum.org/EIPS/eip-3074)
`AUTHCALL` opcode.


