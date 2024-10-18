"""
CLI interface for generating blockchain test scripts.

It extracts a specified transaction and its required state from a blockchain network
using the transaction hash and generates a Python test script based on that information.
"""

from sys import stderr
from typing import TextIO

import click
import jinja2

from ethereum_test_base_types import Hash

from .request_manager import RPCRequest
from .test_providers import BlockchainTestProvider

template_loader = jinja2.PackageLoader("cli.gentest")
template_env = jinja2.Environment(loader=template_loader, keep_trailing_newline=True)


@click.command()
@click.argument("transaction_hash")
@click.argument("output_file", type=click.File("w", lazy=True))
def generate(transaction_hash: str, output_file: TextIO):
    """
    Extracts a transaction and required state from a network to make a blockchain test out of it.

    TRANSACTION_HASH is the hash of the transaction to be used.

    OUTPUT_FILE is the path to the output python script.
    """
    request = RPCRequest()

    print(
        "Perform tx request: eth_get_transaction_by_hash(" + f"{transaction_hash}" + ")",
        file=stderr,
    )
    transaction = request.eth_get_transaction_by_hash(Hash(transaction_hash))

    print("Perform debug_trace_call", file=stderr)
    state = request.debug_trace_call(transaction)

    print("Perform eth_get_block_by_number", file=stderr)
    block = request.eth_get_block_by_number(transaction.block_number)

    print("Generate py test", file=stderr)
    context = BlockchainTestProvider(
        block=block, transaction=transaction, state=state
    ).get_context()

    template = template_env.get_template("blockchain_test/transaction.py.j2")
    output_file.write(template.render(context))

    print("Finished", file=stderr)
