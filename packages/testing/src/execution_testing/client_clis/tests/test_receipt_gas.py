"""Test receipt normalization at the live client boundary."""

from types import SimpleNamespace

import pytest

from execution_testing.base_types import Bloom, Hash
from execution_testing.client_clis import ClientBackend
from execution_testing.client_clis.cli_types import Result
from execution_testing.forks import Amsterdam, Bogota, Fork
from execution_testing.test_types import TransactionReceipt


def build_result(fork: Fork, receipts: list[TransactionReceipt]) -> Result:
    """Build a Result at the live-client receipt boundary."""
    backend = ClientBackend.__new__(ClientBackend)
    return backend._build_result(
        built_payload=SimpleNamespace(
            state_root=Hash(0),
            receipts_root=Hash(0),
            logs_bloom=Bloom(0),
            gas_used=100_000,
            base_fee_per_gas=7,
            excess_blob_gas=0,
            blob_gas_used=0,
        ),
        execution_requests=[],
        receipts=receipts,
        withdrawals=[],
        block_fork=fork,
    )


@pytest.mark.parametrize("fork", [Amsterdam, Bogota])
@pytest.mark.parametrize(
    "rpc_cumulative", [[90_000, 10_000], [90_000, 100_000]]
)
def test_live_receipt_cumulative_gas(
    fork: Fork, rpc_cumulative: list[int]
) -> None:
    """Normalize post-fork receipts while preserving pre-fork RPC values."""
    receipts = [
        TransactionReceipt(gas_used=used, cumulative_gas_used=cumulative)
        for used, cumulative in zip(
            [90_000, 10_000], rpc_cumulative, strict=True
        )
    ]
    result = build_result(fork, receipts)
    expected = (
        [90_000, 100_000] if fork.is_eip_enabled(8116) else rpc_cumulative
    )
    assert [r.cumulative_gas_used for r in result.receipts] == expected
    assert [r.gas_used for r in result.receipts] == [90_000, 10_000]
    assert [r.cumulative_gas_used for r in receipts] == rpc_cumulative


def test_live_receipt_missing_individual_gas() -> None:
    """Reject a post-fork receipt whose on-chain gas cannot be recovered."""
    with pytest.raises(ValueError, match="missing gasUsed"):
        build_result(Bogota, [TransactionReceipt(cumulative_gas_used=90_000)])


def test_live_empty_block_receipts() -> None:
    """Allow an empty post-fork block without fabricating a receipt."""
    assert build_result(Bogota, []).receipts == []
