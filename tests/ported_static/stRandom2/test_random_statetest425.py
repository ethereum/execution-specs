"""
Test_random_statetest425.

Ported from:
state_tests/stRandom2/randomStatetest425Filler.json

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
    ["state_tests/stRandom2/randomStatetest425Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest425(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest425."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x7f0000000000000000000000010000000000000000000000000000000000000000417f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff6f885707818b889a89975552f01284425560005155  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.COINBASE
        + Op.PUSH32[0x1]
        + Op.PUSH32[0xC350]
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x885707818B889A89975552F012844255
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
            "7f0000000000000000000000010000000000000000000000000000000000000000417f00000000000000000000000000000000000000000000000000000000000000017f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff6f885707818b889a89975552f0128442"  # noqa: E501
        ),
        value=0x22371A75,
    )

    post = {
        target: Account(
            storage={0: 0x885707818B889A89975552F012844255},
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
