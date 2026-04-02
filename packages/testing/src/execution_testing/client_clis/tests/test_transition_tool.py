"""Test the transition tool and subclasses."""

import shutil
import subprocess
from pathlib import Path
from typing import Any, Type

import pytest

from execution_testing.base_types import Bloom, Hash
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
    TransitionToolOutput,
)
from execution_testing.forks import Berlin
from execution_testing.test_types import Alloc, Environment, Transaction


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


def test_transition_tool_data_inclusion_list_transactions() -> None:
    """Test that inclusion list txs are serialized into the transition env."""
    il_tx = Transaction(gas_limit=21_000).with_signature_and_sender()

    transition_tool_data = TransitionTool.TransitionToolData(
        alloc=TEST_ALLOC,
        txs=[],
        env=Environment(),
        fork=Berlin,
        chain_id=1,
        reward=0,
        blob_schedule=Berlin.blob_schedule(),
        inclusion_list_txs=[il_tx],
    )

    transition_tool_input = transition_tool_data.to_input()
    assert transition_tool_input.env.inclusion_list_transactions == [
        il_tx.rlp()
    ]


def test_transition_tool_output_parses_inclusion_list_satisfaction() -> None:
    """Test that the transition tool output parses IL satisfaction results."""
    output = TransitionToolOutput.model_validate(
        {
            "alloc": TEST_ALLOC.model_dump(),
            "result": {
                "stateRoot": TEST_ALLOC_STATE_ROOT.hex(),
                "txRoot": Hash(1).hex(),
                "receiptsRoot": Hash(2).hex(),
                "logsHash": Hash(3).hex(),
                "logsBloom": Bloom(0).hex(),
                "receipts": [],
                "gasUsed": hex(0),
                "isInclusionListSatisfied": False,
            },
        }
    )

    assert output.result.is_inclusion_list_satisfied is False
