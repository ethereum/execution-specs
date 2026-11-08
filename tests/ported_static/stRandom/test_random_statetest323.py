"""
Test_random_statetest323.

Ported from:
state_tests/stRandom/randomStatetest323Filler.json
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
    ["state_tests/stRandom/randomStatetest323Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest323(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest323."""
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
    # 0x6f7f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe74977f000000000000000000000000000000000000000000000000000000000000c3506f6b7936181136392060005155  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH16[0x7F000000000000000000000000000000]
            + Op.STOP * 17
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH21[0x977F00000000000000000000000000000000000000]
            + Op.STOP * 11
            + bytes.fromhex("c3506f6b7936181136392060005155")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH16[0x7F000000000000000000000000000000]
            + Op.STOP * 17
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH21[0x977F00000000000000000000000000000000000000]
            + Op.STOP * 11
            + Bytes("c3506f6b79361811363920")
        ),
        gas_limit=100000,
        value=0x7490871F,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
