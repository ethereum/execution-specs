"""
Ported from:
tests/static/state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFiller.yml

contract code:
    coinbase
    push1 0x04
    calldataload
    push1 0x00
    dup2
    iszero
    push1 0xcc
    jumpi
    dup2
    push1 0x01
    eq
    push1 0xba
    jumpi
    pop
    dup1
    push1 0x02
    eq
    push1 0xad
    jumpi
    dup1
    ... (148 more instructions)
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
    ["tests/static/state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
        "693c61390000000000000000000000000000000000000000000000000000000000000006",
        "693c61390000000000000000000000000000000000000000000000000000000000000007",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_warm_account_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x50228c44ed92561d94511e8518a75aa463bd444b")
    sender = Address("0x485fd0fd5c1d0409d2b772a66e98a6ac867b9d8b")
    contract = Address("0xa4a48fc5f3526a9bc06a0136ab0ba1d9574d15ba")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[coinbase] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.COINBASE + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.DUP2
        + Op.ISZERO + Op.PUSH1[0xcc] + Op.JUMPI + Op.DUP2 + Op.PUSH1[0x1] + Op.EQ
        + Op.PUSH1[0xba] + Op.JUMPI + Op.POP + Op.DUP1 + Op.PUSH1[0x2] + Op.EQ
        + Op.PUSH1[0xad] + Op.JUMPI + Op.DUP1 + Op.PUSH1[0x3] + Op.EQ + Op.PUSH1[0xa0]
        + Op.JUMPI + Op.DUP1 + Op.PUSH1[0x4] + Op.EQ + Op.PUSH1[0x8a] + Op.JUMPI
        + Op.DUP1 + Op.PUSH1[0x5] + Op.EQ + Op.PUSH1[0x74] + Op.JUMPI + Op.DUP1
        + Op.PUSH1[0x6] + Op.EQ + Op.PUSH1[0x5f] + Op.JUMPI + Op.PUSH1[0x7] + Op.EQ
        + Op.PUSH1[0x40] + Op.JUMPI + Op.PUSH1[0x0] + Op.DUP1 + Op.REVERT
        + Op.JUMPDEST + Op.PUSH1[0xb] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.GAS + Op.SWAP6 + Op.PUSH2[0x2710] + Op.STATICCALL + Op.SWAP2 + Op.GAS
        + Op.SWAP1 + Op.JUMPDEST + Op.SUB + Op.SUB + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0xb] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.GAS + Op.SWAP6 + Op.PUSH2[0x2710] + Op.DELEGATECALL + Op.SWAP2
        + Op.GAS + Op.SWAP1 + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.POP
        + Op.PUSH1[0xb] + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.GAS + Op.SWAP7 + Op.PUSH2[0x2710] + Op.CALLCODE + Op.SWAP2 + Op.GAS
        + Op.SWAP1 + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0xb]
        + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.GAS + Op.SWAP7
        + Op.PUSH2[0x2710] + Op.CALL + Op.SWAP2 + Op.GAS + Op.SWAP1 + Op.PUSH1[0x51]
        + Op.JUMP + Op.JUMPDEST + Op.POP + Op.PUSH1[0x8] + Op.GAS + Op.SWAP2
        + Op.BALANCE + Op.SWAP2 + Op.GAS + Op.SWAP1 + Op.PUSH1[0x51] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.PUSH1[0x8] + Op.GAS + Op.SWAP2 + Op.EXTCODEHASH
        + Op.SWAP2 + Op.GAS + Op.SWAP1 + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST
        + Op.SWAP2 + Op.PUSH1[0x5] + Op.SWAP2 + Op.POP + Op.PUSH1[0x0] + Op.DUP1
        + Op.DUP1 + Op.GAS + Op.SWAP4 + Op.EXTCODECOPY + Op.GAS + Op.SWAP1
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.PUSH1[0x8]
        + Op.GAS + Op.SWAP2 + Op.EXTCODESIZE + Op.SWAP2 + Op.GAS + Op.SWAP1
        + Op.PUSH1[0x51] + Op.JUMP
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
