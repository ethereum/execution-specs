"""
Structural tests for the Merkle Patricia Trie as a data structure.

Top-level rather than under a fork directory: the trie predates every EIP
and its rules are fork-invariant, so no fork introduced it. Tests are valid
from Osaka on, so every client consumes one identical set per fork. The
committed state root is the oracle; every docstring states the node path
as `pre:`/`post:` lines and asserts it against the reference
`patricialize` at fill time. Keys are mined (`constants.py`) so that
their keccak256 hashes force each shape.

Collapse cells, survivor kind x parent kind, over storage (S) and account
(A) tries; the account trie's root is always a branch of uncontrolled
accounts, so its root cells do not exist:

                 parent:  root    extension    branch
    survivor leaf          S       S A          S A
    survivor extension     S       S A          S A
    survivor branch        S       S A          S A

Each storage cell also runs against nodes the client built in an earlier
block. Extension splits: offset 0, offset 0 with a 1-nibble extension,
middle, last nibble, each at the root and under a branch parent. Root
transitions: every edge among empty, leaf, extension and branch. Arity:
1->2, 2->3, 3->2, 15->16, 16->15, 16->1, 16->0, at depth 4 and at the
root. Encoding: leaf RLP of 30, 31, 32 and 33 bytes reached from the key
side and from the value side; inline <-> hashed by value change and by
path growth; every (deleted child, survivor encoding) pair. One block:
insert+delete, delete+re-insert, delete+update, slot replacement, two
depths, two paths, two tries, a node shared by two tries. Index tries:
withdrawals at 1, 2, 3 and 16 entries; transactions and receipts at 17,
129, 130, 145, 257, 258 and 273. Account bookkeeping: creation, deletion
(same-transaction CREATE2 + SELFDESTRUCT), resurrection by transfer and
by withdrawal, storage-root flips on the collapse survivor.
"""
