"""
Test_call_to_name_registrator_too_much_memory2.

Ported from:
state_tests/stSystemOperationsTest/CallToNameRegistratorTooMuchMemory2Filler.json
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
    [
        "state_tests/stSystemOperationsTest/CallToNameRegistratorTooMuchMemory2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_to_name_registrator_too_much_memory2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_to_name_registrator_too_much_memory2."""
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
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 0xeeffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALL 500 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 987654 1) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xEEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1F4,
                address=0x15EB18969E0925C8E4A76FD7CBCE36A2B056B27E,
                value=0x17,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0xF1206,
                ret_size=0x1,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x12798480F9B1E6534F2D528F84EF12BDA7F49A71),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=23,
        nonce=0,
        address=Address(0x15EB18969E0925C8E4A76FD7CBCE36A2B056B27E),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={}, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
