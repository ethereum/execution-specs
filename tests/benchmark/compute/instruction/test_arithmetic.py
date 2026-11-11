"""
Benchmark arithmetic instructions.

Supported Opcodes:
- ADD
- ADDMOD
- MUL
- MULMOD
- SUB
- SUBMOD
- DIV
- SDIV
- MOD
- SMOD
- EXP
- SIGNEXTEND
"""

import operator
import random

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    JumpLoopGenerator,
    Op,
    Transaction,
)

from tests.benchmark.helper.numeric import (
    DEFAULT_BINOP_ARGS,
    make_dup,
    neg,
)


@pytest.mark.parametrize(
    "opcode,opcode_args",
    [
        pytest.param(
            Op.ADD,
            DEFAULT_BINOP_ARGS,
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            Op.MUL,
            DEFAULT_BINOP_ARGS,
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            # After every 2 SUB operations, values return to initial.
            Op.SUB,
            DEFAULT_BINOP_ARGS,
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            # This has the cycle of 2:
            # v[0] = a // b
            # v[1] = a // v[0] = a // (a // b) = b
            # v[2] = a // b
            Op.DIV,
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                # We want the first divisor to be slightly bigger than 2**128:
                # this is the worst case for the division algorithm with
                # optimized paths for division by 1 and 2 words.
                0x100000000000000000000000000000033,
            ),
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            # This has the cycle of 2, see above.
            Op.DIV,
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                # We want the first divisor to be slightly bigger than 2**64:
                # this is the worst case for the division algorithm with an
                # optimized path for division by 1 word.
                0x10000000000000033,
            ),
        ),
        pytest.param(
            # Same as DIV-0
            # But the numerator made positive, and the divisor made negative.
            Op.SDIV,
            (
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCD,
            ),
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            # Same as DIV-1
            # But the numerator made positive, and the divisor made negative.
            Op.SDIV,
            (
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFCD,
            ),
        ),
        pytest.param(
            # This keeps the values unchanged
            # pow(2**256-1, 2**256-1, 2**256) == 2**256-1.
            Op.EXP,
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            ),
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            # Not great, as we always sign-extend the 4 bytes.
            Op.SIGNEXTEND,
            (
                3,
                0xFFDADADA,  # Negative to have more work.
            ),
            marks=pytest.mark.repricing,
        ),
    ],
    ids=lambda param: "" if isinstance(param, tuple) else param,
)
def test_arithmetic(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
    opcode_args: tuple[int, ...],
) -> None:
    """
    Benchmark arithmetic instructions.

    Supports both binary ops and ternary operations.
    The execution starts with initial values on the stack.
    """
    tx_data = b"".join(
        arg.to_bytes(32, byteorder="big") for arg in opcode_args
    )

    depth = len(opcode_args)
    dup_op = make_dup(depth - 1)

    setup = sum((Op.CALLDATALOAD(32 * i) for i in range(depth)), Bytecode())
    setup += dup_op * depth

    attack_block = dup_op * (depth - 1) + opcode

    cleanup = Op.POP * depth + dup_op * depth

    benchmark_test(
        target_opcode=opcode,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
            tx_kwargs={"data": tx_data},
        ),
    )


@pytest.mark.parametrize("mod_bits", [255, 191, 127, 63])
@pytest.mark.parametrize("opcode", [Op.MOD, Op.SMOD])
@pytest.mark.repricing
def test_mod(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    mod_bits: int,
    opcode: Op,
) -> None:
    """
    Benchmark MOD instructions.

    The code pushes a pool of 15 numerators to the EVM stack, then loops over
    as many "MOD chains" as fit in the code size limit. A chain pushes a
    random `mod_bits`-bit modulus and evaluates `mod = numerators[i] % mod`
    until the modulus has lost 16 bits, so it keeps its word count, and pops
    the result. Every step takes the numerator leaving the largest remainder,
    so the modulus shrinks slowly and a chain runs about 160 steps. The code
    holds thousands of distinct moduli, too many for a branch predictor to
    learn.

    SMOD builds the same kind of chains on negated numerators and moduli.
    The sign takes the top bit, so its numerators have 255-bit magnitudes
    and its moduli at most 254 bits.
    """
    should_negate = opcode == Op.SMOD
    numerator_bits = 256 if not should_negate else 255
    modulus_bits = min(mod_bits, numerator_bits - 1)
    min_modulus = 2 ** (modulus_bits - 16)

    rng = random.Random(1)
    numerators = [
        rng.randint(2 ** (numerator_bits - 1), 2**numerator_bits - 1)
        for _ in range(15)
    ]

    def push(magnitude: int) -> Bytecode:
        value = neg(magnitude) if should_negate else magnitude
        push_op: Op = getattr(Op, f"PUSH{(value.bit_length() + 7) // 8}")
        return push_op[value]

    pool = sum((push(n) for n in numerators), Bytecode())
    code_prefix = pool + Op.JUMPDEST
    code_suffix = Op.JUMP(len(pool))
    room = fork.max_code_size() - len(code_prefix) - len(code_suffix)
    chains = Bytecode()
    while True:
        mod = rng.randint(2 ** (modulus_bits - 1), 2**modulus_bits - 1)
        chain = push(mod)
        while mod >= min_modulus:
            mod, i = max((n % mod, i) for i, n in enumerate(numerators))
            chain += make_dup(len(numerators) - i) + opcode
        chain += Op.POP
        if len(chains) + len(chain) > room:
            break
        chains += chain

    code = code_prefix + chains + code_suffix
    benchmark_test(
        target_opcode=opcode,
        tx=Transaction(
            to=pre.deploy_contract(code=code), sender=pre.fund_eoa()
        ),
    )


@pytest.mark.repricing(mod_bits=191)
@pytest.mark.parametrize("mod_bits", [255, 191, 127, 63])
@pytest.mark.parametrize("opcode", [Op.ADDMOD, Op.MULMOD])
def test_mod_arithmetic(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    mod_bits: int,
    opcode: Op,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark ADDMOD and MULMOD instructions.

    The program consists of code segments evaluating the "op chain":
    mod[0] = calldataload(0)
    mod[1] = (fixed_arg op args[indexes[0]]) % mod[0]
    mod[2] = (fixed_arg op args[indexes[1]]) % mod[1]
    The "args" is a pool of 15 constants pushed to the EVM stack at the program
    start.
    The "fixed_arg" is the 0xFF...FF constant added to the EVM stack by PUSH32
    just before executing the "op".
    The order of accessing the numerators is selected in a way the mod value
    remains in the range as long as possible.
    """
    fixed_arg = 2**256 - 1
    num_args = 15

    max_code_size = fork.max_code_size()

    # Pick the modulus min value so that it is _unlikely_ to drop to the lower
    # word count.
    assert mod_bits >= 63
    mod_min = 2 ** (mod_bits - 63)

    # Select the random seed giving the longest found op chain. You can look
    # for a longer one by increasing the op_chain_len. This will activate the
    # while loop below.
    op_chain_len = 666
    match opcode, mod_bits:
        case Op.ADDMOD, 255:
            seed = 4
        case Op.ADDMOD, 191:
            seed = 2
        case Op.ADDMOD, 127:
            seed = 2
        case Op.ADDMOD, 63:
            seed = 64
        case Op.MULMOD, 255:
            seed = 5
        case Op.MULMOD, 191:
            seed = 389
        case Op.MULMOD, 127:
            seed = 5
        case Op.MULMOD, 63:
            # For this setup we were not able to find an op-chain longer than
            # 600.
            seed = 4193
            op_chain_len = 600
        case _:
            raise ValueError(f"{mod_bits}-bit {opcode} not supported.")

    while True:
        rng = random.Random(seed)
        args = [rng.randint(2**255, 2**256 - 1) for _ in range(num_args)]
        initial_mod = rng.randint(2 ** (mod_bits - 1), 2**mod_bits - 1)

        # Evaluate the op chain and collect the order of accessing numerators.
        op_fn = operator.add if opcode == Op.ADDMOD else operator.mul
        mod = initial_mod
        indexes: list[int] = []
        while mod >= mod_min and len(indexes) < op_chain_len:
            results = [op_fn(a, fixed_arg) % mod for a in args]
            # And pick the best one.
            i = max(range(len(results)), key=results.__getitem__)
            mod = results[i]
            indexes.append(i)

        # Disable if you want to find longer op chains.
        assert len(indexes) == op_chain_len
        if len(indexes) == op_chain_len:
            break
        seed += 1
        print(f"{seed=}")

    code_constant_pool = sum((Op.PUSH32[n] for n in args), Bytecode())
    code_segment = (
        Op.CALLDATALOAD(0)
        + sum(
            make_dup(len(args) - i) + Op.PUSH32[fixed_arg] + opcode
            for i in indexes
        )
        + Op.POP
    )

    code_prefix = code_constant_pool + Op.JUMPDEST
    code_suffix = Op.JUMP(len(code_constant_pool))
    overhead = len(code_prefix) + len(code_suffix)
    num_segments = (max_code_size - overhead) // len(code_segment)
    code = code_prefix + code_segment * num_segments + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_mod.to_bytes(32, byteorder="big"),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    benchmark_test(
        tx=tx,
    )


@pytest.mark.parametrize("base", [3, 5, 7, 11, 13, 136279841])
@pytest.mark.parametrize("exp", [3, 5, 7, 11, 13, 136279841])
def test_exp_bench_arithmetic(
    benchmark_test: BenchmarkTestFiller, base: int, exp: int
) -> None:
    """Benchmark EXP instruction."""
    tx_data = b"".join(
        arg.to_bytes(32, byteorder="big") for arg in (base, exp)
    )

    setup = Op.CALLDATALOAD(0) + Op.CALLDATALOAD(32) + Op.DUP2 + Op.DUP2
    attack_block = Op.DUP2 + Op.EXP
    cleanup = Op.POP + Op.POP + Op.DUP2 + Op.DUP2
    benchmark_test(
        target_opcode=Op.EXP,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
            tx_kwargs={"data": tx_data},
        ),
    )
