"""Stateless chain-ID validation tests."""

from dataclasses import replace
from typing import Callable

import pytest
from ethereum_types.numeric import U64
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Transaction,
)

from ethereum.forks.amsterdam.stateless import StatelessInput

from .gas_helpers import empty_account_value_transfer_gas_limit
from .spec import ref_spec_8025
from .stateless_input_helpers import (
    StatelessInputBytesModifier,
    modify_stateless_input,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version

ChainIdBuilder = Callable[[StatelessInput], U64]


def replace_chain_id(
    build_chain_id: ChainIdBuilder,
) -> StatelessInputBytesModifier:
    """Replace only the decoded stateless input chain ID."""

    def update(stateless_input: StatelessInput) -> StatelessInput:
        return replace(
            stateless_input,
            chain_id=build_chain_id(stateless_input),
        )

    return modify_stateless_input(update)


def wrong_chain_id(stateless_input: StatelessInput) -> U64:
    """Change chain_id from 1 to 2."""
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
