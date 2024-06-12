"""
abstract: Tests [EIP-3855: PUSH0 Instruction](https://eips.ethereum.org/EIPS/eip-3855)
    Tests for [EIP-3855: PUSH0 Instruction](https://eips.ethereum.org/EIPS/eip-3855).

note: Tests ported from:
    - [ethereum/tests/pull/1033](https://github.com/ethereum/tests/pull/1033).
"""

import pytest

from ethereum_test_tools import (
    EOA,
    Account,
    Alloc,
    Code,
    CodeGasMeasure,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import ref_spec_3855

REFERENCE_SPEC_GIT_PATH = ref_spec_3855.git_path
REFERENCE_SPEC_VERSION = ref_spec_3855.version

pytestmark = pytest.mark.valid_from("Shanghai")


@pytest.mark.parametrize(
    "contract_code,expected_storage",
    [
        # Use PUSH0 to set a key for SSTORE.
        pytest.param(
            Op.SSTORE(Op.PUSH0, 1),
            Account(storage={0x00: 0x01}),
            id="key_sstore",
        ),
        # Fill stack with PUSH0, then OR all values and save using SSTORE.
        pytest.param(
            (Op.PUSH0 * 1024) + (Op.OR * 1023) + Op.SSTORE(Op.SWAP1, 1),
            Account(storage={0x00: 0x01}),
            id="fill_stack",
        ),
        # Stack overflow by using PUSH0 1025 times.
        pytest.param(
            Op.SSTORE(Op.PUSH0, 1) + (Op.PUSH0 * 1025),
            Account(storage={0x00: 0x00}),
            id="stack_overflow",
        ),
        # Update an already existing storage value.
        pytest.param(
            Op.SSTORE(Op.PUSH0, 2) + Op.SSTORE(1, Op.PUSH0),
            Account(storage={0x00: 0x02, 0x01: 0x00}),
            id="storage_overwrite",
        ),
        # Jump to a JUMPDEST next to a PUSH0, must succeed.
        pytest.param(
            Op.PUSH1(4) + Op.JUMP + Op.PUSH0 + Op.JUMPDEST + Op.SSTORE(Op.PUSH0, 1) + Op.STOP,
            Account(storage={0x00: 0x01}),
            id="before_jumpdest",
        ),
        # Test PUSH0 gas cost.
        pytest.param(
            CodeGasMeasure(
                code=Op.PUSH0,
                extra_stack_items=1,
            ),
            Account(storage={0x00: 0x02}),
            id="gas_cost",
        ),
    ],
)
def test_push0_contracts(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Alloc,
    sender: EOA,
    contract_code: Code,
    expected_storage: Account,
):
    """
    Tests PUSH0 within various deployed contracts.
    """
    push0_contract = pre.deploy_contract(contract_code)
    tx = Transaction(to=push0_contract, gas_limit=100_000, sender=sender)
    post[push0_contract] = expected_storage
    state_test(env=env, pre=pre, post=post, tx=tx)


def test_push0_contract_during_staticcall(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Alloc,
    sender: EOA,
):
    """
    Test PUSH0 during STATICCALL.
    """
    push0_contract = pre.deploy_contract(Op.MSTORE8(Op.PUSH0, 0xFF) + Op.RETURN(Op.PUSH0, 1))
    staticcall_contract = pre.deploy_contract(
        (
            Op.SSTORE(0, Op.STATICCALL(100000, push0_contract, 0, 0, 0, 0))
            + Op.SSTORE(0, 1)
            + Op.RETURNDATACOPY(0x1F, 0, 1)
            + Op.SSTORE(1, Op.MLOAD(0))
        )
    )
    tx = Transaction(to=staticcall_contract, gas_limit=100_000, sender=sender)
    post[staticcall_contract] = Account(storage={0x00: 0x01, 0x01: 0xFF})
    state_test(env=env, pre=pre, post=post, tx=tx, tag="during_staticcall")
