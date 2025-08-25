"""
Example usage of the pre_alloc_group marker.

This file demonstrates how tests would use the marker in practice.
Note: This is just documentation, not executable tests.
"""

import pytest


# Example 1: Test that deploys beacon root contract with hardcoded deployer
@pytest.mark.pre_alloc_group(
    "separate", reason="Deploys beacon root contract using actual hardcoded deployer address"
)
def test_beacon_root_contract_deployment():
    """Test beacon root contract deployment with the official deployer address."""
    # This test uses the actual beacon root deployer address (e.g., 0x4242...4242)
    # which could conflict with dynamically allocated addresses in other tests
    pass


# Example 2: Test with custom consolidation contract
@pytest.mark.pre_alloc_group(
    "custom_consolidation", reason="Deploys custom consolidation contract with different bytecode"
)
def test_custom_consolidation_contract():
    """Test that deploys a modified consolidation contract."""
    # This test deploys a consolidation contract with custom bytecode that differs
    # from the standard implementation, requiring isolation from other consolidation tests
    pass


# Example 3: Group related tests that need custom contracts
@pytest.mark.pre_alloc_group(
    "custom_consolidation", reason="Uses same custom consolidation contract setup"
)
def test_custom_consolidation_edge_cases():
    """Test edge cases with the custom consolidation contract."""
    # This test can share the pre-allocation with test_custom_consolidation_contract
    # since they both use the same custom contract setup
    pass


# Example 4: Test without marker - uses default grouping
def test_normal_consolidation():
    """Test that uses standard consolidation contract and default grouping."""
    # This test uses dynamic allocation and standard contracts,
    # so it can be grouped normally with other tests
    pass
