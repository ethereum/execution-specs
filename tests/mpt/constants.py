"""
Keys whose keccak256 hashes force specific Merkle Patricia Trie shapes.

Storage slots are hashed as 32-byte big-endian indices, addresses as
20-byte big-endian integers, CREATE2 salts through the deterministic
factory with the self-destructing init code of the account tests. Every
value was found by brute-force search over consecutive integers; each
comment states the search rule precisely enough to reproduce the value
with a few lines of Python. Nothing here is recomputed at fill time: the
tests that use a group assert the trie shape it is meant to produce
against the reference `patricialize`, so a wrong value fails the fill.

"Share exactly n nibbles" means the keccak256 hashes agree on their first
n hex digits and differ on digit n. Searches start at 1 (slots), 0x10000
(addresses, above the precompile range) or 0 (salts) unless stated.
"""

from typing import Final

# --- storage slots ------------------------------------------------------

# An arbitrary slot: single-leaf inserts, updates and deletes.
SINGLE_SLOT: Final = 1

# Lowest pair sharing exactly 4 nibbles: ext(4) -> branch -> 2 leaves.
TWO_SLOTS_EXT4: Final = (325, 370)

# First 4-nibble prefix reached by 16 slots with 16 distinct 5th nibbles,
# ordered by that nibble 0x0..0xf: a full 16-child branch at depth 4.
SIXTEEN_SLOTS_BRANCH4: Final = (
    112364,
    21828,
    13771,
    663311,
    538859,
    613318,
    472265,
    440100,
    195383,
    604163,
    187508,
    428313,
    205780,
    31044,
    192412,
    477936,
)

# (l1, l2, l3): l1/l2 are the lowest pair sharing exactly 5 nibbles; l3 is
# the smallest other slot sharing exactly 2 with them. Trie: ext(2) ->
# branch@2 -> {l3, ext(2) -> branch@5 -> {l1, l2}}.
EXT_MERGE_TRIO: Final = (663, 800, 84)

# (a, b, c): a/b are the lowest pair sharing exactly 3 nibbles; c is the
# smallest other slot sharing exactly 2 with them. Trie: ext(2) ->
# branch@2 -> {c, branch@3 -> {a, b}} with no extension between branches.
BRANCH_SURVIVOR_TRIO: Final = (82, 125, 615)

# SINGLE_SLOT and the smallest slot sharing exactly 0 nibbles with it: a
# root branch with two leaves.
ROOT_PAIR: Final = (SINGLE_SLOT, 2)

# Smallest slot per first nibble 0x0..0xf, ordered by that nibble: a root
# branch with all 16 children.
ROOT_SIXTEEN: Final = (5, 16, 93, 17, 2, 21, 9, 36, 4, 25, 7, 1, 3, 12, 40, 6)

# Lowest pair sharing exactly 8 nibbles: 55 remaining nibbles, so a leaf
# with a single-byte value is 31 bytes (embedded); a 2-byte value makes it
# 33 bytes (hashed).
EMBEDDED_LEAF_PAIR: Final = (40364, 105566)

# Lowest pair sharing exactly 7 nibbles: 56 remaining nibbles, so the same
# single-byte value gives exactly 32 bytes, the first hashed size.
HASHED_LEAF_PAIR: Final = (21471, 23527)

# Smallest slot > 1 sharing exactly 1 nibble with SINGLE_SLOT; with it,
# {SINGLE_SLOT, sibling} is ext(1) -> branch@1 -> 2 leaves.
SINGLE_SLOT_SIBLING_DEPTH1: Final = 14

# Smallest slot > 1 sharing exactly 2 nibbles with SINGLE_SLOT (and hence
# exactly 1 with SINGLE_SLOT_SIBLING_DEPTH1).
SINGLE_SLOT_SIBLING_DEPTH2: Final = 24

# Smallest slot outside TWO_SLOTS_EXT4 sharing exactly 1 nibble with both.
TWO_SLOTS_EXT4_SIBLING_DEPTH1: Final = 40

# Smallest slot outside EXT_MERGE_TRIO sharing exactly 3 nibbles with its
# l1 and l2 (and hence 2 with l3).
EXT_MERGE_TRIO_SIBLING_DEPTH3: Final = 16294

# Smallest slot outside EMBEDDED_LEAF_PAIR sharing exactly 4 nibbles with
# both: ext(4) -> branch@4 -> {sibling, ext(3) -> branch@8 -> pair}.
EMBEDDED_LEAF_PAIR_SIBLING_DEPTH4: Final = 102457

# Smallest slots outside TWO_SLOTS_EXT4 sharing exactly 2 and exactly 3
# nibbles with both: split a committed extension in the middle or at its
# last nibble.
TWO_SLOTS_EXT4_SIBLING_DEPTH2: Final = 1326
TWO_SLOTS_EXT4_SIBLING_DEPTH3: Final = 549

# Lowest pair sharing exactly 10 nibbles: 53 remaining nibbles, so a leaf
# with a single-byte value is 30 bytes and a 2-byte value gives exactly
# 32, the first hashed size, from the value side.
VALUE_BOUNDARY_PAIR: Final = (247476, 515151)

# (x, y, s): x/y share exactly 9 nibbles, s exactly 8 with both, found by
# scanning for the first 8-nibble bucket holding such a triple. Every leaf
# is 31 bytes with a single-byte value: x/y have 54 remaining nibbles
# (even, 28-byte compact path), s has 55 (odd, also 28 bytes).
INLINE_TRIO: Final = (175378, 2311414, 458416)

# --- addresses ----------------------------------------------------------

# Same rules over 20-byte addresses. `pre.fund_address` raises if a mined
# address already exists in the pre-alloc.
TWO_ADDRS_EXT4: Final = (65866, 65956)

SIXTEEN_ADDRS_BRANCH4: Final = (
    538045,
    488954,
    750271,
    375353,
    328630,
    212848,
    401147,
    665194,
    142385,
    523167,
    397065,
    167913,
    82075,
    81870,
    481613,
    82519,
)

ADDR_EXT_MERGE_TRIO: Final = (65755, 66515, 66334)

# Smallest addresses outside TWO_ADDRS_EXT4 sharing exactly 1 and exactly
# 3 nibbles with both: controlled branch parents above the mined group.
TWO_ADDRS_EXT4_SIBLING_DEPTH1: Final = 65545
TWO_ADDRS_EXT4_SIBLING_DEPTH3: Final = 68252

# --- CREATE2 salts ------------------------------------------------------

# Smallest salt whose factory-created address (see `DELETE_INITCODE` in
# the account tests) is a sibling of a mined address group: funding that
# address at genesis, then CREATE2-ing onto it and SELFDESTRUCT-ing in the
# same transaction deletes a committed account leaf (EIP-6780).
COLLAPSE_SALT: Final = 212508  # shares exactly 4 nibbles with TWO_ADDRS_EXT4
EXT_MERGE_SALT: Final = 58  # shares exactly 2 nibbles with ADDR_EXT_MERGE_TRIO
SHARE2_SALT: Final = 30  # shares exactly 2 nibbles with TWO_ADDRS_EXT4
SHARE3_SALT: Final = 2620  # shares exactly 3 nibbles with TWO_ADDRS_EXT4

# Smallest salt whose factory address for the account tests' SLOT_WRITER
# init code (`Initcode(deploy_code=SLOT_WRITER)`) shares exactly 4 nibbles
# with COLLAPSE_SALT's address: a contract survivor in that branch.
SURVIVOR_SALT: Final = 22435

# Smallest salts whose created addresses fall under SIXTEEN_ADDRS_BRANCH4's
# 4-nibble prefix with 5th nibbles 0x1..0xf; with SIXTEEN_ADDRS_BRANCH4[0]
# (5th nibble 0x0) they fill a 16-child branch of deletable leaves.
SIXTEEN_SALTS_BRANCH4: Final = (
    180582,
    952249,
    486347,
    180435,
    1714432,
    662143,
    664659,
    1263774,
    4447739,
    216590,
    1338274,
    1320265,
    85523,
    1275998,
    487577,
)
