"""Helpers to load and run blockchain tests from JSON files."""

from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type
from unittest.mock import call, patch

import pytest
from _pytest.config import Config
from ethereum_rlp import rlp
from ethereum_rlp.exceptions import RLPException
from ethereum_types.numeric import U64, U256, Uint
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.forks import get_forks, get_transition_forks
from execution_testing.forks.base_fork import BaseFork

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import EthereumException, StateWithEmptyAccount
from ethereum.fork_criteria import ByBlockNumber, ByTimestamp, ForkCriteria
from ethereum.state_mpt import close_state
from ethereum.utils.hexadecimal import hex_to_bytes
from ethereum_spec_tools.loaders.fixture_loader import Load

from .. import FORKS
from ..stash_keys import desired_forks_key
from .exceptional_test_patterns import exceptional_blockchain_test_patterns
from .fixtures import Fixture, FixturesFile, FixtureTestItem

TESTING_FORKS: Dict[str, Type[BaseFork]] = {
    fork.name(): fork for fork in get_forks()
}
"""
Forks of the testing framework by name. The network of a fixture, or either
end of a transition fixture's network, is the name of the testing fork it
was filled for.
"""

TRANSITION_FORKS = {fork.name(): fork for fork in get_transition_forks()}
"""
Transition forks of the testing framework by name. The network of a
fork-transition fixture, such as `BPO2ToAmsterdamAtTime15k` or
`BerlinToLondonAt5`, is the name of the transition fork it was filled for:
the chain starts on the first fork and the second fork activates at the
transition fork's timestamp or block number.
"""


class NoTestsFoundError(Exception):
    """
    An exception thrown when the test for a particular fork isn't
    available in the json fixture.
    """


@dataclass(frozen=True)
class ForkTransition:
    """The fork activation described by a transition fixture's network."""

    from_fork: str
    """JSON test name of the fork the chain starts on."""

    to_fork: str
    """JSON test name of the fork that activates."""

    criteria: ForkCriteria
    """When `to_fork` activates."""

    @classmethod
    def parse(cls, network: str) -> Optional["ForkTransition"]:
        """
        Look up a transition fixture's network name among the transition
        forks, or return `None` for a plain fork name.
        """
        fork = TRANSITION_FORKS.get(network)
        if fork is None:
            return None
        criteria: ForkCriteria = (
            ByBlockNumber(fork.at_block)
            if fork.at_block
            else ByTimestamp(fork.at_timestamp)
        )
        return cls(
            fork.transitions_from().name(),
            fork.transitions_to().name(),
            criteria,
        )

    def activates(self, json_block: Dict[str, Any]) -> bool:
        """
        Return whether `to_fork` is active for `json_block`.

        A block that is expected to be invalid carries its RLP and, when
        that RLP decodes, the decoded block under `rlp_decoded`. A block
        without a header to read, because its RLP does not decode, is left
        to the fork that is active before it, as is a header whose
        number or timestamp does not fit in a `Uint` or `U256`, respectively.
        """
        header = json_block.get("blockHeader")
        if header is None:
            header = json_block.get("rlp_decoded", {}).get("blockHeader")
        if header is None:
            return False
        fixture_header = FixtureHeader.model_validate(header)
        try:
            return self.criteria.check(
                Uint(fixture_header.number), U256(fixture_header.timestamp)
            )
        except OverflowError:
            return False


def add_block_to_chain(
    chain: Any, json_block: Any, load: Load, mock_pow: bool
) -> None:
    """Add a block from JSON data to the blockchain chain."""
    (
        block,
        block_header_hash,
        block_rlp,
    ) = load.json_to_block(json_block)

    assert keccak256(rlp.encode(block.header)) == block_header_hash
    assert rlp.encode(block) == block_rlp

    if not mock_pow:
        load.fork.state_transition(chain, block)
    else:
        fork_module = load.fork.hardfork.module("fork")
        with patch.object(
            fork_module,
            "validate_proof_of_work",
            autospec=True,
        ) as mocked_pow_validator:
            load.fork.state_transition(chain, block)
            mocked_pow_validator.assert_has_calls(
                [call(block.header)],
                any_order=False,
            )


class BlockchainTestFixture(Fixture, FixtureTestItem):
    """Single blockchain test fixture from a JSON file."""

    fork_name: str
    transition: Optional[ForkTransition]

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a single blockchain test fixture from a JSON file."""
        super().__init__(*args, **kwargs)
        self.fork_name = self.test_dict["network"]
        self.add_marker(pytest.mark.fork(self.fork_name))
        self.add_marker("json_blockchain_tests")
        self.transition = ForkTransition.parse(self.fork_name)
        if self.transition is None:
            self.eels_fork = FORKS[self.fork_name].short_name
        else:
            self.eels_fork = FORKS[self.transition.to_fork].short_name

        # Mark tests with exceptional markers
        test_patterns = exceptional_blockchain_test_patterns(
            self.fork_name, self.eels_fork
        )
        if any(x.search(self.nodeid) for x in test_patterns.expected_fail):
            self.add_marker(pytest.mark.skip("Expected to fail"))
        if any(x.search(self.nodeid) for x in test_patterns.slow):
            self.add_marker("slow")
        if any(x.search(self.nodeid) for x in test_patterns.big_memory):
            self.add_marker("bigmem")

    @property
    def fixtures_file(self) -> FixturesFile:
        """Fixtures file from which the test fixture was collected."""
        parent = self.parent
        assert parent is not None
        assert isinstance(parent, FixturesFile)
        return parent

    @property
    def test_dict(self) -> Dict[str, Any]:
        """Load test from disk."""
        loaded_file = self.fixtures_file.data
        return loaded_file[self.test_key]

    def runtest(self) -> None:
        """Run a blockchain state test from JSON test case data."""
        json_data = self.test_dict
        has_post_state = "postState" in json_data
        allow_post_state_hash = self.config.getoption(
            "allow_post_state_hash", False
        )
        post_state_hash_only = (
            not has_post_state
            and "postStateHash" in json_data
            and allow_post_state_hash
        )
        if not has_post_state and not post_state_hash_only:
            pytest.xfail(
                f"{self.test_file}[{self.test_key}] doesn't have post state"
            )

        # Currently, there are 5 tests in the ethereum/tests fixtures
        # where we have non block specific exceptions.
        # For example: All the blocks process correctly but the final
        # block hash provided in the test is not correct. Or all the
        # blocks process correctly but the post state provided is not
        # right. Since these tests do not directly have anything to do
        # with the state transition itself, we skip these
        # See src/BlockchainTestsFiller/InvalidBlocks/bcExpectSection
        # in ethereum/tests
        if "exceptions" in json_data:
            pytest.xfail(
                f"{self.test_file}[{self.test_key}] has unrelated exceptions"
            )

        load = Load(self.eels_fork)
        # A transition fixture starts its chain on the previous fork; the
        # genesis and the blocks before the activation belong to it.
        if self.transition is None:
            current = load
        else:
            current = Load(FORKS[self.transition.from_fork].short_name)

        genesis_header = current.json_to_header(
            json_data["genesisBlockHeader"]
        )
        parameters = [
            genesis_header,
            (),
            (),
        ]
        if hasattr(genesis_header, "withdrawals_root"):
            parameters.append(())

        if hasattr(genesis_header, "requests_root"):
            parameters.append(())

        genesis_block = current.fork.Block(*parameters)

        genesis_header_hash = hex_to_bytes(
            json_data["genesisBlockHeader"]["hash"]
        )
        assert keccak256(rlp.encode(genesis_header)) == genesis_header_hash
        genesis_rlp = hex_to_bytes(json_data["genesisRLP"])
        assert rlp.encode(genesis_block) == genesis_rlp

        try:
            state = current.json_to_state(json_data["pre"])
        except StateWithEmptyAccount as e:
            pytest.xfail(str(e))

        chain = current.fork.BlockChain(
            blocks=[genesis_block],
            state=state,
            chain_id=U64(json_data["genesisBlockHeader"].get("chainId", 1)),
        )

        def mock_pow(fork_load: Load) -> bool:
            return (
                json_data["sealEngine"] == "NoProof"
                and not fork_load.fork.proof_of_stake
            )

        with ExitStack() as stack:
            if self.transition is None:
                self._schedule_blob_params(stack, load, self.fork_name)
            else:
                self._schedule_fork(stack, load, self.transition.criteria)
                self._schedule_blob_params(
                    stack, current, self.transition.from_fork
                )
                self._schedule_blob_params(
                    stack, load, self.transition.to_fork
                )

            for json_block in json_data["blocks"]:
                if (
                    self.transition is not None
                    and current is not load
                    and self.transition.activates(json_block)
                ):
                    chain = load.fork.apply_fork(chain)
                    current = load

                block_exception = None
                for key, value in json_block.items():
                    if key.startswith("expectException"):
                        block_exception = value
                        break
                    if key == "exceptions":
                        block_exception = value
                        break

                if block_exception:
                    # TODO: Once all the specific exception types are
                    #       thrown, only `pytest.raises` the correct
                    #       exception type instead of all of them.
                    with pytest.raises((EthereumException, RLPException)):
                        add_block_to_chain(
                            chain, json_block, current, mock_pow(current)
                        )
                        close_state(chain.state)
                    return
                else:
                    add_block_to_chain(
                        chain, json_block, current, mock_pow(current)
                    )

        last_block_hash = hex_to_bytes(json_data["lastblockhash"])
        assert (
            keccak256(rlp.encode(chain.blocks[-1].header)) == last_block_hash
        )

        if has_post_state:
            expected_post_state = current.json_to_state(json_data["postState"])
            assert chain.state == expected_post_state
            close_state(expected_post_state)
        close_state(chain.state)

    @staticmethod
    def _schedule_fork(
        stack: ExitStack, load: Load, criteria: ForkCriteria
    ) -> None:
        """
        Make the fork of `load` activate at `criteria` for the duration of
        `stack`, so that the fork detects its own fork block as a client
        with a matching chain configuration would.

        `FORK_CRITERIA` is defined in the fork's package, where the fork
        tooling reads it. A fork whose `fork` module needs it imports it by
        name, which binds a copy in that module at import time, so that
        copy is patched as well.
        """
        hardfork = load.fork.hardfork
        stack.enter_context(
            patch.object(hardfork.mod, "FORK_CRITERIA", criteria)
        )
        fork_module = hardfork.module("fork")
        if hasattr(fork_module, "FORK_CRITERIA"):
            stack.enter_context(
                patch.object(fork_module, "FORK_CRITERIA", criteria)
            )

    @staticmethod
    def _schedule_blob_params(
        stack: ExitStack, load: Load, fork_name: str
    ) -> None:
        """
        Give the fork of `load` the blob schedule that the testing
        framework's fork `fork_name` is filled with, for the duration of
        `stack`, when that fork is a blob parameter only (BPO) fork.

        A BPO fork of the spec is a copy of its predecessor whose blob
        schedule is a placeholder; the schedule lives in the testing
        framework's fork of the same name. The fill's `T8N` clones the spec
        fork with that schedule, but a clone cannot validate a chain across
        a fork transition: `calculate_excess_blob_gas` recognises the
        parent header by the previous fork's `Header` class, which the
        clone refers to under another name. The constants are patched in
        place instead. `GasCosts.BLOB_TARGET_GAS_PER_BLOCK` and the `fork`
        module's `MAX_BLOB_GAS_PER_BLOCK` are derived from the schedule at
        import time, so they are patched along with it.
        """
        testing_fork = TESTING_FORKS.get(fork_name)
        if testing_fork is None or not testing_fork.bpo_fork():
            return
        gas_costs = load.fork.hardfork.module("vm.gas").GasCosts
        fork_module = load.fork.hardfork.module("fork")
        per_blob: U64 = gas_costs.PER_BLOB
        target = U64(testing_fork.target_blobs_per_block())
        maximum = U64(testing_fork.max_blobs_per_block())
        update_fraction = Uint(testing_fork.blob_base_fee_update_fraction())
        patches = (
            (gas_costs, "BLOB_SCHEDULE_TARGET", target),
            (gas_costs, "BLOB_SCHEDULE_MAX", maximum),
            (gas_costs, "BLOB_TARGET_GAS_PER_BLOCK", per_blob * target),
            (gas_costs, "BLOB_BASE_FEE_UPDATE_FRACTION", update_fraction),
            (fork_module, "MAX_BLOB_GAS_PER_BLOCK", per_blob * maximum),
        )
        for owner, name, value in patches:
            stack.enter_context(patch.object(owner, name, value))

    def reportinfo(self) -> Tuple[Path, int, str]:
        """Return information for test reporting."""
        return self.path, 1, self.name

    @classmethod
    def is_format(cls, test_dict: Dict[str, Any]) -> bool:
        """Return true if the object can be parsed as the fixture type."""
        if "genesisBlockHeader" not in test_dict:
            return False
        if "blocks" not in test_dict:
            return False
        if "engineNewPayloads" in test_dict:
            return False
        if "preHash" in test_dict:
            return False
        if "network" not in test_dict:
            return False
        return True

    @classmethod
    def has_desired_fork(
        cls, test_dict: Dict[str, Any], config: Config
    ) -> bool:
        """
        Check if the item fork is in the desired forks list.

        A transition fixture is desired when the fork it activates is, as
        long as the fork it starts on is known.
        """
        desired_forks = config.stash.get(desired_forks_key, None)
        if desired_forks is None:
            return True
        network = test_dict["network"]
        if network in desired_forks:
            return True
        transition = ForkTransition.parse(network)
        return (
            transition is not None
            and transition.from_fork in FORKS
            and transition.to_fork in desired_forks
        )
