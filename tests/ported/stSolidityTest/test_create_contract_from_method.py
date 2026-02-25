"""
Ported from:
tests/static/state_tests/stSolidityTest/CreateContractFromMethodFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0xe0
    push1 0x02
    exp
    swap1
    div
    dup1
    push4 0x7ee17e12
    eq
    push1 0x1f
    jumpi
    dup1
    push4 0xc0406226
    eq
    push1 0x2b
    jumpi
    stop
    jumpdest
    push1 0x25
    ... (106 more instructions)
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
    ["tests/static/state_tests/stSolidityTest/CreateContractFromMethodFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_contract_from_method(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0x186a0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2] + Op.EXP
        + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH4[0x7ee17e12] + Op.EQ + Op.PUSH1[0x1f]
        + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xc0406226] + Op.EQ + Op.PUSH1[0x2b]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x25] + Op.PUSH1[0x47] + Op.JUMP
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST
        + Op.PUSH1[0x31] + Op.PUSH1[0x3b] + Op.JUMP + Op.JUMPDEST + Op.DUP1
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.JUMPDEST + Op.PUSH1[0x0] + Op.PUSH1[0x43] + Op.PUSH1[0x47] + Op.JUMP
        + Op.JUMPDEST + Op.POP + Op.SWAP1 + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0x60] + Op.PUSH1[0x5d] + Op.PUSH1[0x0] + Op.CODECOPY
        + Op.PUSH1[0x60] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE + Op.SWAP1
        + Op.POP + Op.SWAP1 + Op.JUMP + Op.STOP + Op.PUSH1[0x54] + Op.DUP1
        + Op.PUSH1[0xc] + Op.PUSH1[0x0] + Op.CODECOPY + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0xe0] + Op.PUSH1[0x2]
        + Op.EXP + Op.SWAP1 + Op.DIV + Op.DUP1 + Op.PUSH3[0xf55d9d] + Op.EQ
        + Op.PUSH1[0x1e] + Op.JUMPI + Op.DUP1 + Op.PUSH4[0xb9c3d0a5] + Op.EQ
        + Op.PUSH1[0x2d] + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x27]
        + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH1[0x46] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x33]
        + Op.PUSH1[0x3d] + Op.JUMP + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.JUMPDEST + Op.PUSH1[0x0]
        + Op.PUSH1[0xe1] + Op.SWAP1 + Op.POP + Op.SWAP1 + Op.JUMP + Op.JUMPDEST
        + Op.DUP1 + Op.PUSH1[0x1] + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.SUB
        + Op.AND + Op.SELFDESTRUCT + Op.POP + Op.JUMP
    ),
    )
    pre[sender] = Account(balance=0x5f5e100, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=350000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
