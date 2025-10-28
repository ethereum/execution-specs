"""Test gas cost of opcode."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

# Reference spec constants (required for test framework)
REFERENCE_SPEC_GIT_PATH = "ethereum/execution-specs"
REFERENCE_SPEC_VERSION = "gas-repricing"

pytestmark = pytest.mark.valid_from("GasRepricing")


def test_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test gas cost of CLZ opcode.
    """
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CLZ(Op.PUSH1(1))),
        storage={"0x00": "0xdeadbeef"},
    )
    tx = Transaction(
        to=contract_address,
        sender=sender,
        gas_limit=200_000,
    )
    post = {
        contract_address: Account(storage={"0x00": 255}),
    }
    state_test(pre=pre, post=post, tx=tx)
