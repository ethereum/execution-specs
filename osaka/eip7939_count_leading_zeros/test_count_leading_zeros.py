"""
abstract: Tests [EIP-7939: Count leading zeros (CLZ) opcode](https://eips.ethereum.org/EIPS/eip-7939)
    Test cases for [EIP-7939: Count leading zeros (CLZ) opcode](https://eips.ethereum.org/EIPS/eip-7939).
"""

import pytest

from ethereum_test_base_types import Storage
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ...prague.eip7702_set_code_tx.spec import Spec as Spec7702
from .spec import Spec, ref_spec_7939

REFERENCE_SPEC_GIT_PATH = ref_spec_7939.git_path
REFERENCE_SPEC_VERSION = ref_spec_7939.version


def clz_parameters():
    """Generate all test case parameters."""
    test_cases = []

    # Format 0x000...000: all zeros
    test_cases.append(("zero", 0, 256))

    # Format 0xb000...111: leading zeros followed by ones
    for bits in range(257):
        value = (2**256 - 1) >> bits
        expected_clz = bits
        assert expected_clz == Spec.calculate_clz(value), (
            f"CLZ calculation mismatch for leading_zeros_{bits}: "
            f"manual={expected_clz}, spec={Spec.calculate_clz(value)}, value={hex(value)}"
        )
        test_cases.append((f"leading_zeros_{bits}", value, expected_clz))

    # Format 0xb010...000: single bit set (1 << N for N = 1…256)
    for bits in range(1, 257):
        if bits == 256:
            # Special case: 1 << 256 = 0 in 256-bit arithmetic (overflow)
            value = 0
            expected_clz = 256
        else:
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
def test_clz_gas_cost(state_test: StateTestFiller, pre: Alloc, fork: Fork):
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
            storage={"0x00": fork.gas_costs().G_LOW}
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize("bits", [0, 64, 128, 255])
@pytest.mark.parametrize("gas_cost_delta", [-2, -1, 0, 1, 2])
def test_clz_gas_cost_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    bits: int,
    gas_cost_delta: int,
):
    """Test CLZ opcode gas cost boundary."""
    code = Op.PUSH32(1 << bits) + Op.CLZ

    contract_address = pre.deploy_contract(code=code)

    call_code = Op.SSTORE(
        0,
        Op.CALL(
            gas=fork.gas_costs().G_VERY_LOW + Spec.CLZ_GAS_COST + gas_cost_delta,
            address=contract_address,
        ),
    )
    call_address = pre.deploy_contract(
        code=call_code,
        storage={"0x00": "0xdeadbeef"},
    )

    tx = Transaction(to=call_address, sender=pre.fund_eoa(), gas_limit=200_000)

    post = {call_address: Account(storage={"0x00": 0 if gas_cost_delta < 0 else 1})}

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
        code=Op.SSTORE(Op.TIMESTAMP, Op.CLZ(1 << 100)) + Op.STOP,
        storage={14_999: "0xdeadbeef"},
    )
    caller_address = pre.deploy_contract(
        code=Op.SSTORE(Op.TIMESTAMP, Op.CALL(gas=0xFFFF, address=callee_address)),
        storage={14_999: "0xdeadbeef"},
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
                    14_999: 0,  # Call fails as opcode not valid before Osaka
                    15_000: 1,  # Call succeeds on fork transition block
                    15_001: 1,  # Call continues to succeed after transition
                }
            ),
            callee_address: Account(
                storage={
                    14_999: "0xdeadbeef",  # CLZ not valid before fork, storage unchanged
                    15_000: 155,  # CLZ valid on transition block, CLZ(1 << 100) = 155
                    15_001: 155,  # CLZ continues to be valid after transition
                }
            ),
        },
    )


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize("opcode", [Op.JUMPI, Op.JUMP])
@pytest.mark.parametrize("valid_jump", [True, False])
@pytest.mark.parametrize("jumpi_condition", [True, False])
@pytest.mark.parametrize("bits", [0, 16, 64, 128, 255])
def test_clz_jump_operation(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    valid_jump: bool,
    jumpi_condition: bool,
    bits: int,
):
    """Test CLZ opcode with valid and invalid jump."""
    if opcode == Op.JUMP and not jumpi_condition:
        pytest.skip("Duplicate case for JUMP.")

    code = Op.PUSH32(1 << bits)

    if opcode == Op.JUMPI:
        code += Op.PUSH1(jumpi_condition)

    code += Op.PUSH1(len(code) + 3) + opcode

    if valid_jump:
        code += Op.JUMPDEST

    code += Op.CLZ + Op.PUSH0 + Op.SSTORE + Op.RETURN(0, 0)

    callee_address = pre.deploy_contract(code=code)

    caller_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(gas=0xFFFF, address=callee_address)),
        storage={"0x00": "0xdeadbeef"},
    )

    tx = Transaction(
        to=caller_address,
        sender=pre.fund_eoa(),
        gas_limit=200_000,
    )

    expected_clz = 255 - bits

    post = {
        caller_address: Account(storage={"0x00": 1 if valid_jump or not jumpi_condition else 0}),
    }

    if valid_jump or not jumpi_condition:
        post[callee_address] = Account(storage={"0x00": expected_clz})

    state_test(pre=pre, post=post, tx=tx)


auth_account_start_balance = 0


@pytest.mark.valid_from("Osaka")
def test_clz_from_set_code(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test the address opcode in a set-code transaction."""
    storage = Storage()
    auth_signer = pre.fund_eoa(auth_account_start_balance)

    set_code = Bytecode()
    for bits in [0, 1, 128, 255]:
        expected_clz = 255 - bits
        set_code += Op.SSTORE(storage.store_next(expected_clz), Op.CLZ(1 << bits))
    set_code += Op.STOP

    set_code_to_address = pre.deploy_contract(set_code)

    tx = Transaction(
        gas_limit=200_000,
        to=auth_signer,
        value=0,
        authorization_list=[
            AuthorizationTuple(
                address=set_code_to_address,
                nonce=0,
                signer=auth_signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            set_code_to_address: Account(storage={}),
            auth_signer: Account(
                nonce=1,
                code=Spec7702.delegation_designation(set_code_to_address),
                storage=storage,
            ),
        },
    )


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize("bits", [0, 64, 255])
@pytest.mark.parametrize("opcode", [Op.CODECOPY, Op.EXTCODECOPY])
def test_clz_code_copy_operation(state_test: StateTestFiller, pre: Alloc, bits: int, opcode: Op):
    """Test CLZ opcode with code copy operation."""
    storage = Storage()

    expected_value = 255 - bits
    clz_code_offset = len(Op.CLZ(1 << bits)) - 1  # Offset to CLZ opcode

    mload_value = Spec.CLZ << 248  # CLZ opcode in MSB position (0x1E000...000)

    target_address = pre.deploy_contract(code=Op.CLZ(1 << bits))

    clz_contract_address = pre.deploy_contract(
        code=(
            Op.CLZ(1 << bits)  # Calculate CLZ of the value
            + Op.SSTORE(storage.store_next(expected_value), Op.CLZ(1 << bits))  # Store CLZ result
            + (  # Load CLZ byte from code with CODECOPY or EXTCODECOPY
                Op.CODECOPY(dest_offset=0, offset=clz_code_offset, size=1)
                if opcode == Op.CODECOPY
                else Op.EXTCODECOPY(
                    address=target_address, dest_offset=0, offset=clz_code_offset, size=1
                )
            )
            + Op.SSTORE(storage.store_next(mload_value), Op.MLOAD(0))  # Store loaded CLZ byte
        ),
        storage={"0x00": "0xdeadbeef"},
    )

    post = {
        clz_contract_address: Account(
            storage={
                "0x00": expected_value,
                "0x01": mload_value,
            }
        )
    }
    tx = Transaction(
        to=clz_contract_address,
        sender=pre.fund_eoa(),
        gas_limit=200_000,
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize("bits", [0, 64, 255])
@pytest.mark.parametrize("opcode", [Op.CODECOPY, Op.EXTCODECOPY])
def test_clz_with_memory_operation(state_test: StateTestFiller, pre: Alloc, bits: int, opcode: Op):
    """Test CLZ opcode with memory operation."""
    storage = Storage()

    expected_value = 255 - bits

    # Target code pattern:
    #   PUSH32 (1 << bits)
    #   PUSH0
    #   MSTORE
    #
    # This sequence stores a 32-byte value in memory.
    # Later, we copy the immediate value from the PUSH32 instruction into memory
    # using CODECOPY or EXTCODECOPY, and then load it with MLOAD for the CLZ test.
    target_code = Op.PUSH32(1 << bits)
    offset = 1

    target_address = pre.deploy_contract(code=target_code)

    clz_contract_address = pre.deploy_contract(
        code=(
            target_code
            + Op.SSTORE(storage.store_next(expected_value), Op.CLZ(1 << bits))  # Store CLZ result
            + (
                Op.CODECOPY(dest_offset=0, offset=offset, size=0x20)
                if opcode == Op.CODECOPY
                else Op.EXTCODECOPY(
                    address=target_address, dest_offset=0, offset=offset, size=0x20
                )
            )
            + Op.SSTORE(storage.store_next(expected_value), Op.CLZ(Op.MLOAD(0)))
        ),
        storage={"0x00": "0xdeadbeef"},
    )

    post = {
        clz_contract_address: Account(storage={"0x00": expected_value, "0x01": expected_value}),
    }

    tx = Transaction(
        to=clz_contract_address,
        sender=pre.fund_eoa(),
        gas_limit=200_000,
    )

    state_test(pre=pre, post=post, tx=tx)
