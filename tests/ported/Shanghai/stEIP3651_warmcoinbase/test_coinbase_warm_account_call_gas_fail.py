"""
Ported from:
tests/static/state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml

contract code:
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    push1 0x04
    calldataload
    push1 0x64
    dup2
    dup1
    push20 0x8ddf5d9a5251c41efd2949f53db0a464116c7c6e
    eq
    push1 0x88
    jumpi
    dup1
    push20 0x498516b6b2f25cb6a8e011a7c37a617b77e7d500
    eq
    push1 0x88
    jumpi
    dup1
    ... (30 more instructions)

callee code:
    push1 0x00
    dup1
    dup1
    dup1
    coinbase
    dup2
    staticcall
    stop

callee_1 code:
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    coinbase
    dup2
    callcode
    stop

callee_2 code:
    push1 0x00
    dup1
    dup1
    dup1
    coinbase
    dup2
    delegatecall
    stop

callee_3 code:
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    coinbase
    dup2
    call
    stop
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000008ddf5d9a5251c41efd2949f53db0a464116c7c6e",
        "693c6139000000000000000000000000498516b6b2f25cb6a8e011a7c37a617b77e7d500",
        "693c61390000000000000000000000008873820bb96daa39db93ae64a9d6397e4c6a48d7",
        "693c6139000000000000000000000000303b6790d019874a107418eb549e4e7766a64728",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_warm_account_call_gas_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x50228c44ed92561d94511e8518a75aa463bd444b")
    sender = Address("0x485fd0fd5c1d0409d2b772a66e98a6ac867b9d8b")
    contract = Address("0x0a92fc97bb4c47b3d5e9e96fbb1c3fc2f07dba81")
    callee = Address("0x303b6790d019874a107418eb549e4e7766a64728")
    callee_1 = Address("0x498516b6b2f25cb6a8e011a7c37a617b77e7d500")
    callee_2 = Address("0x8873820bb96daa39db93ae64a9d6397e4c6a48d7")
    callee_3 = Address("0x8ddf5d9a5251c41efd2949f53db0a464116c7c6e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x64] + Op.DUP2 + Op.DUP1
        + Op.PUSH20[0x8ddf5d9a5251c41efd2949f53db0a464116c7c6e] + Op.EQ
        + Op.PUSH1[0x88] + Op.JUMPI + Op.DUP1
        + Op.PUSH20[0x498516b6b2f25cb6a8e011a7c37a617b77e7d500] + Op.EQ
        + Op.PUSH1[0x88] + Op.JUMPI + Op.DUP1
        + Op.PUSH20[0x8873820bb96daa39db93ae64a9d6397e4c6a48d7] + Op.EQ
        + Op.PUSH1[0x80] + Op.JUMPI
        + Op.PUSH20[0x303b6790d019874a107418eb549e4e7766a64728] + Op.EQ
        + Op.PUSH1[0x79] + Op.JUMPI + Op.JUMPDEST + Op.CALL + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x18] + Op.ADD + Op.PUSH1[0x73]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x18] + Op.ADD + Op.PUSH1[0x73]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x1b] + Op.ADD + Op.PUSH1[0x73]
        + Op.JUMP
    ),
    )
    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.COINBASE + Op.DUP2
        + Op.STATICCALL + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.COINBASE
        + Op.DUP2 + Op.CALLCODE + Op.STOP
    ),
    )
    pre[coinbase] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.COINBASE + Op.DUP2
        + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.COINBASE
        + Op.DUP2 + Op.CALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47"
        ),
        to=contract,
        data=tx_data,
        gas_limit=80000,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
