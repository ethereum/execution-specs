"""
Test_random_statetest604.

Ported from:
state_tests/stRandom2/randomStatetest604Filler.json
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
    ["state_tests/stRandom2/randomStatetest604Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest604(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest604."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000010000000000000000000000000000000000000000437f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe44a4418a83039c0587363b0518204006065a06  # noqa: E501
    target = pre.deploy_contract(
        code=Op.LOG4(
            offset=Op.PREVRANDAO,
            size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
            topic_1=Op.PUSH32[0x0],
            topic_2=Op.NUMBER,
            topic_3=Op.PUSH32[0x10000000000000000000000000000000000000000],
            topic_4=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
        )
        + Op.COINBASE
        + Op.SUB(Op.DUP4, Op.DUP11)
        + Op.SWAP13
        + Op.MOD(
            Op.BLOCKHASH(block_number=Op.SHA3),
            Op.XOR(
                Op.SDIV(Op.EXTCODESIZE(address=Op.CALLDATASIZE), Op.DUP8),
                Op.SDIV,
            ),
        )
        + Op.MOD(Op.GAS, Op.MOD),
    )
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

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000010000000000000000000000000000000000000000437f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe44a4418a83039c0587363b0518204006065a06"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x4CC50BAC,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
