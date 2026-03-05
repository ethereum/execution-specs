"""
Test cases for EIP-161: State trie clearing.

EIP-161 introduced the rule that empty accounts (balance=0, nonce=0,
no code) are deleted at the end of a transaction if they were "touched"
during execution.
"""
