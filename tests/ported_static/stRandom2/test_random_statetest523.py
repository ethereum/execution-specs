"""
Test_random_statetest523.

Ported from:
state_tests/stRandom2/randomStatetest523Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
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
    ["state_tests/stRandom2/randomStatetest523Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest523(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest523."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x417f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe4450427f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000003560080b348d5560005155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.COINBASE
        + Op.PUSH32[0x1]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.POP(Op.PREVRANDAO)
        + Op.TIMESTAMP
        + Op.PUSH32[0x1]
        + Op.SIGNEXTEND(0x8, Op.CALLDATALOAD(offset=Op.PUSH32[0x0]))
        + Op.SSTORE(key=Op.DUP14, value=Op.CALLVALUE)
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
        nonce=0,
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
        address=Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "417f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe4450427f00000000000000000000000000000000000000000000000000000000000000017f00000000000000000000000000000000000000000000000000000000000000003560080b348d"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x5741BF83,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
