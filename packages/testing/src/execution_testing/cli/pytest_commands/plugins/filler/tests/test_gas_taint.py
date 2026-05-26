"""Unit tests for the gas_taint plugin."""

from __future__ import annotations

from typing import Any, Callable, Iterator, cast
from unittest.mock import MagicMock

import pytest

from execution_testing.base_types import Account, Address
from execution_testing.base_types.base_types import (
    HashInt,
    HexNumber,
    ZeroPaddedHexNumber,
)
from execution_testing.base_types.composite_types import Storage
from execution_testing.cli.pytest_commands.plugins.filler.gas_taint import (
    GasTainted,
    _is_tainted,
    _origins_of,
    collect_taint_hits,
    install_taint,
    uninstall_taint,
)
from execution_testing.exceptions.exceptions.transaction import (
    TransactionException,
)
from execution_testing.forks.forks.forks import Cancun
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.specs.blockchain import Block, BlockchainTest, Header
from execution_testing.specs.state import StateTest
from execution_testing.test_types.account_types import Alloc
from execution_testing.test_types.receipt_types import TransactionReceipt
from execution_testing.test_types.transaction_types import Transaction

# ---------------------------------------------------------------------------
# GasTainted carrier
# ---------------------------------------------------------------------------


class TestGasTaintedCarrier:
    """The int subclass that carries provenance through arithmetic."""

    def test_construction_attaches_origins(self) -> None:
        """Test construction attaches origins."""
        t = GasTainted(42, ("source.X",))
        assert int(t) == 42
        assert t.origins == ("source.X",)
        assert isinstance(t, int)

    def test_default_origin_when_empty(self) -> None:
        """Test default origin when empty."""
        # An empty tuple gets replaced with the "?" placeholder so callers
        # can always rely on ``origins`` being non-empty.
        t = GasTainted(7)
        assert t.origins == ("?",)

    def test_is_tainted_and_origins_of(self) -> None:
        """Test is tainted and origins of."""
        assert _is_tainted(GasTainted(1, ("X",)))
        assert not _is_tainted(1)
        assert _origins_of(GasTainted(5, ("Y",))) == ("Y",)
        assert _origins_of(5) is None

    @pytest.mark.parametrize(
        "op,expected",
        [
            (lambda a, b: a + b, 13),
            (lambda a, b: a - b, 7),
            (lambda a, b: a * b, 30),
            (lambda a, b: a // b, 3),
            (lambda a, b: a % b, 1),
        ],
    )
    def test_arithmetic_preserves_taint(
        self, op: Callable[[int, int], int], expected: int
    ) -> None:
        """Test arithmetic preserves taint."""
        a = GasTainted(10, ("A",))
        result = op(a, 3)
        assert isinstance(result, GasTainted)
        assert int(result) == expected
        assert result.origins == ("A",)

    def test_negation_preserves_taint(self) -> None:
        """Test negation preserves taint."""
        n = -GasTainted(5, ("X",))
        assert isinstance(n, GasTainted)
        assert int(n) == -5
        assert n.origins == ("X",)

    def test_reflected_ops_preserve_taint(self) -> None:
        """Test reflected ops preserve taint."""
        # ``5 + GasTainted(3)`` triggers __radd__ on the tainted side.
        result = 5 + GasTainted(3, ("R",))
        assert isinstance(result, GasTainted)
        assert int(result) == 8
        assert result.origins == ("R",)

    def test_merge_origins_unions(self) -> None:
        """Test merge origins unions."""
        a = GasTainted(2, ("A",))
        b = GasTainted(3, ("B",))
        s = a + b
        # Order preserved (a's origins first, then b's).
        assert s.origins == ("A", "B")

    def test_merge_origins_deduplicates(self) -> None:
        """Test merge origins deduplicates."""
        a = GasTainted(2, ("X", "Y"))
        b = GasTainted(3, ("Y", "Z"))
        s = a + b
        assert s.origins == ("X", "Y", "Z")

    def test_rmul_with_bytes_returns_notimplemented_gracefully(self) -> None:
        """Test rmul with bytes returns notimplemented gracefully."""
        # ``b"\x01" * GasTainted(n)`` is a real expression in tests that
        # compute calldata sizes from gas. ``bytes.__mul__`` doesn't accept
        # an arbitrary int subclass, so Python falls back to
        # ``GasTainted.__rmul__(n, b"...")``; ``int.__rmul__`` returns
        # ``NotImplemented``, which the dunder must forward — wrapping it
        # in a new GasTainted blows up on ``int(NotImplemented)``.
        result = b"\x01" * GasTainted(5, ("X",))
        assert result == b"\x01\x01\x01\x01\x01"
        assert type(result) is bytes


# ---------------------------------------------------------------------------
# install_taint / uninstall_taint
# ---------------------------------------------------------------------------


@pytest.fixture
def taint_installed() -> Iterator[None]:
    """Install taint patches for one test, then revert."""
    install_taint()
    try:
        yield
    finally:
        uninstall_taint()


@pytest.mark.usefixtures("taint_installed")
class TestTaintInstallation:
    """The monkey-patches that make gas values carry provenance."""

    def test_bytecode_gas_cost_is_tainted(self) -> None:
        """Test bytecode gas cost is tainted."""
        from execution_testing import Op
        from execution_testing.forks.forks.forks import Cancun

        result = Op.PUSH1[1].gas_cost(Cancun)
        assert _is_tainted(result)
        # Origin can be either the per-opcode label (when the wrapped
        # opcode_gas_calculator already returns tainted gas_costs.X) or
        # the outer Bytecode.gas_cost label (when summing untainted
        # constants). The important guarantee is that *some* gas origin
        # is recorded.
        assert any("gas" in o for o in cast(GasTainted, result).origins)

    def test_fork_gas_costs_fields_are_tainted(self) -> None:
        """Test fork gas costs fields are tainted."""
        from execution_testing.forks.forks.forks import Cancun

        gc = Cancun.gas_costs()
        assert _is_tainted(gc.STORAGE_SET)
        assert (
            "gas_costs.STORAGE_SET" in cast(GasTainted, gc.STORAGE_SET).origins
        )

    def test_hashint_preserves_taint(self) -> None:
        """Test hashint preserves taint."""
        # HashInt inherits from FixedSizeHexNumber, *not* from Number.
        # This is the case that motivated patching both __new__ methods.
        tainted = GasTainted(123, ("src",))
        h = HashInt(tainted)
        assert _is_tainted(h)
        assert cast(GasTainted, h).origins == ("src",)

    def test_hexnumber_preserves_taint(self) -> None:
        """Test hexnumber preserves taint."""
        # HexNumber inherits from Number — covered by the Number.__new__
        # patch.
        tainted = GasTainted(456, ("src",))
        x = HexNumber(tainted)
        assert _is_tainted(x)

    def test_zero_padded_hexnumber_preserves_taint(self) -> None:
        """Test zero padded hexnumber preserves taint."""
        tainted = GasTainted(789, ("src",))
        x = ZeroPaddedHexNumber(tainted)
        assert _is_tainted(x)

    def test_plain_value_through_constructors_is_not_tainted(self) -> None:
        """Test plain value through constructors is not tainted."""
        # The patch must be opt-in: an ordinary int passed through these
        # constructors must NOT become tainted, or every storage slot
        # would be flagged.
        assert not _is_tainted(HashInt(42))
        assert not _is_tainted(HexNumber(42))

    def test_storage_dict_preserves_taint(self) -> None:
        """Test storage dict preserves taint."""
        # Storage is a Pydantic RootModel; the value goes through HashInt
        # coercion. This is the critical end-to-end taint path.
        tainted = GasTainted(99, ("from_test",))
        s = Storage(cast(Any, {0: tainted}))
        stored = next(iter(s.root.values()))
        assert _is_tainted(stored)
        assert cast(GasTainted, stored).origins == ("from_test",)

    def test_install_is_idempotent(self) -> None:
        """Test install is idempotent."""
        install_taint()
        try:
            install_taint()  # second call must not double-wrap.
            from execution_testing import Op
            from execution_testing.forks.forks.forks import Cancun

            result = Op.PUSH1[1].gas_cost(Cancun)
            # If install double-wrapped, origins would contain
            # 'Bytecode.gas_cost' twice. The carrier dedupes within a
            # tuple, but the double-wrap would still produce nested
            # GasTainted instances and confused arithmetic.
            assert _is_tainted(result)
            # Sanity check: it's a flat int subclass, not a nested
            # GasTainted-of-GasTainted.
            assert type(result).__name__ == "GasTainted"
            assert type(int(result)) is int
        finally:
            uninstall_taint()

    def test_uninstall_reverts_patches(self) -> None:
        """Test uninstall reverts patches."""
        install_taint()
        uninstall_taint()
        from execution_testing import Op
        from execution_testing.forks.forks.forks import Cancun

        result = Op.PUSH1[1].gas_cost(Cancun)
        assert not _is_tainted(result)
        gc = Cancun.gas_costs()
        assert not _is_tainted(gc.STORAGE_SET)


# ---------------------------------------------------------------------------
# collect_taint_hits walker
#
# These tests instantiate real ``StateTest`` / ``BlockchainTest`` /
# ``BenchmarkTest`` Pydantic models so that the walker's typed signature
# guards the field surface. Renaming or retyping a sink field becomes a
# compile-time error rather than a silent miss.
# ---------------------------------------------------------------------------


_ADDR = Address(0x1234)


def _state_test_with_storage(value: int | None) -> StateTest:
    storage = (
        Storage(cast(Any, {0: value})) if value is not None else Storage()
    )
    return StateTest(
        fork=Cancun,
        pre=Alloc(),
        post=Alloc(cast(Any, {_ADDR: Account(storage=storage)})),
        tx=Transaction(),
    )


def _node_with_marker(name: str | None) -> pytest.Item:
    """Mock ``pytest.Item`` whose ``get_closest_marker`` returns truthy."""
    node = MagicMock(spec=pytest.Item)
    node.get_closest_marker.side_effect = lambda n: (
        object() if name is not None and n == name else None
    )
    return cast(pytest.Item, node)


@pytest.mark.usefixtures("taint_installed")
class TestStorageSink:
    """
    ``post[addr].storage[slot]`` requires taint to flag.

    The ``taint_installed`` fixture is needed so that ``GasTainted``
    values survive the ``Storage`` Pydantic validator (which constructs
    a ``HashInt`` for each value); the walker itself doesn't depend on
    installation.
    """

    def test_tainted_storage_value_is_recorded(self) -> None:
        """Test tainted storage value is recorded."""
        test = _state_test_with_storage(GasTainted(42, ("Y",)))
        hits = collect_taint_hits(test, None)
        assert len(hits) == 1
        assert hits[0]["kind"] == "storage"
        assert hits[0]["value"] == 42
        assert hits[0]["origins"] == ["Y"]
        assert str(_ADDR) in hits[0]["location"]

    def test_untainted_storage_value_is_skipped(self) -> None:
        """Test untainted storage value is skipped."""
        # A plain int in storage — the whole point of using taint here is
        # that storage slots can hold anything.
        test = _state_test_with_storage(42)
        assert collect_taint_hits(test, None) == []

    def test_account_with_no_storage_is_skipped(self) -> None:
        """Test account with no storage is skipped."""
        test = StateTest(
            fork=Cancun,
            pre=Alloc(),
            post=Alloc(cast(Any, {_ADDR: Account()})),
            tx=Transaction(),
        )
        assert collect_taint_hits(test, None) == []

    def test_empty_post_is_skipped(self) -> None:
        """Test empty post is skipped."""
        test = StateTest(
            fork=Cancun, pre=Alloc(), post=Alloc(), tx=Transaction()
        )
        assert collect_taint_hits(test, None) == []


class TestReceiptSink:
    """``expected_receipt`` fields are flagged on presence, not taint."""

    def test_cumulative_gas_used_recorded(self) -> None:
        """Test cumulative gas used recorded."""
        tx = Transaction()
        tx.expected_receipt = TransactionReceipt(cumulative_gas_used=21000)
        test = StateTest(fork=Cancun, pre=Alloc(), post=Alloc(), tx=tx)
        hits = collect_taint_hits(test, None)
        assert len(hits) == 1
        assert hits[0]["kind"] == "receipt"
        assert hits[0]["location"] == "cumulative_gas_used"
        assert hits[0]["value"] == 21000
        # No taint involved — origins absent from the hit dict.
        assert "origins" not in hits[0]

    def test_all_three_receipt_fields(self) -> None:
        """Test all three receipt fields."""
        tx = Transaction()
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=100, gas_used=200, blob_gas_used=300
        )
        test = StateTest(fork=Cancun, pre=Alloc(), post=Alloc(), tx=tx)
        hits = collect_taint_hits(test, None)
        locations = {h["location"] for h in hits}
        assert locations == {
            "cumulative_gas_used",
            "gas_used",
            "blob_gas_used",
        }

    def test_no_expected_receipt_skipped(self) -> None:
        """Test no expected receipt skipped."""
        test = StateTest(
            fork=Cancun, pre=Alloc(), post=Alloc(), tx=Transaction()
        )
        assert collect_taint_hits(test, None) == []


class TestHeaderAndBlockSinks:
    """``header_verify`` and ``expected_gas_used`` flagged on presence."""

    def test_header_verify_blob_gas_used(self) -> None:
        """Test header verify blob gas used."""
        block = Block(header_verify=Header(blob_gas_used=131072))
        test = BlockchainTest(
            fork=Cancun, pre=Alloc(), post=Alloc(), blocks=[block]
        )
        hits = collect_taint_hits(test, None)
        assert len(hits) == 1
        assert hits[0]["kind"] == "header"
        assert hits[0]["location"] == "block[0].blob_gas_used"
        assert hits[0]["value"] == 131072

    def test_block_expected_gas_used(self) -> None:
        """Test block expected gas used."""
        block = Block(expected_gas_used=HexNumber(199_156))
        test = BlockchainTest(
            fork=Cancun, pre=Alloc(), post=Alloc(), blocks=[block]
        )
        hits = collect_taint_hits(test, None)
        # Block inherits gas_used / blob_gas_used from Header (both
        # default None), so only the explicit expected_gas_used is
        # recorded.
        assert len(hits) == 1
        assert hits[0]["kind"] == "block_expected_gas_used"
        assert hits[0]["value"] == 199_156

    def test_multiple_blocks_indexed(self) -> None:
        """Test multiple blocks indexed."""
        blocks = [
            Block(expected_gas_used=HexNumber(100)),
            Block(expected_gas_used=HexNumber(200)),
        ]
        test = BlockchainTest(
            fork=Cancun, pre=Alloc(), post=Alloc(), blocks=blocks
        )
        hits = collect_taint_hits(test, None)
        assert {h["location"] for h in hits} == {
            "block[0].expected_gas_used",
            "block[1].expected_gas_used",
        }


class TestBenchmarkSink:
    """``expected_benchmark_gas_used`` is recorded only on BenchmarkTest."""

    def test_skipped_on_non_benchmark_test(self) -> None:
        """Test skipped on non benchmark test."""
        # The filler auto-defaults expected_benchmark_gas_used on every
        # test; without the isinstance(test, BenchmarkTest) gate, this
        # would emit a benchmark hit even on a plain StateTest.
        test = StateTest(
            fork=Cancun, pre=Alloc(), post=Alloc(), tx=Transaction()
        )
        # Sanity: set it just like the filler would for non-benchmark
        # tests.
        test.expected_benchmark_gas_used = HexNumber(120_000_000)
        assert collect_taint_hits(test, None) == []

    def test_recorded_on_benchmark_test(self) -> None:
        """Test recorded on benchmark test."""
        bench = BenchmarkTest(
            fork=Cancun,
            pre=Alloc(),
            tx=Transaction(),
            expected_benchmark_gas_used=HexNumber(99_999_999),
        )
        hits = collect_taint_hits(bench, None)
        assert len(hits) == 1
        assert hits[0]["kind"] == "benchmark"
        assert hits[0]["value"] == 99_999_999


@pytest.mark.usefixtures("taint_installed")
class TestOOGExclusion:
    """OOG-style tests are excluded — they don't write to positive sinks."""

    def test_tx_error_set_excludes_test(self) -> None:
        """Test tx error set excludes test."""
        # Even with a tainted storage value, a tx.error means the test
        # expects rejection — drop it.
        tx = Transaction(error=TransactionException.INTRINSIC_GAS_TOO_LOW)
        test = StateTest(
            fork=Cancun,
            pre=Alloc(),
            post=Alloc(
                cast(
                    Any,
                    {
                        _ADDR: Account(
                            storage=Storage(
                                cast(Any, {0: GasTainted(1, ("X",))})
                            )
                        )
                    },
                )
            ),
            tx=tx,
        )
        assert collect_taint_hits(test, None) == []

    def test_block_exception_excludes_test(self) -> None:
        """Test block exception excludes test."""
        test = StateTest(
            fork=Cancun,
            pre=Alloc(),
            post=Alloc(
                cast(
                    Any,
                    {
                        _ADDR: Account(
                            storage=Storage(
                                cast(Any, {0: GasTainted(1, ("X",))})
                            )
                        )
                    },
                )
            ),
            tx=Transaction(),
            block_exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
        )
        assert collect_taint_hits(test, None) == []

    def test_exception_test_marker_excludes_test(self) -> None:
        """Test exception test marker excludes test."""
        test = _state_test_with_storage(GasTainted(1, ("X",)))
        node = _node_with_marker("exception_test")
        assert collect_taint_hits(test, node) == []


@pytest.mark.usefixtures("taint_installed")
class TestMixedSinks:
    """Multiple sinks can fire for the same test."""

    def test_storage_and_receipt(self) -> None:
        """Test storage and receipt."""
        tx = Transaction()
        tx.expected_receipt = TransactionReceipt(cumulative_gas_used=21000)
        test = StateTest(
            fork=Cancun,
            pre=Alloc(),
            post=Alloc(
                cast(
                    Any,
                    {
                        _ADDR: Account(
                            storage=Storage(
                                cast(Any, {0: GasTainted(50, ("X",))})
                            )
                        )
                    },
                )
            ),
            tx=tx,
        )
        hits = collect_taint_hits(test, None)
        kinds = {h["kind"] for h in hits}
        assert kinds == {"storage", "receipt"}
