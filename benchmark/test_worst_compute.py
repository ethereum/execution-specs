"""
abstract: Tests that benchmark EVMs in worst-case compute scenarios.
    Tests that benchmark EVMs in worst-case compute scenarios.

Tests that benchmark EVMs when running worst-case compute opcodes and precompile scenarios.
"""

import math
import operator
import random
from enum import Enum, auto
from typing import cast

import pytest
from py_ecc.bn128 import G1, G2, multiply

from ethereum_test_base_types.base_types import Bytes
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    StateTestFiller,
    Transaction,
    add_kzg_version,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types import TransactionType
from ethereum_test_vm.opcode import Opcode

from ..byzantium.eip198_modexp_precompile.test_modexp import ModExpInput
from ..cancun.eip4844_blobs.spec import Spec as BlobsSpec
from ..istanbul.eip152_blake2.common import Blake2bInput
from ..istanbul.eip152_blake2.spec import Spec as Blake2bSpec
from ..osaka.eip7951_p256verify_precompiles import spec as p256verify_spec
from ..osaka.eip7951_p256verify_precompiles.spec import FieldElement
from ..prague.eip2537_bls_12_381_precompiles import spec as bls12381_spec
from ..prague.eip2537_bls_12_381_precompiles.spec import BytesConcatenation
from .helpers import code_loop_precompile_call

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"

KECCAK_RATE = 136


def neg(x: int) -> int:
    """Negate the given integer in the two's complement 256-bit range."""
    assert 0 <= x < 2**256
    return 2**256 - x


def make_dup(index: int) -> Opcode:
    """
    Create a DUP instruction which duplicates the index-th (counting from 0) element
    from the top of the stack. E.g. make_dup(0) → DUP1.
    """
    assert 0 <= index < 16
    return Opcode(0x80 + index, pushed_stack_items=1, min_stack_height=index + 1)


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [
        Op.ADDRESS,
        Op.ORIGIN,
        Op.CALLER,
        Op.CODESIZE,
        Op.GASPRICE,
        Op.COINBASE,
        Op.TIMESTAMP,
        Op.NUMBER,
        Op.PREVRANDAO,
        Op.GASLIMIT,
        Op.CHAINID,
        Op.BASEFEE,
        Op.BLOBBASEFEE,
        Op.GAS,
        # Note that other 0-param opcodes are covered in separate tests.
    ],
)
def test_worst_zero_param(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    fork: Fork,
):
    """Test running a block with as many zero-parameter opcodes as possible."""
    env = Environment()

    opcode_sequence = opcode * fork.max_stack_height()
    target_contract_address = pre.deploy_contract(code=opcode_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("calldata_length", [0, 1_000, 10_000])
def test_worst_calldatasize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    calldata_length: int,
):
    """Test running a block with as many CALLDATASIZE as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST
    iter_loop = Op.POP(Op.CALLDATASIZE)
    code_suffix = Op.PUSH0 + Op.JUMP
    code_iter_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(iter_loop)
    code = code_prefix + iter_loop * code_iter_len + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=bytes(code)),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
        data=b"\x00" * calldata_length,
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("non_zero_value", [True, False])
@pytest.mark.parametrize("from_origin", [True, False])
def test_worst_callvalue(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    non_zero_value: bool,
    from_origin: bool,
):
    """
    Test running a block with as many CALLVALUE opcodes as possible.

    The `non_zero_value` parameter controls whether opcode must return non-zero value.
    The `from_origin` parameter controls whether the call frame is the immediate from the
    transaction or a previous CALL.
    """
    env = Environment()
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST
    iter_loop = Op.POP(Op.CALLVALUE)
    code_suffix = Op.PUSH0 + Op.JUMP
    code_iter_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(iter_loop)
    code = code_prefix + iter_loop * code_iter_len + code_suffix
    assert len(code) <= max_code_size
    code_address = pre.deploy_contract(code=bytes(code))

    tx_to = (
        code_address
        if from_origin
        else pre.deploy_contract(
            code=Op.CALL(address=code_address, value=1 if non_zero_value else 0), balance=10
        )
    )

    tx = Transaction(
        to=tx_to,
        gas_limit=env.gas_limit,
        value=1 if non_zero_value and from_origin else 0,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


class ReturnDataStyle(Enum):
    """Helper enum to specify return data is returned to the caller."""

    RETURN = auto()
    REVERT = auto()
    IDENTITY = auto()


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "return_data_style",
    [
        ReturnDataStyle.RETURN,
        ReturnDataStyle.REVERT,
        ReturnDataStyle.IDENTITY,
    ],
)
@pytest.mark.parametrize("returned_size", [1, 0])
def test_worst_returndatasize_nonzero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    returned_size: int,
    return_data_style: ReturnDataStyle,
):
    """
    Test running a block which execute as many RETURNDATASIZE opcodes which return a non-zero
    buffer as possible.

    The `returned_size` parameter indicates the size of the returned data buffer.
    The `return_data_style` indicates how returned data is produced for the opcode caller.
    """
    env = Environment()
    max_code_size = fork.max_code_size()

    dummy_contract_call = Bytecode()
    if return_data_style != ReturnDataStyle.IDENTITY:
        dummy_contract_call = Op.STATICCALL(
            address=pre.deploy_contract(
                code=Op.REVERT(0, returned_size)
                if return_data_style == ReturnDataStyle.REVERT
                else Op.RETURN(0, returned_size)
            )
        )
    else:
        dummy_contract_call = Op.MSTORE8(0, 1) + Op.STATICCALL(
            address=0x04,  # Identity precompile
            args_size=returned_size,
        )

    code_prefix = dummy_contract_call + Op.JUMPDEST
    iter_loop = Op.POP(Op.RETURNDATASIZE)
    code_suffix = Op.JUMP(len(code_prefix) - 1)
    code_iter_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(iter_loop)
    code = code_prefix + iter_loop * code_iter_len + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=bytes(code)),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_returndatasize_zero(state_test: StateTestFiller, pre: Alloc, fork: Fork):
    """Test running a block with as many RETURNDATASIZE opcodes as possible with a zero buffer."""
    env = Environment()
    max_code_size = fork.max_code_size()

    dummy_contract_call = Bytecode()

    code_prefix = dummy_contract_call + Op.JUMPDEST
    iter_loop = Op.POP(Op.RETURNDATASIZE)
    code_suffix = Op.JUMP(len(code_prefix) - 1)
    code_iter_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(iter_loop)
    code = code_prefix + iter_loop * code_iter_len + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=bytes(code)),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("mem_size", [0, 1, 1_000, 100_000, 1_000_000])
def test_worst_msize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mem_size: int,
):
    """
    Test running a block with as many MSIZE opcodes as possible.

    The `mem_size` parameter indicates by how much the memory is expanded.
    """
    env = Environment()
    max_stack_height = fork.max_stack_height()

    code_sequence = Op.MLOAD(Op.CALLVALUE) + Op.POP + Op.MSIZE * max_stack_height
    target_address = pre.deploy_contract(code=code_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_address, 0, 0, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block, fork)
    assert len(code) <= fork.max_code_size()

    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
        value=mem_size,
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_keccak(
    state_test: StateTestFiller,
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

    max_code_size = fork.max_code_size()

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
        # From the available gas, we subtract the mem expansion costs considering we know the
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
    #   Numerator = max_code_size-3. The -3 is for the JUMPDEST, PUSH0 and JUMP.
    #   Denominator = (PUSHN + PUSH1 + KECCAK256 + POP) + PUSH1_DATA + PUSHN_DATA
    # TODO: the testing framework uses PUSH1(0) instead of PUSH0 which is suboptimal for the
    # attack, whenever this is fixed adjust accordingly.
    start_code = Op.JUMPDEST + Op.PUSH20[optimal_input_length]
    loop_code = Op.POP(Op.SHA3(Op.PUSH0, Op.DUP1))
    end_code = Op.POP + Op.JUMP(Op.PUSH0)
    max_iters_loop = (max_code_size - (len(start_code) + len(end_code))) // len(loop_code)
    code = start_code + (loop_code * max_iters_loop) + end_code
    if len(code) > max_code_size:
        # Must never happen, but keep it as a sanity check.
        raise ValueError(f"Code size {len(code)} exceeds maximum code size {max_code_size}")

    code_address = pre.deploy_contract(code=bytes(code))

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
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
    state_test: StateTestFiller,
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
        # From the available gas, we subtract the mem expansion costs considering we know the
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
    code = code_loop_precompile_call(calldata, attack_block, fork)

    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    ["mod_exp_input"],
    [
        pytest.param(
            ModExpInput(
                base=8 * "ff",
                exponent=112 * "ff",
                modulus=7 * "ff" + "00",
            ),
            id="mod_even_8b_exp_896",
        ),
        pytest.param(
            ModExpInput(
                base=16 * "ff",
                exponent=40 * "ff",
                modulus=15 * "ff" + "00",
            ),
            id="mod_even_16b_exp_320",
        ),
        pytest.param(
            ModExpInput(
                base=24 * "ff",
                exponent=21 * "ff",
                modulus=23 * "ff" + "00",
            ),
            id="mod_even_24b_exp_168",
        ),
        pytest.param(
            ModExpInput(
                base=32 * "ff",
                exponent=5 * "ff",
                modulus=31 * "ff" + "00",
            ),
            id="mod_even_32b_exp_40",
        ),
        pytest.param(
            ModExpInput(
                base=32 * "ff",
                exponent=12 * "ff",
                modulus=31 * "ff" + "00",
            ),
            id="mod_even_32b_exp_96",
        ),
        pytest.param(
            ModExpInput(
                base=32 * "ff",
                exponent=32 * "ff",
                modulus=31 * "ff" + "00",
            ),
            id="mod_even_32b_exp_256",
        ),
        pytest.param(
            ModExpInput(
                base=32 * "ff",
                exponent=12 * "ff",
                modulus=31 * "ff" + "01",
            ),
            id="mod_odd_32b_exp_96",
        ),
        pytest.param(
            ModExpInput(
                base=32 * "ff",
                exponent=32 * "ff",
                modulus=31 * "ff" + "01",
            ),
            id="mod_odd_32b_exp_256",
        ),
        pytest.param(
            ModExpInput(
                base=32 * "ff",
                exponent=8 * "12345670",
                modulus=31 * "ff" + "01",
            ),
            id="mod_odd_32b_exp_cover_windows",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L38
        pytest.param(
            ModExpInput(
                base=192 * "FF",
                exponent="03",
                modulus=6 * ("00" + 31 * "FF"),
            ),
            id="mod_min_as_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L40
        pytest.param(
            ModExpInput(
                base=8 * "FF",
                exponent="07" + 75 * "FF",
                modulus=7 * "FF",
            ),
            id="mod_min_as_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L42
        pytest.param(
            ModExpInput(
                base=40 * "FF",
                exponent="01" + 3 * "FF",
                modulus="00" + 38 * "FF",
            ),
            id="mod_min_as_balanced",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L44
        pytest.param(
            ModExpInput(
                base=32 * "FF",
                exponent=5 * "FF",
                modulus=("00" + 31 * "FF"),
            ),
            id="mod_exp_208_gas_balanced",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L46
        pytest.param(
            ModExpInput(
                base=8 * "FF",
                exponent=81 * "FF",
                modulus=7 * "FF",
            ),
            id="mod_exp_215_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L48
        pytest.param(
            ModExpInput(
                base=8 * "FF",
                exponent=112 * "FF",
                modulus=7 * "FF",
            ),
            id="mod_exp_298_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L50
        pytest.param(
            ModExpInput(
                base=16 * "FF",
                exponent=40 * "FF",
                modulus=15 * "FF",
            ),
            id="mod_pawel_2",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L52
        pytest.param(
            ModExpInput(
                base=24 * "FF",
                exponent=21 * "FF",
                modulus=23 * "FF",
            ),
            id="mod_pawel_3",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L54
        pytest.param(
            ModExpInput(
                base=32 * "FF",
                exponent=12 * "FF",
                modulus="00" + 31 * "FF",
            ),
            id="mod_pawel_4",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L56
        pytest.param(
            ModExpInput(
                base=280 * "FF",
                exponent="03",
                modulus=8 * ("00" + 31 * "FF") + 23 * "FF",
            ),
            id="mod_408_gas_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L58
        pytest.param(
            ModExpInput(
                base=16 * "FF",
                exponent="15" + 37 * "FF",
                modulus=15 * "FF",
            ),
            id="mod_400_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L60
        pytest.param(
            ModExpInput(
                base=48 * "FF",
                exponent="07" + 4 * "FF",
                modulus="00" + 46 * "FF",
            ),
            id="mod_408_gas_balanced",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L62
        pytest.param(
            ModExpInput(
                base=344 * "FF",
                exponent="03",
                modulus=10 * ("00" + 31 * "FF") + 23 * "FF",
            ),
            id="mod_616_gas_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L64
        pytest.param(
            ModExpInput(
                base=16 * "FF",
                exponent="07" + 56 * "FF",
                modulus=15 * "FF",
            ),
            id="mod_600_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L66
        pytest.param(
            ModExpInput(
                base=48 * "FF",
                exponent="07" + 6 * "FF",
                modulus="00" + 46 * "FF",
            ),
            id="mod_600_as_balanced",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L68
        pytest.param(
            ModExpInput(
                base=392 * "FF",
                exponent="03",
                modulus=12 * ("00" + 31 * "FF") + 7 * "FF",
            ),
            id="mod_800_gas_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L70
        pytest.param(
            ModExpInput(
                base=16 * "FF",
                exponent="01" + 75 * "FF",
                modulus=15 * "FF",
            ),
            id="mod_800_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L72
        pytest.param(
            ModExpInput(
                base=56 * "FF",
                exponent=6 * "FF",
                modulus="00" + 54 * "FF",
            ),
            id="mod_767_gas_balanced",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L74
        pytest.param(
            ModExpInput(
                base=16 * "FF",
                exponent=80 * "FF",
                modulus=15 * "FF",
            ),
            id="mod_852_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L76
        pytest.param(
            ModExpInput(
                base=408 * "FF",
                exponent="03",
                modulus=12 * ("00" + 31 * "FF") + 23 * "FF",
            ),
            id="mod_867_gas_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L78
        pytest.param(
            ModExpInput(
                base=56 * "FF",
                exponent="2b" + 7 * "FF",
                modulus="00" + 54 * "FF",
            ),
            id="mod_996_gas_balanced",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L80
        pytest.param(
            ModExpInput(
                base=448 * "FF",
                exponent="03",
                modulus=14 * ("00" + 31 * "FF"),
            ),
            id="mod_1045_gas_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L82
        pytest.param(
            ModExpInput(
                base=32 * "FF",
                exponent=16 * "FF",
                modulus="00" + 31 * "FF",
            ),
            id="mod_677_gas_base_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L84
        pytest.param(
            ModExpInput(
                base=24 * "FF",
                exponent=32 * "FF",
                modulus=23 * "FF",
            ),
            id="mod_765_gas_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/Modexp.cs#L86
        pytest.param(
            ModExpInput(
                base=32 * "FF",
                exponent=32 * "FF",
                modulus="00" + 31 * "FF",
            ),
            id="mod_1360_gas_balanced",
        ),
    ],
)
def test_worst_modexp(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mod_exp_input: ModExpInput,
):
    """
    Test running a block with as many calls to the MODEXP (5) precompile as possible.
    All the calls have the same parametrized input.
    """
    # Skip the trailing zeros from the input to make EVM work even harder.
    calldata = bytes(mod_exp_input).rstrip(b"\x00")

    code = code_loop_precompile_call(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),  # Copy the input to the memory.
        Op.POP(Op.STATICCALL(Op.GAS, 0x5, Op.PUSH0, Op.CALLDATASIZE, Op.PUSH0, Op.PUSH0)),
        fork,
    )

    env = Environment()

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
        input=calldata,
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "precompile_address,parameters",
    [
        pytest.param(
            0x01,
            [
                # The inputs below are a valid signature, thus ECRECOVER call won't
                # be short-circuited by validations and do actual work.
                "38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E",
                "000000000000000000000000000000000000000000000000000000000000001B",
                "38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E",
                "789D1DD423D25F0772D2748D60F7E4B81BB14D086EBA8E8E8EFB6DCFF8A4AE02",
            ],
            id="ecrecover",
        ),
        pytest.param(
            0x06,
            [
                "18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9",
                "063C909C4720840CB5134CB9F59FA749755796819658D32EFC0D288198F37266",
                "07C2B7F58A84BD6145F00C9C2BC0BB1A187F20FF2C92963A88019E7C6A014EED",
                "06614E20C147E940F2D70DA3F74C9A17DF361706A4485C742BD6788478FA17D7",
            ],
            id="bn128_add",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L326
        pytest.param(
            0x06,
            [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
            ],
            id="bn128_add_infinities",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L329
        pytest.param(
            0x06,
            [
                "0000000000000000000000000000000000000000000000000000000000000001",
                "0000000000000000000000000000000000000000000000000000000000000002",
                "0000000000000000000000000000000000000000000000000000000000000001",
                "0000000000000000000000000000000000000000000000000000000000000002",
            ],
            id="bn128_add_1_2",
        ),
        pytest.param(
            0x07,
            [
                "1A87B0584CE92F4593D161480614F2989035225609F08058CCFA3D0F940FEBE3",
                "1A2F3C951F6DADCC7EE9007DFF81504B0FCD6D7CF59996EFDC33D92BF7F9F8F6",
                "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
            ],
            id="bn128_mul",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L335
        pytest.param(
            0x07,
            [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000002",
            ],
            id="bn128_mul_infinities_2_scalar",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L338
        pytest.param(
            0x07,
            [
                "0000000000000000000000000000000000000000000000000000000000000000",
                "0000000000000000000000000000000000000000000000000000000000000000",
                "25f8c89ea3437f44f8fc8b6bfbb6312074dc6f983809a5e809ff4e1d076dd585",
            ],
            id="bn128_mul_infinities_32_byte_scalar",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L341
        pytest.param(
            0x07,
            [
                "0000000000000000000000000000000000000000000000000000000000000001",
                "0000000000000000000000000000000000000000000000000000000000000002",
                "0000000000000000000000000000000000000000000000000000000000000002",
            ],
            id="bn128_mul_1_2_2_scalar",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L344
        pytest.param(
            0x07,
            [
                "0000000000000000000000000000000000000000000000000000000000000001",
                "0000000000000000000000000000000000000000000000000000000000000002",
                "25f8c89ea3437f44f8fc8b6bfbb6312074dc6f983809a5e809ff4e1d076dd585",
            ],
            id="bn128_mul_1_2_32_byte_scalar",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L347
        pytest.param(
            0x07,
            [
                "089142debb13c461f61523586a60732d8b69c5b38a3380a74da7b2961d867dbf",
                "2d5fc7bbc013c16d7945f190b232eacc25da675c0eb093fe6b9f1b4b4e107b36",
                "0000000000000000000000000000000000000000000000000000000000000002",
            ],
            id="bn128_mul_32_byte_coord_and_2_scalar",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L350
        pytest.param(
            0x07,
            [
                "089142debb13c461f61523586a60732d8b69c5b38a3380a74da7b2961d867dbf",
                "2d5fc7bbc013c16d7945f190b232eacc25da675c0eb093fe6b9f1b4b4e107b36",
                "25f8c89ea3437f44f8fc8b6bfbb6312074dc6f983809a5e809ff4e1d076dd585",
            ],
            id="bn128_mul_32_byte_coord_and_scalar",
        ),
        pytest.param(
            0x08,
            [
                # First pairing
                "1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59",
                "3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41",
                "209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7",
                "04BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678",
                "2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D",
                "120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550",
                # Second pairing
                "111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C",
                "103188585E2364128FE25C70558F1560F4F9350BAF3959E603CC91486E110936",
                "198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2",
                "1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED",
                "090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B",
                "12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA",
            ],
            id="bn128_two_pairings",
        ),
        pytest.param(
            0x08,
            [
                # First pairing
                "1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59",
                "3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41",
                "209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7",
                "04BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678",
                "2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D",
                "120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550",
            ],
            id="bn128_one_pairing",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L353
        pytest.param(0x08, [""], id="bn128_two_pairings_empty"),
        pytest.param(
            Blake2bSpec.BLAKE2_PRECOMPILE_ADDRESS,
            [
                Blake2bInput(rounds=0xFFFF, f=True).create_blake2b_tx_data(),
            ],
            id="blake2f",
        ),
        pytest.param(
            BlobsSpec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            [
                "01E798154708FE7789429634053CBF9F99B619F9F084048927333FCE637F549B",
                "564C0A11A0F704F4FC3E8ACFE0F8245F0AD1347B378FBF96E206DA11A5D36306",
                "24D25032E67A7E6A4910DF5834B8FE70E6BCFEEAC0352434196BDF4B2485D5A1",
                "8F59A8D2A1A625A17F3FEA0FE5EB8C896DB3764F3185481BC22F91B4AAFFCCA25F26936857BC3A7C2539EA8EC3A952B7",
                "873033E038326E87ED3E1276FD140253FA08E9FC25FB2D9A98527FC22A2C9612FBEAFDAD446CBC7BCDBDCD780AF2C16A",
            ],
            id="point_evaluation",
        ),
        pytest.param(
            bls12381_spec.Spec.G1ADD,
            [
                bls12381_spec.Spec.G1,
                bls12381_spec.Spec.P1,
            ],
            id="bls12_g1add",
        ),
        pytest.param(
            bls12381_spec.Spec.G1MSM,
            [
                (bls12381_spec.Spec.P1 + bls12381_spec.Scalar(bls12381_spec.Spec.Q))
                * (len(bls12381_spec.Spec.G1MSM_DISCOUNT_TABLE) - 1),
            ],
            id="bls12_g1msm",
        ),
        pytest.param(
            bls12381_spec.Spec.G2ADD,
            [
                bls12381_spec.Spec.G2,
                bls12381_spec.Spec.P2,
            ],
            id="bls12_g2add",
        ),
        pytest.param(
            bls12381_spec.Spec.G2MSM,
            [
                # TODO: the //2 is required due to a limitation of the max contract size limit.
                # In a further iteration we can insert the inputs as calldata or storage and avoid
                # having to do PUSHes which has this limitation. This also applies to G1MSM.
                (bls12381_spec.Spec.P2 + bls12381_spec.Scalar(bls12381_spec.Spec.Q))
                * (len(bls12381_spec.Spec.G2MSM_DISCOUNT_TABLE) // 2),
            ],
            id="bls12_g2msm",
        ),
        pytest.param(
            bls12381_spec.Spec.PAIRING,
            [
                bls12381_spec.Spec.G1,
                bls12381_spec.Spec.G2,
            ],
            id="bls12_pairing_check",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP_TO_G1,
            [
                bls12381_spec.FP(bls12381_spec.Spec.P - 1),
            ],
            id="bls12_fp_to_g1",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP2_TO_G2,
            [
                bls12381_spec.FP2((bls12381_spec.Spec.P - 1, bls12381_spec.Spec.P - 1)),
            ],
            id="bls12_fp_to_g2",
        ),
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            [
                p256verify_spec.Spec.H0,
                p256verify_spec.Spec.R0,
                p256verify_spec.Spec.S0,
                p256verify_spec.Spec.X0,
                p256verify_spec.Spec.Y0,
            ],
            id="p256verify",
        ),
    ],
)
def test_worst_precompile_fixed_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile_address: Address,
    parameters: list[str] | list[BytesConcatenation] | list[bytes],
):
    """Test running a block filled with a precompile with fixed cost."""
    env = Environment()

    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    concatenated_bytes: bytes
    if all(isinstance(p, str) for p in parameters):
        parameters_str = cast(list[str], parameters)
        concatenated_hex_string = "".join(parameters_str)
        concatenated_bytes = bytes.fromhex(concatenated_hex_string)
    elif all(isinstance(p, (bytes, BytesConcatenation, FieldElement)) for p in parameters):
        parameters_bytes_list = [
            bytes(p) for p in cast(list[BytesConcatenation | bytes | FieldElement], parameters)
        ]
        concatenated_bytes = b"".join(parameters_bytes_list)
    else:
        raise TypeError(
            "parameters must be a list of strings (hex) "
            "or a list of byte-like objects (bytes, BytesConcatenation or FieldElement)."
        )

    padding_length = (32 - (len(concatenated_bytes) % 32)) % 32
    input_bytes = concatenated_bytes + b"\x00" * padding_length

    calldata = Bytecode()
    for i in range(0, len(input_bytes), 32):
        chunk = input_bytes[i : i + 32]
        value_to_store = int.from_bytes(chunk, "big")
        calldata += Op.MSTORE(i, value_to_store)

    attack_block = Op.POP(
        Op.STATICCALL(Op.GAS, precompile_address, 0, len(concatenated_bytes), 0, 0)
    )
    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=bytes(code))

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_jumps(state_test: StateTestFiller, pre: Alloc):
    """Test running a JUMP-intensive contract."""
    env = Environment()

    jumps_code = Op.JUMPDEST + Op.JUMP(Op.PUSH0)
    jumps_address = pre.deploy_contract(jumps_code)

    tx = Transaction(
        to=jumps_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        genesis_environment=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_jumpi_fallthrough(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a JUMPI-intensive contract with fallthrough."""
    env = Environment()
    max_code_size = fork.max_code_size()

    def jumpi_seq():
        return Op.JUMPI(Op.PUSH0, Op.PUSH0)

    prefix_seq = Op.JUMPDEST
    suffix_seq = Op.JUMP(Op.PUSH0)
    bytes_per_seq = len(jumpi_seq())
    seqs_per_call = (max_code_size - len(prefix_seq) - len(suffix_seq)) // bytes_per_seq

    # Create and deploy the jumpi-intensive contract
    jumpis_code = prefix_seq + jumpi_seq() * seqs_per_call + suffix_seq
    assert len(jumpis_code) <= max_code_size

    jumpis_address = pre.deploy_contract(code=bytes(jumpis_code))

    tx = Transaction(
        to=jumpis_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_jumpis(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """Test running a JUMPI-intensive contract."""
    env = Environment()

    jumpi_code = Op.JUMPDEST + Op.JUMPI(Op.PUSH0, Op.NUMBER)
    jumpi_address = pre.deploy_contract(jumpi_code)

    tx = Transaction(
        to=jumpi_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_jumpdests(state_test: StateTestFiller, pre: Alloc, fork: Fork):
    """Test running a JUMPDEST-intensive contract."""
    env = Environment()
    max_code_size = fork.max_code_size()

    # Create and deploy a contract with many JUMPDESTs
    code_suffix = Op.JUMP(Op.PUSH0)
    code_body = Op.JUMPDEST * (max_code_size - len(code_suffix))
    code = code_body + code_suffix
    jumpdests_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=jumpdests_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        genesis_environment=env,
        pre=pre,
        post={},
        tx=tx,
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
                # this is the worst case for the division algorithm with optimized paths
                # for division by 1 and 2 words.
                0x100000000000000000000000000000033,
            ),
        ),
        (
            # This has the cycle of 2, see above.
            Op.DIV,
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                # We want the first divisor to be slightly bigger than 2**64:
                # this is the worst case for the division algorithm with an optimized path
                # for division by 1 word.
                0x10000000000000033,
            ),
        ),
        (
            # Same as DIV-0, but the numerator made positive, and the divisor made negative.
            Op.SDIV,
            (
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFCD,
            ),
        ),
        (
            # Same as DIV-1, but the numerator made positive, and the divisor made negative.
            Op.SDIV,
            (
                0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFCD,
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
    state_test: StateTestFiller, pre: Alloc, opcode: Op, fork: Fork, opcode_args: tuple[int, int]
):
    """
    Test running a block with as many binary instructions (takes two args, produces one value)
    as possible. The execution starts with two initial values on the stack, and the stack is
    balanced by the DUP2 instruction.
    """
    env = Environment()
    max_code_size = fork.max_code_size()

    tx_data = b"".join(arg.to_bytes(32, byteorder="big") for arg in opcode_args)

    code_prefix = Op.JUMPDEST + Op.CALLDATALOAD(0) + Op.CALLDATALOAD(32)
    code_suffix = Op.POP + Op.POP + Op.PUSH0 + Op.JUMP
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)
    code_body = (Op.DUP2 + opcode) * (code_body_len // 2)
    code = code_prefix + code_body + code_suffix
    assert len(code) == max_code_size - 1

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=tx_data,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.ISZERO, Op.NOT])
def test_worst_unop(state_test: StateTestFiller, pre: Alloc, opcode: Op, fork: Fork):
    """
    Test running a block with as many unary instructions (takes one arg, produces one value)
    as possible.
    """
    env = Environment()
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST + Op.PUSH0  # Start with the arg 0.
    code_suffix = Op.POP + Op.PUSH0 + Op.JUMP
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)
    code_body = opcode * code_body_len
    code = code_prefix + code_body + code_suffix
    assert len(code) == max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
# `key_mut` indicates the key isn't fixed.
@pytest.mark.parametrize("key_mut", [True, False])
# `val_mut` indicates that at the end of each big-loop, the value of the target key changes.
@pytest.mark.parametrize("val_mut", [True, False])
def test_worst_tload(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    key_mut: bool,
    val_mut: bool,
):
    """Test running a block with as many TLOAD calls as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    start_key = 41
    code_key_mut = Bytecode()
    code_val_mut = Bytecode()
    if key_mut and val_mut:
        code_prefix = Op.PUSH1(start_key) + Op.JUMPDEST
        loop_iter = Op.POP(Op.TLOAD(Op.DUP1))
        code_key_mut = Op.POP + Op.GAS
        code_val_mut = Op.TSTORE(Op.DUP2, Op.GAS)
    if key_mut and not val_mut:
        code_prefix = Op.JUMPDEST
        loop_iter = Op.POP(Op.TLOAD(Op.GAS))
    if not key_mut and val_mut:
        code_prefix = Op.JUMPDEST
        loop_iter = Op.POP(Op.TLOAD(Op.CALLVALUE))
        code_val_mut = Op.TSTORE(Op.CALLVALUE, Op.GAS)  # CALLVALUE configured in the tx
    if not key_mut and not val_mut:
        code_prefix = Op.JUMPDEST
        loop_iter = Op.POP(Op.TLOAD(Op.CALLVALUE))

    code_suffix = code_key_mut + code_val_mut + Op.JUMP(len(code_prefix) - 1)

    code_body_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(loop_iter)
    code_body = loop_iter * code_body_len
    code = code_prefix + code_body + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
        value=start_key if not key_mut and val_mut else 0,
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("key_mut", [True, False])
@pytest.mark.parametrize("dense_val_mut", [True, False])
def test_worst_tstore(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    key_mut: bool,
    dense_val_mut: bool,
):
    """Test running a block with as many TSTORE calls as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    init_key = 42
    code_prefix = Op.PUSH1(init_key) + Op.JUMPDEST

    # If `key_mut` is True, we mutate the key on every iteration of the big loop.
    code_key_mut = Op.POP + Op.GAS if key_mut else Bytecode()
    code_suffix = code_key_mut + Op.JUMP(len(code_prefix) - 1)

    # If `dense_val_mut` is set, we use GAS as a cheap way of always storing a different value than
    # the previous one.
    loop_iter = Op.TSTORE(Op.DUP2, Op.GAS if dense_val_mut else Op.DUP1)

    code_body_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(loop_iter)
    code_body = loop_iter * code_body_len
    code = code_prefix + code_body + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("shift_right", [Op.SHR, Op.SAR])
def test_worst_shifts(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    shift_right: Op,
):
    """
    Test running a block with as many shift instructions with non-trivial arguments.
    This test generates left-right pairs of shifts to avoid zeroing the argument.
    The shift amounts are randomly pre-selected from the constant pool of 15 values on the stack.
    """
    max_code_size = fork.max_code_size()

    def to_signed(x):
        return x if x < 2**255 else x - 2**256

    def to_unsigned(x):
        return x if x >= 0 else x + 2**256

    def shr(x, s):
        return x >> s

    def shl(x, s):
        return x << s

    def sar(x, s):
        return to_unsigned(to_signed(x) >> s)

    match shift_right:
        case Op.SHR:
            shift_right_fn = shr
        case Op.SAR:
            shift_right_fn = sar
        case _:
            raise ValueError(f"Unexpected shift op: {shift_right}")

    rng = random.Random(1)  # Use random with a fixed seed.
    initial_value = 2**256 - 1  # The initial value to be shifted; should be negative for SAR.

    # Create the list of shift amounts with 15 elements (max reachable by DUPs instructions).
    # For the worst case keep the values small and omit values divisible by 8.
    shift_amounts = [x + (x >= 8) + (x >= 15) for x in range(1, 16)]

    code_prefix = sum(Op.PUSH1[sh] for sh in shift_amounts) + Op.JUMPDEST + Op.CALLDATALOAD(0)
    code_suffix = Op.POP + Op.JUMP(len(shift_amounts) * 2)
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)

    def select_shift_amount(shift_fn, v):
        """Select a shift amount that will produce a non-zero result."""
        while True:
            index = rng.randint(0, len(shift_amounts) - 1)
            sh = shift_amounts[index]
            new_v = shift_fn(v, sh) % 2**256
            if new_v != 0:
                return new_v, index

    code_body = Bytecode()
    v = initial_value
    while len(code_body) <= code_body_len - 4:
        v, i = select_shift_amount(shl, v)
        code_body += make_dup(len(shift_amounts) - i) + Op.SHL
        v, i = select_shift_amount(shift_right_fn, v)
        code_body += make_dup(len(shift_amounts) - i) + shift_right

    code = code_prefix + code_body + code_suffix
    assert len(code) == max_code_size - 2

    env = Environment()

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_value.to_bytes(32, byteorder="big"),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "blob_index, blobs_present",
    [
        pytest.param(0, 0, id="no blobs"),
        pytest.param(0, 1, id="one blob and accessed"),
        pytest.param(1, 1, id="one blob but access non-existent index"),
        pytest.param(5, 6, id="six blobs, access latest"),
    ],
)
def test_worst_blobhash(
    fork: Fork,
    state_test: StateTestFiller,
    pre: Alloc,
    blob_index: int,
    blobs_present: bool,
):
    """Test running a block with as many BLOBHASH instructions as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()
    max_stack_height = fork.max_stack_height()

    # Contract that contains a collection of BLOBHASH instructions.
    opcode_sequence = Op.BLOBHASH(blob_index) * max_stack_height
    assert len(opcode_sequence) <= max_code_size

    target_contract_address = pre.deploy_contract(code=opcode_sequence)

    # Contract that contains a loop of STATICCALLs to the target contract.
    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block, fork)
    assert len(code) <= max_code_size

    code_address = pre.deploy_contract(code=code)

    # Create blob transaction if blobs are present.
    tx_type = TransactionType.LEGACY
    blob_versioned_hashes = None
    max_fee_per_blob_gas = None
    if blobs_present > 0:
        tx_type = TransactionType.BLOB_TRANSACTION
        max_fee_per_blob_gas = fork.min_base_fee_per_blob_gas()
        blob_versioned_hashes = add_kzg_version(
            [i.to_bytes() * 32 for i in range(blobs_present)],
            BlobsSpec.BLOB_COMMITMENT_VERSION_KZG,
        )

    tx = Transaction(
        ty=tx_type,
        to=code_address,
        gas_limit=env.gas_limit,
        max_fee_per_blob_gas=max_fee_per_blob_gas,
        blob_versioned_hashes=blob_versioned_hashes,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("mod_bits", [255, 191, 127, 63])
@pytest.mark.parametrize("op", [Op.MOD, Op.SMOD])
def test_worst_mod(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mod_bits: int,
    op: Op,
):
    """
    Test running a block with as many MOD instructions with arguments of the parametrized range.
    The test program consists of code segments evaluating the "MOD chain":
    mod[0] = calldataload(0)
    mod[1] = numerators[indexes[0]] % mod[0]
    mod[2] = numerators[indexes[1]] % mod[1] ...
    The "numerators" is a pool of 15 constants pushed to the EVM stack at the program start.
    The order of accessing the numerators is selected in a way the mod value remains in the range
    as long as possible.
    """
    max_code_size = fork.max_code_size()

    # For SMOD we negate both numerator and modulus. The underlying computation is the same,
    # just the SMOD implementation will have to additionally handle the sign bits.
    # The result stays negative.
    should_negate = op == Op.SMOD

    num_numerators = 15
    numerator_bits = 256 if not should_negate else 255
    numerator_max = 2**numerator_bits - 1
    numerator_min = 2 ** (numerator_bits - 1)

    # Pick the modulus min value so that it is _unlikely_ to drop to the lower word count.
    assert mod_bits >= 63
    mod_min = 2 ** (mod_bits - 63)

    # Select the random seed giving the longest found MOD chain.
    # You can look for a longer one by increasing the numerators_min_len. This will activate
    # the while loop below.
    match op, mod_bits:
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
            raise ValueError(f"{mod_bits}-bit {op} not supported.")

    while True:
        rng = random.Random(seed)

        # Create the list of random numerators.
        numerators = [rng.randint(numerator_min, numerator_max) for _ in range(num_numerators)]

        # Create the random initial modulus.
        initial_mod = rng.randint(2 ** (mod_bits - 1), 2**mod_bits - 1)

        # Evaluate the MOD chain and collect the order of accessing numerators.
        mod = initial_mod
        indexes = []
        while mod >= mod_min:
            results = [n % mod for n in numerators]  # Compute results for each numerator.
            i = max(range(len(results)), key=results.__getitem__)  # And pick the best one.
            mod = results[i]
            indexes.append(i)

        assert len(indexes) > numerators_min_len  # Disable if you want to find longer MOD chains.
        if len(indexes) > numerators_min_len:
            break
        seed += 1
        print(f"{seed=}")

    # TODO: Don't use fixed PUSH32. Let Bytecode helpers to select optimal push opcode.
    code_constant_pool = sum((Op.PUSH32[n] for n in numerators), Bytecode())
    code_prefix = code_constant_pool + Op.JUMPDEST
    code_suffix = Op.JUMP(len(code_constant_pool))
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)
    code_segment = (
        Op.CALLDATALOAD(0) + sum(make_dup(len(numerators) - i) + op for i in indexes) + Op.POP
    )
    code = (
        code_prefix
        # TODO: Add int * Bytecode support
        + sum(code_segment for _ in range(code_body_len // len(code_segment)))
        + code_suffix
    )
    assert (max_code_size - len(code_segment)) < len(code) <= max_code_size

    env = Environment()

    input_value = initial_mod if not should_negate else neg(initial_mod)
    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=input_value.to_bytes(32, byteorder="big"),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.MLOAD, Op.MSTORE, Op.MSTORE8])
@pytest.mark.parametrize("offset", [0, 1, 31])
@pytest.mark.parametrize("offset_initialized", [True, False])
@pytest.mark.parametrize("big_memory_expansion", [True, False])
def test_worst_memory_access(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    offset: int,
    offset_initialized: bool,
    big_memory_expansion: bool,
):
    """Test running a block with as many memory access instructions as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    mem_exp_code = Op.MSTORE8(10 * 1024, 1) if big_memory_expansion else Bytecode()
    offset_set_code = Op.MSTORE(offset, 43) if offset_initialized else Bytecode()
    code_prefix = mem_exp_code + offset_set_code + Op.PUSH1(42) + Op.PUSH1(offset) + Op.JUMPDEST

    code_suffix = Op.JUMP(len(code_prefix) - 1)

    loop_iter = Op.POP(Op.MLOAD(Op.DUP1)) if opcode == Op.MLOAD else opcode(Op.DUP2, Op.DUP2)

    code_body_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(loop_iter)
    code_body = loop_iter * code_body_len
    code = code_prefix + code_body + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("mod_bits", [255, 191, 127, 63])
@pytest.mark.parametrize("op", [Op.ADDMOD, Op.MULMOD])
def test_worst_modarith(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mod_bits: int,
    op: Op,
):
    """
    Test running a block with as many "op" instructions with arguments of the parametrized range.
    The test program consists of code segments evaluating the "op chain":
    mod[0] = calldataload(0)
    mod[1] = (fixed_arg op args[indexes[0]]) % mod[0]
    mod[2] = (fixed_arg op args[indexes[1]]) % mod[1]
    The "args" is a pool of 15 constants pushed to the EVM stack at the program start.
    The "fixed_arg" is the 0xFF...FF constant added to the EVM stack by PUSH32
    just before executing the "op".
    The order of accessing the numerators is selected in a way the mod value remains in the range
    as long as possible.
    """
    fixed_arg = 2**256 - 1
    num_args = 15

    max_code_size = fork.max_code_size()

    # Pick the modulus min value so that it is _unlikely_ to drop to the lower word count.
    assert mod_bits >= 63
    mod_min = 2 ** (mod_bits - 63)

    # Select the random seed giving the longest found op chain.
    # You can look for a longer one by increasing the op_chain_len. This will activate
    # the while loop below.
    op_chain_len = 666
    match op, mod_bits:
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
            # For this setup we were not able to find an op-chain longer than 600.
            seed = 4193
            op_chain_len = 600
        case _:
            raise ValueError(f"{mod_bits}-bit {op} not supported.")

    while True:
        rng = random.Random(seed)
        args = [rng.randint(2**255, 2**256 - 1) for _ in range(num_args)]
        initial_mod = rng.randint(2 ** (mod_bits - 1), 2**mod_bits - 1)

        # Evaluate the op chain and collect the order of accessing numerators.
        op_fn = operator.add if op == Op.ADDMOD else operator.mul
        mod = initial_mod
        indexes: list[int] = []
        while mod >= mod_min and len(indexes) < op_chain_len:
            results = [op_fn(a, fixed_arg) % mod for a in args]
            i = max(range(len(results)), key=results.__getitem__)  # And pick the best one.
            mod = results[i]
            indexes.append(i)

        assert len(indexes) == op_chain_len  # Disable if you want to find longer op chains.
        if len(indexes) == op_chain_len:
            break
        seed += 1
        print(f"{seed=}")

    code_constant_pool = sum((Op.PUSH32[n] for n in args), Bytecode())
    code_segment = (
        Op.CALLDATALOAD(0)
        + sum(make_dup(len(args) - i) + Op.PUSH32[fixed_arg] + op for i in indexes)
        + Op.POP
    )
    # Construct the final code. Because of the usage of PUSH32 the code segment is very long,
    # so don't try to include multiple of these.
    code = code_constant_pool + Op.JUMPDEST + code_segment + Op.JUMP(len(code_constant_pool))
    assert (max_code_size - len(code_segment)) < len(code) <= max_code_size

    env = Environment()

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_mod.to_bytes(32, byteorder="big"),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_empty_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """Test running an empty block as a baseline for fixed proving costs."""
    env = Environment()

    blockchain_test(
        env=env,
        pre=pre,
        post={},
        blocks=[Block(txs=[])],
    )


@pytest.mark.valid_from("Cancun")
def test_amortized_bn128_pairings(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """Test running a block with as many BN128 pairings as possible."""
    env = Environment()

    base_cost = 45_000
    pairing_cost = 34_000
    size_per_pairing = 192

    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    # This is a theoretical maximum number of pairings that can be done in a block.
    # It is only used for an upper bound for calculating the optimal number of pairings below.
    maximum_number_of_pairings = (env.gas_limit - base_cost) // pairing_cost

    # Discover the optimal number of pairings balancing two dimensions:
    # 1. Amortize the precompile base cost as much as possible.
    # 2. The cost of the memory expansion.
    max_pairings = 0
    optimal_per_call_num_pairings = 0
    for i in range(1, maximum_number_of_pairings + 1):
        # We'll pass all pairing arguments via calldata.
        available_gas_after_intrinsic = env.gas_limit - intrinsic_gas_calculator(
            calldata=[0xFF] * size_per_pairing * i  # 0xFF is to indicate non-zero bytes.
        )
        available_gas_after_expansion = max(
            0,
            available_gas_after_intrinsic - mem_exp_gas_calculator(new_bytes=i * size_per_pairing),
        )

        # This is ignoring "glue" opcodes, but helps to have a rough idea of the right
        # cutting point.
        approx_gas_cost_per_call = gsc.G_WARM_ACCOUNT_ACCESS + base_cost + i * pairing_cost

        num_precompile_calls = available_gas_after_expansion // approx_gas_cost_per_call
        num_pairings_done = num_precompile_calls * i  # Each precompile call does i pairings.

        if num_pairings_done > max_pairings:
            max_pairings = num_pairings_done
            optimal_per_call_num_pairings = i

    calldata = Op.CALLDATACOPY(size=Op.CALLDATASIZE)
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, 0x08, 0, Op.CALLDATASIZE, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block, fork)

    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        data=_generate_bn128_pairs(optimal_per_call_num_pairings, 42),
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


def _generate_bn128_pairs(n: int, seed: int = 0):
    rng = random.Random(seed)
    calldata = Bytes()

    for _ in range(n):
        priv_key_g1 = rng.randint(1, 2**32 - 1)
        priv_key_g2 = rng.randint(1, 2**32 - 1)

        point_x_affine = multiply(G1, priv_key_g1)
        point_y_affine = multiply(G2, priv_key_g2)

        assert point_x_affine is not None, "G1 multiplication resulted in point at infinity"
        assert point_y_affine is not None, "G2 multiplication resulted in point at infinity"

        g1_x_bytes = point_x_affine[0].n.to_bytes(32, "big")
        g1_y_bytes = point_x_affine[1].n.to_bytes(32, "big")
        g1_serialized = g1_x_bytes + g1_y_bytes

        g2_x_c1_bytes = point_y_affine[0].coeffs[1].n.to_bytes(32, "big")  # type: ignore
        g2_x_c0_bytes = point_y_affine[0].coeffs[0].n.to_bytes(32, "big")  # type: ignore
        g2_y_c1_bytes = point_y_affine[1].coeffs[1].n.to_bytes(32, "big")  # type: ignore
        g2_y_c0_bytes = point_y_affine[1].coeffs[0].n.to_bytes(32, "big")  # type: ignore
        g2_serialized = g2_x_c1_bytes + g2_x_c0_bytes + g2_y_c1_bytes + g2_y_c0_bytes

        pair_calldata = g1_serialized + g2_serialized
        calldata = Bytes(calldata + pair_calldata)

    return calldata


@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"\x00", id="zero-loop"),
        pytest.param(b"\x00" * 31 + b"\x20", id="one-loop"),
    ],
)
def test_worst_calldataload(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    calldata: bytes,
):
    """Test running a block with as many CALLDATALOAD as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    code_prefix = Op.PUSH0 + Op.JUMPDEST
    code_suffix = Op.PUSH1(1) + Op.JUMP
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)
    code_loop_iter = Op.CALLDATALOAD
    code_body = code_loop_iter * (code_body_len // len(code_loop_iter))
    code = code_prefix + code_body + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=calldata,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.SWAP1,
        Op.SWAP2,
        Op.SWAP3,
        Op.SWAP4,
        Op.SWAP5,
        Op.SWAP6,
        Op.SWAP7,
        Op.SWAP8,
        Op.SWAP9,
        Op.SWAP10,
        Op.SWAP11,
        Op.SWAP12,
        Op.SWAP13,
        Op.SWAP14,
        Op.SWAP15,
        Op.SWAP16,
    ],
)
def test_worst_swap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Opcode,
):
    """Test running a block with as many SWAP as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST + Op.PUSH0 * opcode.min_stack_height
    code_suffix = Op.PUSH0 + Op.JUMP
    opcode_sequence = opcode * (max_code_size - len(code_prefix) - len(code_suffix))
    code = code_prefix + opcode_sequence + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.DUP1),
        pytest.param(Op.DUP2),
        pytest.param(Op.DUP3),
        pytest.param(Op.DUP4),
        pytest.param(Op.DUP5),
        pytest.param(Op.DUP6),
        pytest.param(Op.DUP7),
        pytest.param(Op.DUP8),
        pytest.param(Op.DUP9),
        pytest.param(Op.DUP10),
        pytest.param(Op.DUP11),
        pytest.param(Op.DUP12),
        pytest.param(Op.DUP13),
        pytest.param(Op.DUP14),
        pytest.param(Op.DUP15),
        pytest.param(Op.DUP16),
    ],
)
def test_worst_dup(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
):
    """Test running a block with as many DUP as possible."""
    env = Environment()
    max_stack_height = fork.max_stack_height()

    min_stack_height = opcode.min_stack_height
    code_prefix = Op.PUSH0 * min_stack_height
    opcode_sequence = opcode * (max_stack_height - min_stack_height)
    target_contract_address = pre.deploy_contract(code=code_prefix + opcode_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0))

    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.PUSH0),
        pytest.param(Op.PUSH1),
        pytest.param(Op.PUSH2),
        pytest.param(Op.PUSH3),
        pytest.param(Op.PUSH4),
        pytest.param(Op.PUSH5),
        pytest.param(Op.PUSH6),
        pytest.param(Op.PUSH7),
        pytest.param(Op.PUSH8),
        pytest.param(Op.PUSH9),
        pytest.param(Op.PUSH10),
        pytest.param(Op.PUSH11),
        pytest.param(Op.PUSH12),
        pytest.param(Op.PUSH13),
        pytest.param(Op.PUSH14),
        pytest.param(Op.PUSH15),
        pytest.param(Op.PUSH16),
        pytest.param(Op.PUSH17),
        pytest.param(Op.PUSH18),
        pytest.param(Op.PUSH19),
        pytest.param(Op.PUSH20),
        pytest.param(Op.PUSH21),
        pytest.param(Op.PUSH22),
        pytest.param(Op.PUSH23),
        pytest.param(Op.PUSH24),
        pytest.param(Op.PUSH25),
        pytest.param(Op.PUSH26),
        pytest.param(Op.PUSH27),
        pytest.param(Op.PUSH28),
        pytest.param(Op.PUSH29),
        pytest.param(Op.PUSH30),
        pytest.param(Op.PUSH31),
        pytest.param(Op.PUSH32),
    ],
)
def test_worst_push(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
):
    """Test running a block with as many PUSH as possible."""
    env = Environment()

    op = opcode[1] if opcode.has_data_portion() else opcode
    opcode_sequence = op * fork.max_stack_height()
    target_contract_address = pre.deploy_contract(code=opcode_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0))

    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [Op.RETURN, Op.REVERT],
)
@pytest.mark.parametrize(
    "return_size, return_non_zero_data",
    [
        pytest.param(0, False, id="empty"),
        pytest.param(1024, True, id="1KiB of non-zero data"),
        pytest.param(1024, False, id="1KiB of zero data"),
        pytest.param(1024 * 1024, True, id="1MiB of non-zero data"),
        pytest.param(1024 * 1024, False, id="1MiB of zero data"),
    ],
)
def test_worst_return_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    return_size: int,
    return_non_zero_data: bool,
):
    """Test running a block with as many RETURN or REVERT as possible."""
    env = Environment()
    max_code_size = fork.max_code_size()

    # Create the contract that will be called repeatedly.
    # The bytecode of the contract is:
    # ```
    # [CODECOPY(returned_size) -- Conditional if return_non_zero_data]
    # opcode(returned_size)
    # <Fill with INVALID opcodes up to the max contract size>
    # ```
    # Filling the contract up to the max size is a cheap way of leveraging CODECOPY to return
    # non-zero bytes if requested. Note that since this is a pre-deploy this cost isn't
    # relevant for the benchmark.
    mem_preparation = Op.CODECOPY(size=return_size) if return_non_zero_data else Bytecode()
    executable_code = mem_preparation + opcode(size=return_size)
    code = executable_code
    if return_non_zero_data:
        code += Op.INVALID * (max_code_size - len(executable_code))
    target_contract_address = pre.deploy_contract(code=code)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(address=target_contract_address))
    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )
