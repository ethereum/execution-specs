"""Helpers to load and run blockchain tests from JSON files."""

import re
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from unittest.mock import call, patch

import pytest
from _pytest.config import Config
from ethereum_rlp import rlp
from ethereum_rlp.exceptions import RLPException
from ethereum_types.numeric import U64, U256, Uint

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

TRANSITION_NETWORK = re.compile(
    r"^(?P<from_fork>.+?)To(?P<to_fork>.+?)"
    r"At(?P<by_time>Time)?(?P<value>\d+)(?P<kilo>k)?$"
)
"""
Network name of a fork-transition fixture, such as `BPO2ToAmsterdamAtTime15k`
or `BerlinToLondonAt5`: the chain starts on the first fork and the second
fork activates at the given timestamp (`AtTime`) or block number (`At`).
"""

HEADER_NUMBER_INDEX = 8
HEADER_TIMESTAMP_INDEX = 11
"""Positions of the number and timestamp in an RLP-encoded block header."""


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
        Parse a transition fixture's network name, or return `None` for a
        plain fork name.
        """
        match = TRANSITION_NETWORK.match(network)
        if match is None:
            return None
        value = int(match["value"]) * (1000 if match["kilo"] else 1)
        criteria: ForkCriteria = (
            ByTimestamp(value) if match["by_time"] else ByBlockNumber(value)
        )
        return cls(match["from_fork"], match["to_fork"], criteria)

    def activates(self, json_block: Dict[str, Any]) -> bool:
        """
        Return whether `to_fork` is active for `json_block`.

        A block that is expected to be invalid carries only its RLP, so the
        number and timestamp are read from the encoded header when the
        decoded header is absent. Their positions in the header are the
        same in every fork. A block whose RLP does not decode is left to the
        fork that is active before it.
        """
        if "blockHeader" in json_block:
            json_header = json_block["blockHeader"]
            number = int(json_header["number"], 16)
            timestamp = int(json_header["timestamp"], 16)
        else:
            try:
                block = rlp.decode(hex_to_bytes(json_block["rlp"]))
                if not isinstance(block, list):
                    return False
                header = block[0]
                if not isinstance(header, list):
                    return False
                number_bytes = header[HEADER_NUMBER_INDEX]
                timestamp_bytes = header[HEADER_TIMESTAMP_INDEX]
                if not isinstance(number_bytes, bytes) or not isinstance(
                    timestamp_bytes, bytes
                ):
                    return False
            except (RLPException, IndexError):
                return False
            number = int.from_bytes(number_bytes, "big")
            timestamp = int.from_bytes(timestamp_bytes, "big")
        return self.criteria.check(Uint(number), U256(timestamp))


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
            if self.transition is not None:
                self._schedule_fork(stack, load, self.transition.criteria)

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
        """
        fork_module = load.fork.hardfork.module("fork")
        if hasattr(fork_module, "FORK_CRITERIA"):
            stack.enter_context(
                patch.object(fork_module, "FORK_CRITERIA", criteria)
            )

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
