"""
Test that the appended sync block reaches exactly the fixtures that
should carry it, and changes nothing else.

Only ``blockchain_test_engine_x`` fixtures carry the block, out of
chain in their ``syncPayload`` field, so a default fill must leave
every format's payload list byte-for-byte what the test defines. These
tests fill whole test modules and read the fixtures back, so a sync
block that leaks into a payload list, misses the invalid head it must
sit above, steals an error-code assertion's announcement, or fails to
salt per test fails here rather than in a consumer.
"""

import json
import textwrap
from pathlib import Path
from typing import Any, Dict

import pytest

from ..filler import _strip_any_xdist_group_suffix


class TestStripAnyXdistGroupSuffix:
    """
    Test the salt's node-id normalization.

    The sync block's salt must be identical whether or not the fill ran
    under ``--dist=loadgroup``, so every group suffix is stripped,
    unlike ``_strip_xdist_group_suffix`` which preserves the deliberate
    ones.
    """

    @pytest.mark.parametrize(
        "group", ["t8n-cache-12345678", "bigmem", "custom_group"]
    )
    def test_strips_every_group_suffix(self, group: str) -> None:
        """Any group suffix an xdist worker appends is stripped."""
        expected = "test.py::test[params]"
        assert _strip_any_xdist_group_suffix(f"{expected}@{group}") == expected

    def test_no_suffix_unchanged(self) -> None:
        """Node ids without a group suffix are unchanged."""
        nodeid = "test.py::test[params]"
        assert _strip_any_xdist_group_suffix(nodeid) == nodeid

    def test_at_in_params_preserved(self) -> None:
        """A parameter's own ``@`` is not mistaken for a group."""
        nodeid = "test.py::test[email@example.com]"
        assert _strip_any_xdist_group_suffix(nodeid) == nodeid

    def test_at_in_params_with_group_suffix(self) -> None:
        """A group is stripped from a parameter containing ``@``."""
        nodeid = "test.py::test[email@example.com]@bigmem"
        expected = "test.py::test[email@example.com]"
        assert _strip_any_xdist_group_suffix(nodeid) == expected


VALID_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Block, Transaction


    # Two tests of one pre-allocation group: a client reused across
    # them must not already know either announced sync block.
    @pytest.mark.parametrize("value", [1, 2])
    def test_single_block(blockchain_test, pre, value) -> None:
        tx = Transaction(
            to=0,
            value=value,
            gas_limit=21_000,
            sender=pre.fund_eoa(),
        )
        blockchain_test(pre=pre, post={}, blocks=[Block(txs=[tx])])


    # A state test: the sync block fields live on ``BaseTest`` exactly
    # so that the StateTest to BlockchainTest conversion carries them
    # into the converted chain's engine_x fixture.
    def test_from_state_test(state_test, pre) -> None:
        tx = Transaction(
            to=0,
            value=3,
            gas_limit=21_000,
            sender=pre.fund_eoa(),
        )
        state_test(pre=pre, post={}, tx=tx)
    """
)

INVALID_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Block,
        BlockException,
        Header,
        Transaction,
        TransactionException,
    )


    def invalid_tx(pre):
        return Transaction(
            to=0,
            gas_limit=20_999,
            sender=pre.fund_eoa(),
            error=TransactionException.INTRINSIC_GAS_TOO_LOW,
        )


    @pytest.mark.exception_test
    def test_invalid_underivable_head(blockchain_test, pre) -> None:
        # The pinned blob fields sum to 2**64, overflowing the next
        # block's excess-blob-gas derivation, so no sync block can be
        # built (or derived by a client) above this head.
        tx = Transaction(
            to=0, value=1, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    txs=[tx],
                    rlp_modifier=Header(
                        excess_blob_gas=2**64 - 1,
                        blob_gas_used=1,
                    ),
                    exception=[
                        BlockException.INCORRECT_EXCESS_BLOB_GAS,
                        BlockException.INCORRECT_BLOB_GAS_USED,
                    ],
                )
            ],
        )


    @pytest.mark.exception_test
    def test_invalid_singleton(blockchain_test, pre) -> None:
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    txs=[invalid_tx(pre)],
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
            ],
        )


    @pytest.mark.exception_test
    def test_invalid_multi_block(blockchain_test, pre) -> None:
        valid_tx = Transaction(
            to=0, value=1, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(txs=[valid_tx]),
                Block(
                    txs=[invalid_tx(pre)],
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                ),
            ],
        )
    """
)

ERROR_CODE_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import (
        Block,
        BlockException,
        EngineAPIError,
        Header,
        Transaction,
    )


    @pytest.mark.exception_test
    def test_engine_api_refused(blockchain_test, pre) -> None:
        tx = Transaction(
            to=0, value=1, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    txs=[tx],
                    rlp_modifier=Header(
                        excess_blob_gas=Header.REMOVE_FIELD,
                    ),
                    exception=BlockException.INCORRECT_BLOCK_FORMAT,
                    engine_api_error_code=EngineAPIError.InvalidParams,
                )
            ],
        )
    """
)

OPT_OUT_MODULE = textwrap.dedent(
    """\
    from execution_testing import Block, Transaction


    def single_block_test(blockchain_test, pre, value, **kwargs):
        tx = Transaction(
            to=0, value=value, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(
            pre=pre, post={}, blocks=[Block(txs=[tx])], **kwargs
        )


    def test_opted_out(blockchain_test, pre) -> None:
        # Stands in for a chain whose end state the appended block
        # cannot execute on (e.g. a sabotaged system contract): the
        # test itself declares it cannot carry the block.
        single_block_test(blockchain_test, pre, 1, sync_block=False)


    def test_unopted(blockchain_test, pre) -> None:
        single_block_test(blockchain_test, pre, 2)
    """
)

CEILING_MODULE = textwrap.dedent(
    """\
    from execution_testing import Block, Transaction


    def test_pinned_ceiling_timestamp(blockchain_test, pre) -> None:
        # A valid head at the uint64 timestamp ceiling: no child
        # timestamp fits above it, so the filler declines the sync
        # block and the chain fills as exactly the author's own.
        tx = Transaction(
            to=0, value=1, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(
            pre=pre,
            post={},
            blocks=[Block(txs=[tx], timestamp=2**64 - 1)],
        )
    """
)

# Fixture directory to the format name that appears in a test id.
FORMATS = {
    "blockchain_tests": "blockchain_test",
    "blockchain_tests_engine": "blockchain_test_engine",
    "blockchain_tests_engine_x": "blockchain_test_engine_x",
}


def make_test_module(
    pytester: pytest.Pytester, source: str, name: str
) -> Path:
    """Write a test module into a pytester tests tree."""
    module_dir = pytester.path / "tests" / "cancun" / "sync_block_module"
    module_dir.mkdir(parents=True)
    test_module = module_dir / name
    test_module.write_text(source)
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return test_module


def fill(
    pytester: pytest.Pytester,
    test_module: Path,
    *args: str,
    output_name: str = "fixtures",
    all_formats: bool = False,
) -> Path:
    """
    Fill the module into a fresh output directory and return it.

    An engine_x fill is two pytest sessions - the `fill` CLI runs phase
    1 (pre-allocation grouping) and phase 2 (fixture filling) back to
    back - so both are run here the same way. Without ``all_formats``
    phase 2 emits only the engine_x format.
    """
    output = pytester.path / output_name
    common = (
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Cancun",
        "--skip-index",
        "--no-html",
        f"--output={output}",
        *(("--generate-all-formats",) if all_formats else ()),
        *args,
        str(test_module.relative_to(pytester.path)),
    )
    result = pytester.runpytest("--generate-pre-alloc-groups", *common)
    assert result.ret == 0, "fill phase 1 was expected to succeed"
    result = pytester.runpytest("--use-pre-alloc-groups", *common)
    assert result.ret == 0, "fill phase 2 was expected to succeed"
    return output


def fixtures_of_format(
    output: Path, format_dir: str
) -> Dict[str, Dict[str, Any]]:
    """
    Return the fixtures emitted in a format's directory, keyed by test
    id with the format's own name stripped out so the same test's
    fixtures line up across formats.
    """
    fixtures: Dict[str, Dict[str, Any]] = {}
    for path in sorted((output / format_dir).rglob("*.json")):
        if "pre_alloc" in path.parts:
            continue
        for test_id, fixture in json.loads(path.read_text()).items():
            key = test_id.replace(f"-{FORMATS[format_dir]}", "")
            fixtures[key] = fixture
    assert fixtures, f"no {format_dir} fixtures were emitted"
    return fixtures


def assert_appended_above(fixture: Dict[str, Any], *, blocks: int) -> None:
    """
    Assert that ``fixture`` carries one salted empty payload appended
    above a payload list of exactly ``blocks`` entries.
    """
    payloads = fixture["engineNewPayloads"]
    assert len(payloads) == blocks, (
        "the appended sync block must not enter the payload list"
    )
    head = payloads[-1]["params"][0]
    appended = fixture["syncPayload"]["params"][0]
    assert appended["transactions"] == [], (
        "the appended sync block carries no transactions"
    )
    assert appended["parentHash"] == head["blockHash"], (
        "the appended sync block must name the chain's last block as parent"
    )
    assert int(appended["blockNumber"], 16) == int(head["blockNumber"], 16) + 1
    assert int(appended["timestamp"], 16) > int(head["timestamp"], 16)
    assert appended["extraData"] != "0x", (
        "the appended sync block is salted with a per-test value"
    )


def positions(fixture: Dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return each payload's position and expectation in the chain."""
    return [
        (
            payload["params"][0]["blockNumber"],
            payload["params"][0]["timestamp"],
            str(payload.get("validationError")),
        )
        for payload in fixture["engineNewPayloads"]
    ]


def test_valid_chains_carry_the_appended_block(
    pytester: pytest.Pytester,
) -> None:
    """
    A valid chain's sync block rides out-of-chain in ``syncPayload``,
    built on the test's own head and salted per test; no other format
    gains anything.
    """
    test_module = make_test_module(
        pytester, VALID_MODULE, "test_single_block.py"
    )
    output = fill(pytester, test_module, all_formats=True)

    for fixture in fixtures_of_format(output, "blockchain_tests").values():
        assert len(fixture["blocks"]) == 1
        assert "syncPayload" not in fixture
    for fixture in fixtures_of_format(
        output, "blockchain_tests_engine"
    ).values():
        assert len(fixture["engineNewPayloads"]) == 1
        assert "syncPayload" not in fixture

    engine_x = fixtures_of_format(output, "blockchain_tests_engine_x")
    assert any("test_from_state_test" in test_id for test_id in engine_x), (
        "the state test must reach engine_x through the StateTest to "
        "BlockchainTest conversion, which is what puts the sync block "
        "fields on BaseTest"
    )
    for fixture in engine_x.values():
        assert_appended_above(fixture, blocks=1)
        assert (
            fixture["lastblockhash"]
            == fixture["engineNewPayloads"][0]["params"][0]["blockHash"]
        ), "the fixture's head stays the author's own block"
    salts = {
        fixture["syncPayload"]["params"][0]["extraData"]
        for fixture in engine_x.values()
    }
    assert len(salts) == 3, (
        "each test's appended block must be unique to it, even across "
        "the byte-identical chains of one pre-allocation group"
    )


def test_invalid_chains_carry_the_appended_block(
    pytester: pytest.Pytester,
) -> None:
    """
    An expected-invalid head takes the appended block too, keeping its
    own position: the extra block names it as parent, so a sync-based
    consumer announces the extra block and the invalid block itself
    travels devp2p as ancestry. The engine_x payload list must hold the
    same positions and expectations as the plain engine format's -
    nothing is inserted into or shifted inside the chain.
    """
    test_module = make_test_module(pytester, INVALID_MODULE, "test_invalid.py")
    output = fill(pytester, test_module, all_formats=True)

    engine = fixtures_of_format(output, "blockchain_tests_engine")
    engine_x = fixtures_of_format(output, "blockchain_tests_engine_x")
    assert engine.keys() == engine_x.keys()
    for test_id, packed in engine_x.items():
        assert positions(packed) == positions(engine[test_id])

    singleton = next(
        fixture
        for test_id, fixture in engine_x.items()
        if "test_invalid_singleton" in test_id
    )
    assert_appended_above(singleton, blocks=1)
    invalid = singleton["engineNewPayloads"][0]
    assert invalid.get("validationError") is not None
    assert int(invalid["params"][0]["blockNumber"], 16) == 1, (
        "the test's own block keeps its number"
    )
    assert singleton["lastblockhash"] == invalid["params"][0]["parentHash"], (
        "an invalid singleton's chain still ends at genesis"
    )

    multi_block = next(
        fixture
        for test_id, fixture in engine_x.items()
        if "test_invalid_multi_block" in test_id
    )
    assert_appended_above(multi_block, blocks=2)
    assert multi_block["engineNewPayloads"][0].get("validationError") is None
    assert (
        multi_block["engineNewPayloads"][1].get("validationError") is not None
    )

    underivable = next(
        fixture
        for test_id, fixture in engine_x.items()
        if "test_invalid_underivable_head" in test_id
    )
    assert (
        underivable["engineNewPayloads"][0].get("validationError") is not None
    )
    assert "syncPayload" not in underivable, (
        "no sync block can be derived above a head whose pinned blob "
        "fields overflow the child's excess derivation"
    )


def test_error_code_chain_keeps_its_announcement(
    pytester: pytest.Pytester,
) -> None:
    """
    A chain asserting an Engine API error code must gain no appended
    block: the extra block would be announced instead of the payload
    whose refusal the test verifies.
    """
    test_module = make_test_module(
        pytester, ERROR_CODE_MODULE, "test_error_code.py"
    )
    output = fill(pytester, test_module)

    for fixture in fixtures_of_format(
        output, "blockchain_tests_engine_x"
    ).values():
        assert fixture["engineNewPayloads"][0].get("errorCode") is not None
        assert "syncPayload" not in fixture


def test_opted_out_tests_fill_without_the_block(
    pytester: pytest.Pytester,
) -> None:
    """
    A test that opts out (``sync_block=False``) fills as exactly the
    author's chain rather than being skipped, and its neighbours keep
    their appended block.
    """
    test_module = make_test_module(pytester, OPT_OUT_MODULE, "test_opt_out.py")
    output = fill(pytester, test_module)

    fixtures = fixtures_of_format(output, "blockchain_tests_engine_x")
    assert len(fixtures) == 2, "opted-out tests must still be filled"
    for test_id, fixture in fixtures.items():
        assert len(fixture["engineNewPayloads"]) == 1
        if "test_opted_out" in test_id:
            assert "syncPayload" not in fixture
        else:
            assert_appended_above(fixture, blocks=1)


def test_ceiling_head_fills_bare(pytester: pytest.Pytester) -> None:
    """
    A chain whose head leaves no uint64 room for a child block fills
    as exactly the author's chain - no ``syncPayload``, no error, no
    skip - because the filler declines the block itself.
    """
    test_module = make_test_module(pytester, CEILING_MODULE, "test_ceiling.py")
    output = fill(pytester, test_module)

    fixtures = fixtures_of_format(output, "blockchain_tests_engine_x")
    assert len(fixtures) == 1, "the ceiling head must still be filled"
    for fixture in fixtures.values():
        assert len(fixture["engineNewPayloads"]) == 1
        assert "syncPayload" not in fixture


def test_no_sync_block_restores_the_plain_fill(
    pytester: pytest.Pytester,
) -> None:
    """
    ``--no-sync-block`` removes the appended block and nothing else:
    the fixtures are byte-identical to a default fill's except for the
    ``syncPayload`` field itself.
    """
    test_module = make_test_module(
        pytester, VALID_MODULE, "test_single_block.py"
    )
    default = fill(pytester, test_module, output_name="fixtures-default")
    without = fill(
        pytester,
        test_module,
        "--no-sync-block",
        output_name="fixtures-without",
    )

    default_fixtures = fixtures_of_format(default, "blockchain_tests_engine_x")
    without_fixtures = fixtures_of_format(without, "blockchain_tests_engine_x")
    assert default_fixtures.keys() == without_fixtures.keys()
    for test_id, fixture in default_fixtures.items():
        assert_appended_above(fixture, blocks=1)
        stripped = {k: v for k, v in fixture.items() if k != "syncPayload"}
        other = without_fixtures[test_id]
        assert "syncPayload" not in other
        assert {k: v for k, v in other.items() if k != "_info"} == {
            k: v for k, v in stripped.items() if k != "_info"
        }, "the appended block must not change the author's own fixture"
