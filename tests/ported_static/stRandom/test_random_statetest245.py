"""
Test_random_statetest245.

Ported from:
state_tests/stRandom/randomStatetest245Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest245Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest245(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest245."""
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
    # 0x7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff157f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0469877c39141650434587895560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[coinbase]
        + Op.ISZERO(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        )
        + Op.PUSH32[0x0]
        + Op.PUSH32[coinbase]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.SSTORE(
            key=0x877C3914165043458789,
            value=Op.DIV(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                Op.PUSH32[0xC350],
            ),
        )
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[coinbase]
            + Op.ISZERO(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            )
            + Op.PUSH32[0x0]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.DIV(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                Op.PUSH32[0xC350],
            )
            + Op.PUSH10[0x877C3914165043458789]
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x109B6E97,
    )

    post = {
        target: Account(
            storage={
                0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                0x877C3914165043458789: 0x14F8B588E368F08461F9F01B866E43AA79BBADC0980B242070B8CFBFC6540,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
