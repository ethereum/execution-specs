"""Deterministic benchmark sender and receiver accounts."""

import itertools
from collections.abc import Hashable
from typing import Generator

from execution_testing import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    Address,
    Alloc,
    Hash,
    compute_create2_address,
    compute_create_address,
    keccak256,
)

from tests.benchmark.helper.account_verification import (
    AccountExpectation,
    register_target_range,
)
from tests.prague.eip7702_set_code_tx.spec import Spec

# Deterministic sender pool, pre-funded via system-contract withdrawals
# (funding.txt) during payload generation. Kept out of the pre-allocation so
# the accounts stay uncached.
SENDER_BASE_KEY = int.from_bytes(
    keccak256(b"gas-repricings-private-key"), "big"
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


def delegate_base_key(code_size: int) -> int:
    """
    Return the key base of the delegate authorities for *code_size*.

    Authority i delegates to the EXISTING_CONTRACT_DIFF_MAX receiver i
    deployed at *code_size*; each code size needs its own range because
    an authority can only carry one delegation.
    """
    return int.from_bytes(
        keccak256(b"gas-repricings-7702-delegate" + Hash(code_size)), "big"
    )


def yield_distinct_delegate_receiver(
    code_size: int,
) -> Generator[Address, None, None]:
    """Yield EOA delegating to a distinct EXISTING_CONTRACT_DIFF_MAX."""
    base_key = delegate_base_key(code_size)
    for i in itertools.count(0):
        yield EOA(key=base_key + i)


def expected_delegation() -> AccountExpectation:
    """
    Expected shape of a 7702-delegated authority.

    Only asserts the account carries a delegation designator; the delegate
    target it points to is not checked.
    """
    return AccountExpectation(code_prefix=bytes(Spec.DELEGATION_DESIGNATION))


def register_bittrex_targets(
    pre: Alloc,
    count: int,
    *,
    verified_accounts: dict[Hashable, int],
) -> None:
    """Register the first *count* Bittrex CREATE contract receivers."""
    register_target_range(
        pre,
        key="bittrex_contract",
        count=count,
        expectation=AccountExpectation(is_contract=True),
        address_of=lambda index: Address(
            compute_create_address(
                address=BITTREX_CONTROLLER_ADDRESS, nonce=2 + index
            ),
            label="diff_to_contract",
        ),
        verified_accounts=verified_accounts,
    )


def register_delegate_targets(
    pre: Alloc,
    count: int,
    *,
    code_size: int,
    verified_accounts: dict[Hashable, int],
) -> None:
    """Register the first *count* delegated authorities (7702 designator)."""
    base_key = delegate_base_key(code_size)
    register_target_range(
        pre,
        key=("delegate_authority", code_size),
        count=count,
        expectation=expected_delegation(),
        address_of=lambda index: Address(
            EOA(key=base_key + index), label="delegate_authority"
        ),
        verified_accounts=verified_accounts,
    )
