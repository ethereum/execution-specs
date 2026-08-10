"""Gas helpers for Amsterdam EIP-8025 tests."""

from execution_testing import Fork, RecipientType


def empty_account_value_transfer_gas_limit(fork: Fork) -> int:
    """Return the gas needed to transfer value to an empty account."""
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=True,
        recipient_type=RecipientType.EMPTY_ACCOUNT,
    )
    return intrinsic_gas + top_frame_state_gas
