"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest163Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest163Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest163(
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
            "7f000000000000000000000000000000000000000000000000000000000000000034577f"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000"  # noqa: E501
            "00000100000000000000000000000000000000000000007f000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000426259cb6142a1196e3168c986758aa4"  # noqa: E501
        ),
        nonce=0,
        address=Address("0xe9a32a9ad98c02fa9521b9ab066bcc683a8ab126"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f000000000000000000000000000000000000000000000000000000000000000034577f"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7fffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000"  # noqa: E501
            "00000100000000000000000000000000000000000000007f000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000426259cb6142a1196e3168c986758aa4"  # noqa: E501
        ),
        gas_limit=381441932,
        value=1579124913,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
