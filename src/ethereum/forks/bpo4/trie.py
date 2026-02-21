"""
State Trie.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The state trie is the structure responsible for storing
`.fork_types.Account` objects.
"""

from ethereum.trie import (
    EMPTY_TRIE_ROOT as EMPTY_TRIE_ROOT,
)
from ethereum.trie import (
    Trie as Trie,
)
from ethereum.trie import (
    copy_trie as copy_trie,
)
from ethereum.trie import (
    root as root,
)
from ethereum.trie import (
    trie_get as trie_get,
)
from ethereum.trie import (
    trie_set as trie_set,
)
