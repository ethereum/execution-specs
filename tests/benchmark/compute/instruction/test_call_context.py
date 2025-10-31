"""Benchmark call frame context instructions."""

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
    Transaction,
)

from tests.benchmark.compute.helpers import (
    CallDataOrigin,
    ReturnDataStyle,
)


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
        code_generator=ExtCallGenerator(attack_block=opcode),
    )


@pytest.mark.parametrize("calldata_length", [0, 1_000, 10_000])
def test_calldatasize(
    benchmark_test: BenchmarkTestFiller,
    calldata_length: int,
) -> None:
    """Benchmark CALLDATASIZE instruction."""
    benchmark_test(
        code_generator=JumpLoopGenerator(
            attack_block=Op.POP(Op.CALLDATASIZE),
            tx_kwargs={"data": b"\x00" * calldata_length},
        ),
    )


@pytest.mark.parametrize("non_zero_value", [True, False])
@pytest.mark.parametrize("from_origin", [True, False])
def test_callvalue(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    non_zero_value: bool,
    from_origin: bool,
) -> None:
    """
    Benchmark CALLVALUE instruction.

    - non_zero_value: whether opcode must return non-zero value.
    - from_origin: whether the call frame is the immediate one
    from the transaction or a previous CALL.
    """
    code_address = JumpLoopGenerator(
        attack_block=Op.POP(Op.CALLVALUE)
    ).deploy_contracts(pre=pre, fork=fork)

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
        value=1 if non_zero_value and from_origin else 0,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"\x00", id="zero-loop"),
        pytest.param(b"\x00" * 31 + b"\x20", id="one-loop"),
    ],
)
def test_calldataload(
    benchmark_test: BenchmarkTestFiller,
    calldata: bytes,
) -> None:
    """Benchmark CALLDATALOAD instruction."""
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH0,
            attack_block=Op.CALLDATALOAD,
            tx_kwargs={"data": calldata},
        ),
    )


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
def test_calldatacopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    origin: CallDataOrigin,
    size: int,
    fixed_src_dst: bool,
    non_zero_data: bool,
    gas_benchmark_value: int,
) -> None:
    """Benchmark CALLDATACOPY instruction."""
    if size == 0 and non_zero_data:
        pytest.skip("Non-zero data with size 0 is not applicable.")

    # If `non_zero_data` is True, we fill the calldata with deterministic
    # random data. Note that if `size == 0` and `non_zero_data` is a skipped
    # case.
    data = Bytes([i % 256 for i in range(size)]) if non_zero_data else Bytes()

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    min_gas = intrinsic_gas_calculator(calldata=data)
    if min_gas > gas_benchmark_value:
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
    setup = Bytecode() if non_zero_data or size == 0 else Op.PUSH3(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CALLDATACOPY(
        src_dst,
        src_dst,
        Op.CALLDATASIZE if non_zero_data or size == 0 else Op.DUP1,
    )

    code_address = JumpLoopGenerator(
        setup=setup, attack_block=attack_block
    ).deploy_contracts(pre=pre, fork=fork)

    tx_target = code_address

    # If the origin is CALL, we need to create a contract that will call the
    # target contract with the calldata.
    if origin == CallDataOrigin.CALL:
        # If `non_zero_data` is False we leverage just using zeroed memory.
        # Otherwise, we copy the calldata received from the transaction.
        setup = (
            Op.CALLDATACOPY(Op.PUSH0, Op.PUSH0, Op.CALLDATASIZE)
            if non_zero_data
            else Bytecode()
        ) + Op.JUMPDEST
        arg_size = Op.CALLDATASIZE if non_zero_data else size
        attack_block = Op.STATICCALL(
            address=code_address, args_offset=Op.PUSH0, args_size=arg_size
        )

        tx_target = JumpLoopGenerator(
            setup=setup, attack_block=attack_block
        ).deploy_contracts(pre=pre, fork=fork)

    tx = Transaction(
        to=tx_target,
        gas_limit=gas_benchmark_value,
        data=data,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)


@pytest.mark.parametrize(
    "return_data_style",
    [
        ReturnDataStyle.RETURN,
        ReturnDataStyle.REVERT,
        ReturnDataStyle.IDENTITY,
    ],
)
@pytest.mark.parametrize("returned_size", [1, 0])
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
        code_generator=JumpLoopGenerator(
            setup=setup, attack_block=Op.POP(Op.RETURNDATASIZE)
        ),
    )


def test_returndatasize_zero(
    benchmark_test: BenchmarkTestFiller,
) -> None:
    """Benchmark RETURNDATASIZE instruction with zero buffer."""
    benchmark_test(
        code_generator=ExtCallGenerator(attack_block=Op.RETURNDATASIZE),
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
    "fixed_dst",
    [
        True,
        False,
    ],
)
def test_returndatacopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    size: int,
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
        + Op.MSTORE8(size // 2, Op.GAS)
        + Op.MSTORE8(size - 1, Op.GAS)
        + Op.RETURN(0, size)
    )
    helper_contract = pre.deploy_contract(code=code)

    returndata_gen = (
        Op.STATICCALL(address=helper_contract) if size > 0 else Bytecode()
    )
    dst = 0 if fixed_dst else Op.MOD(Op.GAS, 7)

    # We create the contract that will be doing the RETURNDATACOPY multiple
    # times.
    returndata_gen = (
        Op.STATICCALL(address=helper_contract) if size > 0 else Bytecode()
    )
    attack_block = Op.RETURNDATACOPY(dst, Op.PUSH0, Op.RETURNDATASIZE)

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=returndata_gen,
            attack_block=attack_block,
            cleanup=returndata_gen,
        ),
    )
