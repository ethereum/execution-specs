"""
The recent root contract introduced by [EIP-8272], which lets frame
transactions verify recent application roots.

A frame transaction verifies recent application roots by
running an ordinary [`VERIFY`][v] frame against
[`RECENT_ROOT_ADDRESS`][rra]; root sources publish roots by calling the
same contract. The contract is an ordinary contract created by the
deployment transaction in the EIP; the fork writes nothing at its
address.

[EIP-8272]: https://eips.ethereum.org/EIPS/eip-8272
[v]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameMode.VERIFY
[rra]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_ADDRESS
"""  # noqa: E501

from typing import Final

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, Uint

from ethereum.crypto.hash import Hash32, keccak256

from .fork_types import Address

RECENT_ROOT_ADDRESS: Final[Address] = Address(
    bytes.fromhex("8272D9679689Ea2f307140CdF9002D27dC00Ffff")
)
"""
Address of the recent root contract.

Calls with 64 bytes of calldata publish a root for the caller's source;
calls with one to [`MAX_RECENT_ROOT_REFERENCES`][mrr] tuples of
[`RECENT_ROOT_TUPLE_BYTES`][rtb] bytes each check those references. A
[`VERIFY`][v] frame targeting this address is a _recent root verifier
frame_; if the contract reverts, the frame fails and the transaction is
invalid, as for any [`VERIFY`][v] frame.

[mrr]: ref:ethereum.forks.bogota.recent_roots.MAX_RECENT_ROOT_REFERENCES
[rtb]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_TUPLE_BYTES
[v]: ref:ethereum.forks.bogota.transactions.frame_transaction.FrameMode.VERIFY
"""  # noqa: E501

RECENT_ROOT_NONCE: Final[Uint] = Uint(1)
"""
Nonce of the recent root contract after its deployment transaction.
"""

RECENT_ROOT_LENGTH: Final[Uint] = Uint(8192)
"""
Number of ring buffer entries a root source keeps: the root written in
slot `S` occupies index `S mod RECENT_ROOT_LENGTH`.
"""

RECENT_ROOT_USABLE_WINDOW: Final[Uint] = Uint(8191)
"""
Maximum age, in slots, of a referenceable root. The current slot itself is
never referenceable, so the window is one less than the buffer length.
"""

MAX_RECENT_ROOT_REFERENCES: Final[Uint] = Uint(16)
"""Maximum number of tuples in one validation call."""

RECENT_ROOT_TUPLE_BYTES: Final[Uint] = Uint(72)
"""
Length of a validation tuple: a 32-byte source identifier, an 8-byte
big-endian slot and a 32-byte root.
"""

RECENT_ROOT_WRITE_BYTES: Final[Uint] = Uint(64)
"""Length of a write call's calldata: a 32-byte salt and a 32-byte root."""

RECENT_ROOT_ENTRY_DOMAIN: Final[Hash32] = keccak256(b"RECENT_ROOT_ENTRY")
"""Domain separator of the committed entry hash."""

RECENT_ROOT_STORAGE_DOMAIN: Final[Hash32] = keccak256(b"RECENT_ROOT_STORAGE")
"""Domain separator of the storage key derivation."""

RECENT_ROOT_CODE: Final[Bytes] = Bytes(
    bytes.fromhex(
        "346100ba57366040146100c05736604836066100ba5780156100ba57610480811161"
        "00ba574b60005b602081013560c01c828110156100ba5780830361200011156100ba"
        "577f8f42481679c8e6fefa040974b3c905e0ce3f2e464ba93acdb074a41181617efc"
        "60005260488260203760686000207fbdc897da2177d260ff5f4be5d4b2aad43f89c3"
        "347a305b584fa5a2546d053daa60005290611fff1660c01b60405260486000205414"
        "156100ba5760480182811061002857005b60006000fd5b3360005260206000602037"
        "6034600c20807f8f42481679c8e6fefa040974b3c905e0ce3f2e464ba93acdb074a4"
        "1181617efc6040524b606852606052602060206088376068604020817fbdc897da21"
        "77d260ff5f4be5d4b2aad43f89c3347a305b584fa5a2546d053daa60a852611fff4b"
        "1660d05260c852604860a8205500"
    )
)
"""
Runtime code of the recent root contract, as created at
[`RECENT_ROOT_ADDRESS`][rra] by the deployment transaction in
[EIP-8272] (keccak256
`0xda160390a838ee04013b2ff3abf4decc9aa3cc6c2f59dd90ca176c2b850be4e3`):

* A call carrying value reverts.
* With exactly [`RECENT_ROOT_WRITE_BYTES`][rwb] bytes of calldata, the
  call is a write: with the caller as the source address and calldata
  `0..32` as the salt, it stores
  [`recent_root_entry_hash`][reh] of the current slot and the root in
  calldata `32..64` under the caller's
  [`recent_root_storage_key`][rsk] for that slot, then stops. In a static
  context the store fails, leaving storage unchanged.
* Otherwise the call is a validation: it reverts unless the calldata is
  one to [`MAX_RECENT_ROOT_REFERENCES`][mrr] tuples of
  [`RECENT_ROOT_TUPLE_BYTES`][rtb] bytes, and for each tuple checks that
  its slot is strictly before the current slot, that the root is at most
  [`RECENT_ROOT_USABLE_WINDOW`][ruw] slots old and that the tuple's entry
  hash is stored under its storage key, reverting at the first failure
  and stopping with no return data otherwise.

The current slot is read with `SLOTNUM`. The contract reads no account
other than itself and no storage other than the keys derived from its
calldata.

[EIP-8272]: https://eips.ethereum.org/EIPS/eip-8272
[rra]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_ADDRESS
[rwb]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_WRITE_BYTES
[reh]: ref:ethereum.forks.bogota.recent_roots.recent_root_entry_hash
[rsk]: ref:ethereum.forks.bogota.recent_roots.recent_root_storage_key
[mrr]: ref:ethereum.forks.bogota.recent_roots.MAX_RECENT_ROOT_REFERENCES
[rtb]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_TUPLE_BYTES
[ruw]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_USABLE_WINDOW
"""  # noqa: E501


def recent_root_source_id(source_address: Address, salt: Bytes32) -> Hash32:
    """
    Derive the identifier of a root source: the keccak256 of the source
    address followed by the salt.

    A source address may publish under any number of salts; each pair is
    an independent ring buffer of roots.
    """
    return keccak256(source_address + salt)


def recent_root_entry_hash(
    source_id: Hash32, slot: U64, root: Bytes32
) -> Hash32:
    """
    Derive the entry committed for `(source_id, slot, root)`: the keccak256
    of [`RECENT_ROOT_ENTRY_DOMAIN`][red], the source identifier, the slot as
    an eight-byte big-endian integer and the root.

    Committing to the source and the slot keeps a root of another source,
    or a stale occupant of the same ring buffer index, from satisfying a
    reference.

    [red]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_ENTRY_DOMAIN
    """  # noqa: E501
    return keccak256(
        RECENT_ROOT_ENTRY_DOMAIN + source_id + slot.to_be_bytes8() + root
    )


def recent_root_storage_key(source_id: Hash32, slot: U64) -> Bytes32:
    """
    Derive the storage key holding the entry of `slot` for a root source:
    the keccak256 of [`RECENT_ROOT_STORAGE_DOMAIN`][rsd], the source
    identifier and the ring buffer index `slot mod RECENT_ROOT_LENGTH` as
    an eight-byte big-endian integer.

    [rsd]: ref:ethereum.forks.bogota.recent_roots.RECENT_ROOT_STORAGE_DOMAIN
    """  # noqa: E501
    index = U64(Uint(slot) % RECENT_ROOT_LENGTH)
    return Bytes32(
        keccak256(
            RECENT_ROOT_STORAGE_DOMAIN + source_id + index.to_be_bytes8()
        )
    )
