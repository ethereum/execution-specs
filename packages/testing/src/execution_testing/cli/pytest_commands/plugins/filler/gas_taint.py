"""
Pytest plugin that detects tests which positively assert specific gas values.

Enabled with ``--detect-gas-checks``. After each test body constructs its
``StateTest`` / ``BlockchainTest`` (but before the t8n runs), the walker
inspects two categories of sinks:

1. **Field-name implies gas assertion** — checked by presence (``is not
   None``). No taint needed because the field name itself is the signal:

   - ``tx.expected_receipt.{cumulative_gas_used, gas_used, blob_gas_used}``
   - ``block.header_verify.{gas_used, blob_gas_used}``
   - ``block.expected_gas_used``
   - ``self.expected_benchmark_gas_used``

2. **Storage slots in ``post``** — checked via taint propagation, since
   a storage slot can hold any value (counter, identifier, etc.) and the
   field alone doesn't tell us whether it's gas-related.

For the storage sink the plugin wraps gas-source functions
(``Bytecode.gas_cost``, ``fork.gas_costs()``, ``opcode_gas_calculator``,
``transaction_intrinsic_cost_calculator``) so they return a ``GasTainted``
int subclass carrying provenance, and patches ``Number.__new__`` /
``FixedSizeHexNumber.__new__`` so taint survives construction of
``HashInt`` / ``HexNumber`` / ``ZeroPaddedHexNumber``.

Tests with any sink hit get a ``gas_check`` marker attached and an entry
written to the JSON report. Tests that expect a transaction or block
exception (OOG-style) are skipped — their gas value lives on
``tx.gas_limit`` (an input, not a sink) and would never appear here.
"""

from __future__ import annotations

import json
from dataclasses import fields, replace
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Set,
    Tuple,
)

import pytest

from execution_testing.specs.base import BaseTest
from execution_testing.specs.benchmark import BenchmarkTest
from execution_testing.specs.blockchain import Block, BlockchainTest, Header
from execution_testing.specs.state import StateTest
from execution_testing.test_types.account_types import Alloc
from execution_testing.test_types.transaction_types import Transaction
from execution_testing.test_types.utils import Removable
from execution_testing.vm.bases import OpcodeBase

if TYPE_CHECKING:
    from xdist.workermanage import WorkerController

# ---------------------------------------------------------------------------
# Taint carrier
# ---------------------------------------------------------------------------


class GasTainted(int):
    """An int that remembers it was computed from a gas-cost source."""

    origins: Tuple[str, ...]

    def __new__(
        cls, value: int, origins: Tuple[str, ...] = ()
    ) -> "GasTainted":
        """Build a tainted int with attached provenance tuple."""
        inst = super().__new__(cls, int(value))
        inst.origins = origins or ("?",)
        return inst

    def _merge(self, other: Any) -> Tuple[str, ...]:
        o = getattr(other, "origins", ())
        return tuple(dict.fromkeys((*self.origins, *o)))

    def _propagate(self, raw: Any, other: Any) -> Any:
        if raw is NotImplemented:
            return NotImplemented
        return GasTainted(raw, self._merge(other))

    def __add__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__add__(self, o), o)

    def __radd__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__radd__(self, o), o)

    def __sub__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__sub__(self, o), o)

    def __rsub__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__rsub__(self, o), o)

    def __mul__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__mul__(self, o), o)

    def __rmul__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__rmul__(self, o), o)

    def __floordiv__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__floordiv__(self, o), o)

    def __rfloordiv__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__rfloordiv__(self, o), o)

    def __mod__(self, o: Any) -> Any:  # noqa: D105
        return self._propagate(int.__mod__(self, o), o)

    def __neg__(self) -> "GasTainted":  # noqa: D105
        return GasTainted(int.__neg__(self), self.origins)


def _origins_of(value: Any) -> Tuple[str, ...] | None:
    return getattr(value, "origins", None)


def _is_tainted(value: Any) -> bool:
    return _origins_of(value) is not None


# ---------------------------------------------------------------------------
# Source instrumentation
# ---------------------------------------------------------------------------

_installed = False
_originals: List[Callable[[], None]] = []


def _all_subclasses(cls: type) -> Set[type]:
    out: Set[type] = set()
    for sub in cls.__subclasses__():
        out.add(sub)
        out.update(_all_subclasses(sub))
    return out


def _patch_classmethod_if_local(
    cls: type, name: str, wrap: Callable[[type, Callable, tuple, dict], Any]
) -> None:
    """Wrap ``cls.name`` only if defined on ``cls`` itself (not inherited)."""
    if name not in cls.__dict__:
        return
    original_cm = cls.__dict__[name]
    if not isinstance(original_cm, classmethod):
        return
    original_fn = original_cm.__func__

    def wrapped(c: type, *args: Any, **kwargs: Any) -> Any:
        return wrap(c, original_fn, args, kwargs)

    setattr(cls, name, classmethod(wrapped))

    def revert() -> None:
        setattr(cls, name, original_cm)

    _originals.append(revert)


def _wrap_gas_costs(c: type, fn: Callable, args: tuple, kwargs: dict) -> Any:
    gc = fn(c, *args, **kwargs)
    patched: Dict[str, Any] = {}
    for f in fields(gc):
        v = getattr(gc, f.name)
        if isinstance(v, int) and not _is_tainted(v):
            patched[f.name] = GasTainted(v, (f"gas_costs.{f.name}",))
    return replace(gc, **patched) if patched else gc


def _wrap_intrinsic(c: type, fn: Callable, args: tuple, kwargs: dict) -> Any:
    inner = fn(c, *args, **kwargs)

    def calc(*a: Any, **kw: Any) -> Any:
        result = inner(*a, **kw)
        if isinstance(result, int) and not _is_tainted(result):
            return GasTainted(result, ("intrinsic_gas",))
        return result

    return calc


def _wrap_opcode_calc(c: type, fn: Callable, args: tuple, kwargs: dict) -> Any:
    inner = fn(c, *args, **kwargs)

    def calc(opcode: OpcodeBase) -> int:
        result = inner(opcode)
        if isinstance(result, int) and not _is_tainted(result):
            name = getattr(opcode, "_name_", None) or str(opcode)
            return GasTainted(result, (f"opcode_gas[{name}]",))
        return result

    return calc


def install_taint() -> None:
    """Install all gas-source patches. Idempotent."""
    global _installed
    if _installed:
        return
    _installed = True

    # Bytecode.gas_cost - taint the aggregate result
    from execution_testing.vm.bytecode import Bytecode

    original_bc = Bytecode.gas_cost

    def gas_cost(self: Any, fork: Any) -> Any:
        result = original_bc(self, fork)
        if isinstance(result, int) and not _is_tainted(result):
            return GasTainted(result, ("Bytecode.gas_cost",))
        return result

    Bytecode.gas_cost = gas_cost  # type: ignore[method-assign]
    _originals.append(lambda: setattr(Bytecode, "gas_cost", original_bc))

    # Concrete forks: walk subclasses and wrap any locally-defined
    # gas_costs / transaction_intrinsic_cost_calculator / opcode_gas_calculator
    from execution_testing.forks.base_fork import BaseFork

    for cls in _all_subclasses(BaseFork):
        _patch_classmethod_if_local(cls, "gas_costs", _wrap_gas_costs)
        _patch_classmethod_if_local(
            cls, "transaction_intrinsic_cost_calculator", _wrap_intrinsic
        )
        _patch_classmethod_if_local(
            cls, "opcode_gas_calculator", _wrap_opcode_calc
        )

    # Number.__new__ / FixedSizeHexNumber.__new__ - preserve origins through
    # HexNumber, ZeroPaddedHexNumber, HashInt, etc. (two separate hierarchies).
    from execution_testing.base_types.base_types import (
        FixedSizeHexNumber,
        Number,
    )

    def _wrap_new(target: type) -> None:
        orig = target.__new__

        def new(cls: type, input_number: Any) -> Any:
            inst: Any = orig(cls, input_number)
            origins = getattr(input_number, "origins", None)
            if origins is not None:
                try:
                    inst.origins = origins
                except (AttributeError, TypeError):
                    pass
            return inst

        target.__new__ = new  # type: ignore[assignment,method-assign]

        def revert() -> None:
            target.__new__ = orig  # type: ignore[method-assign]

        _originals.append(revert)

    _wrap_new(Number)
    _wrap_new(FixedSizeHexNumber)


def uninstall_taint() -> None:
    """Revert all patches in LIFO order. Used by tests of the plugin."""
    global _installed
    while _originals:
        try:
            _originals.pop()()
        except Exception:
            pass
    _installed = False


# ---------------------------------------------------------------------------
# Sink walker
# ---------------------------------------------------------------------------


def _record_tainted(
    hits: List[dict], kind: str, location: str, value: int | None
) -> None:
    """Record only if value carries gas-source taint (used for storage)."""
    if value is None:
        return
    origins = _origins_of(value)
    if origins is None:
        return
    hits.append(
        {
            "kind": kind,
            "location": location,
            "value": int(value),
            "origins": list(origins),
        }
    )


def _record_present(
    hits: List[dict], kind: str, location: str, value: int | None
) -> None:
    """Record if value is set (field-name-implies-gas-assertion sinks)."""
    if value is None:
        return
    hit: Dict[str, object] = {
        "kind": kind,
        "location": location,
        "value": int(value),
    }
    origins = _origins_of(value)
    if origins is not None:
        hit["origins"] = list(origins)
    hits.append(hit)


def _walk_storage(hits: List[dict], post: Alloc | None) -> None:
    """Storage slots are general-purpose; only flag tainted values."""
    if post is None:
        return
    for address, account in post.items():
        if account is None:
            continue
        for slot, value in account.storage.root.items():
            _record_tainted(
                hits,
                "storage",
                f"{address}:{int(slot)}",
                value,
            )


def _walk_receipt(hits: List[dict], tx: Transaction | None) -> None:
    """Receipt gas fields are self-identifying — flag on presence."""
    if tx is None:
        return
    receipt = tx.expected_receipt
    if receipt is None:
        return
    _record_present(
        hits, "receipt", "cumulative_gas_used", receipt.cumulative_gas_used
    )
    _record_present(hits, "receipt", "gas_used", receipt.gas_used)
    _record_present(hits, "receipt", "blob_gas_used", receipt.blob_gas_used)


def _walk_header(
    hits: List[dict], header: Header | None, location_prefix: str
) -> None:
    """Record ``gas_used`` and ``blob_gas_used`` from a verified header."""
    if header is None:
        return
    _record_present(
        hits, "header", f"{location_prefix}.gas_used", header.gas_used
    )
    # blob_gas_used is ``Removable | HexNumber | None`` — the
    # ``Removable`` sentinel means "delete this from the verified
    # header" and is not a gas assertion.
    blob_gas_used = header.blob_gas_used
    if not isinstance(blob_gas_used, Removable):
        _record_present(
            hits,
            "header",
            f"{location_prefix}.blob_gas_used",
            blob_gas_used,
        )


def _walk_header_and_block(hits: List[dict], block: Block, i: int) -> None:
    """Header gas fields and expected_gas_used are self-identifying."""
    _walk_header(hits, block.header_verify, f"block[{i}]")
    _record_present(
        hits,
        "block_expected_gas_used",
        f"block[{i}].expected_gas_used",
        block.expected_gas_used,
    )


def _is_oog_test(test: BaseTest, node: pytest.Item | None) -> bool:
    if isinstance(test, StateTest) and test.tx.error is not None:
        return True
    if isinstance(test, StateTest) and test.block_exception is not None:
        return True
    if (
        node is not None
        and node.get_closest_marker("exception_test") is not None
    ):
        return True
    return False


def collect_taint_hits(test: BaseTest, node: pytest.Item | None) -> List[dict]:
    """Walk all known gas-assertion sinks on the test object."""
    if _is_oog_test(test, node):
        return []

    hits: List[dict] = []
    if isinstance(test, StateTest):
        _walk_storage(hits, test.post)
        _walk_receipt(hits, test.tx)
        # A StateTest can carry a header assertion that only fires when
        # the framework promotes it to a blockchain test. The field is
        # copied verbatim onto the generated Block's ``header_verify``,
        # so treat it as the same sink here.
        _walk_header(
            hits,
            test.blockchain_test_header_verify,
            "blockchain_test_header_verify",
        )
    elif isinstance(test, BlockchainTest):
        _walk_storage(hits, test.post)
        for i, block in enumerate(test.blocks):
            _walk_header_and_block(hits, block, i)
            for tx in block.txs:
                _walk_receipt(hits, tx)

    # ``expected_benchmark_gas_used`` is auto-defaulted on every test by
    # the filler, so only treat it as a sink on actual BenchmarkTest
    # instances.
    if isinstance(test, BenchmarkTest):
        _record_present(
            hits,
            "benchmark",
            "expected_benchmark_gas_used",
            test.expected_benchmark_gas_used,
        )

    return hits


# ---------------------------------------------------------------------------
# Pytest hooks
# ---------------------------------------------------------------------------


_RESULTS_ATTR = "_gas_taint_results"
_ENABLED_ATTR = "_gas_taint_enabled"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add ``--detect-gas-checks`` / ``--gas-check-report`` options."""
    group = parser.getgroup(
        "gas-taint", "Detect tests that assert specific gas values"
    )
    group.addoption(
        "--detect-gas-checks",
        action="store_true",
        dest="detect_gas_checks",
        default=False,
        help=(
            "Instrument gas-source functions, propagate provenance, and "
            "emit a JSON report listing tests whose post-state asserts a "
            "gas-derived value."
        ),
    )
    group.addoption(
        "--gas-check-report",
        action="store",
        dest="gas_check_report",
        default="gas_check_report.json",
        help="Output path for the gas-check JSON report.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Install taint and initialize result storage when enabled."""
    config.addinivalue_line(
        "markers",
        "gas_check: test asserts a specific gas value (auto-applied).",
    )
    if not config.getoption("detect_gas_checks", default=False):
        return
    install_taint()
    setattr(config, _ENABLED_ATTR, True)
    setattr(config, _RESULTS_ATTR, {})


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo
) -> Generator[None, None, None]:
    """Attach a ``gas_check`` marker if the item has taint hits."""
    yield
    if call.when != "call":
        return
    for key, value in item.user_properties:
        if key == "gas_taint_hits" and value:
            item.add_marker(pytest.mark.gas_check)
            break


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Forward worker results to master, or write JSON on master."""
    del exitstatus
    config = session.config
    if not getattr(config, _ENABLED_ATTR, False):
        return
    results = getattr(config, _RESULTS_ATTR, {})

    try:
        import xdist

        is_worker = xdist.is_xdist_worker(session)
    except ImportError:
        is_worker = False

    if is_worker:
        # Send worker's results to master via workeroutput.
        config.workeroutput["gas_taint_results"] = results  # type: ignore[attr-defined]
        return

    path = Path(config.getoption("gas_check_report"))
    path.write_text(json.dumps(results, indent=2, sort_keys=True))


def pytest_testnodedown(
    node: "WorkerController", error: object | None
) -> None:
    """Aggregate worker results into the master's results dict."""
    del error
    config = node.config
    if not getattr(config, _ENABLED_ATTR, False):
        return
    worker_results = getattr(node, "workeroutput", {}).get(
        "gas_taint_results", {}
    )
    results = getattr(config, _RESULTS_ATTR, None)
    if results is None:
        return
    results.update(worker_results)
    path = Path(config.getoption("gas_check_report"))
    path.write_text(json.dumps(results, indent=2, sort_keys=True))
