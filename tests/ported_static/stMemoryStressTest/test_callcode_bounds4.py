"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/CALLCODE_Bounds4Filler.json
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
    [
        "tests/static/state_tests/stMemoryStressTest/CALLCODE_Bounds4Filler.json",  # noqa: E501
    ],
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
def test_callcode_bounds4(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0))) + Op.STOP
        ),
        nonce=0,
        address=Address("0x849f53126ade5f72469029537296f2b6644d4d41"),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
    )
    # Source: LLL
    # { (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0xffffffffffffffff 0 0xffffffffffffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (CALLCODE 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFFFFFFFFFFF,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0xFFFFFFFFFFFFFFFF,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFFFFFFFFFFF,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0xFFFFFFFFFFFFFFFF,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    value=0x0,
                    args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.CALLCODE(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                value=0x0,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0479fbac15cb575e66ded014fd60ceb98749b04"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
