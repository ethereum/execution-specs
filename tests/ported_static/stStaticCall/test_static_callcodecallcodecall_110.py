"""
Test_static_callcodecallcodecall_110.

Ported from:
state_tests/stStaticCall/static_callcodecallcodecall_110Filler.json
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
    ["state_tests/stStaticCall/static_callcodecallcodecall_110Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcodecall_110(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcodecallcodecall_110."""
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
    # {  [[ 0 ]] (DELEGATECALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x55730,
                address=0x2BF6D23C6CDD3A7712AD150DFA2680ADABDA8B82,
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
        address=Address(0x4EEF7E2B5AE9BE0FC5B43DC4FE39195A1AE10FC4),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (DELEGATECALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 1 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=0xB10C519306D4D2ACCE66BE84C0EA086D816BA77C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x2BF6D23C6CDD3A7712AD150DFA2680ADABDA8B82),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 1 1)}  # noqa: E501
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
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xB10C519306D4D2ACCE66BE84C0EA086D816BA77C),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x2A142C79A9B097C111CE945214226126B75E332C),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
