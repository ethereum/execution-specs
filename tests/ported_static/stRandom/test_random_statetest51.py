"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest51Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom/randomStatetest51Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest51(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex(
            "7f0000000000000000000000000000000000000000000000000000000000000001757f00"  # noqa: E501
            "0000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57a7f000000"  # noqa: E501
            "000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000"  # noqa: E501
            "000000000000945304eb96065b2a98b57a48a06ae28d285a71b5447fffffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffe83189b60005155"
        ),
        nonce=0,
        address=Address("0x53af81e2a686427de42e7b8b55a0c6c66c8c6051"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f0000000000000000000000000000000000000000000000000000000000000001757f00"  # noqa: E501
            "0000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57a7f000000"  # noqa: E501
            "000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000"  # noqa: E501
            "000000000000945304eb96065b2a98b57a48a06ae28d285a71b5447fffffffffffffffff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffe83189b"
        ),
        gas_limit=100000,
        value=1062041617,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
