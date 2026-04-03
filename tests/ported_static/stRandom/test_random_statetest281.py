"""
Test_random_statetest281.

Ported from:
state_tests/stRandom/randomStatetest281Filler.json
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
    ["state_tests/stRandom/randomStatetest281Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest281(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest281."""
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
    # 0x7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>457f000000000000000000000000000000000000000000000000000000000000c350417f00000000000000000000000000000000000000000000000000000000000000016f649a7a3457645670a27fa170639718a260005155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79] * 2
        + Op.GASLIMIT
        + Op.PUSH32[0xC350]
        + Op.COINBASE
        + Op.PUSH32[0x1]
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0), value=0x649A7A3457645670A27FA170639718A2
        ),
        nonce=0,
        address=Address(0xED3690010055EAB6A7103A13E1E74492E67FD00F),  # noqa: E501
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
            "7f0000000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797f0000000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e79457f000000000000000000000000000000000000000000000000000000000000c350417f00000000000000000000000000000000000000000000000000000000000000016f649a7a3457645670a27fa170639718a2"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x662E647C,
    )

    post = {
        target: Account(
            storage={0: 0x649A7A3457645670A27FA170639718A2},
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
