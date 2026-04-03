"""
Test_static_call_create3.

Ported from:
state_tests/stStaticCall/static_callCreate3Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callCreate3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_create3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_create3."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xA000000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # {  (CALL 600000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x927C0,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 0x6d600060006000600030620186a0fa600052600e6012f3) [[ 0 ]] (CREATE 1 9 23)  [[ 1 ]] (STATICCALL 30000 (SLOAD 0) 0 0 0 0) [[ 2 ]] 1 }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x6D600060006000600030620186A0FA600052600E6012F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0x9, size=0x17))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x7530,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Hash(contract_1, left_padding=True),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        contract_1: Account(
            storage={
                0: 0x13136008B64FF592819B2FA6D43F2835C452020E,
                1: 1,
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
