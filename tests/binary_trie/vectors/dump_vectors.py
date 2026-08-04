"""

TODO: This will be deleted before merging into forks/I*
TODO: It is here so that clients can quickly test only the trie and
TODO: embedding logic in isolation to the STF.

Generate the cross-client conformance vectors for the EIP-8297 binary
tree and its state embedding.

The vectors pin the observable outputs of `ethereum.binary_trie`: tree
roots for a spread of key shapes, the tree keys the embedding derives
for headers, storage slots and code chunks, `chunkify_code` output, and
the packed `encode_basic_data` leaf. On top of those primitives they
pin the composition, whole Ethereum state to root, through
`ethereum.state_pbt`. Client implementations for now should vendor the
emitted JSON as a fixture rather than re-running this script.

A pull request does not need to run this. The `Binary Trie Vectors`
workflow regenerates the JSON on `projects/binary-trie` whenever the
tree, the embedding, or this generator changes, and commits the result.

To run it by hand:

    uv run python tests/binary_trie/vectors/dump_vectors.py

which rewrites `binary_trie_vectors.json` in place. Apart from the
`source_commit` stamp, the output is a pure function of the
implementation (seeded RNG, no timestamps), so a behavior-preserving
change leaves every vector value untouched; the workflow compares with
the stamp removed and commits only when the values actually moved.
"""

import json
import random
import subprocess
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Sequence, Tuple

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U32, U64, U256, Uint

from ethereum.binary_trie.embedding import (
    address20_to_address32,
    chunkify_code,
    encode_basic_data,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_chunk,
    get_tree_key_for_code_hash,
    get_tree_key_for_header,
    get_tree_key_for_storage_slot,
)
from ethereum.binary_trie.trie import BinaryTrie, root, trie_set
from ethereum.crypto.hash import keccak256
from ethereum.state import Account, Address
from ethereum.state_pbt import (
    State,
    set_account,
    set_storage,
    state_root,
    store_code,
)

VECTORS_PATH = Path(__file__).parent / "binary_trie_vectors.json"

SOURCE = "ethereum/execution-specs projects/binary-trie"

V1 = bytes.fromhex("01" * 32)
V2 = bytes.fromhex("02" * 32)
V3 = bytes.fromhex("03" * 32)

ADDRESS20 = bytes.fromhex("00112233445566778899aabbccddeeff00112233")

# Addresses of the `pbt_state` cases. A and B match the ones the
# spec's own `tests/binary_trie/test_state_pbt.py` uses, so a case
# lifted from there keeps its address.
ADDRESS_A = b"\xaa" * 20
ADDRESS_B = b"\xbb" * 20
ADDRESS_C = b"\xcc" * 20

PUSH4 = bytes([0x63])
PUSH32 = bytes([0x7F])

# Code sized to each side of the header/overflow boundary. The header
# holds chunks 0-127, so 128 chunks is the largest code that stays in
# it and 129 chunks the smallest that reaches the code zone.
HEADER_ONLY_CODE = b"\x01" * (31 * 128)
OVERFLOW_CODE = b"\x01" * (31 * 129)

# PUSH32 at position 30, so its data spills across the first chunk
# boundary and the second chunk opens with a non-zero push-data count.
PUSH32_SPILL_CODE = b"\x01" * 30 + PUSH32 + bytes(range(32)) + b"\x01" * 5

# Largest integer a JSON number holds exactly, used as a nonce that
# stresses the packed field without leaving what a JSON parser can
# represent.
MAX_JSON_SAFE_INT = 2**53 - 1


def hx(b: bytes) -> str:
    """Render `b` as a `0x`-prefixed lowercase hex string."""
    return "0x" + bytes(b).hex()


def trie_root_case(
    name: str, entries: Sequence[Tuple[bytes, bytes]]
) -> Dict[str, Any]:
    """
    Build one tree-root case from an ordered list of `(key, value)`
    pairs, applied in order with `trie_set`.

    Duplicates are preserved in the serialized output so consumers can
    replay overwrites in the same order.
    """
    t = BinaryTrie()
    for k, v in entries:
        trie_set(t, Bytes(k), Bytes32(v))
    return {
        "name": name,
        "entries": [{"key": hx(k), "value": hx(v)} for k, v in entries],
        "root": hx(root(t)),
    }


def trie_root_cases() -> List[Dict[str, Any]]:
    """
    Build the tree-root cases: hand-picked key shapes (divergence at the
    first and last bit, shared prefixes, mixed key lengths, an
    overwrite) plus a deterministic pseudo-random spread.
    """
    cases = [
        trie_root_case("empty", []),
        trie_root_case("single_leaf", [(b"\x00" * 34, V1)]),
        trie_root_case("single_leaf_one_byte_key", [(b"\xab", V1)]),
        trie_root_case(
            "two_leaves_diverge_first_bit",
            [(b"\x00" + b"\x11" * 33, V1), (b"\x80" + b"\x11" * 33, V2)],
        ),
        trie_root_case(
            "two_leaves_diverge_last_bit",
            [(b"\x22" * 33 + b"\x00", V1), (b"\x22" * 33 + b"\x01", V2)],
        ),
        trie_root_case(
            "three_leaves_shared_prefix",
            [
                (b"\xf0" + b"\x00" * 33, V1),
                (b"\xf1" + b"\x00" * 33, V2),
                (b"\x0f" + b"\x00" * 33, V3),
            ],
        ),
        trie_root_case(
            "mixed_key_lengths_34_and_66",
            [
                (b"\x00" + b"\xaa" * 32 + b"\x05", V1),
                (b"\xff" + b"\xbb" * 64 + b"\x07", V2),
            ],
        ),
        trie_root_case(
            "overwrite_takes_last_value",
            # same key written twice: the second trie_set overwrites
            [(b"\x42" * 34, V1), (b"\x42" * 34, V2)],
        ),
    ]

    # Deterministic pseudo-random case: 50 distinct 34-byte keys, listed
    # in generation (insertion) order.
    rng = random.Random(8297)
    rand_entries: Dict[bytes, bytes] = {}
    while len(rand_entries) < 50:
        k = bytes(rng.randrange(256) for _ in range(34))
        v = bytes(rng.randrange(256) for _ in range(32))
        rand_entries[k] = v
    cases.append(
        trie_root_case("random_50_keys_seed_8297", list(rand_entries.items()))
    )

    return cases


def embedding_cases() -> Dict[str, Any]:
    """
    Build the embedding cases: the tree keys one fixed account derives
    for its header leaves, storage slots and code chunks.

    The storage slot and code chunk indices straddle the header/overflow
    boundaries, so a client that mis-splits either zone disagrees here.
    """
    address32 = address20_to_address32(Bytes20(ADDRESS20))
    code_hash = keccak256(b"\xfe")  # hash of some 1-byte code
    return {
        "address20": hx(ADDRESS20),
        "address32": hx(address32),
        "basic_data_key": hx(get_tree_key_for_basic_data(address32)),
        "code_hash_key": hx(get_tree_key_for_code_hash(address32)),
        "header_sub_index_255_key": hx(
            get_tree_key_for_header(address32, Uint(255))
        ),
        "storage_slot_keys": {
            str(slot): hx(get_tree_key_for_storage_slot(address32, U256(slot)))
            for slot in [0, 1, 63, 64, 255, 256, 511, 512, 2**200]
        },
        "code_chunk_keys": {
            str(cid): hx(
                get_tree_key_for_code_chunk(
                    address32, Bytes32(code_hash), Uint(cid)
                )
            )
            for cid in [0, 1, 127, 128, 129, 383, 384]
        },
        "code_hash": hx(code_hash),
    }


def chunkify_cases() -> List[Dict[str, Any]]:
    """
    Build the `chunkify_code` cases, covering the empty program, padding
    of a short one, and PUSH data spilling across a chunk boundary.
    """

    def case(name: str, code: bytes) -> Dict[str, Any]:
        return {
            "name": name,
            "code": hx(code),
            "chunks": [hx(c) for c in chunkify_code(Bytes(code))],
        }

    # PUSH4 at position 29: its 4 data bytes spill 2 into chunk 1
    push4_boundary = b"\x01" * 29 + PUSH4 + b"\xaa\xbb\xcc\xdd" + b"\x01" * 10
    push32_spill = b"\x01" * 30 + PUSH32 + bytes(range(32)) + b"\x01" * 5

    return [
        {"name": "empty", "code": hx(b""), "chunks": []},
        case("stop_padded", b"\x00"),
        case("eip_example_push4_boundary", push4_boundary),
        case("push32_at_chunk_end_spills_31", push32_spill),
    ]


def basic_data_cases() -> List[Dict[str, Any]]:
    """
    Build the `encode_basic_data` cases, from an all-zero account up to
    each packed field at its maximum.
    """
    return [
        {
            "code_size": 0,
            "nonce": 0,
            "balance": "0x0",
            "encoded": hx(encode_basic_data(U32(0), U64(0), U256(0))),
        },
        {
            "code_size": 1234,
            "nonce": 42,
            "balance": hex(10**18),
            "encoded": hx(encode_basic_data(U32(1234), U64(42), U256(10**18))),
        },
        {
            "code_size": 2**32 - 1,
            "nonce": 2**64 - 1,
            "balance": hex(2**128 - 1),
            "encoded": hx(
                encode_basic_data(
                    U32(2**32 - 1), U64(2**64 - 1), U256(2**128 - 1)
                )
            ),
        },
    ]


class AccountSpec(NamedTuple):
    """
    Flat description of one account of a `pbt_state` case.

    `storage` is an ordered sequence of `(slot, value)` pairs rather
    than a mapping, so the order of the emitted JSON object is fixed
    by the case itself.
    """

    address: bytes
    nonce: int = 0
    balance: int = 0
    code: bytes = b""
    storage: Tuple[Tuple[int, int], ...] = ()


def pbt_state_case(
    name: str, accounts: Sequence[AccountSpec]
) -> Dict[str, Any]:
    """
    Build one `pbt_state` case: the flat account description as given,
    beside the root `ethereum.state_pbt` commits that state to.

    The root comes from `state_pbt`'s own `state_root`, driven through
    `store_code`, `set_account` and `set_storage`, so what the case
    pins is the composition of embedding and tree rather than a
    re-derivation of it here.

    The description is emitted as written, not as the state ends up
    holding it: a slot declared zero stays in the JSON even though
    `set_storage` drops it, since a consumer must reach the same root
    from the same input.
    """
    state = State()
    for spec in accounts:
        address = Address(spec.address)
        code_hash = store_code(state, Bytes(spec.code))
        set_account(
            state,
            address,
            Account(
                nonce=Uint(spec.nonce),
                balance=U256(spec.balance),
                code_hash=code_hash,
            ),
        )
        for slot, value in spec.storage:
            set_storage(
                state,
                address,
                Bytes32(U256(slot).to_be_bytes32()),
                U256(value),
            )
    return {
        "name": name,
        "accounts": {
            hx(spec.address): {
                "nonce": spec.nonce,
                "balance": hex(spec.balance),
                "code": hx(spec.code),
                "code_hash": hx(keccak256(Bytes(spec.code))),
                "storage": {
                    str(slot): hx(U256(value).to_be_bytes32())
                    for slot, value in spec.storage
                },
            }
            for spec in accounts
        },
        "root": hx(state_root(state)),
    }


def random_state_accounts() -> List[AccountSpec]:
    """
    Build a deterministic pseudo-random spread of accounts: mixed code
    lengths, storage scattered over the whole slot space, and balances
    and nonces filling their packed fields.

    Slots are deduplicated because they become JSON object keys, and
    drawn from `1` upwards because a zero value is a deletion.
    """
    rng = random.Random(8297)
    specs = []
    for _ in range(6):
        address = bytes(rng.randrange(256) for _ in range(20))
        code_length = rng.choice([0, 1, 31, 32, 100])
        code = bytes(rng.randrange(256) for _ in range(code_length))
        storage: Dict[int, int] = {}
        while len(storage) < rng.randrange(4):
            storage[rng.randrange(2**256)] = rng.randrange(1, 2**256)
        specs.append(
            AccountSpec(
                address=address,
                nonce=rng.randrange(2**32),
                balance=rng.randrange(2**128),
                code=code,
                storage=tuple(storage.items()),
            )
        )
    return specs


def pbt_state_cases() -> List[Dict[str, Any]]:
    """
    Build the whole-state cases: flat state descriptions and the roots
    `ethereum.state_pbt` commits them to.

    Between them they cover both sides of every boundary the embedding
    draws, the two ways a leaf collapses to absence, and the sharing of
    content-addressed overflow code.
    """
    boundary_slots = (0, 1, 63, 64, 255, 256, 2**256 - 1)
    return [
        pbt_state_case("empty_state", []),
        pbt_state_case(
            "single_eoa",
            [AccountSpec(address=ADDRESS_A, nonce=3, balance=10**18)],
        ),
        pbt_state_case(
            "eoa_zero_nonce_and_balance",
            [AccountSpec(address=ADDRESS_A)],
        ),
        pbt_state_case(
            "header_code_only",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=1,
                    balance=2**64,
                    code=PUSH32_SPILL_CODE,
                )
            ],
        ),
        pbt_state_case(
            "overflow_code_and_boundary_storage",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=1,
                    code=OVERFLOW_CODE,
                    storage=((63, 1), (64, 2), (256, 3)),
                )
            ],
        ),
        pbt_state_case(
            "storage_across_the_header_boundary",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=1,
                    storage=tuple(
                        (slot, index + 1)
                        for index, slot in enumerate(boundary_slots)
                    ),
                )
            ],
        ),
        pbt_state_case(
            "zero_storage_slot_is_absent",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=1,
                    storage=((7, 0), (8, 9), (300, 0)),
                )
            ],
        ),
        pbt_state_case(
            "full_header_stem",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=1,
                    code=HEADER_ONLY_CODE,
                    storage=tuple((slot, slot + 1) for slot in range(64)),
                )
            ],
        ),
        pbt_state_case(
            "shared_bytecode_two_accounts",
            [
                AccountSpec(
                    address=ADDRESS_A, nonce=1, balance=1, code=OVERFLOW_CODE
                ),
                AccountSpec(
                    address=ADDRESS_B, nonce=2, balance=2, code=OVERFLOW_CODE
                ),
            ],
        ),
        pbt_state_case(
            "delegation_designator",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=1,
                    code=b"\xef\x01\x00" + ADDRESS_C,
                )
            ],
        ),
        pbt_state_case(
            "code_chunks_of_zero_bytes",
            [AccountSpec(address=ADDRESS_A, nonce=1, code=b"\x00" * 62)],
        ),
        pbt_state_case(
            "max_basic_data_fields",
            [
                AccountSpec(
                    address=ADDRESS_A,
                    nonce=MAX_JSON_SAFE_INT,
                    balance=2**128 - 1,
                )
            ],
        ),
        pbt_state_case("random_6_accounts_seed_8297", random_state_accounts()),
    ]


def build_vectors() -> Dict[str, Any]:
    """
    Build the full vector set, without the `source_commit` stamp.

    Deterministic and free of process state: everything here is derived
    from the implementation alone.
    """
    return {
        "source": SOURCE,
        "trie_roots": trie_root_cases(),
        "embedding": embedding_cases(),
        "chunkify_code": chunkify_cases(),
        "encode_basic_data": basic_data_cases(),
        "pbt_state": pbt_state_cases(),
    }


def head_commit() -> str:
    """Return this checkout's HEAD commit."""
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).parent,
        text=True,
    ).strip()


def main() -> None:
    """
    Write the vectors, stamped with this checkout's HEAD.

    The stamp records which revision of the implementation the values
    correspond to, for the benefit of repositories that vendor the file.
    It is not part of the vectors: the workflow that regenerates them
    compares content with `source_commit` removed, so a run that changes
    nothing does not commit a new stamp.
    """
    vectors = build_vectors()
    stamped = {
        "source": vectors["source"],
        "source_commit": head_commit(),
        **{k: v for k, v in vectors.items() if k != "source"},
    }
    VECTORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with VECTORS_PATH.open("w") as f:
        json.dump(stamped, f, indent=2)
        f.write("\n")
    print(f"wrote {VECTORS_PATH}")


if __name__ == "__main__":
    main()
