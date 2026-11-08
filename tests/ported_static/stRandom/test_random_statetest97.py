"""
Test_random_statetest97.

Ported from:
state_tests/stRandom/randomStatetest97Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest97Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest97(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest97."""
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
    # 0x7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>587f0000000000000000000000000000000000000000000000000000000000000001957f0000000000000000000000000000000000000000000000000000000000000000407f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3509781040107338b35071887a186  # noqa: E501
    target_code = (
        Op.PUSH32[coinbase]
        + Op.PC
        + Op.PUSH32[0x1]
        + Op.SWAP6
        + Op.BLOCKHASH(block_number=Op.PUSH32[0x0])
        + Op.PUSH32[0x1]
        + Op.PUSH32[0xC350]
        + Op.SWAP8
        + Op.LOG1(
            offset=Op.DUP8,
            size=Op.XOR(
                Op.SMOD(Op.CALLDATALOAD(offset=Op.DUP12), Op.CALLER), Op.SMOD
            ),
            topic_1=Op.ADD(Op.DIV, Op.DUP2),
        )
        + Op.DUP7
    )
    target = pre.deploy_contract(
        code=target_code,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[coinbase]
            + Op.PC
            + Op.PUSH32[0x1]
            + Op.SWAP6
            + Op.BLOCKHASH(block_number=Op.PUSH32[0x0])
            + Op.PUSH32[0x1]
            + Op.PUSH32[0xC350]
            + Op.SWAP8
            + Op.LOG1(
                offset=Op.DUP8,
                size=Op.XOR(
                    Op.SMOD(Op.CALLDATALOAD(offset=Op.DUP12), Op.CALLER),
                    Op.SMOD,
                ),
                topic_1=Op.ADD(Op.DIV, Op.DUP2),
            )
            + Op.DUP7
        ),
        gas_limit=100000,
        value=0x14008CB2,
    )

    post = {
        target: Account(
            storage={},
            code=target_code,
            balance=0,
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
