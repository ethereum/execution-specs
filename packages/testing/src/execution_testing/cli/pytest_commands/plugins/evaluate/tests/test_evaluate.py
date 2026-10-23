"""Test the `evaluate` command plugin."""

import json
import textwrap
from pathlib import Path
from typing import Generator

import pytest

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
        run = spec.run(pre=pre, txs=txs)
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
        "--traces",
        "--eval-report",
        str(report_path),
        "tests/",
    )
    result.assert_outcomes(passed=3, failed=1)
    assert any("evaluation results" in line for line in result.outlines)

    report = {
        entry["test"].split("::")[-1]: entry
        for entry in json.loads(report_path.read_text())
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
    assert passed["runs"] == 3
    assert passed["records"] == {"value": 1}
    failed = report["eval_store_value[Cancun-2]"]
    assert failed["outcome"] == "failed"
    assert failed["records"] == {"value": 2}
    assert "value is 2" in failed["failure"]
