"""
Test_static_callcallcallcode_abcb_recursive2.

Ported from:
state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVE2Filler.json
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
    [
        "state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVE2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcallcode_abcb_recursive2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: lll
    # {  (MSTORE 1 1) (STATICCALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) (MSTORE 3 1) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x17D7840,
                address=0xA340F8B0F598F6D5AD2856FFE45AADD934F37CF1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x130E754252B72CB20AA752CB31176D9C2E9C8A21),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (STATICCALL 1000000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 2 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0xF4240,
                address=0x812297C04813FEA96B943B246D9D17EA17545526,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x2, value=0x1)
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xA340F8B0F598F6D5AD2856FFE45AADD934F37CF1),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (CALLCODE 500000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) (MSTORE 2 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x7A120,
                address=0xA340F8B0F598F6D5AD2856FFE45AADD934F37CF1,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x2, value=0x1)
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x812297C04813FEA96B943B246D9D17EA17545526),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(storage={0: 0, 1: 0}),
        addr: Account(storage={1: 0, 2: 0}),
        addr_2: Account(storage={1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
