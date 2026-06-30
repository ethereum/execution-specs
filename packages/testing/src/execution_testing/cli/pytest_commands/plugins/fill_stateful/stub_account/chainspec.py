"""
Genesis chainspecs for fill-stateful hive mode.

A :class:`ChainSpec` is a validated list of :mod:`.template` stub-account
models loaded from a user-supplied JSON file. :meth:`ChainSpec.alloc`
expands and merges them into an ``Alloc`` that
``hive_session.configure_hive`` lays on top of the fork's required system
contracts. The ``--chainspec`` CLI flag accepts a path to such a file.

Example chainspecs ship under ``chainspecs/`` next to this module
(``jochemnet.json``, ``perf-devnet-3.json``); copy and edit them as a
starting point.

Chainspecs are intentionally small (local-debug genesis). Large
bloatnet-scale state belongs in a state-actor snapshot, not these
Python-built allocs.
"""

from pathlib import Path
from typing import List, Union

from pydantic import BaseModel

from execution_testing.test_types import Alloc

from .template import AnyStubAccount, StubAlloc

DEFAULT_CHAINSPEC_PATH: Path = (
    Path(__file__).parent / "chainspecs" / "jochemnet.json"
)


class ChainSpec(BaseModel):
    """A named genesis pre-state built from stub-account templates."""

    name: str
    stubs: List[AnyStubAccount]

    def alloc(self) -> Alloc:
        """Expand and merge every stub into a genesis ``Alloc``."""
        merged: StubAlloc = {}
        for stub in self.stubs:
            merged.update(stub.expand())
        return Alloc.model_validate(merged)


def load_chainspec(path: Union[str, Path]) -> ChainSpec:
    """Parse the chainspec JSON file at ``path``."""
    chainspec_path = Path(path)
    if not chainspec_path.is_file():
        raise FileNotFoundError(f"chainspec file not found: {chainspec_path}")
    return ChainSpec.model_validate_json(chainspec_path.read_text())


def get_chainspec(path: Union[str, Path]) -> Alloc:
    """Return the genesis ``Alloc`` for the chainspec JSON at ``path``."""
    return load_chainspec(path).alloc()
