"""
Generate a Python blockchain test from a transaction hash.

This script can be used to generate Python source for a blockchain test case
that replays a mainnet or testnet transaction from its transaction hash.

Requirements:

1. Access to an archive node for the network where the transaction
    originates. A provider may be used.
2. The transaction hash of a type 0 transaction (currently only legacy
    transactions are supported).

Example Usage:

1. Generate a test for a transaction with hash

    ```console
    uv run gentest \
    0xa41f343be7a150b740e5c939fa4d89f3a2850dbe21715df96b612fc20d1906be \
    tests/paris/test_0xa41f.py
    ```

2. Fill the test:

    ```console
    fill --fork=Paris tests/paris/test_0xa41f.py
    ```

Limitations:

1. Only legacy transaction types (type 0) are currently supported.
"""

from .cli import generate  # noqa: 401
