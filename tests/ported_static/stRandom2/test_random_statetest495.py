"""
Test_random_statetest495.

Ported from:
state_tests/stRandom2/randomStatetest495Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
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
    ["state_tests/stRandom2/randomStatetest495Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest495(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest495."""
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
    # 0x7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f00000000000000000000000100000000000000000000000000000000000000006f427ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7e6410f26f519c538ea2070a6c60005155  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.SELFDESTRUCT(address=0x427FFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.SELFDESTRUCT * 16
            + Op.INVALID
            + bytes.fromhex("7e6410f26f519c538ea2070a6c60005155")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.SELFDESTRUCT(address=0x427FFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.SELFDESTRUCT * 16
            + Op.INVALID
            + Bytes("7e6410f26f519c538ea2070a6c")
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0xCA044EE,
    )

    post = {
        Address(0x00000000427FFFFFFFFFFFFFFFFFFFFFFFFFFFFF): Account(
            storage={}, code=b"", nonce=0
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
