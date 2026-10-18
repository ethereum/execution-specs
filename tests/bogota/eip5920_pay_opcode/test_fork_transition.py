"""
Fork transition tests for [EIP-5920: PAY opcode](https://eips.ethereum.org/EIPS/eip-5920).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Storage,
    Transaction,
    TransitionFork,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_5920

REFERENCE_SPEC_GIT_PATH = ref_spec_5920.git_path
REFERENCE_SPEC_VERSION = ref_spec_5920.version


@EIPChecklist.Opcode.Test.ForkTransition.Invalid()
@EIPChecklist.Opcode.Test.ForkTransition.At()
@pytest.mark.valid_at_transition_to("Bogota")
def test_pay_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: TransitionFork,
) -> None:
    """
    Test `PAY` (`0xfc`) across the Amsterdam -> Bogota fork transition:
    - Before transition (Amsterdam, timestamp 14,999): `0xfc` is an undefined
      opcode (`InvalidOpcode`), so subcall returns `0` and no value moves.
    - At transition (Bogota, timestamp 15,000): `0xfc` is `PAY`, so subcall
      returns `1` and value is transferred to the recipient.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(100)

    pay_callee = pre.deploy_contract(
        code=Op.PAY(recipient, 250) + Op.STOP,
        balance=1_000,
    )

    storage = Storage()
    caller = pre.deploy_contract(
        code=(
            Op.SSTORE(
                Op.TIMESTAMP,
                Op.CALL(100_000, pay_callee, 0, 0, 0, 0, 0),
            )
            + Op.STOP
        ),
    )

    pre_fork_timestamp = 14_999
    post_fork_timestamp = 15_000

    storage[pre_fork_timestamp] = 0
    storage[post_fork_timestamp] = 1

    blocks = [
        Block(
            timestamp=pre_fork_timestamp,
            txs=[
                Transaction(
                    sender=sender,
                    to=caller,
                    gas_limit=500_000,
                )
            ],
        ),
        Block(
            timestamp=post_fork_timestamp,
            txs=[
                Transaction(
                    sender=sender,
                    to=caller,
                    gas_limit=500_000,
                )
            ],
        ),
    ]

    post = {
        caller: Account(storage=storage),
        pay_callee: Account(balance=750),
        recipient: Account(balance=350),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)
