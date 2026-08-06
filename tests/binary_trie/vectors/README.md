# Binary Trie Conformance Vectors

Cross-client conformance vectors for the [EIP-8297] binary trie and its
state embedding, generated from the reference implementation in
`src/ethereum/binary_trie/`.

While things are moving quickly, client implementations vendor
`binary_trie_vectors.json` and check against it. This mainly makes
debugging quicker, since you don't need to run through the whole
STF to debug an issue.

[EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297

## Important Files

- `binary_trie_vectors.json`: the file clients vendor. Not committed by
  hand — the `Binary Trie Vectors` workflow generates it on
  `projects/binary-trie` and commits it there.
- `dump_vectors.py`: the generator that produces it.

## Regenerating

To run it by hand, from the repository root:

```console
uv run python tests/binary_trie/vectors/dump_vectors.py
```

## Schema

Every byte string is a `0x`-prefixed lowercase hex string. Numbers that
fit comfortably in a JSON integer are JSON numbers; anything that could
exceed a JSON-safe integer is hex.

### Top level

| Field | Type | Meaning |
| --- | --- | --- |
| `source` | string | The repository and branch the vectors originate from. |
| `source_commit` | string | Commit of the implementation these values were generated from. |
| `trie_roots` | array | Tree roots for a spread of key shapes. |
| `embedding` | object | Tree keys derived for one fixed account and one fixed code hash. |
| `chunkify_code` | array | `chunkify_code` inputs and outputs. |
| `encode_basic_data` | array | Packed account header leaves. |
| `pbt_state` | array | Whole states and the roots they commit to. |

### `trie_roots`

An array of `{name, entries, root}`.

- `entries`: an **ordered** array of `{key, value}` objects. The order
  is significant and duplicate keys are legal: writes are applied in
  sequence and the last write to a key wins. The
  `overwrite_takes_last_value` case depends on this, so a consumer must
  replay the entries in order rather than loading them into an
  unordered map.
- `key`: a variable-length tree key.
- `value`: 32 bytes.
- `root`: the 32-byte root after all entries have been applied in
  order.

The nine cases and the structural property each one covers:

| Name | Covers |
| --- | --- |
| `empty` | The root of a tree with no entries. |
| `single_leaf` | One 34-byte (account-zone length) key. |
| `single_leaf_one_byte_key` | A key far shorter than a real zone key, exercising short-key handling. |
| `two_leaves_diverge_first_bit` | Divergence at the very first bit, so the split happens at the root. |
| `two_leaves_diverge_last_bit` | Divergence at the very last bit, the deepest split the keys allow. |
| `three_leaves_shared_prefix` | Two keys sharing a prefix alongside a third that does not, exercising internal-node reuse. |
| `mixed_key_lengths_34_and_66` | The two real key lengths together: 34 bytes for account/code-zone keys, 66 for storage-zone keys. |
| `overwrite_takes_last_value` | The same key written twice; the second value must win. |
| `random_50_keys_seed_8297` | 50 distinct pseudo-random 34-byte keys, listed in insertion order, as a broad spread over the key space. |

### `embedding`

The header and storage keys in this section belong to a single test
account; the chunk keys belong to a standalone code hash, which no
address touches.

| Field | Type | Meaning |
| --- | --- | --- |
| `address20` | hex | The legacy 20-byte test address. |
| `address32` | hex | Its 32-byte tree form. |
| `basic_data_key` | hex | Tree key of the account's basic-data header leaf. |
| `code_hash_key` | hex | Tree key of the account's code-hash header leaf. |
| `delegation_key` | hex | Tree key of the account's delegation header leaf. An account holds this or the code-hash leaf, never both. |
| `storage_slot_keys` | object | Decimal-string slot number to tree key. |
| `code_chunk_keys` | object | Decimal-string chunk index to tree key. |
| `code_hash` | hex | Keccak hash of a standalone one-byte code; the content address every chunk key derives from. |

`storage_slot_keys` carries slots 0, 1, 63, 64, 255, 256, 511, 512, and
`2**200`. Slots below 64 live in the account header, so the 63/64 pair
straddles the boundary between the header and the storage zone; the
remaining values walk across successive overflow stems, and `2**200`
exercises the `U256` arithmetic on a slot number no fixture can reach by
counting. Note that the object key for the large slot is its full
decimal expansion, not an exponent.

`code_chunk_keys` carries chunk indices 0, 1, 255, 256, 257, 511, 512
and 2114. Every chunk lives in the code zone, 256 chunks to a stem
("code groups"), so the 255/256 and 511/512 pairs each cross from one
stem to the next; 2114 is the last chunk of a maximum-size (65536-byte)
code, in group 8.

Code is content-addressed: chunk keys are derived from `code_hash` and
the chunk index alone, with no address involved, so contracts with
identical bytecode share their chunk leaves. A consumer reproducing
these keys must feed in that same hash.

A delegation indicator is the exception, and is not code: it is keyed
by its account, at `delegation_key`, so two accounts delegating to the
same target share nothing.

### `chunkify_code`

An array of `{name, code, chunks}`, where `code` is the input bytecode
and `chunks` is the resulting list of 32-byte chunks.

Each chunk is one leading byte followed by 31 bytes of code, zero-padded
if the code runs out. The leading byte counts how many of the chunk's
31 payload bytes are push data continuing from a push instruction that
began in an earlier chunk, capped at 31. That count is what lets a chunk
be interpreted without fetching its predecessors.

### `encode_basic_data`

An array of `{code_size, nonce, balance, encoded}`.

`code_size` and `nonce` are JSON numbers; `balance` is a `0x` hex string
because its values exceed what a JSON integer holds safely. `encoded` is
the 32-byte packed leaf, laid out big-endian throughout:

| Offset | Length | Field |
| --- | --- | --- |
| 0 | 1 | Version byte, currently zero. |
| 1 | 3 | Reserved, zero. |
| 4 | 4 | Code size. |
| 8 | 8 | Nonce. |
| 16 | 16 | Balance. |

The balance field is 16 bytes, so a balance must be less than `2**128`
to be encodable.

### `pbt_state`

The other sections pin the trie and the embedding primitives
separately. This one pins their composition: whole Ethereum state to
root, which is where an embedding mistake actually shows up. The roots
come from `src/ethereum/state_pbt.py`, the reference state provider
built on that embedding.

An array of `{name, accounts, root}`.

- `accounts`: an object keyed by the account's 20-byte address, as
  hex. Order is not significant; the root is a function of the account
  set alone.
- `root`: the 32-byte state root of exactly that set of accounts.

Each account value:

| Field | Type | Meaning |
| --- | --- | --- |
| `nonce` | number | Account nonce. |
| `balance` | hex | Account balance, as a `0x` hex string since it can exceed a JSON-safe integer. |
| `code` | hex | The account's bytecode; `0x` for an account with none. |
| `code_hash` | hex | `keccak256(code)`, the value of the code-hash leaf. Derived, and repeated here because the chunk keys are content-addressed by it. |
| `storage` | object | Decimal-string slot number to the slot's 32-byte value. |

Nonces are JSON numbers and every case keeps them at or below
`2**53 - 1`, the largest integer a JSON number holds exactly. Storage
slot numbers are object keys in full decimal expansion, matching
`embedding`'s `storage_slot_keys`, because they range over the whole
`2**256` space.

Building the state is: for each account, write its basic data leaf
(`encode_basic_data` over `len(code)`, `nonce`, `balance`), its
code-hash leaf, one leaf per `chunkify_code` chunk, and one leaf per
storage slot. Three rules decide what is *not* written that way, and
cases below depend on all of them:

- **Zero is absent.** A leaf whose 32-byte value is all zeros is not
  stored; it reads back as the zero it stood for. This reaches a
  storage slot written to zero, a code chunk of 31 zero bytes, and the
  basic data of an account with no code, zero nonce and zero balance.
  A `storage` entry with a zero value is therefore still listed in the
  case, as part of the input a consumer must reproduce the root from,
  even though no leaf results.
- **Code is sized, not delimited.** Because a chunk can be absent, the
  number of chunk leaves does not give the code's length; `code_size`
  in the basic data leaf does.
- **Exactly one of the code-hash and delegation leaves.** An account
  whose `code` is an EIP-7702 indicator — the three bytes `0xef0100`
  and a 20-byte address, 23 bytes exactly — writes that code to its
  delegation leaf instead, right-padded with nine zero bytes, and
  writes neither a code-hash leaf nor any chunk. Every other account
  writes a code-hash leaf and no delegation leaf. The test is on the
  code, never on its hash: `code_hash_starting_with_the_delegation_marker`
  is a contract whose `code_hash` begins with the marker and must
  still be embedded as code.

The eighteen cases and what each one covers:

| Name | Covers |
| --- | --- |
| `empty_state` | No accounts at all. The root is `EMPTY_TRIE_ROOT`, 32 zero bytes, not the hash of anything. |
| `single_eoa` | One EOA: exactly two leaves, basic data and code hash. |
| `eoa_zero_nonce_and_balance` | An EOA whose basic data encodes to 32 zero bytes, so only its code-hash leaf exists; that leaf alone is what distinguishes it from an absent account. |
| `code_with_push_data_spill` | Short code with a `PUSH32` spilling across a chunk boundary, so a chunk's leading push-data count is non-zero. |
| `code_and_boundary_storage` | 129 chunks of code beside storage on both sides of the header boundary. Its root is independently pinned by `tests/binary_trie/test_state_pbt.py::test_embedded_state_root_is_pinned`. |
| `code_across_the_group_boundary` | 257 chunks of code, one past a full code group, so its chunk keys span two stems (`tree_index` 0 and 1). |
| `storage_across_the_header_boundary` | Slots 0, 1, 63 in the header and 64, 255, 256, `2**256 - 1` in the storage zone, each with a distinct value so a swap between any two leaves is detectable. |
| `zero_storage_slot_is_absent` | Slots declared with a zero value beside a non-zero one; the root is that of the non-zero slot alone. |
| `full_header_occupancy` | Slots 0-63 filling every header storage sub-index beside 128 chunks of code: the header holds exactly `{0, 1}` and `64`-`127` -- sub-indices 128-255 are unallocated -- and every chunk leaf sits in the code zone. |
| `shared_bytecode_two_accounts` | Two accounts with identical 129-chunk code. Every chunk is content-addressed and must land on a single shared leaf per chunk, so the state has 133 leaves rather than 262. |
| `short_shared_code_two_accounts` | Two accounts with identical 2-chunk code, the common sharing case: 6 leaves rather than 8. |
| `delegation_designator` | An EIP-7702 designator, `0xef0100` followed by an address: 23 bytes held in one account-header leaf, right-padded with nine zero bytes, with `code_size` 23 and no code-hash or code-zone leaf. |
| `two_authorities_one_target` | Two accounts delegating to the same target. Their leaves carry identical values under different header stems, so the state has four leaves and the code zone stays empty — a client that content-addressed the indicator would produce one shared leaf and a different root. |
| `delegation_with_storage` | A delegated account with storage on both sides of the header boundary: the delegation leaf sits below the storage sub-indices and neither disturbs the other. |
| `code_hash_starting_with_the_delegation_marker` | A deployable contract whose `code_hash` begins `0xef0100`. It must embed as code — a code-hash leaf and a chunk — since the delegation test reads the code, not its hash. |
| `code_chunks_of_zero_bytes` | 62 zero bytes of code: both chunks are 32 zero bytes and are absent, so the account commits no chunk leaf at all while its `code_size` stays 62. |
| `max_basic_data_fields` | A balance of `2**128 - 1`, the largest the 16-byte field holds, beside the largest JSON-safe nonce. A balance of `2**128` or more cannot be committed at all. |
| `random_6_accounts_seed_8297` | Six pseudo-random accounts with mixed code lengths, scattered storage, and full-width balances, as a broad spread over the composition. |
