"""
Test_static_callcallcallcode_001_oogm_before.

Ported from:
state_tests/stStaticCall/static_callcallcallcode_001_OOGMBeforeFiller.json
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
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMBeforeFiller.json"  # noqa: E501
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
def test_static_callcallcallcode_001_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcallcode_001_oogm_before."""
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
    # {  (MSTORE 3 1) (STATICCALL 400080 (CALLDATALOAD 0) 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x61AD0,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x10F374FCA091CACD3E57E847BA123BC16695C44E),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x335C5531B84765A7626E6E76688F18B81BE5259C),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000001> 0 32 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0x10F374FCA091CACD3E57E847BA123BC16695C44E,
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
        address=Address(0xC6DF53AF8AAF7C046B42CF493D4C6819EBEC7994),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 1 1) (DELEGATECALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 3 1) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x1D4D4,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xEB89BE27EB1850F5F46204E0609023F43C2EDC35),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)  ) (DELEGATECALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 3 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x1D4D4,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x8214B87BB9FD41ED6C19255D74B7FCC66178C4D5),  # noqa: E501
    )

    tx_data = [
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [1720000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        target: Account(storage={0: 1, 1: 1, 2: 0, 3: 0}),
        addr: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_2: Account(storage={2: 0, 3: 0}),
        addr_4: Account(storage={3: 0}),
        sender: Account(storage={1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
