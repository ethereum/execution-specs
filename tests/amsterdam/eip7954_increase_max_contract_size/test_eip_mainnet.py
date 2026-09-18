"""
Mainnet tests for
[EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).
"""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
    keccak256,
)

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = [pytest.mark.valid_at("EIP7954"), pytest.mark.mainnet]


def test_over_max_code_size_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify deployment above the new limit is rejected on mainnet.

    The transaction is funded for a successful deposit of this size, so
    the size rule is the only thing that makes it fail. With the capped
    gas limit alone the deposit ran out of state gas first, and raising
    the limit did not change the outcome.
    """
    deploy_code = Op.JUMPDEST * (fork.max_code_size() + 1)
    initcode = Initcode(deploy_code=deploy_code)

    alice = pre.fund_eoa()
    create_address = compute_create_address(address=alice, nonce=0)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        contract_creation=True,
    )
    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=(
            intrinsic_gas
            + top_frame_state_gas
            + initcode.evm_gas(fork)
            + initcode.deployment_gas(fork)
        ),
    )
    # The oversized deposit halts the frame: the whole execution
    # allowance burns while the state gas reservoir is handed back.
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    tx.expected_receipt = TransactionReceipt(cumulative_gas_used=gas_limit_cap)

    post: dict[Any, Account | None] = {
        create_address: Account.NONEXISTENT,
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.inclusion_test
@pytest.mark.exception_test
def test_over_max_initcode_size_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify a CREATE transaction over the new initcode limit is rejected."""
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=fork.max_initcode_size() + 1,
    )

    alice = pre.fund_eoa()
    create_address = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
        error=TransactionException.INITCODE_SIZE_EXCEEDED,
    )

    post: dict[Any, Account | None] = {
        create_address: Account.NONEXISTENT,
    }

    state_test(pre=pre, tx=tx, post=post)


def test_max_code_size_with_max_initcode_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    max_code_size_contract: tuple,
) -> None:
    """
    Verify max-size contract works on mainnet.

    Calls the deterministic max-size contract which checks EXTCODESIZE,
    EXTCODEHASH, and EXTCODECOPY on itself. The contract bytecode is
    the same used for deployment tests, padded to max code size.
    """
    target, target_code = max_code_size_contract

    alice = pre.fund_eoa()

    tx = Transaction(
        sender=alice,
        to=target,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post = {
        target: Account(
            storage={
                0: len(target_code),
                1: keccak256(bytes(target_code)),
                2: keccak256(bytes(target_code)),
            }
        )
    }

    state_test(pre=pre, tx=tx, post=post)
