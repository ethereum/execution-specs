"""
Test_static_callcodecallcallcode_101_oogm_after2.

Ported from:
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter2Filler.json
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter2Filler.json"  # noqa: E501
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
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcodecallcallcode_101_oogm_after2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcodecallcallcode_101_oogm_after2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1000000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000001)
    contract_2 = Address(0x1000000000000000000000000000000000000002)
    contract_3 = Address(0x1000000000000000000000000000000000000003)
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
    # {  (MSTORE 3 1) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (MSTORE 3 1) (CALLCODE 20020 0x1000000000000000000000000000000000000003 0 0 64 0 64 ) }  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.CALLCODE(
            gas=0x4E34,
            address=contract_3,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 40080 0x1000000000000000000000000000000000000002 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x9C90,
                address=contract_2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x43, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x27)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  [[ 0 ]] (CALLCODE 60150 0x1000000000000000000000000000000000000001 (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0xEAF6,
                address=contract_1,
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
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [172000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {contract_0: Account(storage={0: 0, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
