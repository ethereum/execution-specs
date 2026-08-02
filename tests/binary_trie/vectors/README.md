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
| `embedding` | object | Tree keys derived for one fixed account. |
| `chunkify_code` | array | `chunkify_code` inputs and outputs. |
| `encode_basic_data` | array | Packed account header leaves. |

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

All keys in this section belong to a single test account.

| Field | Type | Meaning |
| --- | --- | --- |
| `address20` | hex | The legacy 20-byte test address. |
| `address32` | hex | Its 32-byte tree form. |
| `basic_data_key` | hex | Tree key of the account's basic-data header leaf. |
| `code_hash_key` | hex | Tree key of the account's code-hash header leaf. |
| `header_sub_index_255_key` | hex | Tree key at header sub-index 255, the last sub-index of the header stem. |
| `storage_slot_keys` | object | Decimal-string slot number to tree key. |
| `code_chunk_keys` | object | Decimal-string chunk index to tree key. |
| `code_hash` | hex | Keccak hash of the test account's bytecode; the content address the overflow chunk keys derive from. |

`storage_slot_keys` carries slots 0, 1, 63, 64, 255, 256, 511, 512, and
`2**200`. Slots below 64 live in the account header, so the 63/64 pair
straddles the boundary between the header and the storage zone; the
remaining values walk across successive overflow stems, and `2**200`
exercises the `U256` arithmetic on a slot number no fixture can reach by
counting. Note that the object key for the large slot is its full
decimal expansion, not an exponent.

`code_chunk_keys` carries chunk indices 0, 1, 127, 128, 129, 383 and
384. Chunks below 128 live in the account header, so the 127/128 pair
straddles the boundary between the header and the code zone, and the
383/384 pair crosses from one overflow stem to the next.

Overflow code is content-addressed, so the chunk keys past the header
are derived from `code_hash` rather than from the address
alone. A consumer reproducing these keys must feed in that same hash.

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
