"""
Test that appended sync payloads reach exactly the authored leaves that
should carry them, and change nothing else.

Only ``blockchain_test_engine_x`` fixtures carry the blocks, out of
chain in their ``syncPayloads`` list, so a default fill must leave every
format's authored payload list byte-for-byte what the test defines.
These tests fill whole test modules and read the fixtures back, so a
sync payload that leaks into that list, misses a branch leaf, steals an
error-code assertion's announcement, or fails to salt per test fails
here rather than in a consumer.
"""

import json
import textwrap
from pathlib import Path
from typing import Any, Dict

import pytest

from ...shared.helpers import strip_any_xdist_group_suffix


class TestStripAnyXdistGroupSuffix:
    """
    Test the node-id normalization.

    Everything derived from a node id - the sync block's salt, the
    fixture's own id, the pre-alloc group keys and entropy - must be
    identical whether or not the fill ran under ``--dist=loadgroup``,
    so every group suffix is stripped.
    """

    @pytest.mark.parametrize(
        "group", ["t8n-cache-12345678", "bigmem", "custom_group"]
    )
    def test_strips_every_group_suffix(self, group: str) -> None:
        """Any group suffix an xdist worker appends is stripped."""
        expected = "test.py::test[params]"
        assert strip_any_xdist_group_suffix(f"{expected}@{group}") == expected

    def test_no_suffix_unchanged(self) -> None:
        """Node ids without a group suffix are unchanged."""
        nodeid = "test.py::test[params]"
        assert strip_any_xdist_group_suffix(nodeid) == nodeid

    def test_at_in_params_preserved(self) -> None:
        """A parameter's own ``@`` is not mistaken for a group."""
        nodeid = "test.py::test[email@example.com]"
        assert strip_any_xdist_group_suffix(nodeid) == nodeid

    def test_at_in_params_with_group_suffix(self) -> None:
        """A group is stripped from a parameter containing ``@``."""
        nodeid = "test.py::test[email@example.com]@bigmem"
        expected = "test.py::test[email@example.com]"
        assert strip_any_xdist_group_suffix(nodeid) == expected


VALID_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Block, Transaction


    @pytest.mark.parametrize("value", [1, 2])
    def test_single_block(blockchain_test, pre, value) -> None:
        tx = Transaction(
            to=0,
            value=value,
            gas_limit=21_000,
            sender=pre.fund_eoa(),
        )
        blockchain_test(pre=pre, post={}, blocks=[Block(txs=[tx])])


    # Two tests of one pre-allocation group whose authored payloads are
    # byte-identical: only the salt keeps their appended blocks apart,
    # and a client reused across the group only starts a sync for a
    # head it has never seen.
    @pytest.mark.parametrize("copy", [1, 2])
    def test_identical_chains(blockchain_test, pre, copy) -> None:
        blockchain_test(pre=pre, post={}, blocks=[Block()])


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
        # built (or derived by a client) above this head. The excess
        # alone is small enough to price.
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
                        excess_blob_gas=1,
                        blob_gas_used=2**64 - 1,
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


    @pytest.mark.exception_test
    def test_identical_invalid_siblings(blockchain_test, pre) -> None:
        # Both rejected blocks are built on genesis from one transaction,
        # so they are one block, and one sync target covers both.
        tx = invalid_tx(pre)
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    txs=[tx],
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                )
                for _ in range(2)
            ],
        )


    @pytest.mark.exception_test
    def test_invalid_then_valid_siblings(blockchain_test, pre) -> None:
        valid_tx = Transaction(
            to=0, value=1, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    txs=[invalid_tx(pre)],
                    exception=TransactionException.INTRINSIC_GAS_TOO_LOW,
                ),
                Block(txs=[valid_tx]),
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
    import pytest

    from execution_testing import Block, BlockException, Header, Transaction


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


    @pytest.mark.exception_test
    def test_pinned_ceiling_block_number(blockchain_test, pre) -> None:
        # The authored block number fits uint64, but its successor does
        # not. The block is invalid because it is not its parent's number
        # plus one; the framework still needs it as a sync-path leaf.
        blockchain_test(
            pre=pre,
            post={},
            blocks=[
                Block(
                    rlp_modifier=Header(number=2**64 - 1),
                    exception=BlockException.INVALID_BLOCK_NUMBER,
                )
            ],
        )
    """
)

XDIST_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Block, Transaction


    def single_block_test(blockchain_test, pre, value):
        tx = Transaction(
            to=0, value=value, gas_limit=21_000, sender=pre.fund_eoa()
        )
        blockchain_test(pre=pre, post={}, blocks=[Block(txs=[tx])])


    @pytest.mark.parametrize("value", [1, 2])
    def test_grouped_by_the_fill(blockchain_test, pre, value) -> None:
        single_block_test(blockchain_test, pre, value)


    @pytest.mark.xdist_group(name="bigmem")
    def test_grouped_by_the_author(blockchain_test, pre) -> None:
        single_block_test(blockchain_test, pre, 3)
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
    subprocess: bool = False,
) -> Path:
    """
    Fill the module into a fresh output directory and return it.

    An engine_x fill is two pytest sessions - the `fill` CLI runs phase
    1 (pre-allocation grouping) and phase 2 (fixture filling) back to
    back - so both are run here the same way. Without ``all_formats``
    phase 2 emits only the engine_x format. ``subprocess`` runs each
    session in its own process, which an xdist fill needs.
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
    run = pytester.runpytest_subprocess if subprocess else pytester.runpytest
    result = run("--generate-pre-alloc-groups", *common)
    assert result.ret == 0, "fill phase 1 was expected to succeed"
    result = run("--use-pre-alloc-groups", *common)
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


def assert_sync_payloads_above(
    fixture: Dict[str, Any], *, blocks: int, leaf_indices: list[int]
) -> None:
    """
    Assert that ``fixture`` carries one salted empty payload above every
    authored leaf in ``leaf_indices``.
    """
    payloads = fixture["engineNewPayloads"]
    assert len(payloads) == blocks, (
        "appended sync payloads must not enter the authored payload list"
    )
    sync_payloads = fixture["syncPayloads"]
    assert len(sync_payloads) == len(leaf_indices)
    for sync_payload, leaf_index in zip(
        sync_payloads, leaf_indices, strict=True
    ):
        head = payloads[leaf_index]["params"][0]
        appended = sync_payload["params"][0]
        assert appended["transactions"] == [], (
            "an appended sync payload carries no transactions"
        )
        assert appended["parentHash"] == head["blockHash"], (
            "each appended sync payload must name its authored leaf"
        )
        assert int(appended["blockNumber"], 16) == (
            int(head["blockNumber"], 16) + 1
        )
        assert int(appended["timestamp"], 16) > int(head["timestamp"], 16)
        assert appended["feeRecipient"] != head["feeRecipient"], (
            "each appended sync payload is salted per test through its "
            "fee recipient"
        )
        assert appended["extraData"] == "0x", (
            "the salt lives in the fee recipient, not in extraData"
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
    A valid chain gets one out-of-chain entry in ``syncPayloads``, built
    on the test's own head and salted per test; no other format gains
    anything.
    """
    test_module = make_test_module(
        pytester, VALID_MODULE, "test_single_block.py"
    )
    output = fill(pytester, test_module, all_formats=True)

    for fixture in fixtures_of_format(output, "blockchain_tests").values():
        assert len(fixture["blocks"]) == 1
        assert "syncPayloads" not in fixture
    for fixture in fixtures_of_format(
        output, "blockchain_tests_engine"
    ).values():
        assert len(fixture["engineNewPayloads"]) == 1
        assert "syncPayloads" not in fixture

    engine_x = fixtures_of_format(output, "blockchain_tests_engine_x")
    assert any("test_from_state_test" in test_id for test_id in engine_x), (
        "the state test must reach engine_x through the StateTest to "
        "BlockchainTest conversion, which is what puts the sync block "
        "fields on BaseTest"
    )
    for fixture in engine_x.values():
        assert_sync_payloads_above(fixture, blocks=1, leaf_indices=[0])
        assert (
            fixture["lastblockhash"]
            == fixture["engineNewPayloads"][0]["params"][0]["blockHash"]
        ), "the fixture's head stays the author's own block"
    salts = {
        fixture["syncPayloads"][0]["params"][0]["feeRecipient"]
        for fixture in engine_x.values()
    }
    assert len(salts) == 5, "each test's appended block is salted by its id"

    identical = [
        fixture
        for test_id, fixture in engine_x.items()
        if "test_identical_chains" in test_id
    ]
    assert len(identical) == 2
    authored, appended = (
        {fixture[field][0]["params"][0]["blockHash"] for fixture in identical}
        for field in ("engineNewPayloads", "syncPayloads")
    )
    assert len(authored) == 1, "the two tests author the same block"
    assert len(appended) == 2, (
        "the salt must keep the appended blocks of byte-identical chains apart"
    )


def test_invalid_chains_carry_the_appended_block(
    pytester: pytest.Pytester,
) -> None:
    """
    Every expected-invalid leaf gets its own appended target. A final
    valid sibling gets another target after it, so every branch can be
    announced without inserting or shifting anything in the authored
    payload list.
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
    assert_sync_payloads_above(singleton, blocks=1, leaf_indices=[0])
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
    assert_sync_payloads_above(multi_block, blocks=2, leaf_indices=[1])
    assert multi_block["engineNewPayloads"][0].get("validationError") is None
    assert (
        multi_block["engineNewPayloads"][1].get("validationError") is not None
    )

    siblings = next(
        fixture
        for test_id, fixture in engine_x.items()
        if "test_invalid_then_valid_siblings" in test_id
    )
    assert_sync_payloads_above(siblings, blocks=2, leaf_indices=[0, 1])
    invalid, valid = siblings["engineNewPayloads"]
    assert invalid.get("validationError") is not None
    assert valid.get("validationError") is None
    assert invalid["params"][0]["blockNumber"] == "0x1"
    assert valid["params"][0]["blockNumber"] == "0x1"
    assert (
        invalid["params"][0]["parentHash"] == valid["params"][0]["parentHash"]
    ), "the rejected and accepted authored payloads are siblings"
    assert siblings["lastblockhash"] == valid["params"][0]["blockHash"]

    duplicates = next(
        fixture
        for test_id, fixture in engine_x.items()
        if "test_identical_invalid_siblings" in test_id
    )
    first, second = duplicates["engineNewPayloads"]
    assert first == second, "both rejected payloads are the same block"
    assert len(duplicates["syncPayloads"]) == 1, (
        "a leaf authored twice gets one sync target"
    )
    assert_sync_payloads_above(duplicates, blocks=2, leaf_indices=[0])

    underivable = next(
        fixture
        for test_id, fixture in engine_x.items()
        if "test_invalid_underivable_head" in test_id
    )
    assert (
        underivable["engineNewPayloads"][0].get("validationError") is not None
    )
    assert "syncPayloads" not in underivable, (
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
        assert "syncPayloads" not in fixture


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
            assert "syncPayloads" not in fixture
        else:
            assert_sync_payloads_above(fixture, blocks=1, leaf_indices=[0])


def test_ceiling_head_fills_bare(pytester: pytest.Pytester) -> None:
    """
    A chain whose head leaves no uint64 room for a child block fills
    as exactly the author's chain - no ``syncPayloads``, no error, no
    skip - because the filler declines the block itself.
    """
    test_module = make_test_module(pytester, CEILING_MODULE, "test_ceiling.py")
    output = fill(pytester, test_module)

    fixtures = fixtures_of_format(output, "blockchain_tests_engine_x")
    assert len(fixtures) == 2, "every ceiling head must still be filled"
    for fixture in fixtures.values():
        assert len(fixture["engineNewPayloads"]) == 1
        assert "syncPayloads" not in fixture


def test_no_sync_block_restores_the_plain_fill(
    pytester: pytest.Pytester,
) -> None:
    """
    ``--no-sync-block`` removes the appended block and nothing else:
    the formats without sync payloads are byte-identical to a default
    fill's, and engine_x differs only by ``syncPayloads`` and the
    ``_info`` derived from the complete serialized fixture.
    """
    test_module = make_test_module(
        pytester, VALID_MODULE, "test_single_block.py"
    )
    default = fill(
        pytester,
        test_module,
        output_name="fixtures-default",
        all_formats=True,
    )
    without = fill(
        pytester,
        test_module,
        "--no-sync-block",
        output_name="fixtures-without",
        all_formats=True,
    )

    for format_dir in ("blockchain_tests", "blockchain_tests_engine"):
        assert fixtures_of_format(default, format_dir) == fixtures_of_format(
            without, format_dir
        ), f"{format_dir} must not depend on the sync block"

    default_fixtures = fixtures_of_format(default, "blockchain_tests_engine_x")
    without_fixtures = fixtures_of_format(without, "blockchain_tests_engine_x")
    assert default_fixtures.keys() == without_fixtures.keys()
    for test_id, fixture in default_fixtures.items():
        assert_sync_payloads_above(fixture, blocks=1, leaf_indices=[0])
        other = without_fixtures[test_id]
        assert "syncPayloads" not in other
        assert {k: v for k, v in other.items() if k != "_info"} == {
            k: v
            for k, v in fixture.items()
            if k not in ("_info", "syncPayloads")
        }, "the appended block must not change the author's own fixture"


@pytest.mark.slow
def test_xdist_fill_matches_the_serial_fill(
    pytester: pytest.Pytester, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    An engine_x fill under ``--dist=loadgroup`` emits the same fixtures
    as a serial fill. Xdist appends each test's group to its node id,
    including a group the author set; neither the fixture ids nor the
    sync block's salt may carry it.
    """
    test_module = make_test_module(pytester, XDIST_MODULE, "test_xdist.py")
    serial = fill(pytester, test_module, output_name="fixtures-serial")
    distributed = fill(
        pytester,
        test_module,
        "-n",
        "2",
        output_name="fixtures-xdist",
        subprocess=True,
    )
    capsys.readouterr()

    def without_info(output: Path) -> Dict[str, Dict[str, Any]]:
        return {
            test_id: {k: v for k, v in fixture.items() if k != "_info"}
            for test_id, fixture in fixtures_of_format(
                output, "blockchain_tests_engine_x"
            ).items()
        }

    serial_fixtures = without_info(serial)
    distributed_fixtures = without_info(distributed)
    assert len(serial_fixtures) == 3
    assert not any("@" in test_id for test_id in distributed_fixtures)
    assert distributed_fixtures == serial_fixtures
