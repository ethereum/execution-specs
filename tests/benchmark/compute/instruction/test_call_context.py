"""
Benchmark call frame context instructions.

Supported Opcodes:
- ADDRESS
- CALLER
- CALLVALUE
- CALLDATASIZE
- CALLDATACOPY
- CALLDATALOAD
- RETURNDATASIZE
- RETURNDATACOPY
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Bytes,
    ExtCallGenerator,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import (
    ReturnDataStyle,
)


@pytest.mark.repricing
@pytest.mark.parametrize(
    "opcode",
    [
        Op.ADDRESS,
        Op.CALLER,
    ],
)
def test_call_frame_context_ops(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark call zero-parameter instructions."""
    benchmark_test(
        target_opcode=opcode,
        code_generator=ExtCallGenerator(attack_block=opcode),
    )


@pytest.mark.repricing(calldata_size=1024)
@pytest.mark.parametrize("calldata_size", [0, 32, 256, 1024])
@pytest.mark.parametrize("zero_data", [True, False])
def test_calldatasize(
    benchmark_test: BenchmarkTestFiller, calldata_size: int, zero_data: bool
) -> None:
    """Benchmark CALLDATASIZE instruction."""
    calldata = (
        b"\x00" * calldata_size
        if zero_data
        else Bytes([i % 256 for i in range(calldata_size)])
    )

    benchmark_test(
        target_opcode=Op.CALLDATASIZE,
        code_generator=ExtCallGenerator(
            attack_block=Op.CALLDATASIZE,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing(non_zero_value=True)
@pytest.mark.parametrize("non_zero_value", [True, False])
def test_callvalue_from_origin(
    benchmark_test: BenchmarkTestFiller,
    non_zero_value: bool,
) -> None:
    """
    Benchmark CALLVALUE instruction from origin.
    """
    benchmark_test(
        target_opcode=Op.CALLVALUE,
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(Op.CALLVALUE),
            tx_kwargs={"value": int(non_zero_value)},
        ),
    )


@pytest.mark.parametrize("non_zero_value", [True, False])
def test_callvalue_from_call(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    non_zero_value: bool,
    fork: Fork,
) -> None:
    """
    Benchmark CALLVALUE instruction from call.
    """
    code_address = pre.deploy_contract(
        code=Op.CALLVALUE * fork.max_stack_height()
    )
    benchmark_test(
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(
                Op.CALL(
                    address=code_address,
                    value=int(non_zero_value),
                    args_offset=Op.PUSH0,
                    args_size=Op.PUSH0,
                    ret_offset=Op.PUSH0,
                    ret_size=Op.PUSH0,
                )
            ),
            tx_kwargs={"value": 10**18},
        ),
    )


@pytest.mark.parametrize("calldata_size", [0, 32, 256, 1024])
@pytest.mark.parametrize("zero_data", [True, False])
def test_calldataload(
    benchmark_test: BenchmarkTestFiller, calldata_size: int, zero_data: bool
) -> None:
    """Benchmark CALLDATALOAD instruction."""
    calldata = (
        b"\x00" * calldata_size
        if zero_data
        else Bytes([i % 256 for i in range(calldata_size)])
    )
    benchmark_test(
        target_opcode=Op.CALLDATALOAD,
        code_generator=JumpLoopGenerator(
            attack_block=Op.CALLDATALOAD(Op.PUSH0),
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing(size=0, fixed_src_dst=True, non_zero_data=False)
@pytest.mark.parametrize(
    "mem_size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(32, id="32 bytes"),
        pytest.param(256, id="256 bytes"),
        pytest.param(1024, id="1KiB"),
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
    "calldata_size",
    [0, 32, 256, 1024],
)
def test_calldatacopy_from_origin(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    mem_size: int,
    fixed_src_dst: bool,
    calldata_size: int,
    tx_gas_limit: int,
) -> None:
    """Benchmark CALLDATACOPY instruction."""
    # Generate calldata of the specified size with deterministic data.
    data = Bytes([i % 256 for i in range(calldata_size)])

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    min_gas = intrinsic_gas_calculator(calldata=data)
    if min_gas > tx_gas_limit:
        pytest.skip(
            f"Minimum gas required for calldata ({min_gas}) is greater "
            "than the gas limit"
        )

    # Setup pushes the memory size to copy onto the stack.
    # The attack block uses DUP1 to reuse this value for the copy length.
    setup = Op.PUSH3(mem_size) if mem_size > 0 else Op.PUSH0
    src_dst = 0 if fixed_src_dst else Op.AND(Op.GAS, 7)
    attack_block = Op.CALLDATACOPY(
        src_dst,
        src_dst,
        Op.CALLDATASIZE,
    )

    benchmark_test(
        target_opcode=Op.CALLDATACOPY,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            tx_kwargs={"data": data},
        ),
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
@pytest.mark.parametrize(
    "calldata_size",
    [0, 32, 256, 1024],
)
def test_calldatacopy_from_call(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    calldata_size: int,
    fixed_src_dst: bool,
    non_zero_data: bool,
    tx_gas_limit: int,
) -> None:
    """Benchmark CALLDATACOPY instruction."""
    if calldata_size == 0 and non_zero_data:
        pytest.skip("Non-zero data with size 0 is not applicable.")

    # If `non_zero_data` is True, we fill the calldata with deterministic
    # random data. Note that if `size == 0` and `non_zero_data` is a skipped
    # case.
    data = (
        Bytes([i % 256 for i in range(calldata_size)])
        if non_zero_data
        else Bytes()
    )

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    min_gas = intrinsic_gas_calculator(calldata=data)
    if min_gas > tx_gas_limit:
        pytest.skip(
            "Minimum gas required for calldata ({min_gas}) is greater "
            "than the gas limit"
        )

    # We create the contract that will be doing the CALLDATACOPY multiple
    # times.
    #
    # If `non_zero_data` is True, we leverage CALLDATASIZE for the copy
    # length. Otherwise, since we
    # don't send zero data explicitly via calldata, PUSH the target size and
    # use DUP1 to copy it.
    setup = (
        Bytecode()
        if non_zero_data or calldata_size == 0
        else Op.PUSH3(calldata_size)
    )
    src_dst = 0 if fixed_src_dst else Op.AND(Op.GAS, 7)
    attack_block = Op.CALLDATACOPY(
        src_dst,
        src_dst,
        Op.CALLDATASIZE if non_zero_data or calldata_size == 0 else Op.DUP1,
    )

    benchmark_test(
        target_opcode=Op.CALLDATACOPY,
        code_generator=ExtCallGenerator(
            setup=setup,
            attack_block=attack_block,
            tx_kwargs={"data": data},
        ),
    )


@pytest.mark.repricing(
    returned_size=0,
    return_data_style=ReturnDataStyle.IDENTITY,
)
@pytest.mark.parametrize(
    "return_data_style",
    [
        ReturnDataStyle.RETURN,
        ReturnDataStyle.REVERT,
        ReturnDataStyle.IDENTITY,
    ],
)
@pytest.mark.parametrize("returned_size", [0, 32, 256, 1024])
def test_returndatasize_nonzero(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    returned_size: int,
    return_data_style: ReturnDataStyle,
) -> None:
    """
    Benchmark RETURNDATASIZE instruction with non-zero buffer.

    - returned_size: the size of the returned data buffer.
    - return_data_style: how returned data is produced for the opcode caller.
    """
    setup = Bytecode()
    if return_data_style != ReturnDataStyle.IDENTITY:
        setup += Op.STATICCALL(
            address=pre.deploy_contract(
                code=Op.REVERT(0, returned_size)
                if return_data_style == ReturnDataStyle.REVERT
                else Op.RETURN(0, returned_size)
            )
        )
    else:
        setup += Op.MSTORE8(0, 1) + Op.STATICCALL(
            address=0x04,  # Identity precompile
            args_size=returned_size,
        )

    benchmark_test(
        target_opcode=Op.RETURNDATASIZE,
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=Op.POP(Op.RETURNDATASIZE)
        ),
    )


@pytest.mark.repricing
def test_returndatasize_zero(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark RETURNDATASIZE instruction with zero buffer."""
    benchmark_test(
        target_opcode=Op.RETURNDATASIZE,
        code_generator=ExtCallGenerator(attack_block=Op.RETURNDATASIZE),
    )


@pytest.mark.repricing(size=0, fixed_dst=True)
@pytest.mark.parametrize("mem_size", [0, 32, 256, 1024])
@pytest.mark.parametrize(
    "return_size",
    [
        pytest.param(0, id="0 bytes"),
        pytest.param(32, id="32 bytes"),
        pytest.param(256, id="256 bytes"),
        pytest.param(1024, id="1024 bytes"),
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
def test_returndatacopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    mem_size: int,
    return_size: int,
    fixed_dst: bool,
) -> None:
    """Benchmark RETURNDATACOPY instruction."""
    # Create the contract that will RETURN the data that will be used for
    # RETURNDATACOPY.
    # Random-ish data is injected at different points in memory to avoid
    # making the content
    # predictable. If `size` is 0, this helper contract won't be used.
    code = (
        Op.MSTORE8(0, Op.GAS)
        + Op.MSTORE8(return_size // 2, Op.GAS)
        + Op.MSTORE8(return_size - 1, Op.GAS)
        + Op.RETURN(0, return_size)
    )
    helper_contract = pre.deploy_contract(code=code)

    setup = Bytecode()
    setup += Op.MSTORE8(mem_size - 1, 0xFF) if mem_size > 0 else Bytecode()
    setup += (
        Op.STATICCALL(address=helper_contract)
        if return_size > 0
        else Bytecode()
    )

    cleanup = (
        Op.STATICCALL(address=helper_contract)
        if return_size > 0
        else Bytecode()
    )
    dst = 0 if fixed_dst else Op.MOD(Op.GAS, 7)

    attack_block = Op.RETURNDATACOPY(dst, Op.PUSH0, Op.RETURNDATASIZE)

    benchmark_test(
        target_opcode=Op.RETURNDATACOPY,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            cleanup=cleanup,
        ),
    )
