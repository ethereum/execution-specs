"""
Verify the Ropsten "crashing transaction" attack replay: a creation
transaction whose init code CREATEs children in a loop while more than
50000 gas remains, then deposits its runtime code.

Ported from:
state_tests/stAttackTest/CrashingTransactionFiller.json

@manually-enhanced: Do not overwrite. On pre-EIP-8037 forks the loop
drains to the ported child count (created nonce 124); under EIP-8037
with the revised EIP-8038 pricing an iteration is dearer (new-account
plus code-deposit state gas spill from the frame) but still fits the
loop's 50000-gas guard, so the loop drains earlier and deposits with
fewer children — the split post pins both child counts.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stAttackTest/CrashingTransactionFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_crashing_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Replay the attack loop; EIP-8037 shrinks the child count."""
    sender = pre.fund_eoa()
    tx_balance = 1
    initcode = (
        Op.MSTORE(offset=0x40, value=0x60)
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
        + Op.STOP
    )
    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=4657786,
        value=tx_balance,
    )

    created = compute_create_address(address=sender, nonce=0)
    expected_created_contracts = 124
    if fork.is_eip_enabled(8037):
        # An iteration's state gas spill makes each pass dearer while
        # still fitting the loop's 50000-gas guard, so the loop drains
        # after far fewer children than the ported count.
        expected_created_contracts = 23
    created_account = Account(
        code=Op.MSTORE(offset=0x40, value=0x60)
        + Op.JUMP(pc=0x8)
        + Op.JUMPDEST
        + Op.STOP,
        balance=tx_balance,
        nonce=expected_created_contracts,
    )
    post = {
        sender: Account(nonce=1),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
