Signature Types
===============

This is a list of existing, reserved and tentative signature types
for payloads signed using secp256k1.

Signature Types
---------------

See the sections below for additional notes on prefix bytes marked
Reserved or Tentative.

| Prefix byte | Specs or Purpose |
|-------------|------------------|
| 0x00  | Reserved: indicates legacy (untyped) trancactions |
| 0x01  | Reserved: [EIP-2930](https://eips.ethereum.org/EIPS/eip-2930) *(available in Berlin)* |
| 0x02  | Reserved: [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) *(available in London)* |
| 0x03  | Reserved: [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844) *(available in Cancun)* |
| 0x04  | Reserved: [EIP-3074](https://eips.ethereum.org/EIPS/eip-3074) |
| 0x19  | Reserved: prevents collision with [EIP-191](https://eips.ethereum.org/EIPS/eip-191) |
| 0xc0 - 0xff  | Invalid; collides with the initial byte of valid RLP encoded transactions |


Reserved Signature Types Motivation and History
-----------------------------------------------

Reserved prefix bytes are currently in use and should never be reused. This
avoids signature collisions that could have unintentional consequences, such as
authorizing unintended actions.

### Type 0x00 (0)

The prefix byte `0x00` is reserved to identify transactions which are untyped legacy
transactions. It is not prefixed, but allows software to use a numeric enum
value to indicate a legacy transaction.

This was an unintentional consequence of the internal type of 0 being exposed
in early JSON-RPC implementations, but is convenient as a canonical value to
use within APIs or databases.

### Type 0x19 (25)

The prefix byte `0x19` is reserved for data payloads to be signed according to
[EIP-191](https://eips.ethereum.org/EIPS/eip-191).

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
