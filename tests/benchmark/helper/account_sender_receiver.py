"""Deterministic benchmark sender and receiver accounts."""

import itertools
from typing import Generator

from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    Address,
    compute_create2_address,
    compute_create_address,
    keccak256,
)

# Deterministic sender pool, pre-funded via system-contract withdrawals
# (funding.txt) during payload generation. Kept out of the pre-allocation so
# the accounts stay uncached.
SENDER_BASE_KEY = int.from_bytes(
    keccak256(b"gas-repricings-private-key"), "big"
)

# Deterministic EIP-7702 delegate authorities:
# Authority i delegates to EXISTING_CONTRACT_DIFF receiver i.
DELEGATE_BASE_KEY = int.from_bytes(
    keccak256(b"gas-repricings-7702-delegate"), "big"
)

# Bittrex controller mainnet address: it created 1.5M contracts via CREATE with
# deterministic addresses, none self-destructed. Used as existing-contract
# receivers.
BITTREX_CONTROLLER_ADDRESS = Address(
    0xA3C1E324CA1CE40DB73ED6026C4A177F099B5770
)


def yield_distinct_sender() -> Generator[EOA, None, None]:
    """Yield deterministic sender EOAs pre-funded on-chain."""
    for i in itertools.count(0):
        yield EOA(key=SENDER_BASE_KEY + i)


def yield_distinct_create2_receiver(
    initcode: bytes,
) -> Generator[Address, None, None]:
    """Yield addresses deployed by the deterministic CREATE2 factory."""
    for salt in itertools.count(0):
        yield compute_create2_address(
            address=DETERMINISTIC_FACTORY_ADDRESS,
            salt=salt,
            initcode=initcode,
        )


def yield_distinct_contract_receiver() -> Generator[Address, None, None]:
    """Yield contracts created by the Bittrex controller via CREATE."""
    for nonce in itertools.count(2):
        yield compute_create_address(
            address=BITTREX_CONTROLLER_ADDRESS, nonce=nonce
        )


def yield_distinct_existent_receiver() -> Generator[Address, None, None]:
    """
    Yield existing balance-only EOAs on bloatnet, pre-funded by Spamoor
    (https://github.com/CPerezz/spamoor/pull/12).
    """
    for address in itertools.count(0x1000):
        yield Address(address)


def yield_distinct_nonexistent_receiver() -> Generator[Address, None, None]:
    """Yield non-existent accounts starting from keccak256('random')."""
    for address in itertools.count(0xF3CF193BB4AF1022AF7D2089F37D8BAE7157B85F):
        yield Address(address)


def yield_distinct_delegate_receiver() -> Generator[Address, None, None]:
    """Yield EOA that delegates to distinct EXISTING_CONTRACT_DIFF receiver."""
    for i in itertools.count(0):
        yield EOA(key=DELEGATE_BASE_KEY + i)
