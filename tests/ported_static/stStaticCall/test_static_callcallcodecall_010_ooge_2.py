"""
Test_static_callcallcodecall_010_ooge_2.

Ported from:
state_tests/stStaticCall/static_callcallcodecall_010_OOGE_2Filler.json
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
    ["state_tests/stStaticCall/static_callcallcodecall_010_OOGE_2Filler.json"],
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
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecall_010_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcodecall_010_ooge_2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (STATICCALL 120020 (CALLDATALOAD 0) 0 64 0 64 ) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x1D4D4,
            address=Op.CALLDATALOAD(offset=0x0),
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x77E67836C6A30F95E117469CAEFB6C1FDCAD0C2E),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0xB126C622075B1189FB6C45E851641CFADDF65B36),  # noqa: E501
    )
    # Source: lll
    # {  (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0xFBEF21C5A6C2ADCF3D769F085E0CC9FE9A8DF954),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) (CALLCODE 200000 <contract:0x1000000000000000000000000000000000000002> 0 0 32 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALLCODE(
            gas=0x30D40,
            address=0x77E67836C6A30F95E117469CAEFB6C1FDCAD0C2E,
            value=0x0,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x87B79D9A4C004A23C7A12074BA8DA784E201EA8C),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 32 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x55730,
                address=0x87B79D9A4C004A23C7A12074BA8DA784E201EA8C,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x519393D984BEAF4FD226309E9F0704B2DB3164B5),  # noqa: E501
    )

    tx_data = [
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    tx_gas = [1720000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
