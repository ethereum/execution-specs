"""
Structural tests for the Merkle Patricia Trie.

No fork changes the trie's rules, so the suite sits above the fork
directories and fills from Osaka, the latest deployed fork. Keys are
mined (`constants.py`) so that their keccak256 hashes force each node
shape, and every test asserts the shape it exercises against the
reference `patricialize` at fill time (`trie_shape.py`). The committed
root is the oracle: a client that builds or encodes a node differently
computes a different root.

Docstrings give the node path along the key under test as `pre:` and
`post:` lines. `ext(n)` is an extension of `n` nibbles, `branch@d` a
branch at depth `d`, `leaf(r)` a leaf with `r` nibbles left, `{a, b}` a
branch's children, `k x leaf(r)` `k` such children, `h: node` the child
under nibble `h`, `..` nodes the test leaves alone, and `31 B` a node's
RLP size: under 32 bytes a node is inlined in its parent, from 32 bytes
on it is referenced by hash.
"""
