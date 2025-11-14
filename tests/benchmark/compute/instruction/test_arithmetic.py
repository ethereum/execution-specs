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

from tests.benchmark.compute.helpers import DEFAULT_BINOP_ARGS, make_dup, neg


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
            # Not suitable for MOD, as values quickly become zero.
            Op.MOD,
            DEFAULT_BINOP_ARGS,
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            # Not suitable for SMOD, as values quickly become zero.
            Op.SMOD,
            DEFAULT_BINOP_ARGS,
            marks=pytest.mark.repricing,
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
    opcode_args: tuple[int, int],
) -> None:
    """
    Benchmark binary instructions (takes two args, pushes one value).
    The execution starts with two initial values on the stack
    The stack is balanced by the DUP2 instruction.
    """
    tx_data = b"".join(
        arg.to_bytes(32, byteorder="big") for arg in opcode_args
    )

    setup = Op.CALLDATALOAD(0) + Op.CALLDATALOAD(32) + Op.DUP2 + Op.DUP2
    attack_block = Op.DUP2 + opcode
    cleanup = Op.POP + Op.POP + Op.DUP2 + Op.DUP2
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
            tx_kwargs={"data": tx_data},
        ),
    )


@pytest.mark.repricing(mod_bits=255)
@pytest.mark.parametrize("mod_bits", [255, 191, 127, 63])
@pytest.mark.parametrize("opcode", [Op.MOD, Op.SMOD])
def test_mod(
    benchmark_test: BenchmarkTestFiller,
    mod_bits: int,
    opcode: Op,
) -> None:
    """
    Benchmark MOD instructions.

    The program consists of code segments evaluating the "MOD chain":
    mod[0] = calldataload(0)
    mod[1] = numerators[indexes[0]] % mod[0]
    mod[2] = numerators[indexes[1]] % mod[1] ...

    The "numerators" is a pool of 15 constants pushed to the EVM stack at the
    program start.

    The order of accessing the numerators is selected in a way the mod value
    remains in the range as long as possible.
    """
    # For SMOD we negate both numerator and modulus. The underlying
    # computation is the same,
    # just the SMOD implementation will have to additionally handle the
    # sign bits.
    # The result stays negative.
    should_negate = opcode == Op.SMOD

    num_numerators = 15
    numerator_bits = 256 if not should_negate else 255
    numerator_max = 2**numerator_bits - 1
    numerator_min = 2 ** (numerator_bits - 1)

    # Pick the modulus min value so that it is _unlikely_ to drop to the lower
    # word count.
    assert mod_bits >= 63
    mod_min = 2 ** (mod_bits - 63)

    # Select the random seed giving the longest found MOD chain. You can look
    # for a longer one by increasing the numerators_min_len. This will activate
    # the while loop below.
    match opcode, mod_bits:
        case Op.MOD, 255:
            seed = 20393
            numerators_min_len = 750
        case Op.MOD, 191:
            seed = 25979
            numerators_min_len = 770
        case Op.MOD, 127:
            seed = 17671
            numerators_min_len = 750
        case Op.MOD, 63:
            seed = 29181
            numerators_min_len = 730
        case Op.SMOD, 255:
            seed = 4015
            numerators_min_len = 750
        case Op.SMOD, 191:
            seed = 17355
            numerators_min_len = 750
        case Op.SMOD, 127:
            seed = 897
            numerators_min_len = 750
        case Op.SMOD, 63:
            seed = 7562
            numerators_min_len = 720
        case _:
            raise ValueError(f"{mod_bits}-bit {opcode} not supported.")

    while True:
        rng = random.Random(seed)

        # Create the list of random numerators.
        numerators = [
            rng.randint(numerator_min, numerator_max)
            for _ in range(num_numerators)
        ]

        # Create the random initial modulus.
        initial_mod = rng.randint(2 ** (mod_bits - 1), 2**mod_bits - 1)

        # Evaluate the MOD chain and collect the order of accessing numerators.
        mod = initial_mod
        indexes = []
        while mod >= mod_min:
            # Compute results for each numerator.
            results = [n % mod for n in numerators]
            # And pick the best one.
            i = max(range(len(results)), key=results.__getitem__)
            mod = results[i]
            indexes.append(i)

        # Disable if you want to find longer MOD chains.
        assert len(indexes) > numerators_min_len
        if len(indexes) > numerators_min_len:
            break
        seed += 1
        print(f"{seed=}")

    # TODO: Don't use fixed PUSH32. Let Bytecode helpers to select optimal
    # push opcode.
    setup = sum((Op.PUSH32[n] for n in numerators), Bytecode())
    attack_block = (
        Op.CALLDATALOAD(0)
        + sum(make_dup(len(numerators) - i) + opcode for i in indexes)
        + Op.POP
    )

    input_value = initial_mod if not should_negate else neg(initial_mod)
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            tx_kwargs={"data": input_value.to_bytes(32, byteorder="big")},
        ),
    )


@pytest.mark.repricing(mod_bits=255)
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
    # Construct the final code. Because of the usage of PUSH32 the code segment
    # is very long, so don't try to include multiple of these.
    code = (
        code_constant_pool
        + Op.JUMPDEST
        + code_segment
        + Op.JUMP(len(code_constant_pool))
    )
    assert (max_code_size - len(code_segment)) < len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_mod.to_bytes(32, byteorder="big"),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)
