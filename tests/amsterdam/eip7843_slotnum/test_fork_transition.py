"""Tests for EIP-7843 fork transition behavior."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Op,
    Transaction,
)

from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version


@pytest.mark.valid_at_transition_to("EIP7843")
def test_slotnum_at_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test SLOTNUM behavior across the EIP-7843 fork transition.

    Before EIP-7843, opcode 0x4B is undefined: execution halts with an
    invalid-opcode exception and consumes all gas, so no SSTORE is observed.

    From EIP-7843 onward, SLOTNUM pushes the block's slot number provided
    by the consensus layer and the SSTORE succeeds.

    The contract keys storage by block number so each block's outcome is
    independently visible in the final post-state:

    * block 1 (pre-fork): slot 1 stays 0 — execution halted before SSTORE.
    * block 2 (transition): slot 2 == ``at_fork_slot``.
    * block 3 (post-fork): slot 3 == ``post_fork_slot``.
    """
    sender = pre.fund_eoa()
    # Pin SSTORE metadata so code.gas_cost(fork) covers EIP-8037 state
    # gas in post-fork blocks (the key is fresh per block because NUMBER
    # differs).
    code = (
        Op.SSTORE(
            Op.NUMBER,
            Op.SLOTNUM,
            key_warm=False,
            original_value=0,
            current_value=0,
            new_value=1,
        )
        + Op.STOP
    )
    contract = pre.deploy_contract(code)

    at_fork_slot = 200
    post_fork_slot = 201

    # `fork` is the transitioning class; the SSTORE state-gas budget
    # under EIP-8037 only applies after the transition, so size the
    # gas_limit against the destination fork.
    post_fork = fork.fork_at(timestamp=15_000)
    intrinsic_cost = post_fork.transaction_intrinsic_cost_calculator()()
    code_state = code.state_cost(post_fork)
    code_regular = code.gas_cost(post_fork) - code_state
    tx_gas_limit = intrinsic_cost + code_regular + code_state

    blocks = [
        Block(
            timestamp=ts,
            slot_number=slot,
            txs=[
                Transaction(sender=sender, to=contract, gas_limit=tx_gas_limit)
            ],
        )
        for ts, slot in [
            (14_999, None),
            (15_000, at_fork_slot),
            (15_001, post_fork_slot),
        ]
    ]
    post = {
        contract: Account(
            storage={
                1: 0,
                2: at_fork_slot,
                3: post_fork_slot,
            },
        ),
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
