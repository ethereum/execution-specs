"""Test the pre_alloc_group marker functionality."""

import textwrap
from pathlib import Path
from typing import Any, ClassVar, Dict, List
from unittest.mock import Mock

import pytest

from execution_testing.base_types import Address
from execution_testing.fixtures import PreAllocGroups
from execution_testing.forks import Fork, Prague
from execution_testing.specs.base import BaseTest, FillResult
from execution_testing.test_types import Environment
from execution_testing.vm import Op

from ...shared.pre_alloc import AllocFlags
from ..filler import default_output_directory
from ..pre_alloc import Alloc


class MockTest(BaseTest):
    """Mock test class for testing."""

    pre: Alloc
    genesis_environment: Environment

    def __init__(
        self,
        pre: Alloc,
        fork: Fork,
        genesis_environment: Environment,
    ) -> None:
        """Initialize mock test."""
        super().__init__(  # type: ignore
            pre=pre,
            fork=fork,
            genesis_environment=genesis_environment,
        )

    def generate(self, *args: Any, **kwargs: Any) -> FillResult:
        """Mock generate method."""
        raise NotImplementedError("This is a mock test class")

    def get_genesis_environment(self) -> Environment:
        """Return the genesis environment."""
        return self.genesis_environment.set_fork_requirements(
            self.fork.fork_at(
                block_number=self.genesis_environment.number,
                timestamp=self.genesis_environment.timestamp,
            )
        )


def test_pre_alloc_group_same() -> None:
    """Test that pre_alloc_group("separate") forces unique grouping."""
    # Create mock environment and pre-allocation
    env = Environment()
    pre_1 = Alloc(fork=Prague, flags=AllocFlags.NONE)
    pre_2 = Alloc(fork=Prague, flags=AllocFlags.NONE)

    # Deploy different contracts and fund eoas with different amounts,
    # should still result in the same group hash.
    pre_1.deploy_contract(code=Op.STOP)
    pre_2.deploy_contract(code=Op.INVALID)

    pre_1.fund_eoa(amount=0)
    pre_2.fund_eoa(amount=1)

    # Create test without marker
    hash1 = pre_1.compute_pre_alloc_group_hash(
        fork=Prague, genesis_environment=env, group_salt=None
    )
    hash2 = pre_1.compute_pre_alloc_group_hash(
        fork=Prague, genesis_environment=env, group_salt=None
    )

    # Hashes should be equal
    assert hash1 == hash2


def test_pre_alloc_group_separate() -> None:
    """Test that pre_alloc_group("separate") forces unique grouping."""
    # Create mock environment and pre-allocation
    env = Environment()
    pre = Alloc(fork=Prague, flags=AllocFlags.NONE)
    fork = Prague

    # Create test without marker
    test1 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()
    hash1 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt=None
    )

    # Create test with "separate" marker
    mock_request = Mock()
    mock_request.node = Mock()
    mock_request.node.nodeid = "test_module.py::test_function"
    mock_marker = Mock()
    mock_marker.args = ("separate",)
    mock_request.node.get_closest_marker = Mock(return_value=mock_marker)

    test2 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env2 = test2.get_genesis_environment()
    # For "separate" marker, use the node ID as the salt
    hash2 = pre.compute_pre_alloc_group_hash(
        fork=fork,
        genesis_environment=genesis_env2,
        group_salt=mock_request.node.nodeid,
    )

    # Hashes should be different due to "separate" marker
    assert hash1 != hash2

    # Create another test without marker - should match first test
    test3 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env3 = test3.get_genesis_environment()
    hash3 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env3, group_salt=None
    )

    assert hash1 == hash3


def test_pre_alloc_group_custom_salt() -> None:
    """Test that custom group names create consistent grouping."""
    env = Environment()
    pre = Alloc(fork=Prague, flags=AllocFlags.NONE)
    fork = Prague

    # Create test with custom group "eip1234"
    mock_request1 = Mock()
    mock_request1.node = Mock()
    mock_request1.node.nodeid = "test_module.py::test_function1"
    mock_marker1 = Mock()
    mock_marker1.args = ("eip1234",)
    mock_request1.node.get_closest_marker = Mock(return_value=mock_marker1)

    test1 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()
    hash1 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt="eip1234"
    )

    # Create another test with same custom group "eip1234"
    mock_request2 = Mock()
    mock_request2.node = Mock()
    mock_request2.node.nodeid = (
        "test_module.py::test_function2"  # Different nodeid
    )
    mock_marker2 = Mock()
    mock_marker2.args = ("eip1234",)  # Same group
    mock_request2.node.get_closest_marker = Mock(return_value=mock_marker2)

    test2 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env2 = test2.get_genesis_environment()
    hash2 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env2, group_salt="eip1234"
    )

    # Hashes should be the same - both in "eip1234" group
    assert hash1 == hash2

    # Create test with different custom group "eip5678"
    mock_request3 = Mock()
    mock_request3.node = Mock()
    mock_request3.node.nodeid = "test_module.py::test_function3"
    mock_marker3 = Mock()
    mock_marker3.args = ("eip5678",)  # Different group
    mock_request3.node.get_closest_marker = Mock(return_value=mock_marker3)

    test3 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env3 = test3.get_genesis_environment()
    hash3 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env3, group_salt="eip5678"
    )

    # Hash should be different - different custom group
    assert hash1 != hash3
    assert hash2 != hash3


def test_pre_alloc_group_separate_different_nodeids() -> None:
    """Test that different tests with "separate" get different hashes."""
    env = Environment()
    pre = Alloc(fork=Prague, flags=AllocFlags.NONE)
    fork = Prague

    # Create test with "separate" and nodeid1
    mock_request1 = Mock()
    mock_request1.node = Mock()
    mock_request1.node.nodeid = "test_module.py::test_function1"
    mock_marker1 = Mock()
    mock_marker1.args = ("separate",)
    mock_request1.node.get_closest_marker = Mock(return_value=mock_marker1)

    test1 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()
    hash1 = pre.compute_pre_alloc_group_hash(
        fork=fork,
        genesis_environment=genesis_env1,
        group_salt=mock_request1.node.nodeid,
    )

    # Create test with "separate" and nodeid2
    mock_request2 = Mock()
    mock_request2.node = Mock()
    mock_request2.node.nodeid = "test_module.py::test_function2"
    mock_marker2 = Mock()
    mock_marker2.args = ("separate",)
    mock_request2.node.get_closest_marker = Mock(return_value=mock_marker2)

    test2 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env2 = test2.get_genesis_environment()
    hash2 = pre.compute_pre_alloc_group_hash(
        fork=fork,
        genesis_environment=genesis_env2,
        group_salt=mock_request2.node.nodeid,
    )

    # Hashes should be different due to different nodeids
    assert hash1 != hash2


def test_no_pre_alloc_group_marker() -> None:
    """Test normal grouping without pre_alloc_group marker."""
    env = Environment()
    pre = Alloc(fork=Prague, flags=AllocFlags.NONE)
    fork = Prague

    # Create test without marker but with request object
    mock_request = Mock()
    mock_request.node = Mock()
    mock_request.node.nodeid = "test_module.py::test_function"
    mock_request.node.get_closest_marker = Mock(return_value=None)  # No marker

    test1 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()
    hash1 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt=None
    )

    # Create test without any request
    test2 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env2 = test2.get_genesis_environment()
    hash2 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env2, group_salt=None
    )

    # Hashes should be the same - both have no marker
    assert hash1 == hash2


def test_pre_alloc_group_with_reason() -> None:
    """Test that reason kwarg is accepted but doesn't affect grouping."""
    env = Environment()
    pre = Alloc(fork=Prague, flags=AllocFlags.NONE)
    fork = Prague

    # Create test with custom group and reason
    mock_request1 = Mock()
    mock_request1.node = Mock()
    mock_request1.node.nodeid = "test_module.py::test_function1"
    mock_marker1 = Mock()
    mock_marker1.args = ("hardcoded_addresses",)
    mock_marker1.kwargs = {
        "reason": "Uses legacy hardcoded addresses for backwards compatibility"
    }
    mock_request1.node.get_closest_marker = Mock(return_value=mock_marker1)

    test1 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()
    hash1 = pre.compute_pre_alloc_group_hash(
        fork=fork,
        genesis_environment=genesis_env1,
        group_salt="hardcoded_addresses",
    )

    # Create another test with same group but different reason
    mock_request2 = Mock()
    mock_request2.node = Mock()
    mock_request2.node.nodeid = "test_module.py::test_function2"
    mock_marker2 = Mock()
    mock_marker2.args = ("hardcoded_addresses",)
    mock_marker2.kwargs = {"reason": "Different reason but same group"}
    mock_request2.node.get_closest_marker = Mock(return_value=mock_marker2)

    test2 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env2 = test2.get_genesis_environment()
    hash2 = pre.compute_pre_alloc_group_hash(
        fork=fork,
        genesis_environment=genesis_env2,
        group_salt="hardcoded_addresses",
    )

    # Hashes should be the same - reason doesn't affect grouping
    assert hash1 == hash2


def test_pre_alloc_group_with_modified_alloc() -> None:
    """Test that modifications to Alloc affect grouping via group_salt()."""
    env = Environment()
    fork = Prague

    # Create unmodified pre-allocation
    pre1 = Alloc(fork=fork, flags=AllocFlags.NONE)
    test1 = MockTest(pre=pre1, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()
    hash1 = pre1.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt=None
    )

    # Create pre-allocation with a funded address
    pre2 = Alloc(fork=fork, flags=AllocFlags.NONE)
    pre2.fund_address(
        Address("0x1234567890123456789012345678901234567890"), amount=100
    )
    test2 = MockTest(pre=pre2, genesis_environment=env, fork=fork)
    genesis_env2 = test2.get_genesis_environment()
    hash2 = pre2.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env2, group_salt=None
    )

    # Hashes should be different - pre2 has modifications
    assert hash1 != hash2


def test_pre_alloc_explicit_salt_overrides_group_salt() -> None:
    """
    Test that explicit group_salt parameter overrides group_salt() method.
    """
    env = Environment()
    fork = Prague

    # Create pre-allocation with modifications
    pre = Alloc(fork=fork, flags=AllocFlags.NONE)
    pre.fund_address(
        Address("0x1234567890123456789012345678901234567890"), amount=100
    )

    test1 = MockTest(pre=pre, genesis_environment=env, fork=fork)
    genesis_env1 = test1.get_genesis_environment()

    # Hash with explicit salt should ignore the internal group_salt()
    hash1 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt="custom_salt"
    )

    # Hash without explicit salt uses internal group_salt()
    hash2 = pre.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt=None
    )

    # Hashes should be different
    assert hash1 != hash2


def test_pre_alloc_group_same_modifications() -> None:
    """Test that identical modifications produce the same hash."""
    env = Environment()
    fork = Prague

    # Create two pre-allocations with same modification
    pre1 = Alloc(fork=fork, flags=AllocFlags.NONE)
    pre1.fund_address(
        Address("0x1234567890123456789012345678901234567890"), amount=100
    )

    pre2 = Alloc(fork=fork, flags=AllocFlags.NONE)
    pre2.fund_address(
        Address("0x1234567890123456789012345678901234567890"), amount=100
    )

    test1 = MockTest(pre=pre1, genesis_environment=env, fork=fork)
    test2 = MockTest(pre=pre2, genesis_environment=env, fork=fork)

    genesis_env1 = test1.get_genesis_environment()
    genesis_env2 = test2.get_genesis_environment()

    hash1 = pre1.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env1, group_salt=None
    )

    hash2 = pre2.compute_pre_alloc_group_hash(
        fork=fork, genesis_environment=genesis_env2, group_salt=None
    )

    # Hashes should be the same - both have identical modifications
    assert hash1 == hash2


class FormattedTest:
    """Represents a single formatted test."""

    kwargs: Dict[str, str]
    template: ClassVar[str]

    def __init__(self, **kwargs: str) -> None:  # noqa: D107
        self.kwargs = kwargs

    def format(self) -> str:  # noqa: D102
        return self.template.format(**self.kwargs)


class StateTest(FormattedTest):  # noqa: D101
    template: ClassVar[str] = textwrap.dedent(
        """\
        import pytest

        from execution_testing import  (
            Account,
            Alloc,
            Environment,
            Op,
            StateTestFiller,
            Transaction
        )

        @pytest.mark.valid_from("Istanbul")
        def test_chainid(state_test: StateTestFiller, pre: Alloc) -> None:
            contract_address = pre.deploy_contract(Op.SSTORE(1, Op.CHAINID) + Op.STOP)
            sender = pre.fund_eoa()

            tx = Transaction(
                ty=0x0,
                chain_id=0x01,
                to=contract_address,
                gas_limit=100_000,
                sender=sender,
            )

            post = {{
                contract_address: Account(storage={{"0x01": "0x01"}}),
            }}

            state_test(env={env}, pre=pre, post=post, tx=tx)
        """  # noqa: E501
    )


class BlockchainTest(FormattedTest):  # noqa: D101
    template: ClassVar[str] = textwrap.dedent(
        """\
        import pytest

        from execution_testing import  (
            Account,
            Alloc,
            Block,
            BlockchainTestFiller,
            Environment,
            Op,
            Transaction
        )

        @pytest.mark.valid_from("Istanbul")
        def test_chainid_blockchain(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
            contract_address = pre.deploy_contract(Op.SSTORE(1, Op.CHAINID) + Op.STOP)
            sender = pre.fund_eoa()

            tx = Transaction(
                ty=0x0,
                chain_id=0x01,
                to=contract_address,
                gas_limit=100_000,
                sender=sender,
            )

            post = {{
                contract_address: Account(storage={{"0x01": "0x01"}}),
            }}

            blockchain_test(
                genesis_environment={env},
                pre=pre,
                post=post,
                blocks=[Block(txs=[tx])],
            )
        """  # noqa: E501
    )


@pytest.mark.parametrize(
    "test_definitions,expected_different_pre_alloc_groups",
    [
        # Environment fields not affecting the pre-alloc groups
        pytest.param(
            [
                BlockchainTest(env="Environment()"),
                StateTest(env="Environment()"),
            ],
            1,
            id="different_types_default_environment",
        ),
        pytest.param(
            [
                StateTest(
                    env="Environment(fee_recipient=pre.fund_eoa(amount=0))"
                ),
                StateTest(env="Environment(fee_recipient=1)"),
                StateTest(env="Environment(fee_recipient=2)"),
            ],
            1,
            id="different_fee_recipients",
        ),
        pytest.param(
            [
                StateTest(env="Environment(fee_recipient=1)"),
                BlockchainTest(env="Environment(fee_recipient=1)"),
            ],
            2,
            id="different_fee_recipients_different_types",
        ),
        pytest.param(
            [
                StateTest(env="Environment(prev_randao=1)"),
                StateTest(env="Environment(prev_randao=2)"),
            ],
            1,
            id="different_prev_randaos",
        ),
        pytest.param(
            [
                StateTest(env="Environment(prev_randao=1)"),
                BlockchainTest(env="Environment(prev_randao=2)"),
            ],
            2,
            id="different_prev_randaos_different_types",
        ),
        pytest.param(
            [
                StateTest(env="Environment(timestamp=1)"),
                StateTest(env="Environment(timestamp=2)"),
            ],
            1,
            id="different_timestamps",
        ),
        pytest.param(
            [
                StateTest(env="Environment(extra_data='0x01')"),
                StateTest(env="Environment(extra_data='0x02')"),
            ],
            1,
            id="different_extra_data",
        ),
        pytest.param(
            [
                StateTest(env="Environment(extra_data='0x01')"),
                BlockchainTest(env="Environment(extra_data='0x02')"),
            ],
            2,
            id="different_extra_data_different_types",
            marks=pytest.mark.xfail(
                reason="Extra data is excluded=True in the Environment "
                "model, so it does not propagate correctly to the genesis "
                "header without a lot of code changes.",
            ),
        ),
        # Environment fields affecting the pre-alloc groups
        pytest.param(
            [
                StateTest(env="Environment(gas_limit=100_000_000)"),
                StateTest(env="Environment(gas_limit=200_000_000)"),
            ],
            2,
            id="different_gas_limits",
        ),
        pytest.param(
            [
                StateTest(env="Environment(number=10)"),
                StateTest(env="Environment(number=20)"),
            ],
            2,
            id="different_block_numbers",
        ),
        pytest.param(
            [
                StateTest(env="Environment(base_fee_per_gas=10)"),
                StateTest(env="Environment(base_fee_per_gas=20)"),
            ],
            2,
            id="different_base_fee",
        ),
        pytest.param(
            [
                StateTest(env="Environment(excess_blob_gas=10)"),
                StateTest(env="Environment(excess_blob_gas=20)"),
            ],
            2,
            id="different_excess_blob_gas",
        ),
    ],
)
def test_pre_alloc_grouping_by_test_type(
    pytester: pytest.Pytester,
    test_definitions: List[FormattedTest],
    expected_different_pre_alloc_groups: int,
) -> None:
    """
    Test pre-alloc grouping when filling state tests, and the effect of the
    `state_test.env`.
    """
    tests_dir = Path(pytester.mkdir("tests"))
    for i, test in enumerate(test_definitions):
        test_module = tests_dir / f"test_{i}.py"
        test_module.write_text(test.format())
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    args = [
        "-c",
        "pytest-fill.ini",
        "--generate-pre-alloc-groups",
        "--fork=Cancun",
    ]
    result = pytester.runpytest(*args)
    result.assert_outcomes(
        passed=len(test_definitions),
        failed=0,
        skipped=0,
        errors=0,
    )

    output_dir = (
        Path(default_output_directory()).absolute()
        / "blockchain_tests_engine_x"
        / "pre_alloc"
    )
    assert output_dir.exists()
    groups = PreAllocGroups.from_folder(output_dir, lazy_load=False)
    if (
        len([f for f in output_dir.iterdir() if f.name.endswith(".json")])
        != expected_different_pre_alloc_groups
    ):
        error_message = (
            f"Expected {expected_different_pre_alloc_groups} different "
            f"pre-alloc groups, but got {len(groups)}"
        )
        for group_hash, group in groups.items():
            error_message += f"\n{group_hash}: \n"
            error_message += f"tests: {group.test_ids}\n"
            env_json = group.environment.model_dump_json(
                indent=2, exclude_none=True
            )
            error_message += f"env: {env_json}\n"
        raise AssertionError(error_message)

    for group_hash, group in groups.items():
        assert (
            group.environment.fee_recipient == group.genesis.fee_recipient
        ), (
            f"Fee recipient mismatch for group {group_hash}: "
            f"{group.environment.fee_recipient} != "
            f"{group.genesis.fee_recipient}"
        )
        assert group.environment.prev_randao == group.genesis.prev_randao, (
            f"Prev randao mismatch for group {group_hash}: "
            f"{group.environment.prev_randao} != {group.genesis.prev_randao}"
        )
        assert group.environment.extra_data == group.genesis.extra_data, (
            f"Extra data mismatch for group {group_hash}: "
            f"{group.environment.extra_data} != {group.genesis.extra_data}"
        )
        assert group.environment.number == group.genesis.number, (
            f"Number mismatch for group {group_hash}: "
            f"{group.environment.number} != {group.genesis.number}"
        )
        assert group.environment.timestamp == group.genesis.timestamp, (
            f"Timestamp mismatch for group {group_hash}: "
            f"{group.environment.timestamp} != {group.genesis.timestamp}"
        )
        assert group.environment.difficulty == group.genesis.difficulty, (
            f"Difficulty mismatch for group {group_hash}: "
            f"{group.environment.difficulty} != {group.genesis.difficulty}"
        )
        assert group.environment.gas_limit == group.genesis.gas_limit, (
            f"Gas limit mismatch for group {group_hash}: "
            f"{group.environment.gas_limit} != {group.genesis.gas_limit}"
        )
        assert (
            group.environment.base_fee_per_gas
            == group.genesis.base_fee_per_gas
        ), (
            f"Base fee per gas mismatch for group {group_hash}: "
            f"{group.environment.base_fee_per_gas} != "
            f"{group.genesis.base_fee_per_gas}"
        )
        assert (
            group.environment.excess_blob_gas == group.genesis.excess_blob_gas
        ), (
            f"Excess blob gas mismatch for group {group_hash}: "
            f"{group.environment.excess_blob_gas} != "
            f"{group.genesis.excess_blob_gas}"
        )
        assert (
            group.environment.blob_gas_used == group.genesis.blob_gas_used
        ), (
            f"Blob gas used mismatch for group {group_hash}: "
            f"{group.environment.blob_gas_used} != "
            f"{group.genesis.blob_gas_used}"
        )
        assert (
            group.environment.parent_beacon_block_root
            == group.genesis.parent_beacon_block_root
        ), (
            f"Parent beacon block root mismatch for group {group_hash}: "
            f"{group.environment.parent_beacon_block_root} != "
            f"{group.genesis.parent_beacon_block_root}"
        )
