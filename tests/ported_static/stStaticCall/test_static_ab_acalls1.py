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

TX_DATA = [
    "000000000000000000000000d0a73d84aa7112e8d5179cae211b268d16dafd73",
    "000000000000000000000000c1eb8f73f2e1e269acd146c961210b665078841b",
]
TX_GAS = [1000000000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_ABAcalls1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
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
        address=Address("0xe7fe01f115e85f0487086659fa9bbf09579b0e3a"),  # noqa: E501
    )
    # Source: lll
    # {  [[ (PC) ]] (STATICCALL (- (GAS) 100000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(  # noqa: F841
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
        address=Address("0xd0a73d84aa7112e8d5179cae211b268d16dafd73"),  # noqa: E501
    )
    # Source: lll
    # { [[ (PC) ]] (ADD 1 (STATICCALL (- (GAS) 100000) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) }  # noqa: E501
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(  # noqa: F841
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
        address=Address("0xcc7901b70dcec81d198ac6cf196ef14bca9870be"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 (PC)) (STATICCALL (- (GAS) 100000) <contract:0x245304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr_0x195e7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(  # noqa: F841
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
        address=Address("0xc1eb8f73f2e1e269acd146c961210b665078841b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE (PC) (ADD 1 (STATICCALL (- (GAS) 100000) <contract:0x195e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) ) }  # noqa: E501
    addr_0x245304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(  # noqa: F841
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
        address=Address("0x5e75046384134a4554c3c7061d4637cb978d5699"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87: Account(
                    storage={38: 0}
                ),
                addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(
                    storage={41: 0}
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87: Account(
                    storage={38: 0}
                ),
                addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(
                    storage={41: 0}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
