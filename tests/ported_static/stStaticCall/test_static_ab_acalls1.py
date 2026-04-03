"""
Test_static_ab_acalls1.

Ported from:
state_tests/stStaticCall/static_ABAcalls1Filler.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_ABAcalls1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
def test_static_ab_acalls1(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_ab_acalls1."""
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
        gas_limit=10000000000,
    )

    # Source: lll
    # { [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xE7FE01F115E85F0487086659FA9BBF09579B0E3A),  # noqa: E501
    )
    # Source: lll
    # {  [[ (PC) ]] (STATICCALL (- (GAS) 100000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0xCC7901B70DCEC81D198AC6CF196EF14BCA9870BE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD0A73D84AA7112E8D5179CAE211B268D16DAFD73),  # noqa: E501
    )
    # Source: lll
    # { [[ (PC) ]] (ADD 1 (STATICCALL (- (GAS) 100000) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.ADD(
                0x1,
                Op.STATICCALL(
                    gas=Op.SUB(Op.GAS, 0x186A0),
                    address=0xD0A73D84AA7112E8D5179CAE211B268D16DAFD73,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            ),
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0xCC7901B70DCEC81D198AC6CF196EF14BCA9870BE),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 (PC)) (STATICCALL (- (GAS) 100000) <contract:0x245304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=Op.PC)
        + Op.STATICCALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0x5E75046384134A4554C3C7061D4637CB978D5699,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xC1EB8F73F2E1E269ACD146C961210B665078841B),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE (PC) (ADD 1 (STATICCALL (- (GAS) 100000) <contract:0x195e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) ) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=Op.PC,
            value=Op.ADD(
                0x1,
                Op.STATICCALL(
                    gas=Op.SUB(Op.GAS, 0x186A0),
                    address=0xC1EB8F73F2E1E269ACD146C961210B665078841B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            ),
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x5E75046384134A4554C3C7061D4637CB978D5699),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr: Account(storage={38: 0}),
                addr_2: Account(storage={41: 0}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr: Account(storage={38: 0}),
                addr_2: Account(storage={41: 0}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [1000000000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
