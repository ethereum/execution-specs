"""
abstract: Tests that benchmark EVMs in the worst-case memory opcodes.
    Tests that benchmark EVMs in the worst-case memory opcodes.

Tests that benchmark EVMs in the worst-case memory opcodes.
"""

import pytest

from ethereum_test_base_types.base_types import Bytes
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Alloc,
    Bytecode,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import code_loop_precompile_call

REFERENCE_SPEC_GIT_PATH = "TODO"
REFERENCE_SPEC_VERSION = "TODO"


class CallDataOrigin:
    """Enum for calldata origins."""

    TRANSACTION = 1
    CALL = 2


@pytest.mark.valid_from("Cancun")
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
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    origin: CallDataOrigin,
    size: int,
    fixed_src_dst: bool,
    non_zero_data: bool,
):
    """Test running a block filled with CALLDATACOPY executions."""
    env = Environment()

    if size == 0 and non_zero_data:
        pytest.skip("Non-zero data with size 0 is not applicable.")

    # We create the contract that will be doing the CALLDATACOPY multiple times.
    #
    # If `non_zero_data` is True, we leverage CALLDATASIZE for the copy length. Otherwise, since we
    # don't send zero data explicitly via calldata, PUSH the target size and use DUP1 to copy it.
    prefix = Bytecode() if non_zero_data or size == 0 else Op.PUSH3(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CALLDATACOPY(
        src_dst, src_dst, Op.CALLDATASIZE if non_zero_data or size == 0 else Op.DUP1
    )
    code = code_loop_precompile_call(prefix, attack_block, fork)
    code_address = pre.deploy_contract(code=code)

    tx_target = code_address

    # If the origin is CALL, we need to create a contract that will call the target contract with
    # the calldata.
    if origin == CallDataOrigin.CALL:
        # If `non_zero_data` is False we leverage just using zeroed memory. Otherwise, we
        # copy the calldata received from the transaction.
        prefix = (
            Op.CALLDATACOPY(Op.PUSH0, Op.PUSH0, Op.CALLDATASIZE) if non_zero_data else Bytecode()
        )
        arg_size = Op.CALLDATASIZE if non_zero_data else size
        code = prefix + Op.STATICCALL(
            address=code_address, args_offset=Op.PUSH0, args_size=arg_size
        )
        tx_target = pre.deploy_contract(code=code)

    # If `non_zero_data` is True, we fill the calldata with deterministic random data.
    # Note that if `size == 0` and `non_zero_data` is a skipped case.
    data = Bytes([i % 256 for i in range(size)]) if non_zero_data else Bytes()

    tx = Transaction(
        to=tx_target,
        gas_limit=env.gas_limit,
        data=data,
        sender=pre.fund_eoa(),
    )

    state_test(
        genesis_environment=env,
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.valid_from("Cancun")
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
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    max_code_size_ratio: float,
    fixed_src_dst: bool,
):
    """Test running a block filled with CODECOPY executions."""
    env = Environment()
    max_code_size = fork.max_code_size()

    size = int(max_code_size * max_code_size_ratio)

    code_prefix = Op.PUSH32(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CODECOPY(src_dst, src_dst, Op.DUP1)  # DUP1 copies size.
    code = code_loop_precompile_call(code_prefix, attack_block, fork)

    # The code generated above is not guaranteed to be of max_code_size, so we pad it since
    # a test parameter targets CODECOPYing a contract with max code size. Padded bytecode values
    # are not relevant.
    code = code + Op.INVALID * (max_code_size - len(code))
    assert len(code) == max_code_size, (
        f"Code size {len(code)} is not equal to max code size {max_code_size}."
    )

    tx = Transaction(
        to=pre.deploy_contract(code=code),
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
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    size: int,
    fixed_dst: bool,
):
    """Test running a block filled with RETURNDATACOPY executions."""
    env = Environment()
    max_code_size = fork.max_code_size()

    # Create the contract that will RETURN the data that will be used for RETURNDATACOPY.
    # Random-ish data is injected at different points in memory to avoid making the content
    # predictable. If `size` is 0, this helper contract won't be used.
    code = (
        Op.MSTORE8(0, Op.GAS)
        + Op.MSTORE8(size // 2, Op.GAS)
        + Op.MSTORE8(size - 1, Op.GAS)
        + Op.RETURN(0, size)
    )
    helper_contract = pre.deploy_contract(code=code)

    # We create the contract that will be doing the RETURNDATACOPY multiple times.
    returndata_gen = Op.STATICCALL(address=helper_contract) if size > 0 else Bytecode()
    dst = 0 if fixed_dst else Op.MOD(Op.GAS, 7)
    attack_iter = Op.RETURNDATACOPY(dst, Op.PUSH0, Op.RETURNDATASIZE)

    jumpdest = Op.JUMPDEST
    jump_back = Op.JUMP(len(returndata_gen))
    # The attack loop is constructed as:
    # ```
    # JUMPDEST(#)
    # RETURNDATACOPY(...)
    # RETURNDATACOPY(...)
    # ...
    # STATICCALL(address=helper_contract)
    # JUMP(#)
    # ```
    # The goal is that once per (big) loop iteration, the helper contract is called to
    # generate fresh returndata to continue calling RETURNDATACOPY.
    max_iters_loop = (
        max_code_size - 2 * len(returndata_gen) - len(jumpdest) - len(jump_back)
    ) // len(attack_iter)
    code = (
        returndata_gen
        + jumpdest
        + sum([attack_iter] * max_iters_loop)
        + returndata_gen
        + jump_back
    )
    assert len(code) <= max_code_size, (
        f"Code size {len(code)} is not equal to max code size {max_code_size}."
    )

    tx = Transaction(
        to=pre.deploy_contract(code=code),
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
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    size: int,
    fixed_src_dst: bool,
):
    """Test running a block filled with MCOPY executions."""
    env = Environment()
    max_code_size = fork.max_code_size()

    mem_touch = (
        Op.MSTORE8(0, Op.GAS) + Op.MSTORE8(size // 2, Op.GAS) + Op.MSTORE8(size - 1, Op.GAS)
        if size > 0
        else Bytecode()
    )
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.MCOPY(src_dst, src_dst, size)

    jumpdest = Op.JUMPDEST
    jump_back = Op.JUMP(len(mem_touch))
    max_iters_loop = (max_code_size - 2 * len(mem_touch) - len(jumpdest) - len(jump_back)) // len(
        attack_block
    )
    code = mem_touch + jumpdest + sum([attack_block] * max_iters_loop) + mem_touch + jump_back
    assert len(code) <= max_code_size, (
        f"Code size {len(code)} is not equal to max code size {max_code_size}."
    )

    tx = Transaction(
        to=pre.deploy_contract(code=code),
        gas_limit=env.gas_limit,
        sender=pre.fund_eoa(),
    )

    state_test(
        genesis_environment=env,
        pre=pre,
        post={},
        tx=tx,
    )
