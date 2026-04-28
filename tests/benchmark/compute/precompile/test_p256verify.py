"""Benchmark P256VERIFY precompile."""

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
    Transaction,
    WhileGas,
)

from tests.osaka.eip7951_p256verify_precompiles import spec as p256verify_spec

from ..helpers import Precompile, concatenate_parameters


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    p256verify_spec.Spec.H0,
                    p256verify_spec.Spec.R0,
                    p256verify_spec.Spec.S0,
                    p256verify_spec.Spec.X0,
                    p256verify_spec.Spec.Y0,
                ]
            ),
            id="p256verify",
            marks=[
                pytest.mark.eip_checklist(
                    "precompile/test/excessive_gas_usage", eip=[7951]
                ),
                pytest.mark.repricing,
            ],
        ),
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    "235060CAFE19A407880C272BC3E73600E3A12294F56143ED61929C2FF4525ABB",
                    "182E5CBDF96ACCB859E8EEA1850DE5FF6E430A19D1D9A680ECD5946BBEA8A32B",
                    "76DDFAE6797FA6777CAAB9FA10E75F52E70A4E6CEB117B3C5B2F445D850BD64C",
                    "3828736CDFC4C8696008F71999260329AD8B12287846FEDCEDE3BA1205B12729",
                    "3E5141734E971A8D55015068D9B3666760F4608A49B11F92E500ACEA647978C7",
                ]
            ),
            id="p256verify_wrong_endianness",
        ),
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    "BB5A52F42F9C9261ED4361F59422A1E30036E7C32B270C8807A419FECA605023",
                    "000000000000000000000000000000004319055358E8617B0C46353D039CDAAB",
                    "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC63254E",
                    "0AD99500288D466940031D72A9F5445A4D43784640855BF0A69874D2DE5FE103",
                    "C5011E6EF2C42DCD50D5D3D29F99AE6EBA2C80C9244F4C5422F0979FF0C3BA5E",
                ]
            ),
            id="p256verify_modular_comp_x_coordinate_exceeds_n",
        ),
    ],
)
def test_p256verify(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark P256VERIFY precompile."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=Precompile.P256VERIFY,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    p256verify_spec.Spec.H0,
                    p256verify_spec.Spec.R0,
                    p256verify_spec.Spec.S0,
                    p256verify_spec.Spec.X0,
                    p256verify_spec.Spec.Y0,
                ]
            ),
            id="p256verify",
        ),
    ],
)
def test_p256verify_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark P256VERIFY with unique input per call."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()

    precompile_cost = gsc.PRECOMPILE_P256VERIFY

    # h: data[0:32] 32 bytes
    # r: data[32:64] 32 bytes
    # s: data[64:96] 32 bytes
    # qx: data[96:128] 32 bytes
    # qy: data[128:160] 32 bytes
    attack_block = Op.MSTORE(
        0,
        Op.ADD(
            Op.MLOAD(0),
            Op.STATICCALL(
                gas=Op.GAS,
                address=precompile_address,
                args_size=Op.CALLDATASIZE,
                ret_offset=Op.CALLDATASIZE,
                ret_size=0x20,
                # gas accounting
                address_warm=True,
                inner_call_cost=precompile_cost,
            ),
        ),
        # gas accounting
        old_memory_size=160,
        new_memory_size=160,
    )

    setup = Op.CALLDATACOPY(
        0,
        0,
        Op.CALLDATASIZE,
        # gas accounting
        data_size=160,
        old_memory_size=0,
        new_memory_size=160,
    )
    setup_cost = setup.gas_cost(fork)

    loop = WhileGas(
        body=attack_block,
        fork=fork,
        extra_gas=precompile_cost,
    )
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    iteration_cost = loop.gas_cost(fork)

    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value
    seed = 0
    expected_opcode_count = 0
    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        h = int.from_bytes(calldata[:32], "big") + seed

        tx_calldata = Bytes(
            h.to_bytes(32, "big")  # hash
            + calldata[32:]  # r, s, qx, qy
        )

        intrinsic = intrinsic_gas_calculator(
            calldata=tx_calldata,
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
                data=tx_calldata,
            )
        )
        remaining_gas -= per_tx_gas
        seed += 10000

    assert len(txs) != 0, "No transactions were added to the test."

    benchmark_test(
        target_opcode=Precompile.P256VERIFY,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
        expected_opcode_count=expected_opcode_count,
    )
