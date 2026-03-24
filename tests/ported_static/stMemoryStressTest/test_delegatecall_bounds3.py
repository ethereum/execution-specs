"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/DELEGATECALL_Bounds3Filler.json
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
        "tests/static/state_tests/stMemoryStressTest/DELEGATECALL_Bounds3Filler.json",  # noqa: E501
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
def test_delegatecall_bounds3(
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

    # Source: LLL
    # { (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffff 0 0xffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff 0xffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffff) (DELEGATECALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    args_offset=0x0,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    args_offset=0xFFFFFFFFFFFFFFFF,
                    args_size=0xFFFFFFFFFFFFFFFF,
                    ret_offset=0xFFFFFFFFFFFFFFFF,
                    ret_size=0xFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                    args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
            )
            + Op.DELEGATECALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x849F53126ADE5F72469029537296F2B6644D4D41,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x5a6cc254b318bb5f7539fcc10cfb01c517154c5c"),  # noqa: E501
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

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
