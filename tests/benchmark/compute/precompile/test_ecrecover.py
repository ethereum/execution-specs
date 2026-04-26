"""Benchmark ECRECOVER precompile."""

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from ..helpers import Precompile, ecrecover_calldata


@pytest.mark.repricing
@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            Precompile.ECRECOVER_ADDRESS,
            ecrecover_calldata(
                # Valid signature: full computation, not
                # blocked by validation.
                msg_hash="38D18ACB67D25C8BB9942764B62F18E1"
                "7054F66A817BD4295423ADF9ED98873E",
                v="1B",
                r="38D18ACB67D25C8BB9942764B62F18E1"
                "7054F66A817BD4295423ADF9ED98873E",
                s="789D1DD423D25F0772D2748D60F7E4B8"
                "1BB14D086EBA8E8E8EFB6DCFF8A4AE02",
            ),
            id="ecrecover",
        )
    ],
)
def test_ecrecover(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """
    Benchmark ECRECOVER precompile with unique input per call.

    Each loop iteration increments the hash at memory[0] by
    the STATICCALL success flag (1) so every call receives a
    distinct input, avoiding precompile result caching in
    clients.
    """
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    attack_block = Op.MSTORE(
        0,
        Op.ADD(
            Op.MLOAD(0),
            Op.STATICCALL(
                gas=Op.GAS,
                address=precompile_address,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        ),
    )

    benchmark_test(
        target_opcode=Precompile.ECRECOVER,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )
