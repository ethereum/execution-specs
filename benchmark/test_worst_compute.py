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
    gas_benchmark_value: int,
):
    """Test running a block with as many zero-parameter opcodes as possible."""
    opcode_sequence = opcode * fork.max_stack_height()
    target_contract_address = pre.deploy_contract(code=opcode_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0))
    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many CALLDATASIZE as possible."""
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST
    iter_loop = Op.POP(Op.CALLDATASIZE)
    code_suffix = Op.PUSH0 + Op.JUMP
    code_iter_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(iter_loop)
    code = code_prefix + iter_loop * code_iter_len + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=bytes(code)),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
        data=b"\x00" * calldata_length,
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """
    Test running a block with as many CALLVALUE opcodes as possible.

    The `non_zero_value` parameter controls whether opcode must return non-zero value.
    The `from_origin` parameter controls whether the call frame is the immediate from the
    transaction or a previous CALL.
    """
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST
    iter_loop = Op.POP(Op.CALLVALUE)
    code_suffix = Op.PUSH0 + Op.JUMP
    code_iter_len = (max_code_size - len(code_prefix) - len(code_suffix)) // len(iter_loop)
    code = code_prefix + iter_loop * code_iter_len + code_suffix
    assert len(code) <= max_code_size
    code_address = pre.deploy_contract(code=bytes(code))

    if from_origin:
        tx_to = code_address
    else:
        entry_code = (
            Op.JUMPDEST
            + Op.CALL(address=code_address, value=1 if non_zero_value else 0)
            + Op.JUMP(Op.PUSH0)
        )
        tx_to = pre.deploy_contract(code=entry_code, balance=1_000_000)

    tx = Transaction(
        to=tx_to,
        gas_limit=gas_benchmark_value,
        value=1 if non_zero_value and from_origin else 0,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """
    Test running a block which execute as many RETURNDATASIZE opcodes which return a non-zero
    buffer as possible.

    The `returned_size` parameter indicates the size of the returned data buffer.
    The `return_data_style` indicates how returned data is produced for the opcode caller.
    """
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_returndatasize_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test running a block with as many RETURNDATASIZE opcodes as possible with a zero buffer."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """
    Test running a block with as many MSIZE opcodes as possible.

    The `mem_size` parameter indicates by how much the memory is expanded.
    """
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
        value=mem_size,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_keccak(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test running a block with as many KECCAK256 permutations as possible."""
    # Intrinsic gas cost is paid once.
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    available_gas = gas_benchmark_value - intrinsic_gas_calculator()

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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many precompile calls which have a single `data` input."""
    # Intrinsic gas cost is paid once.
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    available_gas = gas_benchmark_value - intrinsic_gas_calculator()

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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
                base=64 * "ff",
                exponent=64 * "ff",
                modulus=63 * "ff" + "00",
            ),
            id="mod_even_64b_exp_512",
        ),
        pytest.param(
            ModExpInput(
                base=128 * "ff",
                exponent=128 * "ff",
                modulus=127 * "ff" + "00",
            ),
            id="mod_even_128b_exp_1024",
        ),
        pytest.param(
            ModExpInput(
                base=256 * "ff",
                exponent=128 * "ff",
                modulus=255 * "ff" + "00",
            ),
            id="mod_even_256b_exp_1024",
        ),
        pytest.param(
            ModExpInput(
                base=512 * "ff",
                exponent=128 * "ff",
                modulus=511 * "ff" + "00",
            ),
            id="mod_even_512b_exp_1024",
        ),
        pytest.param(
            ModExpInput(
                base=1024 * "ff",
                exponent=128 * "ff",
                modulus=1023 * "ff" + "00",
            ),
            id="mod_even_1024b_exp_1024",
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
                base=64 * "ff",
                exponent=64 * "ff",
                modulus=63 * "ff" + "01",
            ),
            id="mod_odd_64b_exp_512",
        ),
        pytest.param(
            ModExpInput(
                base=128 * "ff",
                exponent=128 * "ff",
                modulus=127 * "ff" + "01",
            ),
            id="mod_odd_128b_exp_1024",
        ),
        pytest.param(
            ModExpInput(
                base=256 * "ff",
                exponent=128 * "ff",
                modulus=255 * "ff" + "01",
            ),
            id="mod_odd_256b_exp_1024",
        ),
        pytest.param(
            ModExpInput(
                base=512 * "ff",
                exponent=128 * "ff",
                modulus=511 * "ff" + "01",
            ),
            id="mod_odd_512b_exp_1024",
        ),
        pytest.param(
            ModExpInput(
                base=1024 * "ff",
                exponent=128 * "ff",
                modulus=1023 * "ff" + "01",
            ),
            id="mod_odd_1024b_exp_1024",
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
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L122
        pytest.param(
            ModExpInput(
                base="03",
                exponent="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2e",
                modulus="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
            ),
            id="mod_vul_example_1",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L124
        pytest.param(
            ModExpInput(
                base="",
                exponent="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2e",
                modulus="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
            ),
            id="mod_vul_example_2",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L126
        pytest.param(
            ModExpInput(
                base="e09ad9675465c53a109fac66a445c91b292d2bb2c5268addb30cd82f80fcb0033ff97c80a5fc6f39193ae969c6ede6710a6b7ac27078a06d90ef1c72e5c85fb5",
                exponent="02",
                modulus="fc9e1f6beb81516545975218075ec2af118cd8798df6e08a147c60fd6095ac2bb02c2908cf4dd7c81f11c289e4bce98f3553768f392a80ce22bf5c4f4a248c6b",
            ),
            id="mod_vul_nagydani_1_square",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L128
        pytest.param(
            ModExpInput(
                base="e09ad9675465c53a109fac66a445c91b292d2bb2c5268addb30cd82f80fcb0033ff97c80a5fc6f39193ae969c6ede6710a6b7ac27078a06d90ef1c72e5c85fb5",
                exponent="03",
                modulus="fc9e1f6beb81516545975218075ec2af118cd8798df6e08a147c60fd6095ac2bb02c2908cf4dd7c81f11c289e4bce98f3553768f392a80ce22bf5c4f4a248c6b",
            ),
            id="mod_vul_nagydani_1_qube",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L130
        pytest.param(
            ModExpInput(
                base="e09ad9675465c53a109fac66a445c91b292d2bb2c5268addb30cd82f80fcb0033ff97c80a5fc6f39193ae969c6ede6710a6b7ac27078a06d90ef1c72e5c85fb5",
                exponent="010001",
                modulus="fc9e1f6beb81516545975218075ec2af118cd8798df6e08a147c60fd6095ac2bb02c2908cf4dd7c81f11c289e4bce98f3553768f392a80ce22bf5c4f4a248c6b",
            ),
            id="mod_vul_nagydani_1_pow_0x10001",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L132
        pytest.param(
            ModExpInput(
                base="cad7d991a00047dd54d3399b6b0b937c718abddef7917c75b6681f40cc15e2be0003657d8d4c34167b2f0bbbca0ccaa407c2a6a07d50f1517a8f22979ce12a81dcaf707cc0cebfc0ce2ee84ee7f77c38b9281b9822a8d3de62784c089c9b18dcb9a2a5eecbede90ea788a862a9ddd9d609c2c52972d63e289e28f6a590ffbf51",
                exponent="02",
                modulus="e6d893b80aeed5e6e9ce9afa8a5d5675c93a32ac05554cb20e9951b2c140e3ef4e433068cf0fb73bc9f33af1853f64aa27a0028cbf570d7ac9048eae5dc7b28c87c31e5810f1e7fa2cda6adf9f1076dbc1ec1238560071e7efc4e9565c49be9e7656951985860a558a754594115830bcdb421f741408346dd5997bb01c287087",
            ),
            id="mod_vul_nagydani_2_square",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L134
        pytest.param(
            ModExpInput(
                base="cad7d991a00047dd54d3399b6b0b937c718abddef7917c75b6681f40cc15e2be0003657d8d4c34167b2f0bbbca0ccaa407c2a6a07d50f1517a8f22979ce12a81dcaf707cc0cebfc0ce2ee84ee7f77c38b9281b9822a8d3de62784c089c9b18dcb9a2a5eecbede90ea788a862a9ddd9d609c2c52972d63e289e28f6a590ffbf51",
                exponent="03",
                modulus="e6d893b80aeed5e6e9ce9afa8a5d5675c93a32ac05554cb20e9951b2c140e3ef4e433068cf0fb73bc9f33af1853f64aa27a0028cbf570d7ac9048eae5dc7b28c87c31e5810f1e7fa2cda6adf9f1076dbc1ec1238560071e7efc4e9565c49be9e7656951985860a558a754594115830bcdb421f741408346dd5997bb01c287087",
            ),
            id="mod_vul_nagydani_2_qube",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L136
        pytest.param(
            ModExpInput(
                base="cad7d991a00047dd54d3399b6b0b937c718abddef7917c75b6681f40cc15e2be0003657d8d4c34167b2f0bbbca0ccaa407c2a6a07d50f1517a8f22979ce12a81dcaf707cc0cebfc0ce2ee84ee7f77c38b9281b9822a8d3de62784c089c9b18dcb9a2a5eecbede90ea788a862a9ddd9d609c2c52972d63e289e28f6a590ffbf51",
                exponent="010001",
                modulus="e6d893b80aeed5e6e9ce9afa8a5d5675c93a32ac05554cb20e9951b2c140e3ef4e433068cf0fb73bc9f33af1853f64aa27a0028cbf570d7ac9048eae5dc7b28c87c31e5810f1e7fa2cda6adf9f1076dbc1ec1238560071e7efc4e9565c49be9e7656951985860a558a754594115830bcdb421f741408346dd5997bb01c287087",
            ),
            id="mod_vul_nagydani_2_pow_0x10001",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L138
        pytest.param(
            ModExpInput(
                base="c9130579f243e12451760976261416413742bd7c91d39ae087f46794062b8c239f2a74abf3918605a0e046a7890e049475ba7fbb78f5de6490bd22a710cc04d30088179a919d86c2da62cf37f59d8f258d2310d94c24891be2d7eeafaa32a8cb4b0cfe5f475ed778f45907dc8916a73f03635f233f7a77a00a3ec9ca6761a5bbd558a2318ecd0caa1c5016691523e7e1fa267dd35e70c66e84380bdcf7c0582f540174e572c41f81e93da0b757dff0b0fe23eb03aa19af0bdec3afb474216febaacb8d0381e631802683182b0fe72c28392539850650b70509f54980241dc175191a35d967288b532a7a8223ce2440d010615f70df269501944d4ec16fe4a3cb",
                exponent="02",
                modulus="d7a85909174757835187cb52e71934e6c07ef43b4c46fc30bbcd0bc72913068267c54a4aabebb493922492820babdeb7dc9b1558fcf7bd82c37c82d3147e455b623ab0efa752fe0b3a67ca6e4d126639e645a0bf417568adbb2a6a4eef62fa1fa29b2a5a43bebea1f82193a7dd98eb483d09bb595af1fa9c97c7f41f5649d976aee3e5e59e2329b43b13bea228d4a93f16ba139ccb511de521ffe747aa2eca664f7c9e33da59075cc335afcd2bf3ae09765f01ab5a7c3e3938ec168b74724b5074247d200d9970382f683d6059b94dbc336603d1dfee714e4b447ac2fa1d99ecb4961da2854e03795ed758220312d101e1e3d87d5313a6d052aebde75110363d",
            ),
            id="mod_vul_nagydani_3_square",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L140
        pytest.param(
            ModExpInput(
                base="c9130579f243e12451760976261416413742bd7c91d39ae087f46794062b8c239f2a74abf3918605a0e046a7890e049475ba7fbb78f5de6490bd22a710cc04d30088179a919d86c2da62cf37f59d8f258d2310d94c24891be2d7eeafaa32a8cb4b0cfe5f475ed778f45907dc8916a73f03635f233f7a77a00a3ec9ca6761a5bbd558a2318ecd0caa1c5016691523e7e1fa267dd35e70c66e84380bdcf7c0582f540174e572c41f81e93da0b757dff0b0fe23eb03aa19af0bdec3afb474216febaacb8d0381e631802683182b0fe72c28392539850650b70509f54980241dc175191a35d967288b532a7a8223ce2440d010615f70df269501944d4ec16fe4a3cb",
                exponent="03",
                modulus="d7a85909174757835187cb52e71934e6c07ef43b4c46fc30bbcd0bc72913068267c54a4aabebb493922492820babdeb7dc9b1558fcf7bd82c37c82d3147e455b623ab0efa752fe0b3a67ca6e4d126639e645a0bf417568adbb2a6a4eef62fa1fa29b2a5a43bebea1f82193a7dd98eb483d09bb595af1fa9c97c7f41f5649d976aee3e5e59e2329b43b13bea228d4a93f16ba139ccb511de521ffe747aa2eca664f7c9e33da59075cc335afcd2bf3ae09765f01ab5a7c3e3938ec168b74724b5074247d200d9970382f683d6059b94dbc336603d1dfee714e4b447ac2fa1d99ecb4961da2854e03795ed758220312d101e1e3d87d5313a6d052aebde75110363d",
            ),
            id="mod_vul_nagydani_3_qube",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L142
        pytest.param(
            ModExpInput(
                base="c9130579f243e12451760976261416413742bd7c91d39ae087f46794062b8c239f2a74abf3918605a0e046a7890e049475ba7fbb78f5de6490bd22a710cc04d30088179a919d86c2da62cf37f59d8f258d2310d94c24891be2d7eeafaa32a8cb4b0cfe5f475ed778f45907dc8916a73f03635f233f7a77a00a3ec9ca6761a5bbd558a2318ecd0caa1c5016691523e7e1fa267dd35e70c66e84380bdcf7c0582f540174e572c41f81e93da0b757dff0b0fe23eb03aa19af0bdec3afb474216febaacb8d0381e631802683182b0fe72c28392539850650b70509f54980241dc175191a35d967288b532a7a8223ce2440d010615f70df269501944d4ec16fe4a3cb",
                exponent="010001",
                modulus="d7a85909174757835187cb52e71934e6c07ef43b4c46fc30bbcd0bc72913068267c54a4aabebb493922492820babdeb7dc9b1558fcf7bd82c37c82d3147e455b623ab0efa752fe0b3a67ca6e4d126639e645a0bf417568adbb2a6a4eef62fa1fa29b2a5a43bebea1f82193a7dd98eb483d09bb595af1fa9c97c7f41f5649d976aee3e5e59e2329b43b13bea228d4a93f16ba139ccb511de521ffe747aa2eca664f7c9e33da59075cc335afcd2bf3ae09765f01ab5a7c3e3938ec168b74724b5074247d200d9970382f683d6059b94dbc336603d1dfee714e4b447ac2fa1d99ecb4961da2854e03795ed758220312d101e1e3d87d5313a6d052aebde75110363d",
            ),
            id="mod_vul_nagydani_3_pow_0x10001",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L144
        pytest.param(
            ModExpInput(
                base="db34d0e438249c0ed685c949cc28776a05094e1c48691dc3f2dca5fc3356d2a0663bd376e4712839917eb9a19c670407e2c377a2de385a3ff3b52104f7f1f4e0c7bf7717fb913896693dc5edbb65b760ef1b00e42e9d8f9af17352385e1cd742c9b006c0f669995cb0bb21d28c0aced2892267637b6470d8cee0ab27fc5d42658f6e88240c31d6774aa60a7ebd25cd48b56d0da11209f1928e61005c6eb709f3e8e0aaf8d9b10f7d7e296d772264dc76897ccdddadc91efa91c1903b7232a9e4c3b941917b99a3bc0c26497dedc897c25750af60237aa67934a26a2bc491db3dcc677491944bc1f51d3e5d76b8d846a62db03dedd61ff508f91a56d71028125035c3a44cbb041497c83bf3e4ae2a9613a401cc721c547a2afa3b16a2969933d3626ed6d8a7428648f74122fd3f2a02a20758f7f693892c8fd798b39abac01d18506c45e71432639e9f9505719ee822f62ccbf47f6850f096ff77b5afaf4be7d772025791717dbe5abf9b3f40cff7d7aab6f67e38f62faf510747276e20a42127e7500c444f9ed92baf65ade9e836845e39c4316d9dce5f8e2c8083e2c0acbb95296e05e51aab13b6b8f53f06c9c4276e12b0671133218cc3ea907da3bd9a367096d9202128d14846cc2e20d56fc8473ecb07cecbfb8086919f3971926e7045b853d85a69d026195c70f9f7a823536e2a8f4b3e12e94d9b53a934353451094b81",
                exponent="02",
                modulus="df3143a0057457d75e8c708b6337a6f5a4fd1a06727acf9fb93e2993c62f3378b37d56c85e7b1e00f0145ebf8e4095bd723166293c60b6ac1252291ef65823c9e040ddad14969b3b340a4ef714db093a587c37766d68b8d6b5016e741587e7e6bf7e763b44f0247e64bae30f994d248bfd20541a333e5b225ef6a61199e301738b1e688f70ec1d7fb892c183c95dc543c3e12adf8a5e8b9ca9d04f9445cced3ab256f29e998e69efaa633a7b60e1db5a867924ccab0a171d9d6e1098dfa15acde9553de599eaa56490c8f411e4985111f3d40bddfc5e301edb01547b01a886550a61158f7e2033c59707789bf7c854181d0c2e2a42a93cf09209747d7082e147eb8544de25c3eb14f2e35559ea0c0f5877f2f3fc92132c0ae9da4e45b2f6c866a224ea6d1f28c05320e287750fbc647368d41116e528014cc1852e5531d53e4af938374daba6cee4baa821ed07117253bb3601ddd00d59a3d7fb2ef1f5a2fbba7c429f0cf9a5b3462410fd833a69118f8be9c559b1000cc608fd877fb43f8e65c2d1302622b944462579056874b387208d90623fcdaf93920ca7a9e4ba64ea208758222ad868501cc2c345e2d3a5ea2a17e5069248138c8a79c0251185d29ee73e5afab5354769142d2bf0cb6712727aa6bf84a6245fcdae66e4938d84d1b9dd09a884818622080ff5f98942fb20acd7e0c916c2d5ea7ce6f7e173315384518f",
            ),
            id="mod_vul_nagydani_4_square",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L146
        pytest.param(
            ModExpInput(
                base="db34d0e438249c0ed685c949cc28776a05094e1c48691dc3f2dca5fc3356d2a0663bd376e4712839917eb9a19c670407e2c377a2de385a3ff3b52104f7f1f4e0c7bf7717fb913896693dc5edbb65b760ef1b00e42e9d8f9af17352385e1cd742c9b006c0f669995cb0bb21d28c0aced2892267637b6470d8cee0ab27fc5d42658f6e88240c31d6774aa60a7ebd25cd48b56d0da11209f1928e61005c6eb709f3e8e0aaf8d9b10f7d7e296d772264dc76897ccdddadc91efa91c1903b7232a9e4c3b941917b99a3bc0c26497dedc897c25750af60237aa67934a26a2bc491db3dcc677491944bc1f51d3e5d76b8d846a62db03dedd61ff508f91a56d71028125035c3a44cbb041497c83bf3e4ae2a9613a401cc721c547a2afa3b16a2969933d3626ed6d8a7428648f74122fd3f2a02a20758f7f693892c8fd798b39abac01d18506c45e71432639e9f9505719ee822f62ccbf47f6850f096ff77b5afaf4be7d772025791717dbe5abf9b3f40cff7d7aab6f67e38f62faf510747276e20a42127e7500c444f9ed92baf65ade9e836845e39c4316d9dce5f8e2c8083e2c0acbb95296e05e51aab13b6b8f53f06c9c4276e12b0671133218cc3ea907da3bd9a367096d9202128d14846cc2e20d56fc8473ecb07cecbfb8086919f3971926e7045b853d85a69d026195c70f9f7a823536e2a8f4b3e12e94d9b53a934353451094b81",
                exponent="03",
                modulus="df3143a0057457d75e8c708b6337a6f5a4fd1a06727acf9fb93e2993c62f3378b37d56c85e7b1e00f0145ebf8e4095bd723166293c60b6ac1252291ef65823c9e040ddad14969b3b340a4ef714db093a587c37766d68b8d6b5016e741587e7e6bf7e763b44f0247e64bae30f994d248bfd20541a333e5b225ef6a61199e301738b1e688f70ec1d7fb892c183c95dc543c3e12adf8a5e8b9ca9d04f9445cced3ab256f29e998e69efaa633a7b60e1db5a867924ccab0a171d9d6e1098dfa15acde9553de599eaa56490c8f411e4985111f3d40bddfc5e301edb01547b01a886550a61158f7e2033c59707789bf7c854181d0c2e2a42a93cf09209747d7082e147eb8544de25c3eb14f2e35559ea0c0f5877f2f3fc92132c0ae9da4e45b2f6c866a224ea6d1f28c05320e287750fbc647368d41116e528014cc1852e5531d53e4af938374daba6cee4baa821ed07117253bb3601ddd00d59a3d7fb2ef1f5a2fbba7c429f0cf9a5b3462410fd833a69118f8be9c559b1000cc608fd877fb43f8e65c2d1302622b944462579056874b387208d90623fcdaf93920ca7a9e4ba64ea208758222ad868501cc2c345e2d3a5ea2a17e5069248138c8a79c0251185d29ee73e5afab5354769142d2bf0cb6712727aa6bf84a6245fcdae66e4938d84d1b9dd09a884818622080ff5f98942fb20acd7e0c916c2d5ea7ce6f7e173315384518f",
            ),
            id="mod_vul_nagydani_4_qube",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L148
        pytest.param(
            ModExpInput(
                base="db34d0e438249c0ed685c949cc28776a05094e1c48691dc3f2dca5fc3356d2a0663bd376e4712839917eb9a19c670407e2c377a2de385a3ff3b52104f7f1f4e0c7bf7717fb913896693dc5edbb65b760ef1b00e42e9d8f9af17352385e1cd742c9b006c0f669995cb0bb21d28c0aced2892267637b6470d8cee0ab27fc5d42658f6e88240c31d6774aa60a7ebd25cd48b56d0da11209f1928e61005c6eb709f3e8e0aaf8d9b10f7d7e296d772264dc76897ccdddadc91efa91c1903b7232a9e4c3b941917b99a3bc0c26497dedc897c25750af60237aa67934a26a2bc491db3dcc677491944bc1f51d3e5d76b8d846a62db03dedd61ff508f91a56d71028125035c3a44cbb041497c83bf3e4ae2a9613a401cc721c547a2afa3b16a2969933d3626ed6d8a7428648f74122fd3f2a02a20758f7f693892c8fd798b39abac01d18506c45e71432639e9f9505719ee822f62ccbf47f6850f096ff77b5afaf4be7d772025791717dbe5abf9b3f40cff7d7aab6f67e38f62faf510747276e20a42127e7500c444f9ed92baf65ade9e836845e39c4316d9dce5f8e2c8083e2c0acbb95296e05e51aab13b6b8f53f06c9c4276e12b0671133218cc3ea907da3bd9a367096d9202128d14846cc2e20d56fc8473ecb07cecbfb8086919f3971926e7045b853d85a69d026195c70f9f7a823536e2a8f4b3e12e94d9b53a934353451094b81",
                exponent="010001",
                modulus="df3143a0057457d75e8c708b6337a6f5a4fd1a06727acf9fb93e2993c62f3378b37d56c85e7b1e00f0145ebf8e4095bd723166293c60b6ac1252291ef65823c9e040ddad14969b3b340a4ef714db093a587c37766d68b8d6b5016e741587e7e6bf7e763b44f0247e64bae30f994d248bfd20541a333e5b225ef6a61199e301738b1e688f70ec1d7fb892c183c95dc543c3e12adf8a5e8b9ca9d04f9445cced3ab256f29e998e69efaa633a7b60e1db5a867924ccab0a171d9d6e1098dfa15acde9553de599eaa56490c8f411e4985111f3d40bddfc5e301edb01547b01a886550a61158f7e2033c59707789bf7c854181d0c2e2a42a93cf09209747d7082e147eb8544de25c3eb14f2e35559ea0c0f5877f2f3fc92132c0ae9da4e45b2f6c866a224ea6d1f28c05320e287750fbc647368d41116e528014cc1852e5531d53e4af938374daba6cee4baa821ed07117253bb3601ddd00d59a3d7fb2ef1f5a2fbba7c429f0cf9a5b3462410fd833a69118f8be9c559b1000cc608fd877fb43f8e65c2d1302622b944462579056874b387208d90623fcdaf93920ca7a9e4ba64ea208758222ad868501cc2c345e2d3a5ea2a17e5069248138c8a79c0251185d29ee73e5afab5354769142d2bf0cb6712727aa6bf84a6245fcdae66e4938d84d1b9dd09a884818622080ff5f98942fb20acd7e0c916c2d5ea7ce6f7e173315384518f",
            ),
            id="mod_vul_nagydani_4_pow_0x10001",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L150
        pytest.param(
            ModExpInput(
                base="c5a1611f8be90071a43db23cc2fe01871cc4c0e8ab5743f6378e4fef77f7f6db0095c0727e20225beb665645403453e325ad5f9aeb9ba99bf3c148f63f9c07cf4fe8847ad5242d6b7d4499f93bd47056ddab8f7dee878fc2314f344dbee2a7c41a5d3db91eff372c730c2fdd3a141a4b61999e36d549b9870cf2f4e632c4d5df5f024f81c028000073a0ed8847cfb0593d36a47142f578f05ccbe28c0c06aeb1b1da027794c48db880278f79ba78ae64eedfea3c07d10e0562668d839749dc95f40467d15cf65b9cfc52c7c4bcef1cda3596dd52631aac942f146c7cebd46065131699ce8385b0db1874336747ee020a5698a3d1a1082665721e769567f579830f9d259cec1a836845109c21cf6b25da572512bf3c42fd4b96e43895589042ab60dd41f497db96aec102087fe784165bb45f942859268fd2ff6c012d9d00c02ba83eace047cc5f7b2c392c2955c58a49f0338d6fc58749c9db2155522ac17914ec216ad87f12e0ee95574613942fa615898c4d9e8a3be68cd6afa4e7a003dedbdf8edfee31162b174f965b20ae752ad89c967b3068b6f722c16b354456ba8e280f987c08e0a52d40a2e8f3a59b94d590aeef01879eb7a90b3ee7d772c839c85519cbeaddc0c193ec4874a463b53fcaea3271d80ebfb39b33489365fc039ae549a17a9ff898eea2f4cb27b8dbee4c17b998438575b2b8d107e4a0d66ba7fca85b41a58a8d51f191a35c856dfbe8aef2b00048a694bbccff832d23c8ca7a7ff0b6c0b3011d00b97c86c0628444d267c951d9e4fb8f83e154b8f74fb51aa16535e498235c5597dac9606ed0be3173a3836baa4e7d756ffe1e2879b415d3846bccd538c05b847785699aefde3e305decb600cd8fb0e7d8de5efc26971a6ad4e6d7a2d91474f1023a0ac4b78dc937da0ce607a45974d2cac1c33a2631ff7fe6144a3b2e5cf98b531a9627dea92c1dc82204d09db0439b6a11dd64b484e1263aa45fd9539b6020b55e3baece3986a8bffc1003406348f5c61265099ed43a766ee4f93f5f9c5abbc32a0fd3ac2b35b87f9ec26037d88275bd7dd0a54474995ee34ed3727f3f97c48db544b1980193a4b76a8a3ddab3591ce527f16d91882e67f0103b5cda53f7da54d489fc4ac08b6ab358a5a04aa9daa16219d50bd672a7cb804ed769d218807544e5993f1c27427104b349906a0b654df0bf69328afd3013fbe430155339c39f236df5557bf92f1ded7ff609a8502f49064ec3d1dbfb6c15d3a4c11a4f8acd12278cbf68acd5709463d12e3338a6eddb8c112f199645e23154a8e60879d2a654e3ed9296aa28f134168619691cd2c6b9e2eba4438381676173fc63c2588a3c5910dc149cf3760f0aa9fa9c3f5faa9162b0bf1aac9dd32b706a60ef53cbdb394b6b40222b5bc80eea82ba8958386672564cae3794f977871ab62337cf",
                exponent="02",
                modulus="e30049201ec12937e7ce79d0f55d9c810e20acf52212aca1d3888949e0e4830aad88d804161230eb89d4d329cc83570fe257217d2119134048dd2ed167646975fc7d77136919a049ea74cf08ddd2b896890bb24a0ba18094a22baa351bf29ad96c66bbb1a598f2ca391749620e62d61c3561a7d3653ccc8892c7b99baaf76bf836e2991cb06d6bc0514568ff0d1ec8bb4b3d6984f5eaefb17d3ea2893722375d3ddb8e389a8eef7d7d198f8e687d6a513983df906099f9a2d23f4f9dec6f8ef2f11fc0a21fac45353b94e00486f5e17d386af42502d09db33cf0cf28310e049c07e88682aeeb00cb833c5174266e62407a57583f1f88b304b7c6e0c84bbe1c0fd423072d37a5bd0aacf764229e5c7cd02473460ba3645cd8e8ae144065bf02d0dd238593d8e230354f67e0b2f23012c23274f80e3ee31e35e2606a4a3f31d94ab755e6d163cff52cbb36b6d0cc67ffc512aeed1dce4d7a0d70ce82f2baba12e8d514dc92a056f994adfb17b5b9712bd5186f27a2fda1f7039c5df2c8587fdc62f5627580c13234b55be4df3056050e2d1ef3218f0dd66cb05265fe1acfb0989d8213f2c19d1735a7cf3fa65d88dad5af52dc2bba22b7abf46c3bc77b5091baab9e8f0ddc4d5e581037de91a9f8dcbc69309be29cc815cf19a20a7585b8b3073edf51fc9baeb3e509b97fa4ecfd621e0fd57bd61cac1b895c03248ff12bdbc57509250df3517e8a3fe1d776836b34ab352b973d932ef708b14f7418f9eceb1d87667e61e3e758649cb083f01b133d37ab2f5afa96d6c84bcacf4efc3851ad308c1e7d9113624fce29fab460ab9d2a48d92cdb281103a5250ad44cb2ff6e67ac670c02fdafb3e0f1353953d6d7d5646ca1568dea55275a050ec501b7c6250444f7219f1ba7521ba3b93d089727ca5f3bbe0d6c1300b423377004954c5628fdb65770b18ced5c9b23a4a5a6d6ef25fe01b4ce278de0bcc4ed86e28a0a68818ffa40970128cf2c38740e80037984428c1bd5113f40ff47512ee6f4e4d8f9b8e8e1b3040d2928d003bd1c1329dc885302fbce9fa81c23b4dc49c7c82d29b52957847898676c89aa5d32b5b0e1c0d5a2b79a19d67562f407f19425687971a957375879d90c5f57c857136c17106c9ab1b99d80e69c8c954ed386493368884b55c939b8d64d26f643e800c56f90c01079d7c534e3b2b7ae352cefd3016da55f6a85eb803b85e2304915fd2001f77c74e28746293c46e4f5f0fd49cf988aafd0026b8e7a3bab2da5cdce1ea26c2e29ec03f4807fac432662b2d6c060be1c7be0e5489de69d0a6e03a4b9117f9244b34a0f1ecba89884f781c6320412413a00c4980287409a2a78c2cd7e65cecebbe4ec1c28cac4dd95f6998e78fc6f1392384331c9436aa10e10e2bf8ad2c4eafbcf276aa7bae64b74428911b3269c749338b0fc5075ad",
            ),
            id="mod_vul_nagydani_5_square",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L152
        pytest.param(
            ModExpInput(
                base="c5a1611f8be90071a43db23cc2fe01871cc4c0e8ab5743f6378e4fef77f7f6db0095c0727e20225beb665645403453e325ad5f9aeb9ba99bf3c148f63f9c07cf4fe8847ad5242d6b7d4499f93bd47056ddab8f7dee878fc2314f344dbee2a7c41a5d3db91eff372c730c2fdd3a141a4b61999e36d549b9870cf2f4e632c4d5df5f024f81c028000073a0ed8847cfb0593d36a47142f578f05ccbe28c0c06aeb1b1da027794c48db880278f79ba78ae64eedfea3c07d10e0562668d839749dc95f40467d15cf65b9cfc52c7c4bcef1cda3596dd52631aac942f146c7cebd46065131699ce8385b0db1874336747ee020a5698a3d1a1082665721e769567f579830f9d259cec1a836845109c21cf6b25da572512bf3c42fd4b96e43895589042ab60dd41f497db96aec102087fe784165bb45f942859268fd2ff6c012d9d00c02ba83eace047cc5f7b2c392c2955c58a49f0338d6fc58749c9db2155522ac17914ec216ad87f12e0ee95574613942fa615898c4d9e8a3be68cd6afa4e7a003dedbdf8edfee31162b174f965b20ae752ad89c967b3068b6f722c16b354456ba8e280f987c08e0a52d40a2e8f3a59b94d590aeef01879eb7a90b3ee7d772c839c85519cbeaddc0c193ec4874a463b53fcaea3271d80ebfb39b33489365fc039ae549a17a9ff898eea2f4cb27b8dbee4c17b998438575b2b8d107e4a0d66ba7fca85b41a58a8d51f191a35c856dfbe8aef2b00048a694bbccff832d23c8ca7a7ff0b6c0b3011d00b97c86c0628444d267c951d9e4fb8f83e154b8f74fb51aa16535e498235c5597dac9606ed0be3173a3836baa4e7d756ffe1e2879b415d3846bccd538c05b847785699aefde3e305decb600cd8fb0e7d8de5efc26971a6ad4e6d7a2d91474f1023a0ac4b78dc937da0ce607a45974d2cac1c33a2631ff7fe6144a3b2e5cf98b531a9627dea92c1dc82204d09db0439b6a11dd64b484e1263aa45fd9539b6020b55e3baece3986a8bffc1003406348f5c61265099ed43a766ee4f93f5f9c5abbc32a0fd3ac2b35b87f9ec26037d88275bd7dd0a54474995ee34ed3727f3f97c48db544b1980193a4b76a8a3ddab3591ce527f16d91882e67f0103b5cda53f7da54d489fc4ac08b6ab358a5a04aa9daa16219d50bd672a7cb804ed769d218807544e5993f1c27427104b349906a0b654df0bf69328afd3013fbe430155339c39f236df5557bf92f1ded7ff609a8502f49064ec3d1dbfb6c15d3a4c11a4f8acd12278cbf68acd5709463d12e3338a6eddb8c112f199645e23154a8e60879d2a654e3ed9296aa28f134168619691cd2c6b9e2eba4438381676173fc63c2588a3c5910dc149cf3760f0aa9fa9c3f5faa9162b0bf1aac9dd32b706a60ef53cbdb394b6b40222b5bc80eea82ba8958386672564cae3794f977871ab62337cf",
                exponent="03",
                modulus="e30049201ec12937e7ce79d0f55d9c810e20acf52212aca1d3888949e0e4830aad88d804161230eb89d4d329cc83570fe257217d2119134048dd2ed167646975fc7d77136919a049ea74cf08ddd2b896890bb24a0ba18094a22baa351bf29ad96c66bbb1a598f2ca391749620e62d61c3561a7d3653ccc8892c7b99baaf76bf836e2991cb06d6bc0514568ff0d1ec8bb4b3d6984f5eaefb17d3ea2893722375d3ddb8e389a8eef7d7d198f8e687d6a513983df906099f9a2d23f4f9dec6f8ef2f11fc0a21fac45353b94e00486f5e17d386af42502d09db33cf0cf28310e049c07e88682aeeb00cb833c5174266e62407a57583f1f88b304b7c6e0c84bbe1c0fd423072d37a5bd0aacf764229e5c7cd02473460ba3645cd8e8ae144065bf02d0dd238593d8e230354f67e0b2f23012c23274f80e3ee31e35e2606a4a3f31d94ab755e6d163cff52cbb36b6d0cc67ffc512aeed1dce4d7a0d70ce82f2baba12e8d514dc92a056f994adfb17b5b9712bd5186f27a2fda1f7039c5df2c8587fdc62f5627580c13234b55be4df3056050e2d1ef3218f0dd66cb05265fe1acfb0989d8213f2c19d1735a7cf3fa65d88dad5af52dc2bba22b7abf46c3bc77b5091baab9e8f0ddc4d5e581037de91a9f8dcbc69309be29cc815cf19a20a7585b8b3073edf51fc9baeb3e509b97fa4ecfd621e0fd57bd61cac1b895c03248ff12bdbc57509250df3517e8a3fe1d776836b34ab352b973d932ef708b14f7418f9eceb1d87667e61e3e758649cb083f01b133d37ab2f5afa96d6c84bcacf4efc3851ad308c1e7d9113624fce29fab460ab9d2a48d92cdb281103a5250ad44cb2ff6e67ac670c02fdafb3e0f1353953d6d7d5646ca1568dea55275a050ec501b7c6250444f7219f1ba7521ba3b93d089727ca5f3bbe0d6c1300b423377004954c5628fdb65770b18ced5c9b23a4a5a6d6ef25fe01b4ce278de0bcc4ed86e28a0a68818ffa40970128cf2c38740e80037984428c1bd5113f40ff47512ee6f4e4d8f9b8e8e1b3040d2928d003bd1c1329dc885302fbce9fa81c23b4dc49c7c82d29b52957847898676c89aa5d32b5b0e1c0d5a2b79a19d67562f407f19425687971a957375879d90c5f57c857136c17106c9ab1b99d80e69c8c954ed386493368884b55c939b8d64d26f643e800c56f90c01079d7c534e3b2b7ae352cefd3016da55f6a85eb803b85e2304915fd2001f77c74e28746293c46e4f5f0fd49cf988aafd0026b8e7a3bab2da5cdce1ea26c2e29ec03f4807fac432662b2d6c060be1c7be0e5489de69d0a6e03a4b9117f9244b34a0f1ecba89884f781c6320412413a00c4980287409a2a78c2cd7e65cecebbe4ec1c28cac4dd95f6998e78fc6f1392384331c9436aa10e10e2bf8ad2c4eafbcf276aa7bae64b74428911b3269c749338b0fc5075ad",
            ),
            id="mod_vul_nagydani_5_qube",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L154
        pytest.param(
            ModExpInput(
                base="c5a1611f8be90071a43db23cc2fe01871cc4c0e8ab5743f6378e4fef77f7f6db0095c0727e20225beb665645403453e325ad5f9aeb9ba99bf3c148f63f9c07cf4fe8847ad5242d6b7d4499f93bd47056ddab8f7dee878fc2314f344dbee2a7c41a5d3db91eff372c730c2fdd3a141a4b61999e36d549b9870cf2f4e632c4d5df5f024f81c028000073a0ed8847cfb0593d36a47142f578f05ccbe28c0c06aeb1b1da027794c48db880278f79ba78ae64eedfea3c07d10e0562668d839749dc95f40467d15cf65b9cfc52c7c4bcef1cda3596dd52631aac942f146c7cebd46065131699ce8385b0db1874336747ee020a5698a3d1a1082665721e769567f579830f9d259cec1a836845109c21cf6b25da572512bf3c42fd4b96e43895589042ab60dd41f497db96aec102087fe784165bb45f942859268fd2ff6c012d9d00c02ba83eace047cc5f7b2c392c2955c58a49f0338d6fc58749c9db2155522ac17914ec216ad87f12e0ee95574613942fa615898c4d9e8a3be68cd6afa4e7a003dedbdf8edfee31162b174f965b20ae752ad89c967b3068b6f722c16b354456ba8e280f987c08e0a52d40a2e8f3a59b94d590aeef01879eb7a90b3ee7d772c839c85519cbeaddc0c193ec4874a463b53fcaea3271d80ebfb39b33489365fc039ae549a17a9ff898eea2f4cb27b8dbee4c17b998438575b2b8d107e4a0d66ba7fca85b41a58a8d51f191a35c856dfbe8aef2b00048a694bbccff832d23c8ca7a7ff0b6c0b3011d00b97c86c0628444d267c951d9e4fb8f83e154b8f74fb51aa16535e498235c5597dac9606ed0be3173a3836baa4e7d756ffe1e2879b415d3846bccd538c05b847785699aefde3e305decb600cd8fb0e7d8de5efc26971a6ad4e6d7a2d91474f1023a0ac4b78dc937da0ce607a45974d2cac1c33a2631ff7fe6144a3b2e5cf98b531a9627dea92c1dc82204d09db0439b6a11dd64b484e1263aa45fd9539b6020b55e3baece3986a8bffc1003406348f5c61265099ed43a766ee4f93f5f9c5abbc32a0fd3ac2b35b87f9ec26037d88275bd7dd0a54474995ee34ed3727f3f97c48db544b1980193a4b76a8a3ddab3591ce527f16d91882e67f0103b5cda53f7da54d489fc4ac08b6ab358a5a04aa9daa16219d50bd672a7cb804ed769d218807544e5993f1c27427104b349906a0b654df0bf69328afd3013fbe430155339c39f236df5557bf92f1ded7ff609a8502f49064ec3d1dbfb6c15d3a4c11a4f8acd12278cbf68acd5709463d12e3338a6eddb8c112f199645e23154a8e60879d2a654e3ed9296aa28f134168619691cd2c6b9e2eba4438381676173fc63c2588a3c5910dc149cf3760f0aa9fa9c3f5faa9162b0bf1aac9dd32b706a60ef53cbdb394b6b40222b5bc80eea82ba8958386672564cae3794f977871ab62337cf",
                exponent="010001",
                modulus="e30049201ec12937e7ce79d0f55d9c810e20acf52212aca1d3888949e0e4830aad88d804161230eb89d4d329cc83570fe257217d2119134048dd2ed167646975fc7d77136919a049ea74cf08ddd2b896890bb24a0ba18094a22baa351bf29ad96c66bbb1a598f2ca391749620e62d61c3561a7d3653ccc8892c7b99baaf76bf836e2991cb06d6bc0514568ff0d1ec8bb4b3d6984f5eaefb17d3ea2893722375d3ddb8e389a8eef7d7d198f8e687d6a513983df906099f9a2d23f4f9dec6f8ef2f11fc0a21fac45353b94e00486f5e17d386af42502d09db33cf0cf28310e049c07e88682aeeb00cb833c5174266e62407a57583f1f88b304b7c6e0c84bbe1c0fd423072d37a5bd0aacf764229e5c7cd02473460ba3645cd8e8ae144065bf02d0dd238593d8e230354f67e0b2f23012c23274f80e3ee31e35e2606a4a3f31d94ab755e6d163cff52cbb36b6d0cc67ffc512aeed1dce4d7a0d70ce82f2baba12e8d514dc92a056f994adfb17b5b9712bd5186f27a2fda1f7039c5df2c8587fdc62f5627580c13234b55be4df3056050e2d1ef3218f0dd66cb05265fe1acfb0989d8213f2c19d1735a7cf3fa65d88dad5af52dc2bba22b7abf46c3bc77b5091baab9e8f0ddc4d5e581037de91a9f8dcbc69309be29cc815cf19a20a7585b8b3073edf51fc9baeb3e509b97fa4ecfd621e0fd57bd61cac1b895c03248ff12bdbc57509250df3517e8a3fe1d776836b34ab352b973d932ef708b14f7418f9eceb1d87667e61e3e758649cb083f01b133d37ab2f5afa96d6c84bcacf4efc3851ad308c1e7d9113624fce29fab460ab9d2a48d92cdb281103a5250ad44cb2ff6e67ac670c02fdafb3e0f1353953d6d7d5646ca1568dea55275a050ec501b7c6250444f7219f1ba7521ba3b93d089727ca5f3bbe0d6c1300b423377004954c5628fdb65770b18ced5c9b23a4a5a6d6ef25fe01b4ce278de0bcc4ed86e28a0a68818ffa40970128cf2c38740e80037984428c1bd5113f40ff47512ee6f4e4d8f9b8e8e1b3040d2928d003bd1c1329dc885302fbce9fa81c23b4dc49c7c82d29b52957847898676c89aa5d32b5b0e1c0d5a2b79a19d67562f407f19425687971a957375879d90c5f57c857136c17106c9ab1b99d80e69c8c954ed386493368884b55c939b8d64d26f643e800c56f90c01079d7c534e3b2b7ae352cefd3016da55f6a85eb803b85e2304915fd2001f77c74e28746293c46e4f5f0fd49cf988aafd0026b8e7a3bab2da5cdce1ea26c2e29ec03f4807fac432662b2d6c060be1c7be0e5489de69d0a6e03a4b9117f9244b34a0f1ecba89884f781c6320412413a00c4980287409a2a78c2cd7e65cecebbe4ec1c28cac4dd95f6998e78fc6f1392384331c9436aa10e10e2bf8ad2c4eafbcf276aa7bae64b74428911b3269c749338b0fc5075ad",
            ),
            id="mod_vul_nagydani_5_pow_0x10001",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L156
        pytest.param(
            ModExpInput(
                base="ffffff",
                exponent="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffe000007d7d7d83828282348286877d7d827d407d797d7d7d7d7d7d7d7d7d7d7d5b00000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000021000000000000000000000000000000000000000000000000000000000000000cffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff4000007d7d",
                modulus="7d83828282348286877d7d82",
            ),
            id="mod_vul_marius_1_even",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L158
        pytest.param(
            ModExpInput(
                base="ffffffffffffffff76ffffffffffffff",
                exponent="1cffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c76ec7c7c7c7ffffffffffffffc7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7ffffffffffffc7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c76ec7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7c7ffff",
                modulus="ffffff3f000000000000000000000000",
            ),
            id="mod_vul_guido_1_even",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L160
        pytest.param(
            ModExpInput(
                base="e0060000a921212121212121ff000021",
                exponent="2b212121ffff1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f00feffff212121212121ffffffff1fe1e0e0e01e1f1f169f1f1f1f490afcefffffffffffffffff82828282828282828282828282828282828282828200ffff28ff2b212121ffff1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1fffffffffff0afceffffff7ffffffffff7c8282828282a1828282828282828282828282828200ffff28ff2b212121ffff1f1f1f1f1f1fd11f1f1f1f1f1f1f1f1f1f1fffffffffffffffff21212121212121fb2121212121ffff1f1f1f1f1f1f1f1fffaf",
                modulus="82828282828200ffff28ff2b21828200",
            ),
            id="mod_vul_guido_2_even",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L162
        pytest.param(
            ModExpInput(
                base="0193585a48e18aad777e9c1b54221a0f58140392e4f091cd5f42b2e8644a9384fbd58ae1edec2477ebf7edbf7c0a3f8bd21d1890ee87646feab3c47be716f842cc3da9b940af312dc54450a960e3fc0b86e56abddd154068e10571a96fff6259431632bc15695c6c8679057e66c2c25c127e97e64ee5de6ea1fc0a4a0e431343fed1daafa072c238a45841da86a9806680bc9f298411173210790359209cd454b5af7b4d5688b4403924e5f863d97e2c5349e1a04b54fcf385b1e9d7714bab8fbf5835f6ff9ed575e77dff7af5cbb641db5d537933bae1fa6555d6c12d6fb31ca27b57771f4aebfbe0bf95e8990c0108ffe7cbdaf370be52cf3ade594543af75ad9329d2d11a402270b5b9a6bf4b83307506e118fca4862749d04e916fc7a039f0d13f2a02e0eedb800199ec95df15b4ccd8669b52586879624d51219e72102fad810b5909b1e372ddf33888fb9beb09b416e4164966edbabd89e4a286be36277fc576ed519a15643dac602e92b63d0b9121f0491da5b16ef793a967f096d80b6c81ecaaffad7e3f06a4a5ac2796f1ed9f68e6a0fd5cf191f0c5c2eec338952ff8d31abc68bf760febeb57e088995ba1d7726a2fdd6d8ca28a181378b8b4ab699bfd4b696739bbf17a9eb2df6251143046137fdbbfacac312ebf67a67da9741b59600000000000",
                exponent="04",
                modulus="19a2917c61722b0713d3b00a2f0e1dd5aebbbe09615de424700eea3c3020fe6e9ea5de9fa1ace781df28b21f746d2ab61d0da496e08473c90ff7dfe25b43bcde76f4bafb82e0975bea75f5a0591dba80ba2fff80a07d8853bea5be13ab326ba70c57b153acc646151948d1cf061ca31b02d4719fac710e7c723ca44f5b1737824b7ccc74ba5bff980aabdbf267621cafc3d6dcc29d0ca9c16839a92ed34de136da7900aa3ee43d21aa57498981124357cf0ca9b86f9a8d3f9c604ca00c726e48f7a9945021ea6dfff92d6b2d6514693169ca133e993541bfa4c4c191de806aa80c48109bcfc9901eccfdeb2395ab75fe63c67de900829d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="mod_vul_guido_3_even",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L166
        pytest.param(
            ModExpInput(
                base="ffffffffffffffff",
                exponent="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                modulus="ffffffffffffffff",
            ),
            id="mod_vul_pawel_1_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L168
        pytest.param(
            ModExpInput(
                base="ffffffffffffffffffffffffffffffff",
                exponent="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                modulus="ffffffffffffffffffffffffffffffff",
            ),
            id="mod_vul_pawel_2_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L170
        pytest.param(
            ModExpInput(
                base="ffffffffffffffffffffffffffffffffffffffffffffffff",
                exponent="ffffffffffffffffffffffffffffffffffffffffff",
                modulus="ffffffffffffffffffffffffffffffffffffffffffffffff",
            ),
            id="mod_vul_pawel_3_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L172
        pytest.param(
            ModExpInput(
                base="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                exponent="ffffffffffffffffffffffff",
                modulus="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            ),
            id="mod_vul_pawel_4_exp_heavy",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L174
        pytest.param(
            ModExpInput(
                base="29356abadad68ad986c416de6f620bda0e1818b589e84f853a97391694d35496",
                exponent="ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc63254f",
                modulus="ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551",
            ),
            id="mod_vul_common_1360n1",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L176
        pytest.param(
            ModExpInput(
                base="d41afaeaea32f7409827761b68c41b6e535da4ede1f0800bfb4a6aed18394f6b",
                exponent="ffffffff00000001000000000000000000000000fffffffffffffffffffffffd",
                modulus="ffffffff00000001000000000000000000000000ffffffffffffffffffffffff",
            ),
            id="mod_vul_common_1360n2",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L178
        pytest.param(
            ModExpInput(
                base="1a5be8fae3b3fda9ea329494ae8689c04fae4978ecccfa6a6bfb9f04b25846c0",
                exponent="30644e72e131a029b85045b68181585d2833e84879b9709143e1f593efffffff",
                modulus="30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001",
            ),
            id="mod_vul_common_1349n1",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L182
        pytest.param(
            ModExpInput(
                base="0000000000000000000000000000000000000000000000000000000000000003",
                exponent="0000000001000000000000022000000000000000000000000000000000000000",
                modulus="0800000000000011000000000000000000000000000000000000000000000001",
            ),
            id="mod_vul_common_1152n1",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L184
        pytest.param(
            ModExpInput(
                base="1fb473dd1171cf88116aa77ab3612c2c7d2cf466cc2386cc456130e2727c70b4",
                exponent="0000000000000000000000000000000000000000000000000000000001000000",
                modulus="30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001",
            ),
            id="mod_vul_common_200n1",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L186
        pytest.param(
            ModExpInput(
                base="1951441010b2b95a6e47a6075066a50a036f5ba978c050f2821df86636c0facb",
                exponent="0000000000000000000000000000000000000000000000000000000000ffffff",
                modulus="30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001",
            ),
            id="mod_vul_common_200n2",
        ),
        # Ported from https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCases/ModexpVulnerability.cs#L188
        pytest.param(
            ModExpInput(
                base="288254ba43e713afbe36c9f03b54c00fae4c0a82df1cf165eb46a21c20a48ca2",
                exponent="0000000000000000000000000000000000000000000000000000000000ffffff",
                modulus="30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001",
            ),
            id="mod_vul_common_200n3",
        ),
    ],
)
def test_worst_modexp(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    mod_exp_input: ModExpInput,
    gas_benchmark_value: int,
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

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
        input=calldata,
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block filled with a precompile with fixed cost."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_worst_jumps(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
):
    """Test running a JUMP-intensive contract."""
    jumps_code = Op.JUMPDEST + Op.JUMP(Op.PUSH0)
    jumps_address = pre.deploy_contract(jumps_code)

    tx = Transaction(
        to=jumps_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_jumpi_fallthrough(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test running a JUMPI-intensive contract with fallthrough."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
def test_worst_jumpis(
    state_test: StateTestFiller,
    pre: Alloc,
    gas_benchmark_value: int,
):
    """Test running a JUMPI-intensive contract."""
    jumpi_code = Op.JUMPDEST + Op.JUMPI(Op.PUSH0, Op.NUMBER)
    jumpi_address = pre.deploy_contract(jumpi_code)

    tx = Transaction(
        to=jumpi_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_worst_jumpdests(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test running a JUMPDEST-intensive contract."""
    max_code_size = fork.max_code_size()

    # Create and deploy a contract with many JUMPDESTs
    code_suffix = Op.JUMP(Op.PUSH0)
    code_body = Op.JUMPDEST * (max_code_size - len(code_suffix))
    code = code_body + code_suffix
    jumpdests_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=jumpdests_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    fork: Fork,
    opcode_args: tuple[int, int],
    gas_benchmark_value: int,
):
    """
    Test running a block with as many binary instructions (takes two args, produces one value)
    as possible. The execution starts with two initial values on the stack, and the stack is
    balanced by the DUP2 instruction.
    """
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("opcode", [Op.ISZERO, Op.NOT])
def test_worst_unop(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    fork: Fork,
    gas_benchmark_value: int,
):
    """
    Test running a block with as many unary instructions (takes one arg, produces one value)
    as possible.
    """
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST + Op.PUSH0  # Start with the arg 0.
    code_suffix = Op.POP + Op.PUSH0 + Op.JUMP
    code_body_len = max_code_size - len(code_prefix) - len(code_suffix)
    code_body = opcode * code_body_len
    code = code_prefix + code_body + code_suffix
    assert len(code) == max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many TLOAD calls as possible."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
        value=start_key if not key_mut and val_mut else 0,
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many TSTORE calls as possible."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
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

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_value.to_bytes(32, byteorder="big"),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many BLOBHASH instructions as possible."""
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
        gas_limit=gas_benchmark_value,
        max_fee_per_blob_gas=max_fee_per_blob_gas,
        blob_versioned_hashes=blob_versioned_hashes,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
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

    input_value = initial_mod if not should_negate else neg(initial_mod)
    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=input_value.to_bytes(32, byteorder="big"),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many memory access instructions as possible."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
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

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        data=initial_mod.to_bytes(32, byteorder="big"),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    blockchain_test(
        pre=pre,
        post={},
        blocks=[Block(txs=[])],
        expected_benchmark_gas_used=0,
    )


@pytest.mark.valid_from("Cancun")
def test_amortized_bn128_pairings(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
):
    """Test running a block with as many BN128 pairings as possible."""
    base_cost = 45_000
    pairing_cost = 34_000
    size_per_pairing = 192

    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    # This is a theoretical maximum number of pairings that can be done in a block.
    # It is only used for an upper bound for calculating the optimal number of pairings below.
    maximum_number_of_pairings = (gas_benchmark_value - base_cost) // pairing_cost

    # Discover the optimal number of pairings balancing two dimensions:
    # 1. Amortize the precompile base cost as much as possible.
    # 2. The cost of the memory expansion.
    max_pairings = 0
    optimal_per_call_num_pairings = 0
    for i in range(1, maximum_number_of_pairings + 1):
        # We'll pass all pairing arguments via calldata.
        available_gas_after_intrinsic = gas_benchmark_value - intrinsic_gas_calculator(
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
        gas_limit=gas_benchmark_value,
        data=_generate_bn128_pairs(optimal_per_call_num_pairings, 42),
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many CALLDATALOAD as possible."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many SWAP as possible."""
    max_code_size = fork.max_code_size()

    code_prefix = Op.JUMPDEST + Op.PUSH0 * opcode.min_stack_height
    code_suffix = Op.PUSH0 + Op.JUMP
    opcode_sequence = opcode * (max_code_size - len(code_prefix) - len(code_suffix))
    code = code_prefix + opcode_sequence + code_suffix
    assert len(code) <= max_code_size

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many DUP as possible."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many PUSH as possible."""
    op = opcode[1] if opcode.has_data_portion() else opcode
    opcode_sequence = op * fork.max_stack_height()
    target_contract_address = pre.deploy_contract(code=opcode_sequence)

    calldata = Bytecode()
    attack_block = Op.POP(Op.STATICCALL(Op.GAS, target_contract_address, 0, 0, 0, 0))

    code = code_loop_precompile_call(calldata, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=code_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
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
    gas_benchmark_value: int,
):
    """Test running a block with as many RETURN or REVERT as possible."""
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
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )
