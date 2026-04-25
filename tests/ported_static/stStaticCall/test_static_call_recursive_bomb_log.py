"""
Test_static_call_recursive_bomb_log.

Ported from:
state_tests/stStaticCall/static_CallRecursiveBombLogFiller.json
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
    ["state_tests/stStaticCall/static_CallRecursiveBombLogFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb_log(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_recursive_bomb_log."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (LOG0 0 32) (STATICCALL (- (GAS) 25000) (ADDRESS) 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.LOG0(offset=0x0, size=0x20)
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x61A8),
            address=Op.ADDRESS,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL (- (GAS) 100000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0)  [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
