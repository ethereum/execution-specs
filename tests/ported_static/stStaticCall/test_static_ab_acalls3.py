"""
test_static_ab_acalls3

Ported from:
state_tests/stStaticCall/static_ABAcalls3Filler.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000407da20797d4e89c2f4e48c502385c1514d9fa52",
    "000000000000000000000000e40c059876e334b99a5d199693978c39bedb690d",
]
TX_GAS = [10000000]
TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_ABAcalls3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_ab_acalls3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_ab_acalls3"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=Op.CALLVALUE, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (ADD (SLOAD 0) 1) (STATICCALL (- (GAS) 100000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }
    addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(gas=Op.SUB(Op.GAS, 0x186a0), address=0xe278f8058bef1396c2b1df4d1dc4b65233133c57, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xfa3e8,
        nonce=0,
        address=Address("0x407da20797d4e89c2f4e48c502385c1514d9fa52"),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (ADD (SLOAD 0) 1) (STATICCALL (- (GAS) 100000) <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0) }
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(gas=Op.SUB(Op.GAS, 0x186a0), address=0x407da20797d4e89c2f4e48c502385c1514d9fa52, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xe278f8058bef1396c2b1df4d1dc4b65233133c57"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (ADD (SLOAD 0) 1)) (STATICCALL (- (GAS) 100000) <contract:0x245304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }
    addr_0x195e7baea6a6c7c4c2dfeb977efac326af552d87 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(gas=Op.SUB(Op.GAS, 0x186a0), address=0xb1f7380db647f1d85565b28978ba83861b99965, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xfa3e8,
        nonce=0,
        address=Address("0xe40c059876e334b99a5d199693978c39bedb690d"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 (ADD (SLOAD 0) 1)) (STATICCALL (- (GAS) 100000) <contract:0x195e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0) }
    addr_0x245304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STATICCALL(gas=Op.SUB(Op.GAS, 0x186a0), address=0xe40c059876e334b99a5d199693978c39bedb690d, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x0b1f7380db647f1d85565b28978ba83861b99965"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x095e7baea6a6c7c4c2dfeb977efac326af552d87: Account(storage={0: 1}),
        addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={0: 0}),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(storage={0: 1, 1: 1}),
        addr_0x195e7baea6a6c7c4c2dfeb977efac326af552d87: Account(storage={0: 0}),
        addr_0x245304eb96065b2a98b57a48a06ae28d285a71b5: Account(storage={0: 0}),
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
