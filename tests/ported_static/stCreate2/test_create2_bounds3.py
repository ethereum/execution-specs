"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreate2/CREATE2_Bounds3Filler.json
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
    ["tests/static/state_tests/stCreate2/CREATE2_Bounds3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (1000000, {}),
        (16777216, {}),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_create2_bounds3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: LLL
    # {  (MSTORE 0 0x6001600155601080600c6000396000f3006000355415600957005b6020356000 )  (MSTORE8 32 0x35) (MSTORE8 33 0x55) (CREATE2 1 0 0xffffffffffffffff 0) (CREATE2 1 0 0xffffffffffffffffffffffffffffffff 0) (CREATE2 1 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) (CREATE2 1 0xfffffff 0 0) (CREATE2 1 0xffffffff 0 0) (CREATE2 1 0xffffffffffffffff 0 0) (CREATE2 1 0xffffffffffffffffffffffffffffffff 0 0) (CREATE2 1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0) (CREATE2 1 0xfffffff 0xfffffff 0) (CREATE2 1 0xffffffff 0xffffffff 0) (CREATE2 1 0xffffffffffffffff 0xffffffffffffffff 0) (CREATE2 1 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0) (CREATE2 1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x6001600155601080600C6000396000F3006000355415600957005B6020356000,  # noqa: E501
            )
            + Op.MSTORE8(offset=0x20, value=0x35)
            + Op.MSTORE8(offset=0x21, value=0x55)
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0x0,
                    size=0xFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0x0,
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0x0,
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(value=0x1, offset=0xFFFFFFF, size=0x0, salt=0x0)
            )
            + Op.POP(
                Op.CREATE2(value=0x1, offset=0xFFFFFFFF, size=0x0, salt=0x0)
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFF,
                    size=0x0,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    size=0x0,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    size=0x0,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1, offset=0xFFFFFFF, size=0xFFFFFFF, salt=0x0
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFF,
                    size=0xFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFF,
                    size=0xFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.POP(
                Op.CREATE2(
                    value=0x1,
                    offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    salt=0x0,
                ),
            )
            + Op.CREATE2(
                value=0x1,
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                salt=0x0,
            )
            + Op.STOP
        ),
        balance=100,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
