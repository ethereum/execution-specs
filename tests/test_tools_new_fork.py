from pathlib import Path
from tempfile import TemporaryDirectory

from ethereum_spec_tools.new_fork.cli import main as new_fork


def test_end_to_end() -> None:
    with TemporaryDirectory() as base_dir:
        output_dir = Path(base_dir) / "ethereum"
        fork_dir = output_dir / "e2e_fork"

        new_fork(
            [
                "--new-fork",
                "e2e_fork",
                "--template-fork",
                "osaka",
                "--target-blob-gas-per-block",
                "199",
                "--blob-base-fee-update-fraction",
                "750",
                "--min-blob-gasprice",
                "2",
                "--gas-per-blob",
                "1",
                "--at-timestamp",
                "7",
                "--max-blob-gas-per-block",
                "99",
                "--blob-schedule-target",
                "88",
                "--output",
                str(output_dir),
            ]
        )

        with (fork_dir / "__init__.py").open("r") as f:
            source = f.read()

            assert "FORK_CRITERIA = ByTimestamp(7)" in source
            assert "E2E Fork" in source
            assert "Osaka" not in source

        with (fork_dir / "vm" / "gas.py").open("r") as f:
            source = f.read()

            expected = [
                "TARGET_BLOB_GAS_PER_BLOCK = U64(199)",
                "GAS_PER_BLOB = U64(1)",
                "MIN_BLOB_GASPRICE = Uint(2)",
                "BLOB_BASE_FEE_UPDATE_FRACTION = Uint(750)",
                "BLOB_SCHEDULE_TARGET = U64(88)",
            ]

            for needle in expected:
                assert needle in source

        with (fork_dir / "fork.py").open("r") as f:
            assert "MAX_BLOB_GAS_PER_BLOCK = U64(99)" in f.read()

        with (fork_dir / "trie.py").open("r") as f:
            assert (
                "from ethereum.paris import trie as previous_trie" in f.read()
            )
