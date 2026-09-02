"""Stateless chain-ID validation tests."""

from dataclasses import replace
from typing import Any, Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Fork,
    Transaction,
)

from .gas_helpers import empty_account_value_transfer_gas_limit

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

StatelessInputBytesModifier = Callable[[Bytes], Bytes]
ChainIdBuilder = Callable[[Any], Any]


def replace_chain_id(
    build_chain_id: ChainIdBuilder,
) -> StatelessInputBytesModifier:
    """Replace only the decoded stateless input chain ID."""

    def modifier(input_bytes: Bytes) -> Bytes:
        from ethereum_types.bytes import Bytes as AmsterdamBytes

        from ethereum.forks.amsterdam.stateless_guest import (
            deserialize_stateless_input,
        )
        from ethereum.forks.amsterdam.stateless_host import (
            serialize_stateless_input,
        )

        stateless_input = deserialize_stateless_input(
            AmsterdamBytes(bytes(input_bytes))
        )
        modified_input = replace(
            stateless_input,
            chain_id=build_chain_id(stateless_input),
        )
        return Bytes(bytes(serialize_stateless_input(modified_input)))

    return modifier


def wrong_chain_id(stateless_input: Any) -> Any:
    """Change chain_id from 1 to 2."""
    from ethereum_types.numeric import U64

    if int(stateless_input.chain_id) != 1:
        raise AssertionError(
            f"expected canonical chain_id 1, got {stateless_input.chain_id}"
        )
    return U64(2)


def test_validation_wrong_chain_id_legacy_signature(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A protected legacy signature for chain 1 fails under chain 2."""
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    tx = Transaction(
        chain_id=1,
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=empty_account_value_transfer_gas_limit(fork),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_bytes_modifier=replace_chain_id(
                    wrong_chain_id
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )
