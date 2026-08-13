"""Test the declaration of `safe` and `finalized` blocks on a chain."""

from typing import List, Literal

import pytest

from execution_testing.exceptions import BlockException
from execution_testing.forks import Cancun
from execution_testing.test_types import Alloc

from ..blockchain import Block, BlockchainTest

FORK = Cancun


def chain(*tags: Literal["safe", "finalized"] | None) -> List[Block]:
    """Return one block per tag, untagged where the tag is None."""
    return [Block(forkchoice_tag=tag) for tag in tags]


def build(blocks: List[Block]) -> BlockchainTest:
    """Return a test over the given blocks."""
    return BlockchainTest(fork=FORK, pre=Alloc(), post=Alloc(), blocks=blocks)


def test_a_valid_declaration_is_accepted() -> None:
    """Finalized behind safe, behind a head that is neither."""
    test = build(chain("finalized", "safe", None))

    assert [block.forkchoice_tag for block in test.blocks] == [
        "finalized",
        "safe",
        None,
    ]


def test_no_declaration_is_the_normal_case() -> None:
    """An ordinary test declares nothing and is unaffected."""
    build(chain(None, None))


def test_one_tag_alone_is_rejected() -> None:
    """
    Both tags or neither.

    A client handed only a safe block has to invent behaviour for the
    finalized one, and what it invents is not something a conformance test
    should be asserting against.
    """
    with pytest.raises(ValueError, match="finalized"):
        build(chain("safe", None))


def test_a_repeated_tag_is_rejected() -> None:
    """A chain has one safe block, not two."""
    with pytest.raises(ValueError, match="both tagged"):
        build(chain("safe", "safe", None))


def test_finalized_ahead_of_safe_is_rejected() -> None:
    """
    Finalization trails the safe head, never leads it.

    A client told otherwise is entitled to reject the forkchoice update, so
    the test would be measuring the harness's mistake.
    """
    with pytest.raises(ValueError, match="finalizes behind"):
        build(chain("safe", "finalized", None))


def test_tagging_the_head_is_rejected() -> None:
    """
    Head and safe must differ, or the test proves nothing.

    This is exactly the weakness of a recorded corpus that points all three
    tags at one block: a client that ignores both fields and answers with
    the head passes every one of them.
    """
    with pytest.raises(ValueError, match="answers every tag"):
        build(chain("finalized", "safe"))


def test_tagging_a_rejected_block_is_rejected() -> None:
    """A block outside the canonical chain is neither safe nor final."""
    blocks = chain("finalized", "safe", None)
    blocks[1].exception = BlockException.INCORRECT_BLOCK_FORMAT

    with pytest.raises(ValueError, match="expected to be rejected"):
        build(blocks)


def test_an_unmarked_test_cannot_declare_tags() -> None:
    """
    Tagging without the `rpc` marker fails rather than doing nothing.

    Only a marked test emits an `rpc` section, and the section is the only
    thing that carries the declaration to a consumer, so an unmarked test
    would tag its blocks and assert nothing at all.
    """
    test = build(chain("finalized", "safe", None))

    with pytest.raises(ValueError, match="not marked `rpc`"):
        test.check_forkchoice_declaration()


def test_a_marked_test_may_declare_tags() -> None:
    """The same declaration is accepted once the marker sets the flag."""
    test = build(chain("finalized", "safe", None))
    test.emit_rpc_expectations = True

    test.check_forkchoice_declaration()
