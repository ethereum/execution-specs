"""Tests for the --trace-opcodes output file (gas-benchmarks format)."""

import json
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.fill_stateful.opcode_tracing import (  # noqa: E501
    node_id_to_test_key,
    write_opcode_trace_file,
)
from execution_testing.client_clis.cli_types import OpcodeCount

# ---------------------------------------------------------------------------
# node_id_to_test_key
# ---------------------------------------------------------------------------


def test_key_strips_module_directory() -> None:
    """Reduce the module path to its basename."""
    node_id = (
        "tests/benchmark/stateful/bloatnet/test_single_opcode.py::"
        "test_sload_erc20_generic[fork_Amsterdam-benchmark_300M]"
    )
    assert node_id_to_test_key(node_id) == (
        "test_single_opcode.py__"
        "test_sload_erc20_generic[fork_Amsterdam-benchmark_300M]"
    )


def test_key_without_parameters() -> None:
    """Handle node ids without a parametrization suffix."""
    assert (
        node_id_to_test_key("tests/test_mod.py::test_case")
        == "test_mod.py__test_case"
    )


def test_key_class_based_test() -> None:
    """Flatten every ``::`` separator to ``__``."""
    assert (
        node_id_to_test_key("tests/test_mod.py::TestClass::test_case")
        == "test_mod.py__TestClass__test_case"
    )


def test_key_without_separator() -> None:
    """Pass through strings that are not node ids."""
    assert node_id_to_test_key("not-a-node-id") == "not-a-node-id"


# ---------------------------------------------------------------------------
# write_opcode_trace_file
# ---------------------------------------------------------------------------


def test_write_matches_gas_benchmarks_format(tmp_path: Path) -> None:
    """Produce the exact JSON layout of gas-benchmarks' trace output."""
    output = tmp_path / "opcodes_tracing.json"
    write_opcode_trace_file(
        output,
        {
            "tests/benchmark/test_account_query.py::"
            "test_account_access[fork_Amsterdam-opcode_BALANCE]": (
                OpcodeCount.model_validate({"PUSH1": 55674, "BALANCE": 11132})
            ),
        },
    )
    expected = (
        "{\n"
        '  "test_account_query.py__'
        'test_account_access[fork_Amsterdam-opcode_BALANCE]": {\n'
        '    "PUSH1": 55674,\n'
        '    "BALANCE": 11132\n'
        "  }\n"
        "}"
    )
    assert output.read_text(encoding="utf-8") == expected


def test_write_restores_keccak256_name(tmp_path: Path) -> None:
    """Serialise SHA3 back to KECCAK256, as clients report it."""
    output = tmp_path / "opcodes_tracing.json"
    write_opcode_trace_file(
        output,
        {
            "tests/t.py::test_x": OpcodeCount.model_validate(
                {"KECCAK256": 3, "ADD": 1}
            )
        },
    )
    counts = json.loads(output.read_text(encoding="utf-8"))["t.py__test_x"]
    assert counts == {"KECCAK256": 3, "ADD": 1}


def test_write_suffixes_colliding_keys(tmp_path: Path) -> None:
    """Suffix keys that collide once module paths are flattened."""
    output = tmp_path / "opcodes_tracing.json"
    write_opcode_trace_file(
        output,
        {
            f"tests/{subdir}/test_mod.py::test_case": (
                OpcodeCount.model_validate({"ADD": count})
            )
            for subdir, count in [("a", 1), ("b", 2), ("c", 3)]
        },
    )
    results = json.loads(output.read_text(encoding="utf-8"))
    assert results == {
        "test_mod.py__test_case": {"ADD": 1},
        "test_mod.py__test_case__1": {"ADD": 2},
        "test_mod.py__test_case__2": {"ADD": 3},
    }


def test_write_empty_collection(tmp_path: Path) -> None:
    """Write an empty JSON object when nothing was collected."""
    output = tmp_path / "opcodes_tracing.json"
    write_opcode_trace_file(output, {})
    assert json.loads(output.read_text(encoding="utf-8")) == {}


def test_write_creates_parent_directories(tmp_path: Path) -> None:
    """Create missing parent directories for the output path."""
    output = tmp_path / "nested" / "dir" / "opcodes_tracing.json"
    write_opcode_trace_file(
        output, {"tests/t.py::test_x": OpcodeCount.model_validate({"STOP": 1})}
    )
    assert output.is_file()
