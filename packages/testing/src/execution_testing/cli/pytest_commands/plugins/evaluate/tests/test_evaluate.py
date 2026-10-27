"""Test the `evaluate` command plugin."""

import json
import textwrap
from pathlib import Path
from typing import Any, Generator
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from execution_testing.base_types import HexNumber
from execution_testing.forks import Cancun

from ..evaluate import _test_params

EVALUATION_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Block,
        Op,
        SpecRunner,
        Transaction,
    )


    @pytest.mark.valid_at("Cancun")
    @pytest.mark.parametrize("value", [1, 2])
    def eval_store_value(spec: SpecRunner, pre: Alloc, value: int) -> None:
        contract = pre.deploy_contract(
            code=Op.SSTORE(0, Op.ADD(Op.CALLDATALOAD(0), 1)) + Op.STOP
        )
        tx = Transaction(to=contract, gas_limit=100_000, sender=pre.fund_eoa())
        for data in range(3):
            run = spec.run(pre=pre, txs=[tx.copy(data=data.to_bytes(32))])
            assert int(run.receipts[0].status) == 1
            assert run.storage(contract, 0) == data + 1
        spec.record(value=value)
        assert value == 1, f"value is {value}"


    @pytest.mark.valid_at("Cancun")
    def eval_receipts_and_traces(spec: SpecRunner, pre: Alloc) -> None:
        contract = pre.deploy_contract(code=Op.SSTORE(Op.NUMBER, 1) + Op.STOP)
        sender = pre.fund_eoa()
        txs = [
            Transaction(to=contract, gas_limit=100_000, sender=sender),
            Transaction(to=contract, gas_limit=100_000, sender=sender),
        ]
        run = spec.run(pre=pre, txs=txs, traces=True)
        gas_used = [int(receipt.gas_used) for receipt in run.receipts]
        assert all(gas > 0 for gas in gas_used)
        assert sum(gas_used) == int(run.receipts[-1].cumulative_gas_used)
        traces = run.traces[0]
        assert traces is not None
        assert len(traces.root) == 2


    @pytest.mark.valid_at("Cancun")
    def eval_block_numbers(spec: SpecRunner, pre: Alloc) -> None:
        contract = pre.deploy_contract(
            code=Op.SSTORE(Op.NUMBER, Op.NUMBER) + Op.STOP
        )
        sender = pre.fund_eoa()
        tx = Transaction(to=contract, gas_limit=100_000, sender=sender)
        tx2 = Transaction(to=contract, gas_limit=100_000, sender=sender)
        run = spec.run(
            pre=pre, blocks=[Block(number=1000, txs=[tx]), Block(txs=[tx2])]
        )
        assert run.storage(contract, 1000) == 1000
        assert run.storage(contract, 1001) == 1001
        with pytest.raises(ValueError, match="consecutive"):
            spec.run(
                pre=pre,
                blocks=[Block(number=1000, txs=[tx]), Block(number=1005)],
            )
    """
)

OUTCOMES_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Block,
        Hash,
        Op,
        SpecRunner,
        TraceError,
        Transaction,
    )


    @pytest.mark.valid_at("Cancun")
    def eval_outcomes(spec: SpecRunner, pre: Alloc) -> None:
        emitter = pre.deploy_contract(code=Op.LOG1(0, 0, 0xAA) + Op.STOP)
        reverter = pre.deploy_contract(code=Op.REVERT(0, 0))
        caller = pre.deploy_contract(
            code=Op.POP(Op.CALL(gas=100_000, address=reverter)) + Op.STOP
        )
        sender = pre.fund_eoa()
        log_tx = Transaction(to=emitter, gas_limit=100_000, sender=sender)
        revert_tx = Transaction(to=reverter, gas_limit=100_000, sender=sender)
        call_tx = Transaction(to=caller, gas_limit=200_000, sender=sender)
        block = Block(txs=[log_tx, revert_tx, call_tx])

        run = spec.run(pre=pre, blocks=[block], traces=True)
        assert run.tx(log_tx).successful
        assert [log.topics[0] for log in run.tx(log_tx).logs] == [Hash(0xAA)]
        assert run.tx(revert_tx).failed
        assert run.tx(revert_tx).error == TraceError.REVERT
        assert run.tx(revert_tx).logs == []
        assert run.tx(call_tx).error is None
        call_trace = run.tx(call_tx).trace
        assert call_trace is not None
        assert call_trace.at_address(reverter)[0].failed_at == Op.REVERT
        assert run.block(block).failed
        assert run.failed

        untraced = spec.run(pre=pre, txs=[log_tx])
        assert untraced.successful
        with pytest.raises(ValueError, match="traces=True"):
            untraced.tx(log_tx).trace
    """
)

TRACES_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Alloc,
        Conditional,
        Initcode,
        Op,
        SpecRunner,
        TraceError,
        Transaction,
        compute_create_address,
    )


    @pytest.mark.valid_at("Cancun")
    def eval_frames(spec: SpecRunner, pre: Alloc) -> None:
        # B stores when called with 2, re-enters itself with 2 when called
        # with 1, and reverts when called with 3.
        b = pre.deploy_contract(
            code=Conditional(
                condition=Op.EQ(Op.CALLDATALOAD(0), 3),
                if_true=Op.REVERT(0, 0),
                if_false=Conditional(
                    condition=Op.EQ(Op.CALLDATALOAD(0), 1),
                    if_true=Op.MSTORE(0, 2)
                    + Op.POP(
                        Op.CALL(gas=Op.GAS, address=Op.ADDRESS, args_size=32)
                    ),
                    if_false=Op.SSTORE(0, 1),
                ),
            )
            + Op.STOP
        )
        a = pre.deploy_contract(
            code=Op.MSTORE(0, 1)
            + Op.POP(Op.CALL(gas=200_000, address=b, args_size=32))
            + Op.MSTORE(0, 3)
            + Op.POP(Op.CALL(gas=200_000, address=b, args_size=32))
            + Op.STOP
        )
        tx = Transaction(to=a, gas_limit=500_000, sender=pre.fund_eoa())
        run = spec.run(pre=pre, txs=[tx], traces=True)

        assert run.tx(tx).successful
        assert run.storage(b, 0) == 1
        trace = run.tx(tx).trace
        assert trace is not None
        assert trace.error is None
        assert trace.addresses == [a, b]
        assert [frame.address for frame in trace.at_depth(1)] == [a]
        # Two calls from A to B are two frames; the re-entry is a third.
        calls = trace.at_depth(2)
        assert [frame.address for frame in calls] == [b, b]
        assert calls[0].error is None
        assert calls[1].error == TraceError.REVERT
        assert calls[1].failed_at == Op.REVERT
        assert [frame.address for frame in trace.at_depth(3)] == [b]
        assert [frame.depth for frame in trace.at_address(b)] == [2, 3, 2]
        # A frame holds only its own lines, not those of its calls.
        assert Op.SSTORE not in calls[0]
        assert Op.SSTORE in trace.at_depth(3)[0]


    @pytest.mark.valid_at("Cancun")
    def eval_delegatecall_and_create(spec: SpecRunner, pre: Alloc) -> None:
        library = pre.deploy_contract(code=Op.SSTORE(5, 5) + Op.STOP)
        a = pre.deploy_contract(
            code=Op.POP(Op.DELEGATECALL(gas=100_000, address=library))
            # Initcode at 0 returns no code; at 1 it is INVALID.
            + Op.MSTORE8(0, 0x00)
            + Op.MSTORE8(1, 0xFE)
            + Op.POP(Op.CREATE(value=0, offset=0, size=1))
            + Op.POP(Op.CREATE2(value=0, offset=1, size=1, salt=0))
            + Op.STOP
        )
        tx = Transaction(to=a, gas_limit=500_000, sender=pre.fund_eoa())
        run = spec.run(pre=pre, txs=[tx], traces=True)

        created = compute_create_address(address=a, nonce=1)
        assert created in run.post
        # The library's code wrote to A's storage.
        assert run.storage(a, 5) == 5
        trace = run.tx(tx).trace
        assert trace is not None
        delegated, create, failed_create2 = trace.at_depth(2)
        assert delegated.address == a
        assert create.address == created
        assert failed_create2.address is None
        assert failed_create2.error == TraceError.INVALID_OPCODE
        assert failed_create2.failed_at == Op.INVALID
        assert trace.at_address(library) == []
        assert trace.addresses == [a, created]


    @pytest.mark.valid_at("Cancun")
    def eval_creating_transaction(spec: SpecRunner, pre: Alloc) -> None:
        tx = Transaction(
            to=None,
            data=Initcode(deploy_code=Op.STOP),
            gas_limit=200_000,
            sender=pre.fund_eoa(),
        )
        run = spec.run(pre=pre, txs=[tx], traces=True)

        trace = run.tx(tx).trace
        assert trace is not None
        assert trace.addresses == [tx.created_contract]
        assert trace.ops[-1] == Op.RETURN


    @pytest.mark.valid_at("Cancun")
    def eval_failures(spec: SpecRunner, pre: Alloc) -> None:
        underflow = pre.deploy_contract(
            code=Op.SSTORE(0, 1) + Op.SSTORE(1, 1) + Op.ADD
        )
        undefined = pre.deploy_contract(code=bytes([0x0C]))
        sstore = pre.deploy_contract(code=Op.SSTORE(0, 1) + Op.STOP)
        sender = pre.fund_eoa()
        underflow_tx = Transaction(
            to=underflow, gas_limit=100_000, sender=sender
        )
        undefined_tx = Transaction(
            to=undefined, gas_limit=100_000, sender=sender
        )
        # Enough for the pushes, not for SSTORE.
        out_of_gas_tx = Transaction(
            to=sstore, gas_limit=21_010, sender=sender
        )
        run = spec.run(
            pre=pre,
            txs=[underflow_tx, undefined_tx, out_of_gas_tx],
            traces=True,
        )

        assert all(tx.failed for tx in run.txs)
        trace = run.tx(underflow_tx).trace
        assert trace is not None
        store = [Op.PUSH1, Op.PUSH1, Op.SSTORE]
        assert trace.ops == store + store + [Op.ADD]
        assert trace.count(Op.SSTORE) == 2
        assert Op.SLOAD not in trace
        assert len(trace) == 7
        assert trace.error == TraceError.STACK_UNDERFLOW
        assert trace.failed_at == Op.ADD

        trace = run.tx(undefined_tx).trace
        assert trace is not None
        assert trace.ops == []
        assert trace.error == TraceError.INVALID_OPCODE
        assert trace.failed_at is None

        assert run.tx(out_of_gas_tx).error == TraceError.OUT_OF_GAS
        trace = run.tx(out_of_gas_tx).trace
        assert trace is not None
        assert trace.failed_at == Op.SSTORE
    """
)

FILL_MODULE = textwrap.dedent(
    """\
    import pytest

    @pytest.mark.valid_at("Cancun")
    def test_not_collected(state_test) -> None:
        raise AssertionError("evaluate must not collect fill tests")
    """
)


@pytest.fixture(autouse=True)
def restore_chain_config_defaults() -> Generator[None, None, None]:
    """Reset the default chain id set by the nested in-process session."""
    from execution_testing.test_types.chain_config_types import (
        DEFAULT_CHAIN_ID,
        ChainConfigDefaults,
    )

    yield
    ChainConfigDefaults.chain_id = DEFAULT_CHAIN_ID


@pytest.fixture
def evaluation_tests(pytester: pytest.Pytester) -> pytest.Pytester:
    """Write the evaluation module and a fill module to the test dir."""
    tests_dir = pytester.mkdir("tests") / "cancun" / "evaluations"
    tests_dir.mkdir(parents=True)
    (tests_dir / "eval_examples.py").write_text(EVALUATION_MODULE)
    (tests_dir / "test_fill_only.py").write_text(FILL_MODULE)
    pytester.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands/pytest_ini_files/"
            "pytest-evaluate.ini"
        )
    )
    return pytester


def test_evaluate(evaluation_tests: pytest.Pytester) -> None:
    """Run the evaluations and check the outcomes and the report."""
    report_path = Path(evaluation_tests.path) / "report.json"
    result = evaluation_tests.runpytest(
        "-c",
        "pytest-evaluate.ini",
        "--fork",
        "Cancun",
        "--eval-report",
        str(report_path),
        "tests/",
    )
    result.assert_outcomes(passed=3, failed=1)
    assert any("evaluation results" in line for line in result.outlines)

    report_json = json.loads(report_path.read_text())
    assert report_json["version"] == 1
    assert set(report_json["env"]) == {"t8n", "commit"}
    report = {
        entry["test"].split("::")[-1]: entry
        for entry in report_json["results"]
    }
    assert set(report) == {
        "eval_store_value[Cancun-1]",
        "eval_store_value[Cancun-2]",
        "eval_receipts_and_traces[Cancun]",
        "eval_block_numbers[Cancun]",
    }
    passed = report["eval_store_value[Cancun-1]"]
    assert passed["outcome"] == "passed"
    assert passed["fork"] == "Cancun"
    assert passed["params"] == {"value": 1}
    assert passed["runs"] == 3
    assert passed["records"] == {"value": 1}
    failed = report["eval_store_value[Cancun-2]"]
    assert failed["outcome"] == "failed"
    assert failed["params"] == {"value": 2}
    assert failed["records"] == {"value": 2}
    assert "value is 2" in failed["failure"]
    assert report["eval_block_numbers[Cancun]"]["params"] == {}


class ModelWithCallable(BaseModel):
    """A pydantic model with a field pydantic cannot serialize."""

    callback: Any = lambda: None


def test_test_params_skips_unsupported_values() -> None:
    """Test that a parameter of an unsupported type is left out."""
    item = Mock()
    item.callspec.params = {
        "fork": Cancun,
        "size": HexNumber(32),
        "callback": object(),
        "model": ModelWithCallable(),
    }
    assert _test_params(item) == {"size": 32}


def test_test_params_without_parametrization() -> None:
    """Test that a test without parameters has none."""
    assert _test_params(Mock(spec=pytest.Item)) == {}


def run_traced_evaluations(
    pytester: pytest.Pytester,
    capsys: pytest.CaptureFixture[str],
    module_name: str,
    module: str,
) -> pytest.RunResult:
    """
    Run the evaluations of `module` for Cancun.

    Runs in a subprocess: a second in-process session of the in-process
    transition tool writes no traces.
    """
    tests_dir = pytester.mkdir("tests") / "cancun"
    tests_dir.mkdir()
    (tests_dir / module_name).write_text(module)
    pytester.copy_example(
        name=(
            "src/execution_testing/cli/pytest_commands/pytest_ini_files/"
            "pytest-evaluate.ini"
        )
    )
    result = pytester.runpytest_subprocess(
        "-c", "pytest-evaluate.ini", "--fork", "Cancun", "tests/"
    )
    capsys.readouterr()
    return result


def test_evaluate_has_no_traces_option(
    evaluation_tests: pytest.Pytester,
) -> None:
    """Test that `evaluate` rejects `--traces`: runs ask for traces."""
    result = evaluation_tests.runpytest(
        "-c", "pytest-evaluate.ini", "--traces", "tests/"
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*unrecognized arguments: --traces*"])


def test_evaluate_outcomes(
    pytester: pytest.Pytester, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Run an evaluation that checks the outcome of transactions, collecting
    traces for one run only.
    """
    result = run_traced_evaluations(
        pytester, capsys, "eval_outcomes.py", OUTCOMES_MODULE
    )
    result.assert_outcomes(passed=1)


def test_evaluate_traces(
    pytester: pytest.Pytester, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Run evaluations that check the frames, opcodes and errors of the traces
    of transactions.
    """
    result = run_traced_evaluations(
        pytester, capsys, "eval_traces.py", TRACES_MODULE
    )
    result.assert_outcomes(passed=4)
