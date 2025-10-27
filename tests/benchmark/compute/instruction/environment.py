"""Benchmark environmental instructions."""

import math
from typing import Any, Dict

import pytest
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Environment,
    Hash,
    Transaction,
    While,
    compute_create2_address,
)
from ethereum_test_types import TransactionType, add_kzg_version
from ethereum_test_vm import Opcodes as Op

from tests.benchmark.compute.helpers import (
    XOR_TABLE,
    CallDataOrigin,
    ReturnDataStyle,
)
from tests.benchmark.test_worst_compute import (
    BenchmarkTestFiller,
    ExtCallGenerator,
    JumpLoopGenerator,
)
from tests.cancun.eip4844_blobs.spec import Spec as BlobsSpec

# Environmental instructions:
# ADDRESS, BALANCE, ORIGIN, CALLER, CALLVALUE
# CALLDATALOAD, CALLDATASIZE, CALLDATACOPY, CODESIZE, CODECOPY, GASPRICE,
# EXTCODESIZE, EXTCODECOPY, RETURNDATASIZE, RETURNDATACOPY, EXTCODEHASH,
# SELFBALANCE, BASEFEE, BLOBHASH, BLOBBASEFEE


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
        Op.EXTCODECOPY,
    ],
)
def test_extcode_ops(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark a block execution where a single opcode execution.
    """
    # The attack gas limit is the gas limit which the target tx will use The
    # test will scale the block gas limit to setup the contracts accordingly to
    # be able to pay for the contract deposit. This has to take into account
    # the 200 gas per byte, but also the quadratic memory expansion costs which
    # have to be paid each time the memory is being setup
    attack_gas_limit = gas_benchmark_value
    max_contract_size = fork.max_code_size()

    gas_costs = fork.gas_costs()

    # Calculate the absolute minimum gas costs to deploy the contract This does
    # not take into account setting up the actual memory (using KECCAK256 and
    # XOR) so the actual costs of deploying the contract is higher
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    memory_gas_minimum = memory_expansion_gas_calculator(
        new_bytes=len(bytes(max_contract_size))
    )
    code_deposit_gas_minimum = (
        fork.gas_costs().G_CODE_DEPOSIT_BYTE * max_contract_size
        + memory_gas_minimum
    )

    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # Calculate the loop cost of the attacker to query one address
    loop_cost = (
        gas_costs.G_KECCAK_256  # KECCAK static cost
        + math.ceil(85 / 32) * gas_costs.G_KECCAK_256_WORD  # KECCAK dynamic
        # cost for CREATE2
        + gas_costs.G_VERY_LOW * 3  # ~MSTOREs+ADDs
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # Opcode cost
        + 30  # ~Gluing opcodes
    )
    # Calculate the number of contracts to be targeted
    num_contracts = (
        # Base available gas = GAS_LIMIT - intrinsic - (out of loop MSTOREs)
        attack_gas_limit - intrinsic_gas_cost_calc() - gas_costs.G_VERY_LOW * 4
    ) // loop_cost

    # Set the block gas limit to a relative high value to ensure the code
    # deposit tx fits in the block (there is enough gas available in the block
    # to execute this)
    minimum_gas_limit = code_deposit_gas_minimum * 2 * num_contracts
    if env.gas_limit < minimum_gas_limit:
        raise Exception(
            f"`BENCHMARKING_MAX_GAS` ({env.gas_limit}) is no longer enough to"
            f" support this test, which requires {minimum_gas_limit} gas for "
            "its setup. Update the value or consider optimizing gas usage "
            "during the setup phase of this test."
        )

    # The initcode will take its address as a starting point to the input to
    # the keccak hash function. It will reuse the output of the hash function
    # in a loop to create a large amount of seemingly random code, until it
    # reaches the maximum contract size.
    initcode = (
        Op.MSTORE(0, Op.ADDRESS)
        + While(
            body=(
                Op.SHA3(Op.SUB(Op.MSIZE, 32), 32)
                # Use a xor table to avoid having to call the "expensive" sha3
                # opcode as much
                + sum(
                    (
                        Op.PUSH32[xor_value]
                        + Op.XOR
                        + Op.DUP1
                        + Op.MSIZE
                        + Op.MSTORE
                    )
                    for xor_value in XOR_TABLE
                )
                + Op.POP
            ),
            condition=Op.LT(Op.MSIZE, max_contract_size),
        )
        # Despite the whole contract has random bytecode, we make the first
        # opcode be a STOP so CALL-like attacks return as soon as possible,
        # while EXTCODE(HASH|SIZE) work as intended.
        + Op.MSTORE8(0, 0x00)
        + Op.RETURN(0, max_contract_size)
    )
    initcode_address = pre.deploy_contract(code=initcode)

    # The factory contract will simply use the initcode that is already
    # deployed, and create a new contract and return its address if successful.
    factory_code = (
        Op.EXTCODECOPY(
            address=initcode_address,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(initcode_address),
        )
        + Op.MSTORE(
            0,
            Op.CREATE2(
                value=0,
                offset=0,
                size=Op.EXTCODESIZE(initcode_address),
                salt=Op.SLOAD(0),
            ),
        )
        + Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.RETURN(0, 32)
    )
    factory_address = pre.deploy_contract(code=factory_code)

    # The factory caller will call the factory contract N times, creating N new
    # contracts. Calldata should contain the N value.
    factory_caller_code = Op.CALLDATALOAD(0) + While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )
    factory_caller_address = pre.deploy_contract(code=factory_caller_code)

    contracts_deployment_tx = Transaction(
        to=factory_caller_address,
        gas_limit=env.gas_limit,
        gas_price=10**6,
        data=Hash(num_contracts),
        sender=pre.fund_eoa(),
    )

    post = {}
    deployed_contract_addresses = []
    for i in range(num_contracts):
        deployed_contract_address = compute_create2_address(
            address=factory_address,
            salt=i,
            initcode=initcode,
        )
        post[deployed_contract_address] = Account(nonce=1)
        deployed_contract_addresses.append(deployed_contract_address)

    attack_call = Bytecode()
    if opcode == Op.EXTCODECOPY:
        attack_call = Op.EXTCODECOPY(
            address=Op.SHA3(32 - 20 - 1, 85), dest_offset=96, size=1000
        )
    else:
        # For the rest of the opcodes, we can use the same generic attack call
        # since all only minimally need the `address` of the target.
        attack_call = Op.POP(opcode(address=Op.SHA3(32 - 20 - 1, 85)))
    attack_code = (
        # Setup memory for later CREATE2 address generation loop.
        # 0xFF+[Address(20bytes)]+[seed(32bytes)]+[initcode keccak(32bytes)]
        Op.MSTORE(0, factory_address)
        + Op.MSTORE8(32 - 20 - 1, 0xFF)
        + Op.MSTORE(32, 0)
        + Op.MSTORE(64, initcode.keccak256())
        # Main loop
        + While(
            body=attack_call + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
        )
    )

    if len(attack_code) > max_contract_size:
        # TODO: A workaround could be to split the opcode code into multiple
        # contracts and call them in sequence.
        raise ValueError(
            f"Code size {len(attack_code)} exceeds maximum "
            f"code size {max_contract_size}"
        )
    opcode_address = pre.deploy_contract(code=attack_code)
    opcode_tx = Transaction(
        to=opcode_address,
        gas_limit=attack_gas_limit,
        gas_price=10**9,
        sender=pre.fund_eoa(),
    )

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(txs=[contracts_deployment_tx]),
            Block(txs=[opcode_tx]),
        ],
        exclude_full_post_state_in_output=True,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.ADDRESS,
        Op.ORIGIN,
        Op.CALLER,
        Op.CODESIZE,
        Op.GASPRICE,
        Op.BASEFEE,
        Op.BLOBBASEFEE,
        # Note that other 0-param opcodes are covered in separate tests.
    ],
)
def test_environment_ops(
    benchmark_test: BenchmarkTestFiller,
    opcode: Op,
) -> None:
    """Benchmark environmental zero-parameter instructions."""
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
    "blob_index, blobs_present",
    [
        pytest.param(0, 0, id="no blobs"),
        pytest.param(0, 1, id="one blob and accessed"),
        pytest.param(1, 1, id="one blob but access non-existent index"),
        pytest.param(5, 6, id="six blobs, access latest"),
    ],
)
def test_blobhash(
    fork: Fork,
    benchmark_test: BenchmarkTestFiller,
    blob_index: int,
    blobs_present: bool,
) -> None:
    """Benchmark BLOBHASH instruction."""
    tx_kwargs: Dict[str, Any] = {}
    if blobs_present > 0:
        tx_kwargs["ty"] = TransactionType.BLOB_TRANSACTION
        tx_kwargs["max_fee_per_blob_gas"] = fork.min_base_fee_per_blob_gas()
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version(
            [i.to_bytes() * 32 for i in range(blobs_present)],
            BlobsSpec.BLOB_COMMITMENT_VERSION_KZG,
        )

    benchmark_test(
        code_generator=ExtCallGenerator(
            attack_block=Op.BLOBHASH(blob_index),
            tx_kwargs=tx_kwargs,
        ),
    )


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
def test_codecopy(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    max_code_size_ratio: float,
    fixed_src_dst: bool,
) -> None:
    """Benchmark CODECOPY instruction."""
    max_code_size = fork.max_code_size()

    size = int(max_code_size * max_code_size_ratio)

    setup = Op.PUSH32(size)
    src_dst = 0 if fixed_src_dst else Op.MOD(Op.GAS, 7)
    attack_block = Op.CODECOPY(src_dst, src_dst, Op.DUP1)  # DUP1 copies size.

    code = JumpLoopGenerator(
        setup=setup, attack_block=attack_block
    ).generate_repeated_code(
        repeated_code=attack_block, setup=setup, fork=fork
    )

    # Pad the generated code to ensure the contract size matches the maximum
    # The content of the padding bytes is arbitrary.
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


@pytest.mark.parametrize(
    "opcode",
    [
        Op.BALANCE,
    ],
)
@pytest.mark.parametrize(
    "absent_accounts",
    [
        True,
        False,
    ],
)
def test_worst_address_state_cold(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    absent_accounts: bool,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """
    Benchmark stateful opcodes accessing cold accounts.
    """
    attack_gas_limit = gas_benchmark_value

    gas_costs = fork.gas_costs()
    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    # For calculation robustness, the calculation below ignores "glue" opcodes
    # like  PUSH and POP. It should be considered a worst-case number of
    # accounts, and a few of them might not be targeted before the attacking
    # transaction runs out of gas.
    num_target_accounts = (
        attack_gas_limit - intrinsic_gas_cost_calc()
    ) // gas_costs.G_COLD_ACCOUNT_ACCESS

    blocks = []
    post = {}

    # Setup The target addresses are going to be constructed (in the case of
    # absent=False) and called as addr_offset + i, where i is the index of the
    # account. This is to avoid collisions with the addresses indirectly
    # created by the testing framework.
    addr_offset = int.from_bytes(pre.fund_eoa(amount=0))

    if not absent_accounts:
        factory_code = Op.PUSH4(num_target_accounts) + While(
            body=Op.POP(
                Op.CALL(address=Op.ADD(addr_offset, Op.DUP6), value=10)
            ),
            condition=Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO,
        )
        factory_address = pre.deploy_contract(
            code=factory_code, balance=10**18
        )

        setup_tx = Transaction(
            to=factory_address,
            gas_limit=env.gas_limit,
            sender=pre.fund_eoa(),
        )
        blocks.append(Block(txs=[setup_tx]))

        for i in range(num_target_accounts):
            addr = Address(i + addr_offset + 1)
            post[addr] = Account(balance=10)

    # Execution
    op_code = Op.PUSH4(num_target_accounts) + While(
        body=Op.POP(opcode(Op.ADD(addr_offset, Op.DUP1))),
        condition=Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.ISZERO
        + Op.ISZERO,
    )
    op_address = pre.deploy_contract(code=op_code)
    op_tx = Transaction(
        to=op_address,
        gas_limit=attack_gas_limit,
        sender=pre.fund_eoa(),
    )
    blocks.append(Block(txs=[op_tx]))

    benchmark_test(
        post=post,
        blocks=blocks,
    )


@pytest.mark.parametrize("contract_balance", [0, 1])
def test_selfbalance(
    benchmark_test: BenchmarkTestFiller,
    contract_balance: int,
) -> None:
    """Benchmark SELFBALANCE instruction."""
    benchmark_test(
        code_generator=ExtCallGenerator(
            attack_block=Op.SELFBALANCE,
            contract_balance=contract_balance,
        ),
    )


@pytest.mark.parametrize(
    "copied_size",
    [
        pytest.param(512, id="512"),
        pytest.param(1024, id="1KiB"),
        pytest.param(5 * 1024, id="5KiB"),
    ],
)
def test_extcodecopy_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    copied_size: int,
    gas_benchmark_value: int,
) -> None:
    """Benchmark EXTCODECOPY instruction."""
    copied_contract_address = pre.deploy_contract(
        code=Op.JUMPDEST * copied_size,
    )

    execution_code = (
        Op.PUSH10(copied_size)
        + Op.PUSH20(copied_contract_address)
        + While(
            body=Op.EXTCODECOPY(Op.DUP4, 0, 0, Op.DUP2),
        )
    )
    execution_code_address = pre.deploy_contract(code=execution_code)
    tx = Transaction(
        to=execution_code_address,
        gas_limit=gas_benchmark_value,
        sender=pre.fund_eoa(),
    )

    benchmark_test(tx=tx)
