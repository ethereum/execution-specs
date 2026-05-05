"""
Https://ropsten.etherscan.io/tx/0x8ec445380649f6c75a042a438ea9256c2fab2a...

Ported from:
state_tests/stAttackTest/CrashingTransactionFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stAttackTest/CrashingTransactionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_crashing_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Https://ropsten."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000, nonce=3270)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4712388,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.MSTORE(offset=0x40, value=0x60)
        + Op.JUMPDEST * 2
        + Op.JUMPI(pc=0x2C, condition=Op.ISZERO(Op.GT(Op.GAS, 0xC350)))
        + Op.MLOAD(offset=0x40)
        + Op.PUSH1[0x34]
        + Op.CODECOPY(dest_offset=Op.DUP4, offset=0x39, size=Op.DUP1)
        + Op.ADD
        + Op.DUP1
        + Op.SWAP1
        + Op.POP
        + Op.MLOAD(offset=0x40)
        + Op.DUP1
        + Op.SWAP2
        + Op.SUB
        + Op.SWAP1
        + Op.PUSH1[0x0]
        + Op.POP(Op.CREATE)
        + Op.JUMP(pc=0x6)
        + Op.JUMPDEST * 2
        + Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0x6D, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.MSTORE(offset=0x40, value=0x60)
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(
            address=Op.AND(
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, Op.CALLER
            )
        )
        + Op.JUMPDEST
        + Op.PUSH1[0xA]
        + Op.CODECOPY(dest_offset=0x0, offset=0x2A, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.MSTORE(offset=0x40, value=0x60)
        + Op.JUMP(pc=0x8)
        + Op.JUMPDEST
        + Op.STOP
        + Op.MSTORE(offset=0x40, value=0x60)
        + Op.JUMP(pc=0x8)
        + Op.JUMPDEST
        + Op.STOP,
        gas_limit=4657786,
        value=1,
        nonce=3270,
        gas_price=11,
    )

    post = {
        sender: Account(nonce=3271),
        compute_create_address(address=sender, nonce=3270): Account(
            code=bytes.fromhex("60606040526008565b00"),
            balance=1,
            nonce=124,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
