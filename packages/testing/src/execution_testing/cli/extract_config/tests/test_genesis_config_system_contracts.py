"""Tests for `GenesisConfig`'s system contract mechanism."""

from typing import ClassVar, Dict, Set

from execution_testing.base_types import Address
from execution_testing.cli.pytest_commands.plugins.execute.eth_config.execute_types import (  # noqa: E501
    ForkActivationTimes,
    GenesisConfig,
)
from execution_testing.forks import Berlin, Fork, Prague

from ..exportable_genesis import GenesisConfigSystemContracts

DEPOSIT_CONTRACT_ADDRESS = Address(0x00000000219AB540356CBB839CBE05303D7705FA)
WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS = Address(
    0x00000961EF480EB55E80D19AD83579A64C007002
)


class _ClientGenesisConfig(GenesisConfigSystemContracts):
    """A stand-in client config."""

    _EXCLUDED_SYSTEM_CONTRACT_LABELS: ClassVar[Set[str]] = {
        "DEPOSIT_CONTRACT_ADDRESS"
    }
    _SYSTEM_CONTRACT_KEY_OVERRIDES: ClassVar[Dict[str, str]] = {
        "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS": "withdrawalAddress"
    }


def _config(
    fork: Fork, **overrides: Dict[str, Address]
) -> GenesisConfigSystemContracts:
    """Build a minimal `GenesisConfig` with `fork` active at genesis."""
    return GenesisConfigSystemContracts(
        chain_id=1,
        terminal_total_difficulty=0,
        terminal_total_difficulty_passed=True,
        fork_activation_times=ForkActivationTimes(root={fork: 0}),
        blob_schedule={},
        **overrides,
    )


def test_system_contracts_default_to_each_contracts_own_address() -> None:
    """Contracts are keyed by camelCase label, using each own address."""
    contracts = _config(Prague).system_contracts
    assert contracts["depositContractAddress"] == DEPOSIT_CONTRACT_ADDRESS
    assert (
        contracts["withdrawalRequestPredeployAddress"]
        == WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS
    )


def test_system_contracts_empty_before_the_defining_fork() -> None:
    """A fork before EIP-6110/7002/7251 defines no system contracts."""
    assert _config(Berlin).system_contracts == {}


def test_subclass_can_exclude_and_override_system_contract_keys() -> None:
    """A subclass's exclude/override class vars apply to its contracts."""
    contracts = _ClientGenesisConfig(
        chain_id=1,
        terminal_total_difficulty=0,
        terminal_total_difficulty_passed=True,
        fork_activation_times=ForkActivationTimes(root={Prague: 0}),
        blob_schedule={},
    ).system_contracts
    assert "depositContractAddress" not in contracts
    assert (
        contracts["withdrawalAddress"] == WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS
    )


def test_system_contract_override_is_reflected_in_system_contracts() -> None:
    """One override replaces its own contract's address, not others'."""
    override = Address(0x1234567890123456789012345678901234567890)
    contracts = _config(
        Prague,
        system_contract_overrides={"DEPOSIT_CONTRACT_ADDRESS": override},
    ).system_contracts
    assert contracts["depositContractAddress"] == override
    assert (
        contracts["withdrawalRequestPredeployAddress"]
        == WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS
    )


def test_address_overrides_only_lists_contracts_that_actually_changed() -> (
    None
):
    """Only overridden contracts appear, mapped default -> override."""
    override = Address(0x1234567890123456789012345678901234567890)
    config = _config(
        Prague,
        system_contract_overrides={"DEPOSIT_CONTRACT_ADDRESS": override},
    )
    assert config.address_overrides.root == {
        DEPOSIT_CONTRACT_ADDRESS: override
    }


def test_override_matching_the_default_produces_no_address_override() -> None:
    """An override equal to the default produces no address override."""
    config = _config(
        Prague,
        system_contract_overrides={
            "DEPOSIT_CONTRACT_ADDRESS": DEPOSIT_CONTRACT_ADDRESS
        },
    )
    assert config.address_overrides.root == {}


def test_deposit_contract_address_key_parses_into_override() -> None:
    """A `depositContractAddress` root key parses into an override."""
    override = "0x1234567890123456789012345678901234567890"
    config = GenesisConfig.model_validate(
        {
            "chainId": 1,
            "terminalTotalDifficulty": 0,
            "terminalTotalDifficultyPassed": True,
            "pragueTime": 0,
            "blobSchedule": {},
            "depositContractAddress": override,
        }
    )
    assert config.system_contract_overrides == {
        "DEPOSIT_CONTRACT_ADDRESS": Address(override)
    }
