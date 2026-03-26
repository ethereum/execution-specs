"""
test_static_callcallcodecall_010_oogm_after

Ported from:
state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfterFiller.json
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
    "000000000000000000000000c00fba9c86d497814a90912f8f6c63801ea59908",
    "0000000000000000000000003a2fb8850eea3cbd892bb77ff68da146ead9c49d",
]
TX_GAS = [1720000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfterFiller.json"],
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
def test_static_callcallcodecall_010_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_callcallcodecall_010_oogm_after"""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 600150 (CALLDATALOAD 0) 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x92856, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf1f083974fd68b961e68130c27fc5ef37b49c1df"),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 400080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (SSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=0x61ad0, address=0x5ad1f77e14fe15f07a2f5df1480dcaba5b4b6435, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xc00fba9c86d497814a90912f8f6c63801ea59908"),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 400080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    addr_0x2000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=0x61ad0, address=0x5ad1f77e14fe15f07a2f5df1480dcaba5b4b6435, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x3f, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x23) + Op.JUMPDEST + Op.STOP,
        nonce=0,
        address=Address("0x3a2fb8850eea3cbd892bb77ff68da146ead9c49d"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 120040 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.STATICCALL(gas=0x1d4e8, address=0x335c5531b84765a7626e6e76688f18b81be5259c, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        nonce=0,
        address=Address("0x5ad1f77e14fe15f07a2f5df1480dcaba5b4b6435"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 0, 1: 1, 2: 0, 3: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
