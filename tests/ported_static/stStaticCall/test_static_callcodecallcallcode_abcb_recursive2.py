"""
Test_static_callcodecallcallcode_abcb_recursive2.

Ported from:
state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcodecallcallcode_abcb_recursive2."""
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
    # {  [[ 0 ]] (CALLCODE 25000000 (CALLDATALOAD 0) (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x17D7840,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xBA3C5101AD0B43DE0F1853243EB3F9811EAEE1E0),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 1000000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0xF4240,
            address=0x1A3C543695D7CA3A7D5522E9C7AABE5512571706,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x2733821FA13C4EAD1C9631C76820333F42059B7C),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 500000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x7A120,
            address=0x2733821FA13C4EAD1C9631C76820333F42059B7C,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x1A3C543695D7CA3A7D5522E9C7AABE5512571706),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 1000000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0xF4240,
            address=0xB81EB378451B4361DF035AEA57913023DFFBF39A,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x6ACC177800643D95AB1DAEE1BD55CF99E3814E07),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 500000 <contract:0x2000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x7A120,
            address=0x6ACC177800643D95AB1DAEE1BD55CF99E3814E07,
            value=0x1,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xB81EB378451B4361DF035AEA57913023DFFBF39A),  # noqa: E501
    )

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [600000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
