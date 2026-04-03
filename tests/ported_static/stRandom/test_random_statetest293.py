"""
Test_random_statetest293.

Ported from:
state_tests/stRandom/randomStatetest293Filler.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stRandom/randomStatetest293Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest293(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest293."""
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
    # 0x7f00000000000000000000000100000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe417f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe6f458962699489837460090897f3056682845560005155  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.COINBASE
        + Op.PUSH32[0x0]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.SSTORE(key=Op.DUP5, value=0x458962699489837460090897F3056682)
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
        nonce=0,
        address=Address(0x7819C78E9547588CDCD915080881E4CCEF857C8D),  # noqa: E501
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
            "7f00000000000000000000000100000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe417f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe6f458962699489837460090897f305668284"  # noqa: E501
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x3CF6D3A7,
    )

    post = {
        target: Account(
            storage={
                0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE: 0x458962699489837460090897F3056682,  # noqa: E501
            },
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
