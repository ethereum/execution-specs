"""
Test block information opcodes.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmTests/blockInfoFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/blockInfoFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="Asserts the block fields of the test env")
)
@pytest.mark.parametrize(
    "opcode, field",
    [
        pytest.param(Op.COINBASE, "fee_recipient", id="coinbase"),
        pytest.param(Op.PREVRANDAO, "prev_randao", id="difficulty"),
        pytest.param(Op.GASLIMIT, "gas_limit", id="gaslimit"),
        pytest.param(Op.NUMBER, "number", id="number"),
        pytest.param(Op.TIMESTAMP, "timestamp", id="timestamp"),
    ],
)
def test_block_info(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Opcode,
    field: str,
) -> None:
    """Store a block field read by its opcode."""
    env = Environment()
    if opcode == Op.PREVRANDAO:
        if fork.header_prev_randao_required():
            env = Environment(prev_randao=0x20000)
        else:
            # Before the merge the same opcode reads the difficulty.
            field = "difficulty"
            env = Environment(difficulty=0x20000)
    contract = pre.deploy_contract(
        code=Op.SSTORE(0, opcode) + Op.STOP, storage={0: SENTINEL}
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage={0: getattr(env, field)})}
    state_test(env=env, pre=pre, post=post, tx=tx)
