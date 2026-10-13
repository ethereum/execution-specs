"""
Benchmark storage commit cost on deep branching self-DELEGATECALL recursion.

Each call frame warm-writes a fixed set of storage slots and then
DELEGATECALLs itself twice. DELEGATECALL keeps the caller's storage context,
so every frame touches one shared account's storage, and the two self-calls
grow a deep tree of call frames that stays within the EIP-7825 per-transaction
gas cap. The scenario maximizes the number of nested frames that each carry a
storage write set, which stresses the per-frame storage bookkeeping a client
performs as the call stack unwinds. ``writes_per_frame`` trades frame count
(small value, cheaper frames, deeper tree) against per-frame write-set size.
"""

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Op,
    Transaction,
)


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize("writes_per_frame", [16, 64, 256])
def test_stacked_storage_commit(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    writes_per_frame: int,
) -> None:
    """Branching self-DELEGATECALL with warm writes per frame."""
    delegate = Op.DELEGATECALL(Op.GAS, Op.ADDRESS, 0, 0, 0, 0)
    # Fixed slot keys stay warm after the first touch, so every write is cheap
    # (the value GAS changes each time, so it is always a real write).
    writes = sum(
        (Op.SSTORE(slot, Op.GAS) for slot in range(writes_per_frame)),
        Bytecode(),
    )
    contract = pre.deploy_contract(writes + delegate + delegate)
    benchmark_test(
        pre=pre,
        tx=Transaction(to=contract, sender=pre.fund_eoa()),
    )
