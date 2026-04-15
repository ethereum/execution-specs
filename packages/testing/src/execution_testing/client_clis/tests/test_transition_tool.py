"""Test the transition tool and subclasses."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Type

import ijson  # type: ignore[import-untyped]
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
    LazyAllocFile,
    LazyAllocJson,
    LazyAllocStr,
    Result,
    TransitionToolInput,
    TransitionToolOutput,
)
from execution_testing.test_types import Alloc, Environment


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


def test_lazy_alloc_file(tmp_path: Path) -> None:
    """LazyAllocFile streams the alloc from disk and yields the same Alloc."""
    alloc_path = tmp_path / "alloc.json"
    alloc_path.write_text(TEST_ALLOC.model_dump_json())
    lazy_instance = LazyAllocFile(
        raw=alloc_path, _state_root=TEST_ALLOC_STATE_ROOT
    )
    assert lazy_instance.get() == TEST_ALLOC
    assert lazy_instance.state_root() == TEST_ALLOC_STATE_ROOT


def test_lazy_alloc_file_handles_mixed_entries(tmp_path: Path) -> None:
    """
    LazyAllocFile correctly reconstructs an Alloc containing None entries,
    non-empty storage, long code, and multiple accounts.
    """
    alloc = Alloc.model_validate(
        {
            0xA: {
                "balance": 1,
                "nonce": 2,
                "code": "0x" + "ab" * 128,
                "storage": {"0x01": "0x02", "0x03": "0x04"},
            },
            0xB: None,
            0xC: {"balance": "0xff", "nonce": 0, "code": "0x"},
        }
    )
    state_root = alloc.state_root()
    alloc_path = tmp_path / "alloc.json"
    alloc_path.write_text(alloc.model_dump_json())
    lazy_instance = LazyAllocFile(raw=alloc_path, _state_root=state_root)
    assert lazy_instance.get() == alloc
    assert lazy_instance.state_root() == state_root


def _write_minimal_result(path: Path, state_root: Any) -> None:
    """Write a minimal valid Result JSON to `path` using `state_root`."""
    result = Result.model_validate(
        {
            "stateRoot": state_root,
            "txRoot": bytes(32),
            "receiptsRoot": bytes(32),
            "logsHash": bytes(32),
            "logsBloom": bytes(256),
            "receipts": [],
            "gasUsed": 0,
        }
    )
    path.write_text(result.model_dump_json(by_alias=True, exclude_none=True))


def test_model_validate_files_uses_lazy_alloc_file(tmp_path: Path) -> None:
    """
    model_validate_files backs the alloc with the on-disk file, not a
    multi-GB string in Python memory.
    """
    alloc_path = tmp_path / "alloc.json"
    alloc_path.write_text(TEST_ALLOC.model_dump_json())
    _write_minimal_result(tmp_path / "result.json", TEST_ALLOC_STATE_ROOT)

    output = TransitionToolOutput.model_validate_files(tmp_path)

    assert isinstance(output.alloc, LazyAllocFile)
    assert output.alloc.raw == alloc_path
    assert output.alloc.get() == TEST_ALLOC


def test_transition_tool_input_serializes_lazy_alloc_file(
    tmp_path: Path,
) -> None:
    """
    A `TransitionToolInput` carrying a `LazyAllocFile` (as happens when
    one t8n invocation's output is chained into the next's input) can be
    serialized via both `to_files` and `model_dump_json` without pulling
    the alloc file into memory at `TransitionToolInput` construction.
    """
    source_alloc = tmp_path / "source_alloc.json"
    source_alloc.write_text(TEST_ALLOC.model_dump_json())
    lazy_alloc = LazyAllocFile(
        raw=source_alloc, _state_root=TEST_ALLOC_STATE_ROOT
    )

    input_data = TransitionToolInput(
        alloc=lazy_alloc, txs=[], env=Environment()
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    paths = input_data.to_files(out_dir, by_alias=True, exclude_none=True)
    written_alloc = Alloc.model_validate_json(Path(paths["alloc"]).read_text())
    assert written_alloc == TEST_ALLOC

    dumped = input_data.model_dump_json(by_alias=True, exclude_none=True)
    parsed = json.loads(dumped)
    assert Alloc.model_validate(parsed["alloc"]) == TEST_ALLOC


def test_dump_files_to_directory_copies_lazy_alloc_file(
    tmp_path: Path,
) -> None:
    """
    `dump_files_to_directory` copies the backing file when given a
    `LazyAllocFile`, preserving exact bytes without round-tripping the
    alloc through Python memory.
    """
    from execution_testing.client_clis.file_utils import (
        dump_files_to_directory,
    )

    source = tmp_path / "source_alloc.json"
    source_text = TEST_ALLOC.model_dump_json()
    source.write_text(source_text)
    lazy = LazyAllocFile(raw=source, _state_root=TEST_ALLOC_STATE_ROOT)

    dump_dir = tmp_path / "dump"
    dump_files_to_directory(dump_dir, {"output/alloc.json": lazy})

    assert (dump_dir / "output" / "alloc.json").read_text() == source_text


@pytest.mark.parametrize(
    "contents",
    [
        pytest.param(b"", id="empty_file"),
        pytest.param(b"not json at all", id="garbage"),
        pytest.param(
            b'{"0x01": {"balance": 1, "nonce"',
            id="truncated_mid_entry",
        ),
        pytest.param(b'{"0x01": {"balance": }}', id="invalid_value"),
    ],
)
def test_lazy_alloc_file_malformed_json_raises(
    tmp_path: Path, contents: bytes
) -> None:
    """
    A malformed `alloc.json` surfaces as `ijson.IncompleteJSONError` when
    `LazyAllocFile.validate()` streams it — no partial `Alloc` is returned.
    """
    alloc_path = tmp_path / "alloc.json"
    alloc_path.write_bytes(contents)
    lazy = LazyAllocFile(raw=alloc_path, _state_root=TEST_ALLOC_STATE_ROOT)

    with pytest.raises(ijson.common.IncompleteJSONError):
        lazy.get()
