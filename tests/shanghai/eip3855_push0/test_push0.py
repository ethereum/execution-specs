"""
Tests [EIP-3855: PUSH0 Instruction](https://eips.ethereum.org/EIPS/eip-3855).

Tests ported from:
[ethereum/tests/pull/1033](https://github.com/ethereum/tests/pull/1033).
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_3855

REFERENCE_SPEC_GIT_PATH = ref_spec_3855.git_path
REFERENCE_SPEC_VERSION = ref_spec_3855.version

pytestmark = pytest.mark.valid_from("Shanghai")


@pytest.mark.xdist_group(name="bigmem")
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
            Op.PUSH1(4)
            + Op.JUMP
            + Op.PUSH0
            + Op.JUMPDEST
            + Op.SSTORE(Op.PUSH0, 1)
            + Op.STOP,
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
    fork: Fork,
    contract_code: Bytecode,
    expected_storage: Account,
) -> None:
    """Tests PUSH0 within various deployed contracts."""
    push0_contract = pre.deploy_contract(contract_code)
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    tx = Transaction(
        to=push0_contract,
        # `contract_code.gas_cost(fork)` covers regular + (under EIP-8037)
        # state work for the parametrized snippets; add EIP-1706 slack for
        # the trailing SSTORE.
        gas_limit=(
            intrinsic_calc()
            + contract_code.gas_cost(fork)
            + fork.sstore_state_gas()
        ),
        sender=sender,
    )
    post[push0_contract] = expected_storage
    state_test(env=env, pre=pre, post=post, tx=tx)


class TestPush0CallContext:
    """
    Test the PUSH0 operation in various contract call contexts.

    Test PUSH0 in the following contract call contexts:

    - CALL,
    - CALLCODE,
    - DELEGATECALL,
    - STATICCALL.
    """

    @pytest.fixture
    def push0_contract_callee(self, pre: Alloc) -> Address:
        """
        Deploys a PUSH0 contract callee to the pre alloc returning its address.
        """
        push0_contract = pre.deploy_contract(
            Op.MSTORE8(Op.PUSH0, 0xFF) + Op.RETURN(Op.PUSH0, 1)
        )
        return push0_contract

    PUSH0_CALL_FORWARDED_GAS = 100_000

    @pytest.fixture
    def push0_contract_caller_code(
        self, call_opcode: Op, push0_contract_callee: Address
    ) -> Bytecode:
        """Bytecode for the caller contract."""
        return (
            Op.SSTORE(
                0,
                call_opcode(
                    gas=self.PUSH0_CALL_FORWARDED_GAS,
                    address=push0_contract_callee,
                ),
            )
            + Op.SSTORE(0, 1)
            + Op.RETURNDATACOPY(0x1F, 0, 1)
            + Op.SSTORE(1, Op.MLOAD(0))
        )

    @pytest.fixture
    def push0_contract_caller(
        self, pre: Alloc, push0_contract_caller_code: Bytecode
    ) -> Address:
        """
        Deploy the contract that calls the callee PUSH0 contract into `pre`.

        This fixture returns its address.
        """
        return pre.deploy_contract(push0_contract_caller_code)

    @pytest.mark.xdist_group(name="bigmem")
    @pytest.mark.parametrize(
        "call_opcode",
        [
            Op.CALL,
            Op.CALLCODE,
            Op.DELEGATECALL,
            Op.STATICCALL,
        ],
        ids=["call", "callcode", "delegatecall", "staticcall"],
    )
    def test_push0_contract_during_call_contexts(
        self,
        state_test: StateTestFiller,
        env: Environment,
        pre: Alloc,
        post: Alloc,
        sender: EOA,
        push0_contract_caller: Address,
        push0_contract_caller_code: Bytecode,
        fork: Fork,
    ) -> None:
        """Test PUSH0 during various call contexts."""
        intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
        tx = Transaction(
            to=push0_contract_caller,
            # Caller's static cost (3 SSTOREs + CALL static + RETURNDATACOPY
            # + MLOAD) plus the forwarded inner-call gas, plus EIP-1706
            # stipend slack on the trailing SSTORE.
            gas_limit=(
                intrinsic_calc()
                + push0_contract_caller_code.gas_cost(fork)
                + self.PUSH0_CALL_FORWARDED_GAS
                + fork.sstore_state_gas()
            ),
            sender=sender,
        )
        post[push0_contract_caller] = Account(storage={0x00: 0x01, 0x01: 0xFF})
        state_test(env=env, pre=pre, post=post, tx=tx)
