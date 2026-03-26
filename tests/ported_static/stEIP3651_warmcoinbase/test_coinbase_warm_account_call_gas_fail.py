"""
test_coinbase_warm_account_call_gas_fail

Ported from:
state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml
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
    "693c61390000000000000000000000008ddf5d9a5251c41efd2949f53db0a464116c7c6e",
    "693c6139000000000000000000000000498516b6b2f25cb6a8e011a7c37a617b77e7d500",
    "693c61390000000000000000000000008873820bb96daa39db93ae64a9d6397e4c6a48d7",
    "693c6139000000000000000000000000303b6790d019874a107418eb549e4e7766a64728",
]
TX_GAS = [80000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml"],
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
        pytest.param(
            2, 0, 0,
            id="d2",
        ),
        pytest.param(
            3, 0, 0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_warm_account_call_gas_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_coinbase_warm_account_call_gas_fail"""
    coinbase = Address("0x50228c44ed92561d94511e8518a75aa463bd444b")
    sender = EOA(
        key=0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: yul
    # berlin
    # {
    #    // Depending on the called contract here, the subcall will perform
    #    // another call/delegatecall/staticcall/callcode that will only succeed
    #    // if coinbase is considered warm by default (post-Shanghai).
    #    let calladdr := calldataload(4)
    # 
    #    let callgas := 100
    #    switch calladdr
    #    case <contract:0x0000000000000000000000000000000000001000> {
    #      // Extra: COINBASE + 6xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 27)
    #    }
    #    case <contract:0x0000000000000000000000000000000000002000> {
    #      // Extra: COINBASE + 6xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 27)
    #    }
    #    case <contract:0x0000000000000000000000000000000000003000> {
    #      // Extra: COINBASE + 5xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 24)
    #    }
    #    case <contract:0x0000000000000000000000000000000000004000> {
    #      // Extra: COINBASE + 5xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 24)
    #    }
    #    // Call and save result
    #    sstore(0, call(callgas, calladdr, 0, 0, 0, 0, 0))
    # 
    # }
    target = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.DUP1 * 4 + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x64] + Op.DUP2
        + Op.JUMPI(pc=0x88, condition=Op.EQ(0x8ddf5d9a5251c41efd2949f53db0a464116c7c6e, Op.DUP1))
        + Op.JUMPI(pc=0x88, condition=Op.EQ(0x498516b6b2f25cb6a8e011a7c37a617b77e7d500, Op.DUP1))
        + Op.JUMPI(pc=0x80, condition=Op.EQ(0x8873820bb96daa39db93ae64a9d6397e4c6a48d7, Op.DUP1))
        + Op.PUSH20[0x303b6790d019874a107418eb549e4e7766a64728]
        + Op.JUMPI(pc=0x79, condition=Op.EQ) + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.CALL) + Op.STOP + Op.JUMPDEST
        + Op.PUSH1[0x18] + Op.ADD + Op.JUMP(pc=0x73) + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x18] + Op.ADD + Op.JUMP(pc=0x73) + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0x1b] + Op.ADD + Op.JUMP(pc=0x73),
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x0a92fc97bb4c47b3d5e9e96fbb1c3fc2f07dba81"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(call(0, cb, 0, 0, 0, 0, 0))
    # }
    addr_0x0000000000000000000000000000000000001000 = pre.deploy_contract(
        code=Op.CALL(gas=Op.DUP2, address=Op.COINBASE, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x8ddf5d9a5251c41efd2949f53db0a464116c7c6e"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(callcode(0, cb, 0, 0, 0, 0, 0))
    # }
    addr_0x0000000000000000000000000000000000002000 = pre.deploy_contract(
        code=Op.CALLCODE(gas=Op.DUP2, address=Op.COINBASE, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x498516b6b2f25cb6a8e011a7c37a617b77e7d500"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(delegatecall(0, cb, 0, 0, 0, 0))
    # }
    addr_0x0000000000000000000000000000000000003000 = pre.deploy_contract(
        code=Op.DELEGATECALL(gas=Op.DUP2, address=Op.COINBASE, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x8873820bb96daa39db93ae64a9d6397e4c6a48d7"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(staticcall(0, cb, 0, 0, 0, 0))
    # }
    addr_0x0000000000000000000000000000000000004000 = pre.deploy_contract(
        code=Op.STATICCALL(gas=Op.DUP2, address=Op.COINBASE, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        address=Address("0x303b6790d019874a107418eb549e4e7766a64728"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {target: Account(storage={0: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
