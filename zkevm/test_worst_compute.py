"""
abstract: Tests zkEVMs worst-case compute scenarios.
    Tests zkEVMs worst-case compute scenarios.

Tests running worst-case compute opcodes and precompile scenarios for zkEVMs.
"""

import math

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Transaction,
    While,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"

MAX_CODE_SIZE = 24 * 1024
KECCAK_RATE = 136
ECRECOVER_GAS_COST = 3_000


@pytest.mark.valid_from("Cancun")
def test_worst_keccak(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a block with as many KECCAK256 permutations as possible."""
    env = Environment()

    # Intrinsic gas cost is paid once.
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    available_gas = env.gas_limit - intrinsic_gas_calculator()

    gsc = fork.gas_costs()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    # Discover the optimal input size to maximize keccak-permutations, not keccak calls.
    # The complication of the discovery arises from the non-linear gas cost of memory expansion.
    max_keccak_perm_per_block = 0
    optimal_input_length = 0
    for i in range(1, 1_000_000, 32):
        iteration_gas_cost = (
            2 * gsc.G_VERY_LOW  # PUSHN + PUSH1
            + gsc.G_KECCAK_256  # KECCAK256 static cost
            + math.ceil(i / 32) * gsc.G_KECCAK_256_WORD  # KECCAK256 dynamic cost
            + gsc.G_BASE  # POP
        )
        # From the available gas, we substract the mem expansion costs considering we know the
        # current input size length i.
        available_gas_after_expansion = max(0, available_gas - mem_exp_gas_calculator(new_bytes=i))
        # Calculate how many calls we can do.
        num_keccak_calls = available_gas_after_expansion // iteration_gas_cost
        # KECCAK does 1 permutation every 136 bytes.
        num_keccak_permutations = num_keccak_calls * math.ceil(i / KECCAK_RATE)

        # If we found an input size that is better (reg permutations/gas), then save it.
        if num_keccak_permutations > max_keccak_perm_per_block:
            max_keccak_perm_per_block = num_keccak_permutations
            optimal_input_length = i

    # max_iters_loop contains how many keccak calls can be done per loop.
    # The loop is as big as possible bounded by the maximum code size.
    #
    # The loop structure is: JUMPDEST + [attack iteration] + PUSH0 + JUMP
    #
    # Now calculate available gas for [attack iteration]:
    #   Numerator = MAX_CODE_SIZE-3. The -3 is for the JUMPDEST, PUSH0 and JUMP.
    #   Denominator = (PUSHN + PUSH1 + KECCAK256 + POP) + PUSH1_DATA + PUSHN_DATA
    # TODO: the testing framework uses PUSH1(0) instead of PUSH0 which is suboptimal for the
    # attack, whenever this is fixed adjust accordingly.
    start_code = Op.JUMPDEST + Op.PUSH20[optimal_input_length]
    loop_code = Op.POP(Op.SHA3(Op.PUSH0, Op.DUP1))
    end_code = Op.POP + Op.JUMP(Op.PUSH0)
    max_iters_loop = (MAX_CODE_SIZE - (len(start_code) + len(end_code))) // len(loop_code)
    code = start_code + (loop_code * max_iters_loop) + end_code
    if len(code) > MAX_CODE_SIZE:
        # Must never happen, but keep it as a sanity check.
        raise ValueError(f"Code size {len(code)} exceeds maximum code size {MAX_CODE_SIZE}")

    code_address = pre.deploy_contract(code=bytes(code))

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "address,static_cost,per_word_dynamic_cost,bytes_per_unit_of_work",
    [
        pytest.param(0x02, 60, 12, 64, id="SHA2-256"),
        pytest.param(0x03, 600, 120, 64, id="RIPEMD-160"),
        pytest.param(0x04, 15, 3, 1, id="IDENTITY"),
    ],
)
def test_worst_precompile_only_data_input(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    address: Address,
    static_cost: int,
    per_word_dynamic_cost: int,
    bytes_per_unit_of_work: int,
):
    """Test running a block with as many precompile calls which have a single `data` input."""
    env = Environment()

    # Intrinsic gas cost is paid once.
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    available_gas = env.gas_limit - intrinsic_gas_calculator()

    gsc = fork.gas_costs()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    # Discover the optimal input size to maximize precompile work, not precompile calls.
    max_work = 0
    optimal_input_length = 0
    for input_length in range(1, 1_000_000, 32):
        parameters_gas = (
            gsc.G_BASE  # PUSH0 = arg offset
            + gsc.G_BASE  # PUSH0 = arg size
            + gsc.G_BASE  # PUSH0 = arg size
            + gsc.G_VERY_LOW  # PUSH0 = arg offset
            + gsc.G_VERY_LOW  # PUSHN = address
            + gsc.G_BASE  # GAS
        )
        iteration_gas_cost = (
            parameters_gas
            + +static_cost  # Precompile static cost
            + math.ceil(input_length / 32) * per_word_dynamic_cost  # Precompile dynamic cost
            + gsc.G_BASE  # POP
        )
        # From the available gas, we substract the mem expansion costs considering we know the
        # current input size length.
        available_gas_after_expansion = max(
            0, available_gas - mem_exp_gas_calculator(new_bytes=input_length)
        )
        # Calculate how many calls we can do.
        num_calls = available_gas_after_expansion // iteration_gas_cost
        total_work = num_calls * math.ceil(input_length / bytes_per_unit_of_work)

        # If we found an input size that is better (reg permutations/gas), then save it.
        if total_work > max_work:
            max_work = total_work
            optimal_input_length = input_length

    calldata = Op.CODECOPY(0, 0, optimal_input_length)
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, address, 0, optimal_input_length, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block)

    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
    )


@pytest.mark.valid_from("Cancun")
def test_worst_modexp(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a block with as many MODEXP calls as possible."""
    env = Environment()

    base_mod_length = 32
    exp_length = 32

    base = 2 ** (8 * base_mod_length) - 1
    mod = 2 ** (8 * base_mod_length) - 2  # Prevents base == mod
    exp = 2 ** (8 * exp_length) - 1

    # MODEXP calldata
    calldata = (
        Op.MSTORE(0 * 32, base_mod_length)
        + Op.MSTORE(1 * 32, exp_length)
        + Op.MSTORE(2 * 32, base_mod_length)
        + Op.MSTORE(3 * 32, base)
        + Op.MSTORE(4 * 32, exp)
        + Op.MSTORE(5 * 32, mod)
    )

    # EIP-2565
    mul_complexity = math.ceil(base_mod_length / 8) ** 2
    iter_complexity = exp.bit_length() - 1
    gas_cost = math.floor((mul_complexity * iter_complexity) / 3)
    attack_block = Op.POP(Op.STATICCALL(gas_cost, 0x5, 0, 32 * 6, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block)

    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
    )


@pytest.mark.valid_from("Cancun")
def test_worst_ecrecover(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a block with as many ECRECOVER calls as possible."""
    env = Environment()

    # Calldata
    calldata = (
        Op.MSTORE(0 * 32, 0x38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E)
        + Op.MSTORE(1 * 32, 27)
        + Op.MSTORE(2 * 32, 0x38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E)
        + Op.MSTORE(3 * 32, 0x789D1DD423D25F0772D2748D60F7E4B81BB14D086EBA8E8E8EFB6DCFF8A4AE02)
    )

    attack_block = Op.POP(Op.STATICCALL(ECRECOVER_GAS_COST, 0x1, 0, 32 * 4, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block)
    code_address = pre.deploy_contract(code=bytes(code))

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
    )


def code_loop_precompile_call(calldata: Bytecode, attack_block: Bytecode):
    """Create a code loop that calls a precompile with the given calldata."""
    # The attack contract is: CALLDATA_PREP + #JUMPDEST + [attack_block]* + JUMP(#)
    jumpdest = Op.JUMPDEST
    jump_back = Op.JUMP(len(calldata))
    max_iters_loop = (MAX_CODE_SIZE - len(calldata) - len(jumpdest) - len(jump_back)) // len(
        attack_block
    )
    code = calldata + jumpdest + sum([attack_block] * max_iters_loop) + jump_back
    if len(code) > MAX_CODE_SIZE:
        # Must never happen, but keep it as a sanity check.
        raise ValueError(f"Code size {len(code)} exceeds maximum code size {MAX_CODE_SIZE}")

    return code


@pytest.mark.zkevm
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_worst_jumps(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a JUMP-intensive contract."""
    env = Environment()

    def jump_seq():
        return Op.JUMP(Op.ADD(Op.PC, 1)) + Op.JUMPDEST

    bytes_per_seq = len(jump_seq())
    seqs_per_call = MAX_CODE_SIZE // bytes_per_seq

    # Create and deploy the jump-intensive contract
    jumps_code = sum([jump_seq() for _ in range(seqs_per_call)])
    jumps_address = pre.deploy_contract(code=bytes(jumps_code))

    # Call the contract repeatedly until gas runs out.
    caller_code = While(body=Op.POP(Op.CALL(address=jumps_address)))
    caller_address = pre.deploy_contract(caller_code)

    txs = [
        Transaction(
            to=caller_address,
            gas_limit=env.gas_limit,
            sender=pre.fund_eoa(),
        )
    ]

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=[Block(txs=txs)],
    )


@pytest.mark.zkevm
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_worst_jumpdests(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a JUMPDEST-intensive contract."""
    env = Environment()

    # Create and deploy a contract with many JUMPDESTs
    jumpdests_code = sum([Op.JUMPDEST] * MAX_CODE_SIZE)
    jumpdests_address = pre.deploy_contract(code=bytes(jumpdests_code))

    # Call the contract repeatedly until gas runs out.
    caller_code = While(body=Op.POP(Op.CALL(address=jumpdests_address)))
    caller_address = pre.deploy_contract(caller_code)

    txs = [
        Transaction(
            to=caller_address,
            gas_limit=env.gas_limit,
            sender=pre.fund_eoa(),
        )
    ]

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post={},
        blocks=[Block(txs=txs)],
    )


DEFAULT_BINOP_ARGS = (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
    0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001,
)


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode,opcode_args",
    [
        (
            Op.ADD,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.MUL,
            DEFAULT_BINOP_ARGS,
        ),
        (
            # This has the cycle of 2, after two SUBs values are back to initials.
            Op.SUB,
            DEFAULT_BINOP_ARGS,
        ),
        (
            # This has the cycle of 2:
            # v[0] = a // b
            # v[1] = a // v[0] = a // (a // b) = b
            # v[2] = a // b
            Op.DIV,
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                # We want the first divisor to be slightly bigger than 2**128:
                # this is the worst case for the division algorithm.
                0x100000000000000000000000000000033,
            ),
        ),
        (
            # Same as DIV, but the numerator made positive, and the divisor made negative.
            Op.SDIV,
            (
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCD,
            ),
        ),
        (
            # This scenario is not suitable for MOD because the values quickly become 0.
            Op.MOD,
            DEFAULT_BINOP_ARGS,
        ),
        (
            # This scenario is not suitable for SMOD because the values quickly become 0.
            Op.SMOD,
            DEFAULT_BINOP_ARGS,
        ),
        (
            # This keeps the values unchanged, pow(2**256-1, 2**256-1, 2**256) == 2**256-1.
            Op.EXP,
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            ),
        ),
        (
            # Not great because we always sign-extend the 4 bytes.
            Op.SIGNEXTEND,
            (
                3,
                0xFFDADADA,  # Negative to have more work.
            ),
        ),
        (
            Op.LT,  # Keeps getting result 1.
            (0, 1),
        ),
        (
            Op.GT,  # Keeps getting result 0.
            (0, 1),
        ),
        (
            Op.SLT,  # Keeps getting result 1.
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 1),
        ),
        (
            Op.SGT,  # Keeps getting result 0.
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, 1),
        ),
        (
            # The worst case is if the arguments are equal (no early return),
            # so let's keep it comparing ones.
            Op.EQ,
            (1, 1),
        ),
        (
            Op.AND,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.OR,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.XOR,
            DEFAULT_BINOP_ARGS,
        ),
        (
            Op.BYTE,  # Keep extracting the last byte: 0x2F.
            (31, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F),
        ),
        (
            Op.SHL,  # Shift by 1 until getting 0.
            (1, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F),
        ),
        (
            Op.SHR,  # Shift by 1 until getting 0.
            (1, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F),
        ),
        (
            Op.SAR,  # Shift by 1 until getting -1.
            (1, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F),
        ),
    ],
    ids=lambda param: "" if isinstance(param, tuple) else param,
)
def test_worst_binop_simple(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    opcode: Op,
    opcode_args: tuple[int, int],
):
    """
    Test running a block with as many binary instructions (takes two args, produces one value)
    as possible. The execution starts with two initial values on the stack, and the stack is
    balanced by the DUP2 instruction.
    """
    env = Environment()

    tx_data = b"".join(arg.to_bytes(32, byteorder="big") for arg in opcode_args)

    code_prefix = Op.JUMPDEST + Op.CALLDATALOAD(0) + Op.CALLDATALOAD(32)
    code_suffix = Op.POP + Op.POP + Op.PUSH0 + Op.JUMP
    code_body_len = MAX_CODE_SIZE - len(code_prefix) - len(code_suffix)
    code_body = (Op.DUP2 + opcode) * (code_body_len // 2)
    code = code_prefix + code_body + code_suffix
    assert len(code) == MAX_CODE_SIZE - 1

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=tx_data,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.ISZERO, Op.NOT])
def test_worst_unop(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    opcode: Op,
):
    """
    Test running a block with as many unary instructions (takes one arg, produces one value)
    as possible.
    """
    env = Environment()

    code_prefix = Op.JUMPDEST + Op.PUSH0  # Start with the arg 0.
    code_suffix = Op.POP + Op.PUSH0 + Op.JUMP
    code_body_len = MAX_CODE_SIZE - len(code_prefix) - len(code_suffix)
    code_body = opcode * code_body_len
    code = code_prefix + code_body + code_suffix
    assert len(code) == MAX_CODE_SIZE

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[tx])],
    )
