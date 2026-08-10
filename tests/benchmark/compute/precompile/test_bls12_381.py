"""Benchmark BLS12_381 precompile."""

import math
import random
from collections.abc import Callable

import pytest
from execution_testing import (
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytes,
    Fork,
    JumpLoopGenerator,
    Op,
    OpcodeTarget,
    Transaction,
    While,
    WhileGas,
)
from py_ecc import optimized_bls12_381 as bls_curve

from tests.benchmark.helper.precompile import Precompile
from tests.prague.eip2537_bls_12_381_precompiles import spec as bls12381_spec
from tests.prague.eip2537_bls_12_381_precompiles.spec import (
    build_gas_calculation_function_map,
)


@pytest.mark.parametrize(
    "precompile_address,calldata,target",
    [
        pytest.param(
            bls12381_spec.Spec.G1ADD,
            bls12381_spec.Spec.G1 + bls12381_spec.Spec.P1,
            Precompile.BLS12_G1ADD,
            id="bls12_g1add",
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            bls12381_spec.Spec.G2ADD,
            bls12381_spec.Spec.G2 + bls12381_spec.Spec.P2,
            Precompile.BLS12_G2ADD,
            id="bls12_g2add",
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            bls12381_spec.Spec.PAIRING,
            bls12381_spec.Spec.G1 + bls12381_spec.Spec.G2,
            Precompile.BLS12_PAIRING,
            id="bls12_pairing_check",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP_TO_G1,
            bls12381_spec.FP(bls12381_spec.Spec.P - 1),
            Precompile.BLS12_MAP_FP_TO_G1,
            id="bls12_fp_to_g1",
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP2_TO_G2,
            bls12381_spec.FP2(
                (bls12381_spec.Spec.P - 1, bls12381_spec.Spec.P - 1)
            ),
            Precompile.BLS12_MAP_FP2_TO_G2,
            id="bls12_fp_to_g2",
            marks=pytest.mark.repricing,
        ),
    ],
)
def test_bls12_381(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
    precompile_address: Address,
    calldata: bytes,
    target: OpcodeTarget,
) -> None:
    """Benchmark BLS12_381 precompile."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata
    )
    if intrinsic_gas_cost > gas_benchmark_value:
        pytest.skip("calldata intrinsic gas cost exceeds the gas limit")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=target,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("k", [1, 16, 64, 128])
def test_bls12_g1_msm(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
    k: int,
) -> None:
    """Benchmark BLS12_G1_MSM precompile with varying number of points."""
    precompile_address = bls12381_spec.Spec.G1MSM
    if precompile_address not in fork.precompiles():
        pytest.skip("BLS12_G1_MSM precompile not enabled")

    calldata = _g1msm_worstcase_calldata(k)

    intrinsic_gas_cost = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata
    )
    if intrinsic_gas_cost > gas_benchmark_value:
        pytest.skip("k configuration exceeds the gas limit")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=Precompile.BLS12_G1MSM,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "k",
    [
        1,
        16,
        64,
        # G2 MSM k=128 costs 1.5M gas
        pytest.param(128, marks=pytest.mark.slow),
    ],
)
def test_bls12_g2_msm(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
    k: int,
) -> None:
    """Benchmark BLS12_G2_MSM precompile with varying number of points."""
    precompile_address = bls12381_spec.Spec.G2MSM
    if precompile_address not in fork.precompiles():
        pytest.skip("BLS12_G2_MSM precompile not enabled")

    calldata = _g2msm_worstcase_calldata(k)

    # The floor data cost can exceed the standard intrinsic cost on this much
    # calldata -- EIP-7976 charges 64 gas per byte -- so the minimum a
    # transaction carrying it can be given is the larger of the two. The
    # per-transaction minimum (this benchmark is split across several
    # transactions) is enforced in BenchmarkTest.split_transaction.
    minimum_gas_cost = max(
        fork.transaction_intrinsic_cost_calculator()(calldata=calldata),
        fork.transaction_data_floor_cost_calculator()(data=calldata),
    )

    if minimum_gas_cost > gas_benchmark_value:
        pytest.skip("k configuration exceeds the gas limit")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=Precompile.BLS12_G2MSM,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("num_pairs", [1, 3, 6, 12, 24])
def test_bls12_pairing(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    num_pairs: int,
) -> None:
    """Benchmark BLS12_PAIRING precompile with varying number of pairs."""
    precompile_address = bls12381_spec.Spec.PAIRING
    if precompile_address not in fork.precompiles():
        pytest.skip("BLS12_PAIRING precompile not enabled")

    # Generate num_pairs pairs of (G1, G2) points
    calldata = Bytes(
        (bls12381_spec.Spec.G1 + bls12381_spec.Spec.G2) * num_pairs
    )

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=Precompile.BLS12_PAIRING,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


def _generate_bls12_g1_point(seed: int) -> Bytes:
    """Generate a valid BLS12-381 G1 point from a seed."""
    rng = random.Random(seed)
    k = rng.randint(1, 2**32 - 1)
    point = bls_curve.normalize(bls_curve.multiply(bls_curve.G1, k))
    x = int(point[0])
    y = int(point[1])
    return Bytes(x.to_bytes(64, "big") + y.to_bytes(64, "big"))


def _generate_bls12_g2_point(seed: int) -> Bytes:
    """Generate a valid BLS12-381 G2 point from a seed."""
    rng = random.Random(seed)
    k = rng.randint(1, 2**32 - 1)
    point = bls_curve.normalize(bls_curve.multiply(bls_curve.G2, k))
    x_im = int(point[0].coeffs[0])
    x_re = int(point[0].coeffs[1])
    y_im = int(point[1].coeffs[0])
    y_re = int(point[1].coeffs[1])
    return Bytes(
        x_im.to_bytes(64, "big")
        + x_re.to_bytes(64, "big")
        + y_im.to_bytes(64, "big")
        + y_re.to_bytes(64, "big")
    )


def _g1msm_worstcase_calldata(k: int) -> Bytes:
    """
    Build a k-pair G1MSM input that resists MSM shortcuts.

    Identical points would let the precompile factor out (sum sᵢ)·P, and
    identical scalars would let Pippenger bucket every term together. Pairing
    distinct points with distinct full-width scalars below the subgroup order
    (so no term collapses to the point at infinity) forces the full k-term
    computation.
    """
    rng = random.Random(0)
    parts = [
        bytes(_generate_bls12_g1_point(i))
        + bytes(
            bls12381_spec.Scalar(rng.randint(2**254, bls12381_spec.Spec.Q - 1))
        )
        for i in range(k)
    ]
    return Bytes(b"".join(parts))


def _g2msm_worstcase_calldata(k: int) -> Bytes:
    """G2MSM counterpart of `_g1msm_worstcase_calldata`."""
    rng = random.Random(0)
    parts = [
        bytes(_generate_bls12_g2_point(i))
        + bytes(
            bls12381_spec.Scalar(rng.randint(2**254, bls12381_spec.Spec.Q - 1))
        )
        for i in range(k)
    ]
    return Bytes(b"".join(parts))


def _generate_bls12_pairs(n: int, seed: int = 0) -> Bytes:
    """Generate n valid BLS12-381 (G1, G2) pairs."""
    calldata = Bytes()
    for i in range(n):
        g1 = _generate_bls12_g1_point(seed + 2 * i)
        g2 = _generate_bls12_g2_point(seed + 2 * i + 1)
        calldata = Bytes(calldata + g1 + g2)
    return calldata


def _g1add_calldata(seed: int) -> Bytes:
    """Generate G1ADD calldata with unique first point."""
    return Bytes(_generate_bls12_g1_point(seed) + bls12381_spec.Spec.P1)


def _g2add_calldata(seed: int) -> Bytes:
    """Generate G2ADD calldata with unique first point."""
    return Bytes(_generate_bls12_g2_point(seed) + bls12381_spec.Spec.P2)


# Full-width scalar just below the subgroup order. Using Q itself would be
# congruent to 0 mod the subgroup order, so Q * P == O and the output fed
# back into the next call would multiply the point at infinity forever. Q - 2
# keeps every call a real scalar multiplication over a long, non-repeating
# sequence of distinct points (its order mod Q exceeds any per-block
# iteration count), preserving both the workload and the anti-caching intent.
_MSM_SCALAR = bls12381_spec.Spec.Q - 2


def _g1msm_calldata(seed: int) -> Bytes:
    """Generate G1MSM calldata with unique point."""
    return Bytes(
        _generate_bls12_g1_point(seed) + bls12381_spec.Scalar(_MSM_SCALAR)
    )


def _g2msm_calldata(seed: int) -> Bytes:
    """Generate G2MSM calldata with unique point."""
    return Bytes(
        _generate_bls12_g2_point(seed) + bls12381_spec.Scalar(_MSM_SCALAR)
    )


def _fp_to_g1_calldata(seed: int) -> Bytes:
    """Generate MAP_FP_TO_G1 calldata with unique FP."""
    rng = random.Random(seed)
    return Bytes(bls12381_spec.FP(rng.randint(1, bls12381_spec.Spec.P - 1)))


def _fp2_to_g2_calldata(seed: int) -> Bytes:
    """Generate MAP_FP2_TO_G2 calldata with unique FP2."""
    rng = random.Random(seed)
    c0 = rng.randint(1, bls12381_spec.Spec.P - 1)
    c1 = rng.randint(1, bls12381_spec.Spec.P - 1)
    return Bytes(bls12381_spec.FP2((c0, c1)))


@pytest.mark.repricing
@pytest.mark.parametrize(
    "precompile_address,ret_size,generate_calldata,target",
    [
        pytest.param(
            bls12381_spec.Spec.G1ADD,
            128,
            _g1add_calldata,
            Precompile.BLS12_G1ADD,
            id="bls12_g1add",
        ),
        pytest.param(
            bls12381_spec.Spec.G2ADD,
            256,
            _g2add_calldata,
            Precompile.BLS12_G2ADD,
            id="bls12_g2add",
        ),
        pytest.param(
            bls12381_spec.Spec.G1MSM,
            128,
            _g1msm_calldata,
            Precompile.BLS12_G1MSM,
            id="bls12_g1msm",
        ),
        pytest.param(
            bls12381_spec.Spec.G2MSM,
            256,
            _g2msm_calldata,
            Precompile.BLS12_G2MSM,
            id="bls12_g2msm",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP_TO_G1,
            64,
            _fp_to_g1_calldata,
            Precompile.BLS12_MAP_FP_TO_G1,
            id="bls12_fp_to_g1",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP2_TO_G2,
            128,
            _fp2_to_g2_calldata,
            Precompile.BLS12_MAP_FP2_TO_G2,
            id="bls12_fp_to_g2",
        ),
    ],
)
def test_bls12_381_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    precompile_address: Address,
    ret_size: int,
    generate_calldata: Callable[[int], Bytes],
    target: OpcodeTarget,
) -> None:
    """
    Benchmark BLS12_381 with unique input per call.

    Each iteration writes the precompile output back to the
    start of the input so every call receives a distinct input,
    avoiding precompile result caching in clients.
    """
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_calc_map = build_gas_calculation_function_map(fork.gas_costs())
    input_size = len(generate_calldata(0))
    precompile_cost = gas_calc_map[int(precompile_address)](input_size)

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=precompile_address,
            args_size=Op.CALLDATASIZE,
            ret_size=ret_size,
            # gas accounting
            address_warm=True,
            inner_call_cost=precompile_cost,
        ),
    )

    setup = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        # gas accounting
        data_size=input_size,
        new_memory_size=input_size,
    )
    setup_cost = setup.gas_cost(fork)

    loop = WhileGas(body=attack_block, fork=fork)

    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    iteration_cost = loop.gas_cost(fork)

    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value
    seed = 0
    expected_opcode_count = 0
    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        calldata = generate_calldata(seed)

        intrinsic = intrinsic_gas_calculator(
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        gas_for_loop = per_tx_gas - intrinsic - setup_cost
        if gas_for_loop < iteration_cost:
            break
        expected_opcode_count += gas_for_loop // iteration_cost

        txs.append(
            Transaction(
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                gas_limit=per_tx_gas,
                data=calldata,
            )
        )
        remaining_gas -= per_tx_gas
        seed += 1

    assert len(txs) != 0, "No transactions were added to the test."

    benchmark_test(
        target_opcode=target,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
        expected_opcode_count=expected_opcode_count,
    )


@pytest.mark.repricing
@pytest.mark.parametrize("num_pairs", [1, 3, 6, 12, 24])
def test_bls12_pairing_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    num_pairs: int,
) -> None:
    """Benchmark BLS12 pairing precompile with unique inputs per call."""
    precompile_address = bls12381_spec.Spec.PAIRING
    if precompile_address not in fork.precompiles():
        pytest.skip("BLS12_PAIRING precompile not enabled")

    pair_size = num_pairs * 384
    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp = fork.memory_expansion_gas_calculator()

    # Each iteration: STATICCALL pairing at advancing offset,
    # then advance offset by pair_size at memory[CALLDATASIZE].
    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=precompile_address,
            args_offset=Op.MLOAD(Op.CALLDATASIZE),
            args_size=pair_size,
            address_warm=True,
        ),
    ) + Op.MSTORE(
        Op.CALLDATASIZE,
        Op.ADD(Op.MLOAD(Op.CALLDATASIZE), pair_size),
    )

    setup = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    loop = While(
        body=attack_block,
        condition=Op.GT(Op.CALLDATASIZE, Op.MLOAD(Op.CALLDATASIZE)),
    )
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    precompile_cost = (
        gsc.PRECOMPILE_BLS_PAIRING_BASE
        + gsc.PRECOMPILE_BLS_PAIRING_PER_PAIR * num_pairs
    )

    iteration_cost = loop.gas_cost(fork) + precompile_cost
    setup_cost = setup.gas_cost(fork)

    # Conservative per-variant estimate: one loop iteration
    # + worst-case calldata floor intrinsic (all non-zero, EIP-7623)
    # + CALLDATACOPY copy and linear memory expansion.
    words_per_variant = math.ceil(pair_size / 32)
    tokens_per_variant = pair_size * 4  # worst case: all non-zero
    per_variant_gas = (
        iteration_cost
        + tokens_per_variant * gsc.TX_DATA_TOKEN_FLOOR
        + words_per_variant * (gsc.OPCODE_COPY_PER_WORD + gsc.MEMORY_PER_WORD)
    )
    empty_intrinsic = intrinsic_gas_calculator(
        calldata=[],
        return_cost_deducted_prior_execution=False,
    )
    fixed_overhead = empty_intrinsic + setup_cost + mem_exp(new_bytes=32)

    seed_offset = 0
    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value
    expected_opcode_count = 0
    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        per_tx_variants = max(
            1,
            (per_tx_gas - fixed_overhead) // per_variant_gas,
        )
        calldata = Bytes(
            b"".join(
                _generate_bls12_pairs(num_pairs, seed=42 + seed_offset + i)
                for i in range(per_tx_variants)
            )
        )

        execution_intrinsic = intrinsic_gas_calculator(
            calldata=calldata,
            return_cost_deducted_prior_execution=False,
        )
        gas_for_loop = (
            per_tx_gas
            - execution_intrinsic
            - setup_cost
            - math.ceil(len(calldata) / 32) * gsc.OPCODE_COPY_PER_WORD
            - mem_exp(new_bytes=len(calldata) + 32)
        )

        if gas_for_loop < per_tx_variants * iteration_cost:
            break
        expected_opcode_count += per_tx_variants

        txs.append(
            Transaction(
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                gas_limit=per_tx_gas,
                data=calldata,
            )
        )
        remaining_gas -= per_tx_gas
        seed_offset += per_tx_variants

    # TODO: 24 pairs exceeds the 1M block gas limit used in CI,
    # which breaks the test run
    if num_pairs == 24:
        pytest.skip(
            f"gas_benchmark_value={gas_benchmark_value} too small for "
            f"num_pairs={num_pairs} "
            f"(need ~{per_variant_gas + fixed_overhead} gas)"
        )

    assert len(txs) != 0, "No transactions were added to the test."

    benchmark_test(
        target_opcode=Precompile.BLS12_PAIRING,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
        expected_opcode_count=expected_opcode_count,
    )
