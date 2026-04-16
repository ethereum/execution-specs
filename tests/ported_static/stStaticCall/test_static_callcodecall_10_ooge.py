"""
Test_static_callcodecall_10_ooge.

Ported from:
state_tests/stStaticCall/static_callcodecall_10_OOGEFiller.json
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
    ["state_tests/stStaticCall/static_callcodecall_10_OOGEFiller.json"],
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
def test_static_callcodecall_10_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcodecall_10_ooge."""
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
    # {  (STATICCALL 20020 (CALLDATALOAD 0) 0 64 0 64 ) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x4E34,
            address=Op.CALLDATALOAD(offset=0x0),
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x33E1AD2A3AE944798E9ED4689B85D9136B59EBD2),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1)}
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x9791FA194F36C71F8BD64A757B7283707075BA99),  # noqa: E501
    )
    # Source: lll
    # {  (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_3 = pre.deploy_contract(  # noqa: F841
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
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x249F0,
                address=0x33E1AD2A3AE944798E9ED4689B85D9136B59EBD2,
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
        address=Address(0xDCFF1EF291EC7B6A606AC4284680DB5A06F33054),  # noqa: E501
    )

    tx_data = [
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [172000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
