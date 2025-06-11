"""Test the pre_alloc_group marker functionality."""

from unittest.mock import Mock

from ethereum_test_forks import Fork, Prague
from ethereum_test_specs.base import BaseTest
from ethereum_test_types import Alloc, Environment


class MockTest(BaseTest):
    """Mock test class for testing."""

    pre: Alloc
    genesis_environment: Environment

    def __init__(self, pre: Alloc, genesis_environment: Environment, request=None):
        """Initialize mock test."""
        super().__init__(pre=pre, genesis_environment=genesis_environment)
        self._request = request

    def generate(self, *args, **kwargs):
        """Mock generate method."""
        pass

    def get_genesis_environment(self, fork: Fork) -> Environment:
        """Return the genesis environment."""
        return self.genesis_environment


def test_pre_alloc_group_separate():
    """Test that pre_alloc_group("separate") forces unique grouping."""
    # Create mock environment and pre-allocation
    env = Environment()
    pre = Alloc()
    fork = Prague

    # Create test without marker
    test1 = MockTest(pre=pre, genesis_environment=env)
    hash1 = test1.compute_shared_pre_alloc_hash(fork)

    # Create test with "separate" marker
    mock_request = Mock()
    mock_request.node = Mock()
    mock_request.node.nodeid = "test_module.py::test_function"
    mock_marker = Mock()
    mock_marker.args = ("separate",)
    mock_request.node.get_closest_marker = Mock(return_value=mock_marker)

    test2 = MockTest(pre=pre, genesis_environment=env, request=mock_request)
    hash2 = test2.compute_shared_pre_alloc_hash(fork)

    # Hashes should be different due to "separate" marker
    assert hash1 != hash2

    # Create another test without marker - should match first test
    test3 = MockTest(pre=pre, genesis_environment=env)
    hash3 = test3.compute_shared_pre_alloc_hash(fork)

    assert hash1 == hash3


def test_pre_alloc_group_custom_salt():
    """Test that custom group names create consistent grouping."""
    env = Environment()
    pre = Alloc()
    fork = Prague

    # Create test with custom group "eip1234"
    mock_request1 = Mock()
    mock_request1.node = Mock()
    mock_request1.node.nodeid = "test_module.py::test_function1"
    mock_marker1 = Mock()
    mock_marker1.args = ("eip1234",)
    mock_request1.node.get_closest_marker = Mock(return_value=mock_marker1)

    test1 = MockTest(pre=pre, genesis_environment=env, request=mock_request1)
    hash1 = test1.compute_shared_pre_alloc_hash(fork)

    # Create another test with same custom group "eip1234"
    mock_request2 = Mock()
    mock_request2.node = Mock()
    mock_request2.node.nodeid = "test_module.py::test_function2"  # Different nodeid
    mock_marker2 = Mock()
    mock_marker2.args = ("eip1234",)  # Same group
    mock_request2.node.get_closest_marker = Mock(return_value=mock_marker2)

    test2 = MockTest(pre=pre, genesis_environment=env, request=mock_request2)
    hash2 = test2.compute_shared_pre_alloc_hash(fork)

    # Hashes should be the same - both in "eip1234" group
    assert hash1 == hash2

    # Create test with different custom group "eip5678"
    mock_request3 = Mock()
    mock_request3.node = Mock()
    mock_request3.node.nodeid = "test_module.py::test_function3"
    mock_marker3 = Mock()
    mock_marker3.args = ("eip5678",)  # Different group
    mock_request3.node.get_closest_marker = Mock(return_value=mock_marker3)

    test3 = MockTest(pre=pre, genesis_environment=env, request=mock_request3)
    hash3 = test3.compute_shared_pre_alloc_hash(fork)

    # Hash should be different - different custom group
    assert hash1 != hash3
    assert hash2 != hash3


def test_pre_alloc_group_separate_different_nodeids():
    """Test that different tests with "separate" get different hashes."""
    env = Environment()
    pre = Alloc()
    fork = Prague

    # Create test with "separate" and nodeid1
    mock_request1 = Mock()
    mock_request1.node = Mock()
    mock_request1.node.nodeid = "test_module.py::test_function1"
    mock_marker1 = Mock()
    mock_marker1.args = ("separate",)
    mock_request1.node.get_closest_marker = Mock(return_value=mock_marker1)

    test1 = MockTest(pre=pre, genesis_environment=env, request=mock_request1)
    hash1 = test1.compute_shared_pre_alloc_hash(fork)

    # Create test with "separate" and nodeid2
    mock_request2 = Mock()
    mock_request2.node = Mock()
    mock_request2.node.nodeid = "test_module.py::test_function2"
    mock_marker2 = Mock()
    mock_marker2.args = ("separate",)
    mock_request2.node.get_closest_marker = Mock(return_value=mock_marker2)

    test2 = MockTest(pre=pre, genesis_environment=env, request=mock_request2)
    hash2 = test2.compute_shared_pre_alloc_hash(fork)

    # Hashes should be different due to different nodeids
    assert hash1 != hash2


def test_no_pre_alloc_group_marker():
    """Test normal grouping without pre_alloc_group marker."""
    env = Environment()
    pre = Alloc()
    fork = Prague

    # Create test without marker but with request object
    mock_request = Mock()
    mock_request.node = Mock()
    mock_request.node.nodeid = "test_module.py::test_function"
    mock_request.node.get_closest_marker = Mock(return_value=None)  # No marker

    test1 = MockTest(pre=pre, genesis_environment=env, request=mock_request)
    hash1 = test1.compute_shared_pre_alloc_hash(fork)

    # Create test without any request
    test2 = MockTest(pre=pre, genesis_environment=env)
    hash2 = test2.compute_shared_pre_alloc_hash(fork)

    # Hashes should be the same - both have no marker
    assert hash1 == hash2


def test_pre_alloc_group_with_reason():
    """Test that reason kwarg is accepted but doesn't affect grouping."""
    env = Environment()
    pre = Alloc()
    fork = Prague

    # Create test with custom group and reason
    mock_request1 = Mock()
    mock_request1.node = Mock()
    mock_request1.node.nodeid = "test_module.py::test_function1"
    mock_marker1 = Mock()
    mock_marker1.args = ("hardcoded_addresses",)
    mock_marker1.kwargs = {"reason": "Uses legacy hardcoded addresses for backwards compatibility"}
    mock_request1.node.get_closest_marker = Mock(return_value=mock_marker1)

    test1 = MockTest(pre=pre, genesis_environment=env, request=mock_request1)
    hash1 = test1.compute_shared_pre_alloc_hash(fork)

    # Create another test with same group but different reason
    mock_request2 = Mock()
    mock_request2.node = Mock()
    mock_request2.node.nodeid = "test_module.py::test_function2"
    mock_marker2 = Mock()
    mock_marker2.args = ("hardcoded_addresses",)
    mock_marker2.kwargs = {"reason": "Different reason but same group"}
    mock_request2.node.get_closest_marker = Mock(return_value=mock_marker2)

    test2 = MockTest(pre=pre, genesis_environment=env, request=mock_request2)
    hash2 = test2.compute_shared_pre_alloc_hash(fork)

    # Hashes should be the same - reason doesn't affect grouping
    assert hash1 == hash2
