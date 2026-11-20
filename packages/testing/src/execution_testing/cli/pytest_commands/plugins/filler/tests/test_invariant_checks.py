"""Test filling with `--invariant-checks`."""

import textwrap

import pytest

# The BAL checks need a fork with block access lists, and the defect
# conftest breaks Amsterdam's BAL builder.
FORK = "Amsterdam"

TEST_MODULE_DIR = "tests/amsterdam/dummy_test_module"

# Each block reads slot 0 and writes a different slot, so a block checked
# against another block's witness breaks the witness bounds.
TWO_BLOCK_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Block,
        BlockchainTestFiller,
        Hash,
        Op,
        Transaction,
    )

    @pytest.mark.valid_at("{fork}")
    def test_case(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
        contract = pre.deploy_contract(
            Op.SSTORE(Op.CALLDATALOAD(0), Op.ADD(Op.SLOAD(0), 1))
        )
        sender = pre.fund_eoa()

        def write(slot: int) -> Transaction:
            return Transaction(sender=sender, to=contract, data=Hash(slot))

        blockchain_test(
            pre=pre,
            post={{contract: Account(storage={{1: 1, 2: 1}})}},
            blocks=[Block(txs=[write(1)]), Block(txs=[write(2)])],
        )
    """
)

# The same read and write as a state test, which CI checks through its
# blockchain form.
STATE_TEST_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Account,
        Alloc,
        Hash,
        Op,
        StateTestFiller,
        Transaction,
    )

    @pytest.mark.valid_at("{fork}")
    def test_case(state_test: StateTestFiller, pre: Alloc) -> None:
        contract = pre.deploy_contract(
            Op.SSTORE(Op.CALLDATALOAD(0), Op.ADD(Op.SLOAD(0), 1))
        )
        tx = Transaction(sender=pre.fund_eoa(), to=contract, data=Hash(1))
        state_test(
            pre=pre, post={{contract: Account(storage={{1: 1}})}}, tx=tx
        )
    """
)

# Breaks the EELS block access list builder, which the BAL hash in the
# header then commits to, so only the invariant checks can notice.
DEFECT_CONFTEST = textwrap.dedent(
    """\
    import pytest

    from ethereum.forks.amsterdam import block_access_lists

    @pytest.fixture(autouse=True)
    def broken_bal_builder(monkeypatch):
        monkeypatch.setattr(
            block_access_lists, "{function}", lambda *args, **kwargs: None
        )
    """
)

# Plants a violation in a check every fork runs, independent of the BAL.
PLANTED_CONFTEST = textwrap.dedent(
    """\
    import pytest

    from execution_testing.specs import invariants
    from execution_testing.specs.invariants import InvariantViolationError

    @pytest.fixture(autouse=True)
    def planted_violation(monkeypatch):
        def planted(*args):
            raise InvariantViolationError(invariant="planted", message="")

        monkeypatch.setattr(invariants, "check_gas_accounting", planted)
    """
)

# Halves the fee EELS pays Osaka's coinbase, which a SELFDESTRUCT could
# otherwise explain away before EIP-8246.
HALVED_COINBASE_FEE_CONFTEST = textwrap.dedent(
    """\
    import pytest
    from ethereum_types.numeric import U256

    from ethereum.forks.osaka import fork

    @pytest.fixture(autouse=True)
    def halved_coinbase_fee(monkeypatch):
        create_ether = fork.create_ether
        monkeypatch.setattr(
            fork,
            "create_ether",
            lambda state, address, amount: create_ether(
                state, address, U256(int(amount) // 2)
            ),
        )
    """
)


def fill(
    pytester: pytest.Pytester,
    module_source: str,
    *args: str,
    fork: str = FORK,
) -> pytest.RunResult:
    """Fill a one-test module at the given fork with the checks on."""
    module_dir = pytester.path / TEST_MODULE_DIR
    module_dir.mkdir(parents=True)
    module = module_dir / "test_dummy.py"
    module.write_text(module_source.format(fork=fork))
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    # An in-process run restores `sys.modules` but not the `ethereum`
    # package's `trace` attribute, so a second run's t8n installs its tracer
    # on the first run's `ethereum.trace` while the EVM emits to a new one.
    # Each fill gets its own process instead.
    return pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        fork,
        "--no-html",
        "--output",
        "fixtures",
        "--invariant-checks",
        *args,
        str(module.relative_to(pytester.path)),
    )


def test_cached_formats_use_their_own_witness(
    pytester: pytest.Pytester,
) -> None:
    """
    Fill two formats of one test, the second from the t8n output cache: each
    block is checked against its own witness and both fill cleanly.
    """
    result = fill(
        pytester,
        TWO_BLOCK_MODULE,
        "-m",
        "blockchain_test or blockchain_test_engine",
    )
    result.assert_outcomes(passed=2, failed=0)


@pytest.mark.parametrize(
    "module_source,fixture_format",
    [
        pytest.param(TWO_BLOCK_MODULE, "blockchain_test", id="blockchain"),
        pytest.param(
            STATE_TEST_MODULE,
            "blockchain_test_from_state_test",
            id="state_test_in_blockchain_form",
        ),
    ],
)
@pytest.mark.parametrize(
    "broken_function,invariant",
    [
        pytest.param(
            "add_storage_read", "bal_access_witness", id="dropped_reads"
        ),
        pytest.param(
            "add_nonce_change", "bal_state_diff", id="dropped_nonce_changes"
        ),
    ],
)
def test_bal_defect_fails(
    pytester: pytest.Pytester,
    capsys: pytest.CaptureFixture[str],
    module_source: str,
    fixture_format: str,
    broken_function: str,
    invariant: str,
) -> None:
    """A defect in the EELS BAL builder fails the fill with its invariant."""
    (pytester.path / "conftest.py").write_text(
        DEFECT_CONFTEST.format(function=broken_function)
    )
    result = fill(pytester, module_source, "-m", fixture_format)
    capsys.readouterr()  # suppress inner failure bleed
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines(
        [f"*InvariantViolationError: [[]{invariant}]*"]
    )


def test_state_test_is_checked(
    pytester: pytest.Pytester, capsys: pytest.CaptureFixture[str]
) -> None:
    """A state test's own fill runs the checks too."""
    (pytester.path / "conftest.py").write_text(PLANTED_CONFTEST)
    result = fill(pytester, STATE_TEST_MODULE, "-m", "state_test")
    capsys.readouterr()  # suppress inner failure bleed
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines(["*InvariantViolationError: [[]planted]*"])


def test_state_test_blockchain_form_checks_only_the_access_list(
    pytester: pytest.Pytester,
) -> None:
    """
    A state test's blockchain form leaves the checks its state form ran,
    so the planted gas violation stays silent there and the fill passes.
    """
    (pytester.path / "conftest.py").write_text(PLANTED_CONFTEST)
    result = fill(
        pytester,
        STATE_TEST_MODULE,
        "-m",
        "blockchain_test_from_state_test",
    )
    result.assert_outcomes(passed=1, failed=0)


def test_lost_ether_fails_before_selfdestruct_burns(
    pytester: pytest.Pytester, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Before EIP-8246 a block that ran no SELFDESTRUCT must still conserve
    ether, so a halved coinbase fee at Osaka fails the fill.
    """
    (pytester.path / "conftest.py").write_text(HALVED_COINBASE_FEE_CONFTEST)
    result = fill(
        pytester,
        STATE_TEST_MODULE,
        "-m",
        "state_test",
        fork="Osaka",
    )
    capsys.readouterr()  # suppress inner failure bleed
    result.assert_outcomes(passed=0, failed=1)


def test_fork_without_bal_fills_cleanly(pytester: pytest.Pytester) -> None:
    """Before EIP-7928 the checks run without tracing storage accesses."""
    result = fill(
        pytester,
        TWO_BLOCK_MODULE,
        "-m",
        "blockchain_test",
        fork="Osaka",
    )
    result.assert_outcomes(passed=1, failed=0)
