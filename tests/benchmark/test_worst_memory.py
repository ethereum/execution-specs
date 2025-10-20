"""
Tests that benchmark EVMs in the worst-case memory opcodes.
"""

from enum import auto

import pytest

from ethereum_test_base_types.base_types import Bytes
from ethereum_test_benchmark.benchmark_code_generator import JumpLoopGenerator
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Transaction,
)
from ethereum_test_vm import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"


class CallDataOrigin:
    """Enum for calldata origins."""

    TRANSACTION = auto()
    CALL = auto()


@pytest.mark.parametrize(
    "origin",
    [
        pytest.param(CallDataOrigin.TRANSACTION, id="transaction"),
        pytest.param(CallDataOrigin.CALL, id="call"),
    ],
)
@pytest.mark.parametrize(
    "size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(100, id="100 bytes"),
        pytest.param(10 * 1024, id="10KiB"),
        pytest.param(1024 * 1024, id="1MiB"),
    ],
)
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "non_zero_data",
    [
        True,
        False,
    ],
)
def test_worst_calldatacopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    origin: CallDataOrigin,
    size: int,
    fixed_src_dst: bool,
    non_zero_data: bool,
    gas_benchmark_value: int,
) -> None:
    """Test running a block filled with CALLDATACOPY executions."""
    if size == 0 and non_zero_data:
        pytest.skip("Non-zero data with size 0 is not applicable.")

    # If `non_zero_data` is True, we fill the calldata with deterministic
    # random data. Note that if `size == 0` and `non_zero_data` is a skipped
    # case.
    data = Bytes([i % 256 for i in range(size)]) if non_zero_data else Bytes()

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    min_gas = intrinsic_gas_calculator(calldata=data)
    if min_gas > gas_benchmark_value:
        pytest.skip("Minimum gas required for calldata ({min_gas}) is greater than the gas limit")

    # We create the contract that will be doing the CALLDATACOPY multiple
    # times.
    #
    # If `non_zero_data` is True, we leverage CALLDATASIZE for the copy
    # length. Otherwise, since we
    # don't send zero data explicitly via calldata, PUSH the target size and
    # use DUP1 to copy it.
    setup = Bytecode() if non_zero_data or size == 0 else Op.PUSH3(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CALLDATACOPY(
        src_dst, src_dst, Op.CALLDATASIZE if non_zero_data or size == 0 else Op.DUP1
    )

    code_address = JumpLoopGenerator(setup=setup, attack_block=attack_block).deploy_contracts(
        pre=pre, fork=fork
    )

    tx_target = code_address

    # If the origin is CALL, we need to create a contract that will call the
    # target contract with the calldata.
    if origin == CallDataOrigin.CALL:
        # If `non_zero_data` is False we leverage just using zeroed memory.
        # Otherwise, we copy the calldata received from the transaction.
        setup = (
            Op.CALLDATACOPY(Op.PUSH0, Op.PUSH0, Op.CALLDATASIZE) if non_zero_data else Bytecode()
        ) + Op.JUMPDEST
        arg_size = Op.CALLDATASIZE if non_zero_data else size
        attack_block = Op.STATICCALL(
            address=code_address, args_offset=Op.PUSH0, args_size=arg_size
        )

        tx_target = JumpLoopGenerator(setup=setup, attack_block=attack_block).deploy_contracts(
            pre=pre, fork=fork
        )

    tx = Transaction(
        to=tx_target,
        gas_limit=gas_benchmark_value,
        data=data,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


@pytest.mark.parametrize(
    "max_code_size_ratio",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(0.25, id="0.25x max code size"),
        pytest.param(0.50, id="0.50x max code size"),
        pytest.param(0.75, id="0.75x max code size"),
        pytest.param(1.00, id="max code size"),
    ],
)
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
def test_worst_codecopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    max_code_size_ratio: float,
    fixed_src_dst: bool,
) -> None:
    """Test running a block filled with CODECOPY executions."""
    max_code_size = fork.max_code_size()

    size = int(max_code_size * max_code_size_ratio)

    setup = Op.PUSH32(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CODECOPY(src_dst, src_dst, Op.DUP1)  # DUP1 copies size.

    code = JumpLoopGenerator(setup=setup, attack_block=attack_block).generate_repeated_code(
        repeated_code=attack_block, setup=setup, fork=fork
    )

    # The code generated above is not guaranteed to be of max_code_size, so
    # we pad it since
    # a test parameter targets CODECOPYing a contract with max code size.
    # Padded bytecode values
    # are not relevant.
    code += Op.INVALID * (max_code_size - len(code))
    assert len(code) == max_code_size, (
        f"Code size {len(code)} is not equal to max code size {max_code_size}."
    )

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


@pytest.mark.parametrize(
    "size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(100, id="100 bytes"),
        pytest.param(10 * 1024, id="10KiB"),
        pytest.param(1024 * 1024, id="1MiB"),
    ],
)
@pytest.mark.parametrize(
    "fixed_dst",
    [
        True,
        False,
    ],
)
def test_worst_returndatacopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    size: int,
    fixed_dst: bool,
) -> None:
    """Test running a block filled with RETURNDATACOPY executions."""
    # Create the contract that will RETURN the data that will be used for
    # RETURNDATACOPY.
    # Random-ish data is injected at different points in memory to avoid
    # making the content
    # predictable. If `size` is 0, this helper contract won't be used.
    code = (
        Op.MSTORE8(0, Op.GAS)
        + Op.MSTORE8(size // 2, Op.GAS)
        + Op.MSTORE8(size - 1, Op.GAS)
        + Op.RETURN(0, size)
    )
    helper_contract = pre.deploy_contract(code=code)

    returndata_gen = Op.STATICCALL(address=helper_contract) if size > 0 else Bytecode()
    dst = 0 if fixed_dst else Op.MOD(Op.GAS, 7)

    # We create the contract that will be doing the RETURNDATACOPY multiple
    # times.
    returndata_gen = Op.STATICCALL(address=helper_contract) if size > 0 else Bytecode()
    attack_block = Op.RETURNDATACOPY(dst, Op.PUSH0, Op.RETURNDATASIZE)

    # The attack loop is constructed as:
    # ```
    # JUMPDEST(#)
    # RETURNDATACOPY(...)
    # RETURNDATACOPY(...)
    # ...
    # STATICCALL(address=helper_contract)
    # JUMP(#)
    # ```
    # The goal is that once per (big) loop iteration, the helper contract is
    # called to
    # generate fresh returndata to continue calling RETURNDATACOPY.

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=returndata_gen, attack_block=attack_block, cleanup=returndata_gen
        ),
    )


@pytest.mark.parametrize(
    "size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(100, id="100 bytes"),
        pytest.param(10 * 1024, id="10KiB"),
        pytest.param(1024 * 1024, id="1MiB"),
    ],
)
@pytest.mark.parametrize(
    "fixed_src_dst",
    [
        True,
        False,
    ],
)
def test_worst_mcopy(
    benchmark_test: BenchmarkTestFiller,
    size: int,
    fixed_src_dst: bool,
) -> None:
    """Test running a block filled with MCOPY executions."""
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.MCOPY(src_dst, src_dst, size)

    mem_touch = (
        Op.MSTORE8(0, Op.GAS) + Op.MSTORE8(size // 2, Op.GAS) + Op.MSTORE8(size - 1, Op.GAS)
        if size > 0
        else Bytecode()
    )
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=mem_touch, attack_block=attack_block, cleanup=mem_touch
        ),
    )
