"""
Test_static_callcodecallcodecall_110_2.

Ported from:
state_tests/stStaticCall/static_callcodecallcodecall_110_2Filler.json
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcodecallcodecall_110_2Filler.json"],
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
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
        pytest.param(
            0,
            0,
            2,
            id="-v2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcodecall_110_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcodecallcodecall_110_2."""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALLCODE 350000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x55730,
                address=0x611CB29449C75E44440DB4985DBB84732BC18342,
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
        address=Address(0x4BE1B24080B17ED1F5F4C0FF9CD820D764A32620),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (CALLCODE 300000 <contract:0x1000000000000000000000000000000000000002> ( - (CALLVALUE) 1) 0 64 0 64 ) (MSTORE 31 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=0xB1927ADAFCD3B2ECEF7B7508CB3A8D7B41FCAE73,
                value=Op.SUB(Op.CALLVALUE, 0x1),
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x1F, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x611CB29449C75E44440DB4985DBB84732BC18342),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 31 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x3D090,
                address=0x2A142C79A9B097C111CE945214226126B75E332C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x1F, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xB1927ADAFCD3B2ECEF7B7508CB3A8D7B41FCAE73),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x2A142C79A9B097C111CE945214226126B75E332C),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [3000000]
    tx_value = [0, 1, 2]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
