"""
Test_random_statetest85.

Ported from:
state_tests/stRandom/randomStatetest85Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest85Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest85(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest85."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
    )
    # Source: raw
    # 0x7f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c350f25b557e348ff374819d123109539b55  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[0xC350]
            + Op.CALLCODE(
                gas=Op.PUSH32[0xC350],
                address=Op.PUSH32[0x1],
                value=Op.PUSH32[0x1],
                args_offset=Op.PUSH32[coinbase],
                args_size=Op.PUSH32[0x0],
                ret_offset=Op.PUSH32[0x0],
                ret_size=Op.PUSH32[0xC350],
            )
            + Op.JUMPDEST
            + Op.SSTORE
            + bytes.fromhex("7e348ff374819d123109539b55")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0xC350]
            + Op.CALLCODE(
                gas=Op.PUSH32[0xC350],
                address=Op.PUSH32[0x1],
                value=Op.PUSH32[0x1],
                args_offset=Op.PUSH32[coinbase],
                args_size=Op.PUSH32[0x0],
                ret_offset=Op.PUSH32[0x0],
                ret_size=Op.PUSH32[0xC350],
            )
            + Op.JUMPDEST
            + Op.SSTORE
            + Bytes("7e348ff374819d123109539b")
        ),
        value=0x3B46EEB1,
    )

    post = {
        target: Account(storage={1: 50000}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
