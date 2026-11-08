"""
Test_random_statetest53.

Ported from:
state_tests/stRandom/randomStatetest53Filler.json
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
    ["state_tests/stRandom/randomStatetest53Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest53(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest53."""
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
    # 0x427f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff583481f36a85646d53671639175b940860005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.TIMESTAMP
        + Op.PUSH32[0x0]
        + Op.PUSH32[0x1]
        + Op.PUSH32[coinbase]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 2
        + Op.PC
        + Op.RETURN(offset=Op.DUP2, size=Op.CALLVALUE)
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x85646D53671639175B9408),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.TIMESTAMP
            + Op.PUSH32[0x0]
            + Op.PUSH32[0x1]
            + Op.PUSH32[coinbase]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF] * 2
            + Op.PC
            + Op.RETURN(offset=Op.DUP2, size=Op.CALLVALUE)
            + Op.PUSH11[0x85646D53671639175B9408]
        ),
        gas_limit=4400000,
        value=0x16AB40,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
