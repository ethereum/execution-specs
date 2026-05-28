"""Stateless chain-config validation tests."""

from dataclasses import replace
from typing import Any, Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Transaction,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

StatelessInputBytesModifier = Callable[[Bytes], Bytes]
ChainConfigBuilder = Callable[[Any], Any]


def replace_chain_config(
    build_chain_config: ChainConfigBuilder,
) -> StatelessInputBytesModifier:
    """Replace only the decoded stateless input chain_config."""

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
            chain_config=build_chain_config(stateless_input),
        )
        return Bytes(bytes(serialize_stateless_input(modified_input)))

    return modifier


def future_timestamp_activation_chain_config(stateless_input: Any) -> Any:
    """Move Amsterdam activation one second after the payload timestamp."""
    from ethereum_types.numeric import U64

    from ethereum.forks.amsterdam.stateless import (
        ForkActivation,
        ProtocolFork,
    )

    payload = stateless_input.new_payload_request.execution_payload
    chain_config = stateless_input.chain_config
    active_fork = chain_config.active_fork
    return replace(
        chain_config,
        active_fork=replace(
            active_fork,
            fork=ProtocolFork.Amsterdam,
            activation=ForkActivation(
                block_number=None,
                timestamp=U64(int(payload.timestamp) + 1),
            ),
        ),
    )


def wrong_chain_id_chain_config(stateless_input: Any) -> Any:
    """Change chain_id from 1 to 2."""
    from ethereum_types.numeric import U64

    chain_config = stateless_input.chain_config
    if int(chain_config.chain_id) != 1:
        raise AssertionError(
            f"expected canonical chain_id 1, got {chain_config.chain_id}"
        )
    return replace(chain_config, chain_id=U64(2))


def test_validation_chain_config_future_timestamp_activation(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """A future Amsterdam timestamp activation fails validation."""
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                stateless_input_bytes_modifier=replace_chain_config(
                    future_timestamp_activation_chain_config
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={},
    )


def test_validation_chain_config_wrong_chain_id_legacy_signature(
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
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_bytes_modifier=replace_chain_config(
                    wrong_chain_id_chain_config
                ),
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )
