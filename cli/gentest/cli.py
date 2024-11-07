"""
CLI interface for generating blockchain test scripts.

It extracts a specified transaction and its required state from a blockchain network
using the transaction hash and generates a Python test script based on that information.
"""

from sys import stderr
from typing import TextIO

import click

from ethereum_test_base_types import Hash

from .source_code_generator import get_test_source
from .test_context_providers import StateTestProvider


@click.command()
@click.argument("transaction_hash")
@click.argument("output_file", type=click.File("w", lazy=True))
def generate(transaction_hash: str, output_file: TextIO):
    """
    Extracts a transaction and required state from a network to make a blockchain test out of it.

    TRANSACTION_HASH is the hash of the transaction to be used.

    OUTPUT_FILE is the path to the output python script.
    """
    provider = StateTestProvider(transaction_hash=Hash(transaction_hash))

    source = get_test_source(provider=provider, template_path="blockchain_test/transaction.py.j2")
    output_file.write(source)

    print("Finished", file=stderr)
