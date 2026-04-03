"""
Test_static_call_recursive_bomb0.

Ported from:
state_tests/stStaticCall/static_CallRecursiveBomb0Filler.json
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
    ["state_tests/stStaticCall/static_CallRecursiveBomb0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_recursive_bomb0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_recursive_bomb0."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL 100000000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0)  [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x5F5E100,
                address=0xC2641F62F868340A29AFB342ECBE22936A4336AE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0x77359400,
        nonce=0,
        address=Address(0xA8F75B202DBA133E3184B84520CF27623E8C993F),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (+ (MLOAD 0) 1)) (STATICCALL (- (GAS) 11000) (ADDRESS) 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x2AF8),
            address=Op.ADDRESS,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xC2641F62F868340A29AFB342ECBE22936A4336AE),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=10000000000,
        value=0x186A0,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
