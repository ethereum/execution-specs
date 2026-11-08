"""
Test_random_statetest322.

Ported from:
state_tests/stRandom/randomStatetest322Filler.json

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
    ["state_tests/stRandom/randomStatetest322Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest322(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest322."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007f0000000000000000000000000000000000000000000000000000000000000000427f000000000000000000000000000000000000000000000000000000000000c3506f1206060508840294304101a3128f345560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x10000000000000000000000000000000000000000] * 2
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.PUSH32[0x0]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x0]
        + Op.TIMESTAMP
        + Op.PUSH32[0xC350]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x1206060508840294304101A3128F3455
        ),
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
            "7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007f0000000000000000000000000000000000000000000000000000000000000000427f000000000000000000000000000000000000000000000000000000000000c3506f1206060508840294304101a3128f34"  # noqa: E501
        ),
        value=0x312238E4,
    )

    post = {
        target: Account(
            storage={0: 0x1206060508840294304101A3128F3455},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
