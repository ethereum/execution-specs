"""Test the transition tool and subclasses."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Type, cast

import pytest

from execution_testing.client_clis import (
    CLINotFoundInPathError,
    EvmOneTransitionTool,
    ExecutionSpecsTransitionTool,
    GethTransitionTool,
    NimbusTransitionTool,
    TransitionTool,
)
from execution_testing.client_clis.cli_types import (
    LazyAlloc,
    LazyAllocJson,
    LazyAllocStr,
    TransactionReceipt,
)
from execution_testing.test_types import Alloc


def test_default_tool() -> None:
    """Tests that the default t8n tool is set."""
    assert TransitionTool.default_tool is ExecutionSpecsTransitionTool


@pytest.mark.parametrize(
    "binary_path,which_result,read_result,expected_class",
    [
        (
            Path("evm"),
            "evm",
            "evm version 1.12.1-unstable-c7b099b2-20230627",
            GethTransitionTool,
        ),
        (
            Path("evmone-t8n"),
            "evmone-t8n",
            "evmone-t8n 0.11.0-dev+commit.93997506",
            EvmOneTransitionTool,
        ),
        pytest.param(
            Path("ethereum-spec-evm"),
            "ethereum-spec-evm",
            "ethereum-spec-evm",
            ExecutionSpecsTransitionTool,
            marks=pytest.mark.skip(
                reason=(
                    "ExecutionSpecsTransitionTool through binary path "
                    "is not supported"
                )
            ),
        ),
        (
            Path("t8n"),
            "t8n",
            "Nimbus-t8n 0.1.2\n\x1b[0m",
            NimbusTransitionTool,
        ),
    ],
)
def test_from_binary(
    monkeypatch: pytest.MonkeyPatch,
    binary_path: Path | None,
    which_result: str,
    read_result: str,
    expected_class: Type[TransitionTool],
) -> None:
    """Test that `from_binary` instantiates the correct subclass."""

    class MockCompletedProcess:
        def __init__(self, stdout: bytes) -> None:
            self.stdout = stdout
            self.stderr = None
            self.returncode = 0

    def mock_which(self: str) -> str:
        del self
        return which_result

    def mock_run(args: list, **kwargs: dict) -> MockCompletedProcess:
        del args, kwargs
        return MockCompletedProcess(read_result.encode())

    monkeypatch.setattr(shutil, "which", mock_which)
    monkeypatch.setattr(subprocess, "run", mock_run)

    assert isinstance(
        TransitionTool.from_binary_path(binary_path=binary_path),
        expected_class,
    )


def test_unknown_binary_path() -> None:
    """
    Test that `from_binary_path` raises `UnknownCLIError` for unknown
    binary paths.
    """
    with pytest.raises(CLINotFoundInPathError):
        TransitionTool.from_binary_path(
            binary_path=Path("unknown_binary_path")
        )


TEST_ALLOC = Alloc.model_validate(
    {0xA: {"balance": 1, "nonce": 2, "code": "0x00"}}
)
TEST_ALLOC_STATE_ROOT = TEST_ALLOC.state_root()


@pytest.mark.parametrize(
    "ty,raw",
    [
        pytest.param(
            LazyAllocJson, TEST_ALLOC.model_dump(), id="lazy_alloc_json"
        ),
        pytest.param(
            LazyAllocStr, TEST_ALLOC.model_dump_json(), id="lazy_alloc_str"
        ),
    ],
)
def test_lazy_alloc(ty: Type[LazyAlloc], raw: Any) -> None:
    """Test LazyAlloc types."""
    lazy_instance = ty(raw=raw, _state_root=TEST_ALLOC_STATE_ROOT)
    assert lazy_instance.get() == TEST_ALLOC
    assert lazy_instance.state_root() == TEST_ALLOC_STATE_ROOT


class _CollectTracesSelf:
    """
    Minimal stand-in for a ``TransitionTool`` instance.

    ``TransitionTool.collect_traces`` only touches ``self.traces`` and
    ``self.append_traces``. Instantiating a real subclass requires an
    exception_mapper, binary discovery, etc. — all unrelated to what
    we're testing here.
    """

    def __init__(self) -> None:
        self.traces: list = []

    def append_traces(self, new_traces: Any) -> None:
        self.traces.append(new_traces)


def _make_receipt(tx_hash: str) -> TransactionReceipt:
    return TransactionReceipt.model_validate({"transactionHash": tx_hash})


def test_collect_traces_writes_empty_placeholder_for_missing_trace(
    tmp_path: Path,
) -> None:
    """
    Regression for issue #2758.

    When a tx produces a receipt but no trace file (TransactionEnd
    tracer event never fired, e.g. EIP-3607 collisions), an empty
    placeholder file must be written into ``debug_output_path`` so a
    later ``--verify-traces`` run loads a matching shape from disk.
    """
    tx_hash_present = "0x" + "a" * 64
    tx_hash_missing = "0x" + "b" * 64

    temp_dir = tempfile.TemporaryDirectory()
    # Only write a trace for the first receipt; the second is missing.
    (Path(temp_dir.name) / f"trace-0-{tx_hash_present}.jsonl").write_text(
        '{"output":"0x","gasUsed":"0x5208"}\n'
    )

    debug_dir = tmp_path / "dump"
    debug_dir.mkdir()

    receipts = [_make_receipt(tx_hash_present), _make_receipt(tx_hash_missing)]

    self_obj = _CollectTracesSelf()
    TransitionTool.collect_traces(
        cast(TransitionTool, self_obj),
        receipts,
        temp_dir,
        debug_output_path=debug_dir,
    )

    placeholder = debug_dir / f"trace-1-{tx_hash_missing}.jsonl"
    copied = debug_dir / f"trace-0-{tx_hash_present}.jsonl"
    assert placeholder.exists(), "missing-trace placeholder not written"
    assert placeholder.read_text() == ""
    assert copied.exists(), "present trace was not copied to dump dir"


def test_collect_traces_no_placeholder_without_debug_path() -> None:
    """
    With ``debug_output_path=None`` the missing-trace branch must still
    produce an in-memory empty ``TransactionTraces`` but must not write
    to disk.
    """
    tx_hash = "0x" + "c" * 64
    temp_dir = tempfile.TemporaryDirectory()
    self_obj = _CollectTracesSelf()
    TransitionTool.collect_traces(
        cast(TransitionTool, self_obj),
        [_make_receipt(tx_hash)],
        temp_dir,
        debug_output_path=None,
    )
    assert len(self_obj.traces) == 1
    assert len(self_obj.traces[0].root) == 1
    assert self_obj.traces[0].root[0].traces == []
