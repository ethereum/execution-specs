"""
Test_random_statetest534.

Ported from:
state_tests/stRandom2/randomStatetest534Filler.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stRandom2/randomStatetest534Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest534(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest534."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x7f000000000000000000000001000000000000000000000000000000000000000045437f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff457f0000000000000000000000000000000000000000000000000000000000000000436ff3075243846d88747b6a9e7ff28c615560005155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.GASLIMIT
        + Op.NUMBER
        + Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.GASLIMIT
        + Op.PUSH32[0x0]
        + Op.NUMBER
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0xF3075243846D88747B6A9E7FF28C6155
        ),
        nonce=0,
        address=Address(0x9114C469B911CB7089FE6B881F7E6F10C2109681),  # noqa: E501
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
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "7f000000000000000000000001000000000000000000000000000000000000000045437f0000000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff457f0000000000000000000000000000000000000000000000000000000000000000436ff3075243846d88747b6a9e7ff28c61"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x55DB76C1,
    )

    post = {
        target: Account(
            storage={0: 0xF3075243846D88747B6A9E7FF28C6155},
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
