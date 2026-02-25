"""
Ported from:
tests/static/state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0xe0
    push1 0x02
    exp
    swap1
    div
    dup1
    push4 0x61a47706
    eq
    push1 0x15
    jumpi
    stop
    jumpdest
    push1 0x1e
    push1 0x04
    calldataload
    push1 0x24
    jump
    jumpdest
    ... (61 more instructions)

callee code:
    push2 0xc350
    push1 0x00
    push1 0x00
    calldatacopy
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
    ["tests/static/state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        150000,
        250000000,
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_quadratic_complexity_solidity_call_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xc9c5a15a403e41498b6f69f6f89dd9f5892d21f7")
    contract = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=350000000,
    )

    pre[contract] = Account(
        balance=0x11c37937e08000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0x61a47706] + Op.EQ + Op.PUSH1[0x15]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x1e] + Op.PUSH1[0x4]
        + Op.CALLDATALOAD + Op.PUSH1[0x24] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP2
        + Op.PUSH1[0x0] + Op.DUP2 + Op.SWAP1 + Op.SSTORE + Op.POP
        + Op.PUSH20[0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b] + Op.SWAP1 + Op.POP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.DUP3 + Op.SGT + Op.ISZERO + Op.PUSH1[0xbf]
        + Op.JUMPI + Op.DUP1 + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SUB + Op.AND + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH32[0x6a75737400000000000000000000000000000000000000000000000000000000]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x4] + Op.ADD
        + Op.PUSH32[0x63616c6c00000000000000000000000000000000000000000000000000000000]
        + Op.DUP2 + Op.MSTORE + Op.PUSH1[0x20] + Op.ADD + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.DUP6 + Op.PUSH1[0x15] + Op.GAS + Op.SUB + Op.CALL
        + Op.POP + Op.POP + Op.PUSH1[0x1] + Op.DUP3 + Op.SUB + Op.SWAP2 + Op.POP
        + Op.PUSH1[0x45] + Op.JUMP + Op.JUMPDEST + Op.POP + Op.POP + Op.JUMP
    ),
    )
    pre[callee] = Account(
        balance=0x4c4b40,
        nonce=0,
        code=Op.PUSH2[0xc350] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATACOPY + Op.STOP,
    )
    pre[sender] = Account(balance=0x11c37937e08000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x6a7eeac5f12b409d42028f66b0b2132535ee158cfda439e3bfdd4558e8f4bf6c"
        ),
        to=contract,
        data=bytes.fromhex("61a47706000000000000000000000000000000000000000000000000000000000000c350"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
