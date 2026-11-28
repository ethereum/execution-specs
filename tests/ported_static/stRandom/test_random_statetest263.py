"""
Test_random_statetest263.

Ported from:
state_tests/stRandom/randomStatetest263Filler.json
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
    ["state_tests/stRandom/randomStatetest263Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
def test_random_statetest263(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest263."""
    sender = pre.fund_eoa()

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
    )
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
        + Op.DUP1
        + Op.PUSH32[0xC350]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x556000),
            value=Op.XOR(
                Op.DIV(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                    Op.PUSH32[0xC350],
                ),
                Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5],
            ),
        ),
    )

    env = Environment(
        fee_recipient=coinbase,
        prev_randao=0x20000,
        gas_limit=9223372036854775807,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(
            "7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5807f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe041862"  # noqa: E501
        ),
        gas_limit=2038963641,
        value=0x2DB8846C,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0x14F8B588E368F08461F9F95EB620FACA1C09044BCFAFAE26DE901D3A614F5,  # noqa: E501
            },
        ),
        coinbase: Account(storage={}),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
