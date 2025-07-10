"""
abstract: Tests [EIP-7825 Transaction Gas Limit Cap](https://eips.ethereum.org/EIPS/eip-7825)
    Test cases for [EIP-7825 Transaction Gas Limit Cap](https://eips.ethereum.org/EIPS/eip-7825)].
"""

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
)
from ethereum_test_tools.utility.pytest import ParameterSet
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7825.md"
REFERENCE_SPEC_VERSION = "47cbfed315988c0bd4d10002c110ae402504cd94"

TX_GAS_LIMIT = 2**24  # 16,777,216
BLOB_COMMITMENT_VERSION_KZG = 1


def tx_gas_limit_cap_tests(fork: Fork) -> List[ParameterSet]:
    """
    Return a list of tests for transaction gas limit cap parametrized for each different
    fork.
    """
    fork_tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    if fork_tx_gas_limit_cap is None:
        # Use a default value for forks that don't have a transaction gas limit cap
        return [
            pytest.param(TX_GAS_LIMIT + 1, None, id="tx_gas_limit_cap_none"),
        ]

    return [
        pytest.param(
            fork_tx_gas_limit_cap + 1,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
            id="tx_gas_limit_cap_exceeds_maximum",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(fork_tx_gas_limit_cap, None, id="tx_gas_limit_cap_none"),
    ]


@pytest.mark.parametrize_by_fork("tx_gas_limit,error", tx_gas_limit_cap_tests)
@pytest.mark.with_all_tx_types
@pytest.mark.valid_from("Prague")
def test_transaction_gas_limit_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    error: TransactionException | None,
    tx_type: int,
):
    """Test the transaction gas limit cap behavior for all transaction types."""
    env = Environment()

    sender = pre.fund_eoa()
    storage = Storage()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
    )

    tx_kwargs = {
        "ty": tx_type,
        "to": contract_address,
        "gas_limit": tx_gas_limit,
        "data": b"",
        "value": 0,
        "sender": sender,
        "error": error,
    }

    # Add extra required fields based on transaction type
    if tx_type >= 1:
        # Type 1: EIP-2930 Access List Transaction
        tx_kwargs["access_list"] = [
            {
                "address": contract_address,
                "storage_keys": [0],
            }
        ]
    if tx_type == 3:
        # Type 3: EIP-4844 Blob Transaction
        tx_kwargs["max_fee_per_blob_gas"] = fork.min_base_fee_per_blob_gas()
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version([0], BLOB_COMMITMENT_VERSION_KZG)
    elif tx_type == 4:
        # Type 4: EIP-7702 Set Code Transaction
        signer = pre.fund_eoa(amount=0)
        tx_kwargs["authorization_list"] = [
            AuthorizationTuple(
                signer=signer,
                address=Address(0),
                nonce=0,
            )
        ]

    tx = Transaction(**tx_kwargs)
    post = {contract_address: Account(storage=storage if error is None else {})}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_at_transition_to("Osaka", subsequent_forks=True)
@pytest.mark.exception_test
def test_transaction_gas_limit_cap_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """
    Test transaction gas limit cap behavior at the Osaka transition.

    Before timestamp 15000: No gas limit cap (transactions with gas > 2^24 are valid)
    At/after timestamp 15000: Gas limit cap of 2^24 is enforced
    """
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1)) + Op.STOP,
    )

    pre_cap = fork.transaction_gas_limit_cap()
    if pre_cap is None:
        pre_cap = TX_GAS_LIMIT

    # Transaction with gas limit above the cap before transition
    high_gas_tx = Transaction(
        ty=0,  # Legacy transaction
        to=contract_address,
        gas_limit=pre_cap + 1,
        data=b"",
        value=0,
        sender=sender,
    )

    post_cap = fork.transaction_gas_limit_cap(timestamp=15_000)
    post_cap_tx_error = TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM

    assert post_cap is not None, "Post cap should not be None"
    assert post_cap <= pre_cap, (
        "Post cap should be less than or equal to pre cap, test needs update"
    )

    # Transaction with gas limit at the cap
    cap_gas_tx = Transaction(
        ty=0,  # Legacy transaction
        to=contract_address,
        gas_limit=post_cap + 1,
        data=b"",
        value=0,
        sender=sender,
        error=post_cap_tx_error,
    )

    blocks = []

    # Before transition (timestamp < 15000): high gas transaction should succeed
    blocks.append(
        Block(
            timestamp=14_999,
            txs=[high_gas_tx],
        )
    )

    # At transition (timestamp = 15000): high gas transaction should fail
    blocks.append(
        Block(
            timestamp=15_000,
            txs=[cap_gas_tx],  # Only transaction at the cap succeeds
            exception=post_cap_tx_error,
        )
    )

    # Post state: storage should be updated by successful transactions
    post = {
        contract_address: Account(
            storage={
                0: 1,  # Set by first transaction (before transition)
            }
        )
    }

    blockchain_test(pre=pre, blocks=blocks, post=post)
