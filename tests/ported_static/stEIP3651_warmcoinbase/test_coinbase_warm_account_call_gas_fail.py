"""
Test_coinbase_warm_account_call_gas_fail.

Ported from:
state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml
@manually-enhanced: Do not overwrite. `tx_gas` bumped on Amsterdam
to cover EIP-8037 state-gas spill; pre-EIP-8037 unchanged.

"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
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
        "state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
def test_coinbase_warm_account_call_gas_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_coinbase_warm_account_call_gas_fail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    addr = pre.deploy_contract(
        code=Op.CALL(
            gas=Op.DUP2,
            address=Op.COINBASE,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    addr_2 = pre.deploy_contract(
        code=Op.CALLCODE(
            gas=Op.DUP2,
            address=Op.COINBASE,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    addr_3 = pre.deploy_contract(
        code=Op.DELEGATECALL(
            gas=Op.DUP2,
            address=Op.COINBASE,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    addr_4 = pre.deploy_contract(
        code=Op.STATICCALL(
            gas=Op.DUP2,
            address=Op.COINBASE,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    target = pre.deploy_contract(
        code=Op.PUSH1[0x0]
        + Op.DUP1 * 4
        + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x64]
        + Op.DUP2
        + Op.JUMPI(
            pc=0x88,
            condition=Op.EQ(Op.PUSH20[addr], Op.DUP1),
        )
        + Op.JUMPI(
            pc=0x88,
            condition=Op.EQ(Op.PUSH20[addr_2], Op.DUP1),
        )
        + Op.JUMPI(
            pc=0x80,
            condition=Op.EQ(Op.PUSH20[addr_3], Op.DUP1),
        )
        + Op.PUSH20[addr_4]
        + Op.JUMPI(pc=0x79, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x18]
        + Op.ADD
        + Op.JUMP(pc=0x73)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x18]
        + Op.ADD
        + Op.JUMP(pc=0x73)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x1B]
        + Op.ADD
        + Op.JUMP(pc=0x73),
        balance=0xBA1A9CE0BA1A9CE,
    )

    tx_data = [
        Bytes("693c6139") + Hash(addr, left_padding=True),
        Bytes("693c6139") + Hash(addr_2, left_padding=True),
        Bytes("693c6139") + Hash(addr_3, left_padding=True),
        Bytes("693c6139") + Hash(addr_4, left_padding=True),
    ]
    # EIP-8037 state-gas spill on Amsterdam exceeds the original 80k.
    outer_tx_gas = 80000
    if fork.is_eip_enabled(8037):
        outer_tx_gas = 500_000
    tx_gas = [outer_tx_gas]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {target: Account(storage={0: 1})}

    state_test(pre=pre, post=post, tx=tx)
