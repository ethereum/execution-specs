"""
abstract: Tests [EIP-7939: Count leading zeros (CLZ) opcode](https://eips.ethereum.org/EIPS/eip-7939)
    Test cases for [EIP-7939: Count leading zeros (CLZ) opcode](https://eips.ethereum.org/EIPS/eip-7939).
"""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import Spec, ref_spec_7939

REFERENCE_SPEC_GIT_PATH = ref_spec_7939.git_path
REFERENCE_SPEC_VERSION = ref_spec_7939.version


def clz_parameters():
    """Generate all test case parameters."""
    test_cases = []

    # Format 0xb000...111: leading zeros followed by ones
    # Special case: bits=256 gives value=0 (all zeros)
    for bits in range(257):
        value = (2**256 - 1) >> bits
        expected_clz = bits
        assert expected_clz == Spec.calculate_clz(value), (
            f"CLZ calculation mismatch for leading_zeros_{bits}: "
            f"manual={expected_clz}, spec={Spec.calculate_clz(value)}, value={hex(value)}"
        )
        test_cases.append((f"leading_zeros_{bits}", value, expected_clz))

    # Format 0xb010...000: single bit set
    for bits in range(256):
        value = 1 << bits
        expected_clz = 255 - bits
        assert expected_clz == Spec.calculate_clz(value), (
            f"CLZ calculation mismatch for single_bit_{bits}: "
            f"manual={expected_clz}, spec={Spec.calculate_clz(value)}, value={hex(value)}"
        )
        test_cases.append((f"single_bit_{bits}", value, expected_clz))

    # Arbitrary edge cases
    arbitrary_values = [
        0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0,
        0x00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF00FF,
        0x0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F,
        0xDEADBEEFCAFEBABE0123456789ABCDEF,
        0x0123456789ABCDEF,
        (1 << 128) + 1,
        (1 << 200) + (1 << 100),
        2**255 - 1,
    ]
    for i, value in enumerate(arbitrary_values):
        expected_clz = Spec.calculate_clz(value)
        test_cases.append((f"arbitrary_{i}", value, expected_clz))

    return test_cases


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "test_id,value,expected_clz",
    clz_parameters(),
    ids=[f"{test_data[0]}-expected_clz_{test_data[2]}" for test_data in clz_parameters()],
)
def test_clz_opcode_scenarios(
    state_test: StateTestFiller,
    pre: Alloc,
    test_id: str,
    value: int,
    expected_clz: int,
):
    """
    Test CLZ opcode functionality.

    Cases:
    - Format 0xb000...111: leading zeros followed by ones (2**256 - 1 >> bits)
    - Format 0xb010...000: single bit set at position (1 << bits)

    Test coverage:
    - Leading zeros pattern: 0b000...111 (0 to 256 leading zeros)
    - Single bit pattern: 0b010...000 (bit at each possible position)
    - Edge cases: CLZ(0) = 256, CLZ(2^256-1) = 0
    """
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CLZ(value)),
        storage={"0x00": "0xdeadbeef"},
    )
    tx = Transaction(
        to=contract_address,
        sender=sender,
        gas_limit=200_000,
    )
    post = {
        contract_address: Account(storage={"0x00": expected_clz}),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_clz_gas(state_test: StateTestFiller, pre: Alloc, fork: Fork):
    """Test CLZ opcode gas cost."""
    contract_address = pre.deploy_contract(
        Op.SSTORE(
            0,
            CodeGasMeasure(
                code=Op.CLZ(Op.PUSH1(1)),
                extra_stack_items=1,
                overhead_cost=fork.gas_costs().G_VERY_LOW,
            ),
        ),
        storage={"0x00": "0xdeadbeef"},
    )
    sender = pre.fund_eoa()
    tx = Transaction(to=contract_address, sender=sender, gas_limit=200_000)
    post = {
        contract_address: Account(  # Cost measured is CLZ + PUSH1
            storage={"0x00": fork.gas_costs().G_VERY_LOW}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_clz_stack_underflow(state_test: StateTestFiller, pre: Alloc):
    """Test CLZ opcode with empty stack (should revert due to stack underflow)."""
    sender = pre.fund_eoa()
    callee_address = pre.deploy_contract(
        code=Op.CLZ + Op.STOP,  # No stack items, should underflow
    )
    caller_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(gas=0xFFFF, address=callee_address)),
        storage={"0x00": "0xdeadbeef"},
    )
    tx = Transaction(
        to=caller_address,
        sender=sender,
        gas_limit=200_000,
    )
    post = {
        caller_address: Account(
            storage={"0x00": 0}  # Call failed due to stack underflow
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_at_transition_to("Osaka", subsequent_forks=True)
def test_clz_fork_transition(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """Test CLZ opcode behavior at fork transition."""
    sender = pre.fund_eoa()
    callee_address = pre.deploy_contract(
        code=Op.SSTORE(Op.NUMBER, Op.CLZ(1 << 100)) + Op.STOP,
        storage={"0x00": "0xdeadbeef"},
    )
    caller_address = pre.deploy_contract(
        code=Op.SSTORE(Op.NUMBER, Op.CALL(gas=0xFFFF, address=callee_address)),
        storage={"0x00": "0xdeadbeef"},
    )
    blocks = [
        Block(
            timestamp=14_999,
            txs=[
                Transaction(
                    to=caller_address,
                    sender=sender,
                    nonce=0,
                    gas_limit=200_000,
                )
            ],
        ),
        Block(
            timestamp=15_000,
            txs=[
                Transaction(
                    to=caller_address,
                    sender=sender,
                    nonce=1,
                    gas_limit=200_000,
                )
            ],
        ),
        Block(
            timestamp=15_001,
            txs=[
                Transaction(
                    to=caller_address,
                    sender=sender,
                    nonce=2,
                    gas_limit=200_000,
                )
            ],
        ),
    ]
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post={
            caller_address: Account(
                storage={
                    14_999: 0,
                    15_000: 1,
                    15_001: 1,
                }
            ),
            callee_address: Account(
                storage={
                    14_999: 155,
                    15_000: 155,
                    15_001: 155,
                }
            ),
        },
    )
